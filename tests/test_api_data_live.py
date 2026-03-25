"""Live integration tests for pydoover.api.data.

These tests run against the user's local ``staging`` auth profile.

Run with:
    uv run pytest tests/test_api_data_live.py -v
"""

from datetime import datetime, timedelta, timezone
from typing import cast

import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.api.auth import AsyncDoover2AuthClient, Doover2AuthClient
from pydoover.api.auth._config import ConfigManager
from pydoover.models.data import Aggregate, Alarm, AlarmOperator, Channel, Message
from pydoover.models.data.exceptions import NotFoundError
from pydoover.models.data.timeseries import TimeseriesResponse


pytestmark = pytest.mark.live

DATA_PROFILE = "staging"
AGENT_ID = 160548444522423041
ORG_ID = 160537971806708483

TEST_CHANNEL = "pydoover_test_channel"

skip_no_profile = pytest.mark.skipif(
    ConfigManager().get(DATA_PROFILE) is None,
    reason=f"Doover auth profile {DATA_PROFILE!r} is required",
)


def _make_sync_client() -> DataClient:
    return DataClient(
        profile=DATA_PROFILE,
        organisation_id=ORG_ID,
    )


def _make_async_client() -> AsyncDataClient:
    return AsyncDataClient(
        profile=DATA_PROFILE,
        organisation_id=ORG_ID,
    )


# ── Sync client tests ─────────────────────────────────────────────────────


@skip_no_profile
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

            messages = client.list_messages(
                AGENT_ID,
                TEST_CHANNEL,
                after=int(msg.id) - 1,
                limit=5,
            )
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
            client.update_channel_aggregate(
                AGENT_ID,
                TEST_CHANNEL,
                data={"agg_test": "hello"},
                replace=False,
            )
            agg = client.fetch_channel_aggregate(AGENT_ID, TEST_CHANNEL)
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
            msg = client.create_message(
                AGENT_ID,
                TEST_CHANNEL,
                data={"temperature": 22.5},
            )
            result = client.fetch_timeseries(
                AGENT_ID,
                TEST_CHANNEL,
                field_names=["temperature"],
                after=int(msg.id) - 1,
                limit=10,
            )
            assert isinstance(result, TimeseriesResponse)
            assert result.count >= 1
            assert len(result.results) >= 1
            assert any(point.message_id == int(msg.id) for point in result.results)


# ── Async client tests ────────────────────────────────────────────────────


@skip_no_profile
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

            messages = await client.list_messages(
                AGENT_ID, TEST_CHANNEL, after=0, limit=5
            )
            assert isinstance(messages, list)
            assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_update_and_get_aggregate(self):
        async with _make_async_client() as client:
            await client.update_channel_aggregate(
                AGENT_ID,
                TEST_CHANNEL,
                data={"async_agg_test": "world"},
                replace=False,
            )
            agg = await client.fetch_channel_aggregate(AGENT_ID, TEST_CHANNEL)
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


@skip_no_profile
class TestTokenRefresh:
    def test_sync_client_refreshes_token(self):
        """Client with a staging profile should refresh when the token is cleared."""
        client = DataClient(
            profile=DATA_PROFILE,
            organisation_id=ORG_ID,
        )
        with client:
            auth = cast(Doover2AuthClient, client.auth)
            auth._set_access_token(
                "stale.token.value",
                token_expires=datetime.now(timezone.utc) - timedelta(minutes=5),
            )
            channel = client.fetch_channel(AGENT_ID, TEST_CHANNEL)
            assert isinstance(channel, Channel)
            assert client.token is not None

    @pytest.mark.asyncio
    async def test_async_client_refreshes_token(self):
        """Async staging-profile client should refresh when the token is cleared."""
        async with AsyncDataClient(
            profile=DATA_PROFILE,
            organisation_id=ORG_ID,
        ) as client:
            auth = cast(AsyncDoover2AuthClient, client.auth)
            auth._set_access_token(
                "stale.token.value",
                token_expires=datetime.now(timezone.utc) - timedelta(minutes=5),
            )
            channel = await client.fetch_channel(AGENT_ID, TEST_CHANNEL)
            assert isinstance(channel, Channel)
            assert client.token is not None
