from types import SimpleNamespace

import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.docker.application import Application as DockerApplication
from pydoover.models.data import (
    DEFAULT_NOTIFICATION_TOPIC_FILTERS,
    Alarm,
    AlarmState,
    NotificationPolicy,
    NotificationSeverity,
    TopicFilterMode,
)
from pydoover.processor.application import Application as ProcessorApplication


def test_sync_subscription_writes_regex_defaults_without_star():
    client = DataClient(base_url="https://data.example", token="test-token")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {"subscriptions": [{"id": "10", "endpoint_id": "20"}]}

    client._request = fake_request
    try:
        result = client.create_notification_subscription(
            1, 2, NotificationSeverity.Info
        )
    finally:
        client.close()

    assert result == [{"id": 10, "endpoint_id": 20}]
    payload = calls[0][2]["data"]
    assert payload["topic_filter_mode"] == TopicFilterMode.Regex.value
    assert payload["topic_filter"] == list(DEFAULT_NOTIFICATION_TOPIC_FILTERS)
    assert "*" not in payload["topic_filter"]


def test_star_expansion_preserves_accompanying_exact_literals():
    client = DataClient(base_url="https://data.example", token="test-token")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {"subscriptions": [{"id": "10", "endpoint_id": "20"}]}

    client._request = fake_request
    try:
        client.create_notification_subscription(
            1,
            2,
            NotificationSeverity.Info,
            ["*", "legacy.topic"],
            topic_filter_mode=TopicFilterMode.Exact,
        )
    finally:
        client.close()

    payload = calls[0][2]["data"]
    assert payload["topic_filter_mode"] == "regex"
    assert payload["topic_filter"][-1] == r"legacy\.topic"


@pytest.mark.asyncio
async def test_async_subscription_expands_deprecated_star():
    client = AsyncDataClient(base_url="https://data.example", token="test-token")
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {"subscriptions": [{"id": "10", "endpoint_id": "20"}]}

    client._request = fake_request
    result = await client.create_notification_subscription(
        1, 2, NotificationSeverity.Info, ["*"]
    )
    await client.close()

    assert result == [{"id": 10, "endpoint_id": 20}]
    payload = calls[0][2]["data"]
    assert payload["topic_filter_mode"] == "regex"
    assert payload["topic_filter"] == list(DEFAULT_NOTIFICATION_TOPIC_FILTERS)


@pytest.mark.asyncio
@pytest.mark.parametrize("application_type", [DockerApplication, ProcessorApplication])
async def test_application_event_builds_topic(application_type):
    calls = []

    async def create_message(*args, **kwargs):
        calls.append((args, kwargs))
        return 123

    if application_type is DockerApplication:
        app = SimpleNamespace(
            app_key="pump-controller",
            device_agent=SimpleNamespace(create_message=create_message),
        )
    else:
        app = SimpleNamespace(
            app_key="pump-controller",
            api=SimpleNamespace(create_message=create_message),
        )

    result = await application_type.send_notification(
        app,
        "Low pressure",
        event="low-pressure",
        notification_policy=NotificationPolicy.ExplicitOptIn,
    )

    assert result == 123
    payload = calls[0][0][1]
    assert payload["topic"] == ("dev/applications/opt-in/pump-controller/low-pressure")


@pytest.mark.asyncio
@pytest.mark.parametrize("application_type", [DockerApplication, ProcessorApplication])
async def test_application_preserves_topicless_and_rejects_topic_with_event(
    application_type,
):
    calls = []

    async def create_message(*args, **kwargs):
        calls.append((args, kwargs))
        return 123

    if application_type is DockerApplication:
        app = SimpleNamespace(
            app_key="pump-controller",
            device_agent=SimpleNamespace(create_message=create_message),
        )
    else:
        app = SimpleNamespace(
            app_key="pump-controller",
            api=SimpleNamespace(create_message=create_message),
        )

    await application_type.send_notification(app, "Legacy")
    assert "topic" not in calls[0][0][1]

    with pytest.raises(ValueError, match="mutually exclusive"):
        await application_type.send_notification(
            app, "Invalid", topic="legacy", event="structured"
        )


def test_alarm_parses_new_and_legacy_notification_fields():
    base = {
        "id": "1",
        "name": "High Temperature",
        "description": "",
        "enabled": True,
        "key": "temperature",
        "operator": "gt",
        "value": 50,
        "state": "AlarmPending",
        "entered_state_ts": 123,
        "last_seen_ts": 120,
        "alarm_pending_ms": 30_000,
    }

    legacy = Alarm.from_dict(base)
    structured = Alarm.from_dict(
        {
            **base,
            "notification_policy": "opt-in",
            "topic_name": "high-temperature",
        }
    )

    assert legacy.state is AlarmState.AlarmPending
    assert legacy.notification_policy is NotificationPolicy.IncludedByDefault
    assert legacy.topic_name is None
    assert structured.notification_policy is NotificationPolicy.ExplicitOptIn
    assert structured.topic_name == "high-temperature"
    assert structured.last_seen_ts == 120
    assert structured.alarm_pending_ms == 30_000


def test_sync_alarm_create_sends_notification_configuration():
    client = DataClient(base_url="https://data.example", token="test-token")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {
            **kwargs["data"],
            "id": "1",
            "state": "NoData",
            "entered_state_ts": 123,
        }

    client._request = fake_request
    try:
        alarm = client.create_alarm(
            1,
            "temperature",
            "High Temperature",
            "temperature",
            "gt",
            50,
            alarm_pending_ms=30_000,
            notification_policy=NotificationPolicy.ExplicitOptIn,
            topic_name="high-temperature",
        )
    finally:
        client.close()

    payload = calls[0][2]["data"]
    assert payload["notification_policy"] == "opt-in"
    assert payload["topic_name"] == "high-temperature"
    assert payload["alarm_pending_ms"] == 30_000
    assert alarm.notification_policy is NotificationPolicy.ExplicitOptIn
