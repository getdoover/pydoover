import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.models.data import MessageLogEntry
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
