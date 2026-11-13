import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.models.data import (
    ConnectionHistoryResponse,
    ConnectionHistoryState,
    MessageCountsResponse,
    MessageLogEntry,
)
from pydoover.processor.data_client import ProcessorDataClient


LOG_ENTRIES = [
    {
        "timestamp": 1777511327615,
        "type": "platform.start",
        "record": {"requestId": "31048238-a0fe-402c-a510-cdfa768d13a9"},
    },
    {
        "timestamp": 1777511327616,
        "type": "user.log",
        "level": "INFO",
        "logger": "pydoover.processor.application",
        "message": "Initialising processor task",
        "requestId": "31048238-a0fe-402c-a510-cdfa768d13a9",
    },
]


def test_sync_client_fetches_message_logs():
    client = DataClient(base_url="https://data.example", token="test-token")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return LOG_ENTRIES

    client._request = fake_request

    try:
        logs = client.fetch_message_logs(
            123,
            "processor-events",
            456,
            organisation_id=789,
        )
    finally:
        client.close()

    assert calls == [
        (
            "GET",
            "/agents/123/channels/processor-events/messages/456/logs",
            {"organisation_id": 789},
        )
    ]
    assert all(isinstance(entry, MessageLogEntry) for entry in logs)
    assert logs[0].type == "platform.start"
    assert logs[1].message == "Initialising processor task"


@pytest.mark.asyncio
async def test_async_client_fetches_message_logs():
    client = AsyncDataClient(base_url="https://data.example", token="test-token")
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return LOG_ENTRIES

    client._request = fake_request

    logs = await client.fetch_message_logs(
        123,
        "processor-events",
        456,
        organisation_id=789,
    )
    await client.close()

    assert calls == [
        (
            "GET",
            "/agents/123/channels/processor-events/messages/456/logs",
            {"organisation_id": 789},
        )
    ]
    assert all(isinstance(entry, MessageLogEntry) for entry in logs)
    assert logs[0].record == {"requestId": "31048238-a0fe-402c-a510-cdfa768d13a9"}
    assert logs[1].request_id == "31048238-a0fe-402c-a510-cdfa768d13a9"


@pytest.mark.asyncio
async def test_processor_client_fetches_message_logs_with_agent_fallback():
    client = ProcessorDataClient("https://data.example")
    client.agent_id = 123
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return LOG_ENTRIES

    client._request = fake_request

    logs = await client.fetch_message_logs(
        "processor-events",
        456,
        organisation_id=789,
    )
    await client.close()

    assert calls == [
        (
            "GET",
            "/agents/123/channels/processor-events/messages/456/logs",
            {"organisation_id": 789},
        )
    ]
    assert logs[1].type == "user.log"


@pytest.mark.asyncio
async def test_update_aggregate_return_aggregate_maps_to_suppress_response():
    # Regression: the shared TagsManager commits tags via
    # update_channel_aggregate(..., return_aggregate=False). Before the fix the
    # REST clients (AsyncDataClient / ProcessorDataClient) rejected that kwarg
    # with TypeError, crashing every processor that writes a tag. It must be
    # accepted and map to the suppress_response (no-echo) path.
    client = ProcessorDataClient("https://data.example")
    client.agent_id = 123
    params_seen = []

    async def fake_request(method, path, **kwargs):
        params_seen.append(kwargs.get("params"))
        return {}

    client._request = fake_request

    result = await client.update_channel_aggregate(
        "tag_values", {"app": {"tag": 1}}, return_aggregate=False
    )
    assert result is None
    assert params_seen[-1]["suppress_response"] is True

    # Default return_aggregate=True leaves the response un-suppressed.
    await client.update_channel_aggregate("tag_values", {"app": {"tag": 2}})
    await client.close()
    assert params_seen[-1]["suppress_response"] is None


CONNECTION_HISTORY = {
    "start": 0,
    "end": 7_200_000,
    "agents": [
        {
            "id": "2",
            "state_at_start": "Sleeping",
            "state_at_end": "Online",
            "uptime": 1.0,
            "truncated": False,
            "segments": [
                {"start": 0, "end": 3_600_000, "state": "Sleeping"},
                {"start": 3_600_000, "end": 7_200_000, "state": "Online"},
            ],
        },
        {
            "id": "1",
            "state_at_start": "Offline",
            "state_at_end": "Offline",
            "uptime": 0.0,
            "truncated": True,
        },
    ],
    "buckets": [
        {
            "start": 0,
            "end": 3_600_000,
            "online": 0,
            "sleeping": 1,
            "offline": 1,
            "unknown": 0,
            "came_up": [],
            "went_down": [],
        },
        {
            "start": 3_600_000,
            "end": 7_200_000,
            "online": 1,
            "sleeping": 0,
            "offline": 1,
            "unknown": 0,
            "came_up": ["2"],
            "went_down": [],
        },
    ],
}

MESSAGE_COUNTS = {
    "start": 0,
    "end": 172_800_000,
    "agents": [{"id": "1", "days": [{"start": 0, "count": 3}]}],
    "totals": [{"start": 0, "count": 3}, {"start": 86_400_000, "count": 0}],
}


def test_sync_client_fetches_multi_agent_connection_history():
    client = DataClient(base_url="https://data.example", token="test-token")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return CONNECTION_HISTORY

    client._request = fake_request

    try:
        history = client.fetch_multi_agent_connection_history(
            [1, 2], after=10, bucket_ms=3_600_000, include_segments=True
        )
    finally:
        client.close()

    assert calls == [
        (
            "GET",
            "/agents/connection_history",
            {
                "params": {
                    "agent_id": [1, 2],
                    "before": None,
                    "after": 10,
                    "bucket_ms": 3_600_000,
                    "include_segments": True,
                },
                "organisation_id": None,
            },
        )
    ]
    assert isinstance(history, ConnectionHistoryResponse)
    sleeper = history.agents_by_id[2]
    assert sleeper.state_at_start is ConnectionHistoryState.sleeping
    assert sleeper.state_at_start.is_up
    assert sleeper.segments is not None and len(sleeper.segments) == 2
    assert history.agents_by_id[1].truncated
    assert history.agents_by_id[1].segments is None
    assert history.buckets is not None
    assert history.buckets[1].up == 1
    assert history.buckets[1].came_up == [2]
    assert history.to_dict() == CONNECTION_HISTORY


@pytest.mark.asyncio
async def test_async_client_fetches_message_counts():
    client = AsyncDataClient(base_url="https://data.example", token="test-token")
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return MESSAGE_COUNTS

    client._request = fake_request

    counts = await client.fetch_multi_agent_message_counts(
        "tag_values", [1], before=99, organisation_id=7
    )

    assert calls == [
        (
            "GET",
            "/agents/channels/tag_values/messages/counts",
            {
                "params": {"agent_id": [1], "before": 99, "after": None},
                "organisation_id": 7,
            },
        )
    ]
    assert isinstance(counts, MessageCountsResponse)
    assert counts.days_by_agent[1][0].count == 3
    assert [d.count for d in counts.totals] == [3, 0]
    assert counts.to_dict() == MESSAGE_COUNTS
