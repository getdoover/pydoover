import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.models.data import (
    ConnectionHistoryResponse,
    ConnectionHistoryState,
    MessageCountsResponse,
    MessageLogEntry,
    PageLimitError,
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
        },
        {
            "id": "1",
            "state_at_start": "Offline",
            "state_at_end": "Offline",
            "uptime": 0.0,
            "truncated": True,
        },
    ],
    "events": [{"t": 3_600_000, "agent_id": "2", "state": "Online"}],
    "count": 1,
    "next": None,
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
            [1, 2], after=10, min_gap_ms=0
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
                    "limit": None,
                    "min_gap_ms": 0,
                    "cursor": None,
                },
                "organisation_id": None,
            },
        )
    ]
    assert isinstance(history, ConnectionHistoryResponse)
    sleeper = history.agents_by_id[2]
    assert sleeper.state_at_start is ConnectionHistoryState.sleeping
    assert sleeper.state_at_start.is_up
    assert history.agents_by_id[1].truncated
    assert history.events[0].agent_id == 2
    assert history.events[0].state is ConnectionHistoryState.online
    assert history.next is None
    # One agent's timeline, derived from its start state and its events.
    segments = history.segments_for(2)
    assert [(s.start, s.end, s.state.value) for s in segments] == [
        (0, 3_600_000, "Sleeping"),
        (3_600_000, 7_200_000, "Online"),
    ]
    assert history.segments_for(1)[0].state is ConnectionHistoryState.offline
    assert history.segments_for(9) == []
    assert history.to_dict() == CONNECTION_HISTORY


def _history_pages(params):
    """Two pages for a chunk of more than one agent, one otherwise; the
    window, and so the agents, the same on both."""
    ids = params["agent_id"]
    cursor = params["cursor"]
    if cursor is None:
        events = [{"t": 3_600_000, "agent_id": str(i), "state": "Online"} for i in ids]
    else:
        events = [{"t": 1_800_000, "agent_id": str(ids[0]), "state": "Offline"}]
    return {
        "start": 0,
        "end": 7_200_000,
        "agents": [
            {
                "id": str(i),
                "state_at_start": "Offline",
                "state_at_end": "Online",
                "uptime": 0.5,
                "truncated": False,
            }
            for i in ids
        ],
        "events": events,
        "count": len(events),
        "next": "3600000" if cursor is None and len(ids) > 1 else None,
    }


def test_sync_client_drains_connection_history_pages():
    client = DataClient(base_url="https://data.example", token="test-token")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append(kwargs["params"])
        return _history_pages(kwargs["params"])

    client._request = fake_request
    try:
        history = client.fetch_all_connection_history([1, 2], after=10)
        # The cursor moves; the window and the page size do not.
        assert [(c["before"], c["after"], c["cursor"], c["limit"]) for c in calls] == [
            (None, 10, None, 5000),
            (None, 10, 3_600_000, 5000),
        ]
        assert [(e.t, e.agent_id) for e in history.events] == [
            (3_600_000, 1),
            (3_600_000, 2),
            (1_800_000, 1),
        ]
        assert history.count == 3 and history.next is None
        assert history.end == 7_200_000
        assert [s.state.value for s in history.segments_by_agent()[1]] == [
            "Offline",
            "Offline",
            "Online",
        ]

        # With no bounds, "now" is taken once here, not afresh per page.
        calls.clear()
        client.fetch_all_connection_history([1, 2])
        assert calls[0]["before"] is not None and calls[0]["after"] is None
        assert calls[1]["before"] == calls[0]["before"]

        # A wide fleet is read 250 agents to a request and merged.
        calls.clear()
        wide = client.fetch_all_connection_history(list(range(1, 302)), after=10)
        assert [len(c["agent_id"]) for c in calls] == [250, 250, 51, 51]
        assert len(wide.agents) == 301 and wide.count == 303

        # A timeline that will not drain is an error, not a short answer.
        with pytest.raises(PageLimitError, match="1 pages"):
            client.fetch_all_connection_history([1, 2], after=10, max_pages=1)
    finally:
        client.close()


def test_segments_need_the_whole_timeline():
    page = ConnectionHistoryResponse.from_dict(
        _history_pages({"agent_id": [1, 2], "cursor": None})
    )
    assert page.next == 3_600_000
    with pytest.raises(ValueError, match="whole timeline"):
        page.segments_for(1)
    with pytest.raises(ValueError, match="whole timeline"):
        page.segments_by_agent()


@pytest.mark.asyncio
async def test_async_client_drains_connection_history_pages():
    client = AsyncDataClient(base_url="https://data.example", token="test-token")
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append(kwargs["params"])
        return _history_pages(kwargs["params"])

    client._request = fake_request

    history = await client.fetch_all_connection_history(list(range(1, 302)), after=10)

    assert sorted(len(c["agent_id"]) for c in calls) == [51, 51, 250, 250]
    assert {c["cursor"] for c in calls} == {None, 3_600_000}
    assert all(c["after"] == 10 and c["before"] is None for c in calls)
    assert len(history.agents) == 301
    assert history.count == 303 and history.next is None
    assert [e.t for e in history.events[-2:]] == [1_800_000, 1_800_000]

    with pytest.raises(PageLimitError, match="1 pages"):
        await client.fetch_all_connection_history([1, 2], after=10, max_pages=1)


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
