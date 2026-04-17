"""Tests for DeviceAgentInterface gRPC error handling and Aggregate return types.

These tests mock the gRPC layer (make_request / process_response) to verify that:
- fetch_channel_aggregate returns Aggregate objects
- gRPC error codes are mapped to the correct exceptions
- The aggregate cache stores and returns Aggregate objects
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct

from pydoover.models.data import Aggregate
from pydoover.models.generated.device_agent import device_agent_pb2
from pydoover.models.data.exceptions import DooverAPIError, HTTPError, NotFoundError
from pydoover.docker.device_agent import DeviceAgentInterface, MockDeviceAgentInterface


# ── helpers ──────────────────────────────────────────────────────────────


def _make_response_header(success=True, code=200, message=None):
    return device_agent_pb2.ResponseHeader(
        success=success,
        cloud_synced=True,
        cloud_ready=True,
        response_code=code,
        response_message=message,
    )


def _make_aggregate_proto(data: dict):
    s = Struct()
    json_format.ParseDict(data, s)
    return device_agent_pb2.Aggregate(data=s, attachments=[], last_updated=0)


def _make_get_aggregate_response(data: dict, success=True, code=200, message=None):
    return device_agent_pb2.GetAggregateResponse(
        response_header=_make_response_header(success, code, message),
        aggregate=_make_aggregate_proto(data),
    )


def _make_create_message_response(message_id=1, success=True, code=200, message=None):
    return device_agent_pb2.CreateMessageResponse(
        response_header=_make_response_header(success, code, message),
        message_id=message_id,
    )


def _make_update_channel_aggregate_response(
    data: dict, success=True, code=200, message=None
):
    return device_agent_pb2.UpdateAggregateResponse(
        response_header=_make_response_header(success, code, message),
        aggregate=_make_aggregate_proto(data),
    )


# ── process_response error mapping ──────────────────────────────────────


class TestProcessResponse:
    """Verify GRPCInterface.process_response maps response codes to exceptions."""

    def setup_method(self):
        self.iface = DeviceAgentInterface(app_key="test", dda_uri="localhost:50051")

    def test_success_returns_response(self):
        resp = _make_get_aggregate_response({"key": "value"})
        result = self.iface.process_response("GetAggregate", resp)
        assert result is resp

    def test_404_raises_not_found(self):
        resp = _make_get_aggregate_response(
            {}, success=False, code=404, message="Channel not found"
        )
        with pytest.raises(NotFoundError, match="Channel not found"):
            self.iface.process_response("GetAggregate", resp)

    def test_400_raises_http_error(self):
        resp = _make_get_aggregate_response(
            {}, success=False, code=400, message="Bad request"
        )
        with pytest.raises(HTTPError, match="Bad request") as exc_info:
            self.iface.process_response("GetAggregate", resp)
        assert exc_info.value.status == 400

    def test_500_raises_http_error(self):
        resp = _make_get_aggregate_response(
            {}, success=False, code=500, message="Internal error"
        )
        with pytest.raises(HTTPError) as exc_info:
            self.iface.process_response("GetAggregate", resp)
        assert exc_info.value.status == 500

    def test_none_response_raises_api_error(self):
        with pytest.raises(DooverAPIError, match="Empty response"):
            self.iface.process_response("GetAggregate", None)

    def test_failure_without_code_defaults_to_500(self):
        resp = _make_get_aggregate_response({}, success=False, code=0, message="fail")
        with pytest.raises(HTTPError) as exc_info:
            self.iface.process_response("GetAggregate", resp)
        assert exc_info.value.status == 500


# ── fetch_channel_aggregate ─────────────────────────────────────────────


class TestFetchChannelAggregate:
    def setup_method(self):
        self.dda = DeviceAgentInterface(app_key="test", dda_uri="localhost:50051")

    @pytest.mark.asyncio
    async def test_returns_aggregate_from_grpc(self):
        resp = _make_get_aggregate_response({"temperature": 22.5})
        self.dda.make_request = AsyncMock(return_value=resp)

        result = await self.dda.fetch_channel_aggregate("sensor_data")

        assert isinstance(result, Aggregate)
        assert result.data == {"temperature": 22.5}

    @pytest.mark.asyncio
    async def test_returns_aggregate_from_cache(self):
        cached = Aggregate(data={"cached": True}, attachments=[], last_updated=None)
        self.dda._aggregates["my_channel"] = cached

        result = await self.dda.fetch_channel_aggregate("my_channel")

        assert isinstance(result, Aggregate)
        assert result.data == {"cached": True}
        # Should be a deep copy, not the same object
        assert result is not cached

    @pytest.mark.asyncio
    async def test_cache_returns_deep_copy(self):
        cached = Aggregate(data={"nested": {"a": 1}}, attachments=[], last_updated=None)
        self.dda._aggregates["ch"] = cached

        result = await self.dda.fetch_channel_aggregate("ch")
        result.data["nested"]["a"] = 999

        # Original cache should be unmodified
        assert self.dda._aggregates["ch"].data["nested"]["a"] == 1

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_channel(self):
        _make_get_aggregate_response(
            {}, success=False, code=404, message="Channel not found"
        )
        self.dda.make_request = AsyncMock(
            side_effect=NotFoundError("Channel not found")
        )

        with pytest.raises(NotFoundError):
            await self.dda.fetch_channel_aggregate("nonexistent")

    @pytest.mark.asyncio
    async def test_raises_api_error_on_grpc_failure(self):
        self.dda.make_request = AsyncMock(
            side_effect=DooverAPIError("gRPC request failed")
        )

        with pytest.raises(DooverAPIError):
            await self.dda.fetch_channel_aggregate("broken_channel")


# ── create_message ──────────────────────────────────────────────────────


class TestCreateMessage:
    def setup_method(self):
        self.dda = DeviceAgentInterface(app_key="test", dda_uri="localhost:50051")

    @pytest.mark.asyncio
    async def test_returns_message_id(self):
        resp = _make_create_message_response(message_id=42)
        self.dda.make_request = AsyncMock(return_value=resp)

        result = await self.dda.create_message("ch", {"hello": "world"})
        assert result == 42

    @pytest.mark.asyncio
    async def test_raises_not_found(self):
        self.dda.make_request = AsyncMock(
            side_effect=NotFoundError("Channel not found")
        )

        with pytest.raises(NotFoundError):
            await self.dda.create_message("nonexistent", {"data": 1})

    @pytest.mark.asyncio
    async def test_raises_on_server_error(self):
        self.dda.make_request = AsyncMock(side_effect=HTTPError(500, "Internal error"))

        with pytest.raises(HTTPError) as exc_info:
            await self.dda.create_message("ch", {"data": 1})
        assert exc_info.value.status == 500


# ── update_channel_aggregate ────────────────────────────────────────────────────


class TestUpdateAggregate:
    def setup_method(self):
        self.dda = DeviceAgentInterface(app_key="test", dda_uri="localhost:50051")

    @pytest.mark.asyncio
    async def test_returns_aggregate(self):
        resp = _make_update_channel_aggregate_response({"updated": True})
        self.dda.make_request = AsyncMock(return_value=resp)

        result = await self.dda.update_channel_aggregate("ch", {"updated": True})
        assert isinstance(result, Aggregate)
        assert result.data == {"updated": True}

    @pytest.mark.asyncio
    async def test_raises_not_found(self):
        self.dda.make_request = AsyncMock(
            side_effect=NotFoundError("Channel not found")
        )

        with pytest.raises(NotFoundError):
            await self.dda.update_channel_aggregate("nonexistent", {"data": 1})


# ── MockDeviceAgentInterface ─────────────────────────────────────────────────────


class TestMockDeviceAgentInterface:
    def setup_method(self):
        self.mock = MockDeviceAgentInterface(app_key="test", dda_uri="localhost:50051")

    @pytest.mark.asyncio
    async def test_fetch_returns_aggregate(self):
        self.mock._aggregates["my_ch"] = Aggregate(
            data={"status": "ok"}, attachments=[], last_updated=None
        )

        result = await self.mock.fetch_channel_aggregate("my_ch")
        assert isinstance(result, Aggregate)
        assert result.data == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_fetch_empty_channel_returns_aggregate(self):
        result = await self.mock.fetch_channel_aggregate("empty")
        assert isinstance(result, Aggregate)
        assert result.data == {}

    @pytest.mark.asyncio
    async def test_update_channel_aggregate_returns_aggregate(self):
        result = await self.mock.update_channel_aggregate("ch", {"key": "val"})
        assert isinstance(result, Aggregate)
        assert result.data == {"key": "val"}

    @pytest.mark.asyncio
    async def test_update_channel_aggregate_merges_data(self):
        self.mock._aggregates["ch"] = Aggregate(
            data={"a": 1}, attachments=[], last_updated=None
        )
        await self.mock.update_channel_aggregate("ch", {"b": 2})

        result = await self.mock.fetch_channel_aggregate("ch")
        assert result.data == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_update_channel_aggregate_updates_cache(self):
        await self.mock.update_channel_aggregate("ch", {"x": 1})
        assert "ch" in self.mock._aggregates
        assert isinstance(self.mock._aggregates["ch"], Aggregate)
        assert self.mock._aggregates["ch"].data == {"x": 1}

    @pytest.mark.asyncio
    async def test_wait_for_channels_sync_populates_cache(self):
        self.mock._aggregates["a"] = Aggregate(
            data={"val": 1}, attachments=[], last_updated=None
        )
        self.mock._aggregates["b"] = Aggregate(
            data={"val": 2}, attachments=[], last_updated=None
        )

        await self.mock.wait_for_channels_sync(["a", "b"])

        assert isinstance(self.mock._aggregates["a"], Aggregate)
        assert isinstance(self.mock._aggregates["b"], Aggregate)
        assert self.mock._aggregates["a"].data == {"val": 1}


# ── _run_channel_stream seeding ─────────────────────────────────────────


class TestRunChannelStreamSeeding:
    def setup_method(self):
        self.dda = DeviceAgentInterface(app_key="test", dda_uri="localhost:50051")
        # Stub out wait_until_healthy so it resolves immediately
        self.dda.wait_until_healthy = AsyncMock(return_value=True)
        # Stub out stream_channel_events so it yields nothing (we only test seeding)
        self.dda.stream_channel_events = MagicMock(return_value=_empty_async_gen())

    @pytest.mark.asyncio
    async def test_waits_for_healthy_before_fetching(self):
        """_run_channel_stream should wait for the DDA to be healthy first."""
        call_order = []

        async def mock_healthy(*a, **kw):
            call_order.append("healthy")
            return True

        async def mock_fetch(name):
            call_order.append("fetch")
            return Aggregate(data={}, attachments=[], last_updated=None)

        self.dda.wait_until_healthy = mock_healthy
        self.dda.fetch_channel_aggregate = mock_fetch

        with pytest.raises(asyncio.CancelledError):
            await self.dda._run_channel_stream("ch")

        assert call_order[0] == "healthy"
        assert call_order[1] == "fetch"

    @pytest.mark.asyncio
    async def test_seeds_cache_on_success(self):
        agg = Aggregate(data={"seeded": True}, attachments=[], last_updated=None)
        self.dda.fetch_channel_aggregate = AsyncMock(return_value=agg)

        with pytest.raises(asyncio.CancelledError):
            await self.dda._run_channel_stream("ch")

        assert isinstance(self.dda._aggregates["ch"], Aggregate)
        assert self.dda._aggregates["ch"].data == {"seeded": True}
        assert self.dda._synced_channels["ch"] is True

    @pytest.mark.asyncio
    async def test_creates_channel_on_not_found(self):
        """When fetch returns NotFoundError, should create channel with empty aggregate."""
        created_agg = Aggregate(data={}, attachments=[], last_updated=None)
        self.dda.fetch_channel_aggregate = AsyncMock(
            side_effect=NotFoundError("Channel not found")
        )
        self.dda.update_channel_aggregate = AsyncMock(return_value=created_agg)

        with pytest.raises(asyncio.CancelledError):
            await self.dda._run_channel_stream("new_ch")

        self.dda.update_channel_aggregate.assert_awaited_once_with("new_ch", {})
        assert isinstance(self.dda._aggregates["new_ch"], Aggregate)
        assert self.dda._synced_channels["new_ch"] is True

    @pytest.mark.asyncio
    async def test_marks_synced_even_if_create_fails(self):
        """If both fetch and create fail, channel should still be marked synced."""
        self.dda.fetch_channel_aggregate = AsyncMock(
            side_effect=NotFoundError("Channel not found")
        )
        self.dda.update_channel_aggregate = AsyncMock(
            side_effect=HTTPError(500, "Server error")
        )

        with pytest.raises(asyncio.CancelledError):
            await self.dda._run_channel_stream("broken_ch")

        assert self.dda._synced_channels["broken_ch"] is True
        assert "broken_ch" not in self.dda._aggregates

    @pytest.mark.asyncio
    async def test_marks_synced_on_other_errors(self):
        """Non-NotFound errors should still mark channel as synced."""
        self.dda.fetch_channel_aggregate = AsyncMock(
            side_effect=DooverAPIError("Connection failed")
        )

        with pytest.raises(asyncio.CancelledError):
            await self.dda._run_channel_stream("err_ch")

        assert self.dda._synced_channels["err_ch"] is True
        assert "err_ch" not in self.dda._aggregates


async def _empty_async_gen():
    # Raise CancelledError to break out of the retry loop in _run_channel_stream;
    # in production stream_channel_events only exits via cancellation.
    if False:
        yield
    raise asyncio.CancelledError
