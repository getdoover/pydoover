"""Integration tests for pydoover.api.

These tests run against a live Doover Data API. Set the following
environment variables before running:

    DOOVER_API_URL        – e.g. https://data.doover.com/api
    DOOVER_TOKEN          – a valid JWT bearer token
                            (or set DOOVER_CLIENT_ID + DOOVER_CLIENT_SECRET)
    DOOVER_CLIENT_ID      – OAuth2 client ID (for token refresh tests)
    DOOVER_CLIENT_SECRET  – OAuth2 client secret
    DOOVER_AGENT_ID       – agent ID to use for testing
    DOOVER_ORG_ID         – (optional) organisation ID

Run with:
    uv run pytest tests/test_api.py -v
"""

import os

import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.models.exceptions import NotFoundError
from pydoover.models import Aggregate, Channel, Message
from pydoover.models.alarm import Alarm, AlarmOperator

# ── env helpers ────────────────────────────────────────────────────────────

API_URL = os.environ.get("DOOVER_API_URL", "")
TOKEN = os.environ.get("DOOVER_TOKEN", "")
CLIENT_ID = os.environ.get("DOOVER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("DOOVER_CLIENT_SECRET", "")
AGENT_ID = os.environ.get("DOOVER_AGENT_ID", "")
ORG_ID = os.environ.get("DOOVER_ORG_ID")

TEST_CHANNEL = "pydoover_test_channel"

skip_no_env = pytest.mark.skipif(
    not (API_URL and (TOKEN or (CLIENT_ID and CLIENT_SECRET)) and AGENT_ID),
    reason="DOOVER_API_URL, DOOVER_TOKEN/DOOVER_CLIENT_ID+SECRET, and DOOVER_AGENT_ID required",
)


def _make_sync_client(**overrides) -> DataClient:
    kwargs = {
        "base_url": API_URL,
        "organisation_id": ORG_ID,
    }
    if TOKEN:
        kwargs["token"] = TOKEN
    if CLIENT_ID:
        kwargs["client_id"] = CLIENT_ID
        kwargs["client_secret"] = CLIENT_SECRET
    kwargs.update(overrides)
    return DataClient(**kwargs)


def _make_async_client(**overrides) -> AsyncDataClient:
    kwargs = {
        "base_url": API_URL,
        "organisation_id": ORG_ID,
    }
    if TOKEN:
        kwargs["token"] = TOKEN
    if CLIENT_ID:
        kwargs["client_id"] = CLIENT_ID
        kwargs["client_secret"] = CLIENT_SECRET
    kwargs.update(overrides)
    return AsyncDataClient(**kwargs)


# ── Sync client tests ─────────────────────────────────────────────────────


@skip_no_env
class TestDataClientSync:
    def test_get_channel(self):
        with _make_sync_client() as client:
            channel = client.fetch_channel(AGENT_ID, TEST_CHANNEL)
            assert isinstance(channel, Channel)
            assert channel.name == TEST_CHANNEL

    def test_list_channels(self):
        with _make_sync_client() as client:
            channels = client.list_channels(AGENT_ID)
            assert isinstance(channels, list)
            assert all(isinstance(c, Channel) for c in channels)

    def test_create_and_list_messages(self):
        with _make_sync_client() as client:
            msg = client.create_message(
                AGENT_ID,
                TEST_CHANNEL,
                data={"test": True, "source": "pydoover_integration_test"},
            )
            assert isinstance(msg, Message)
            assert msg.data["test"] is True

            messages = client.list_messages(AGENT_ID, TEST_CHANNEL, limit=5)
            assert isinstance(messages, list)
            assert len(messages) > 0
            assert any(str(m.id) == str(msg.id) for m in messages)

    def test_get_message(self):
        with _make_sync_client() as client:
            msg = client.create_message(
                AGENT_ID,
                TEST_CHANNEL,
                data={"get_test": True},
            )
            fetched = client.fetch_message(AGENT_ID, TEST_CHANNEL, msg.id)
            assert isinstance(fetched, Message)
            assert str(fetched.id) == str(msg.id)

    def test_update_message(self):
        with _make_sync_client() as client:
            msg = client.create_message(
                AGENT_ID,
                TEST_CHANNEL,
                data={"version": 1},
            )
            client.update_message(
                AGENT_ID,
                TEST_CHANNEL,
                msg.id,
                data={"version": 2},
                replace=True,
            )
            fetched = client.fetch_message(AGENT_ID, TEST_CHANNEL, msg.id)
            assert fetched.data["version"] == 2

    def test_update_and_get_aggregate(self):
        with _make_sync_client() as client:
            client.update_aggregate(
                AGENT_ID,
                TEST_CHANNEL,
                data={"agg_test": "hello"},
                replace=False,
            )
            agg = client.get_aggregate(AGENT_ID, TEST_CHANNEL)
            assert isinstance(agg, Aggregate)
            assert agg.data.get("agg_test") == "hello"

    def test_alarm_lifecycle(self):
        with _make_sync_client() as client:
            alarm = client.create_alarm(
                AGENT_ID,
                TEST_CHANNEL,
                name="test_alarm",
                key="agg_test",
                operator=AlarmOperator.gt,
                value=100,
                description="integration test alarm",
            )
            assert isinstance(alarm, Alarm)
            assert alarm.name == "test_alarm"

            alarms = client.list_alarms(AGENT_ID, TEST_CHANNEL)
            assert any(a.id == alarm.id for a in alarms)

            updated = client.update_alarm(
                AGENT_ID,
                TEST_CHANNEL,
                alarm.id,
                description="updated description",
            )
            assert updated.description == "updated description"

            client.delete_alarm(AGENT_ID, TEST_CHANNEL, alarm.id)
            alarms = client.list_alarms(AGENT_ID, TEST_CHANNEL)
            assert not any(a.id == alarm.id for a in alarms)

    def test_delete_message(self):
        with _make_sync_client() as client:
            msg = client.create_message(
                AGENT_ID,
                TEST_CHANNEL,
                data={"to_delete": True},
            )
            client.delete_message(AGENT_ID, TEST_CHANNEL, msg.id)
            with pytest.raises(NotFoundError):
                client.fetch_message(AGENT_ID, TEST_CHANNEL, msg.id)

    def test_timeseries(self):
        with _make_sync_client() as client:
            # Ensure we have a message with a known field
            client.create_message(
                AGENT_ID,
                TEST_CHANNEL,
                data={"temperature": 22.5},
            )
            result = client.fetch_timeseries(
                AGENT_ID,
                TEST_CHANNEL,
                field_names=["temperature"],
                limit=10,
            )
            assert "results" in result
            assert "count" in result


# ── Async client tests ────────────────────────────────────────────────────


@skip_no_env
class TestDataClientAsync:
    @pytest.mark.asyncio
    async def test_get_channel(self):
        async with _make_async_client() as client:
            channel = await client.fetch_channel(AGENT_ID, TEST_CHANNEL)
            assert isinstance(channel, Channel)
            assert channel.name == TEST_CHANNEL

    @pytest.mark.asyncio
    async def test_list_channels(self):
        async with _make_async_client() as client:
            channels = await client.list_channels(AGENT_ID)
            assert isinstance(channels, list)
            assert all(isinstance(c, Channel) for c in channels)

    @pytest.mark.asyncio
    async def test_create_and_list_messages(self):
        async with _make_async_client() as client:
            msg = await client.create_message(
                AGENT_ID,
                TEST_CHANNEL,
                data={"test": True, "source": "pydoover_async_integration_test"},
            )
            assert isinstance(msg, Message)

            messages = await client.list_messages(AGENT_ID, TEST_CHANNEL, limit=5)
            assert isinstance(messages, list)
            assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_update_and_get_aggregate(self):
        async with _make_async_client() as client:
            await client.update_aggregate(
                AGENT_ID,
                TEST_CHANNEL,
                data={"async_agg_test": "world"},
                replace=False,
            )
            agg = await client.get_aggregate(AGENT_ID, TEST_CHANNEL)
            assert isinstance(agg, Aggregate)
            assert agg.data.get("async_agg_test") == "world"

    @pytest.mark.asyncio
    async def test_alarm_lifecycle(self):
        async with _make_async_client() as client:
            alarm = await client.create_alarm(
                AGENT_ID,
                TEST_CHANNEL,
                name="async_test_alarm",
                key="async_agg_test",
                operator="gt",
                value=50,
            )
            assert isinstance(alarm, Alarm)

            fetched = await client.fetch_alarm(AGENT_ID, TEST_CHANNEL, alarm.id)
            assert fetched.id == alarm.id

            await client.delete_alarm(AGENT_ID, TEST_CHANNEL, alarm.id)


# ── Token refresh tests ───────────────────────────────────────────────────

skip_no_credentials = pytest.mark.skipif(
    not (API_URL and CLIENT_ID and CLIENT_SECRET and AGENT_ID),
    reason="DOOVER_API_URL, DOOVER_CLIENT_ID, DOOVER_CLIENT_SECRET, and DOOVER_AGENT_ID required",
)


@skip_no_credentials
class TestTokenRefresh:
    def test_sync_client_refreshes_token(self):
        """Client with only client credentials (no token) should auto-fetch one."""
        client = DataClient(
            base_url=API_URL,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            organisation_id=ORG_ID,
        )
        with client:
            assert client.token is None
            # This should trigger a token refresh
            channel = client.fetch_channel(AGENT_ID, TEST_CHANNEL)
            assert isinstance(channel, Channel)
            assert client.token is not None

    @pytest.mark.asyncio
    async def test_async_client_refreshes_token(self):
        """Async client with only client credentials should auto-fetch a token."""
        async with AsyncDataClient(
            base_url=API_URL,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            organisation_id=ORG_ID,
        ) as client:
            assert client.token is None
            channel = await client.fetch_channel(AGENT_ID, TEST_CHANNEL)
            assert isinstance(channel, Channel)
            assert client.token is not None
