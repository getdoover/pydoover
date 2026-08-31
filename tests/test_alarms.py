from __future__ import annotations

import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.models.data import (
    Alarm,
    AlarmMessages,
    AlarmState,
    AlarmStateMessage,
    AlarmTriggerEvent,
    NotificationPolicy,
)


THRESHOLD_ALARM = {
    "id": "3092",
    "name": "High Temperature",
    "topic_name": "high-temperature",
    "notification_policy": "opt-in",
    "description": "It's too hot",
    "channel_name": "tag_values",
    "enabled": True,
    "key": "sensors.temperature",
    "operator": "gt",
    "value": 100,
    "state": "Alarm",
    "entered_state_ts": 1777511327615,
    "last_seen_ts": 1777511327999,
    "alarm_pending_ms": 60000,
    "messages": {
        "alarm": {"notify": True, "text": "{{agent_name}} hit {{value}}"},
        "ok": {"notify": False},
    },
}

RATE_ALARM = {
    "id": "3093",
    "name": "Tank Draining",
    "topic_name": "tank-draining",
    "notification_policy": "default",
    "description": "",
    "channel_name": "tag_values",
    "enabled": True,
    "key": "tank.level",
    "operator": "lt",
    "value": None,
    "state": "OK",
    "entered_state_ts": 1777511327615,
    "rate_threshold": -0.5,
    "rate_window_ms": 300000,
    "rate_baseline_value": 82.5,
    "rate_baseline_ts": 1777511320000,
}

# The alarm as it existed before topic names, rate alarms and per-state
# messages — payloads in this shape are still in flight through SNS.
LEGACY_ALARM = {
    "id": "1",
    "name": "Old Alarm",
    "description": "",
    "enabled": True,
    "key": "temperature",
    "operator": "gt",
    "value": 100,
    "state": "OK",
    "entered_state_ts": 1,
}


def test_alarm_parses_threshold_fields():
    alarm = Alarm.from_dict(THRESHOLD_ALARM)

    assert alarm.id == 3092
    assert alarm.topic_name == "high-temperature"
    assert alarm.notification_policy is NotificationPolicy.opt_in
    assert alarm.channel_name == "tag_values"
    assert alarm.state is AlarmState.Alarm
    assert alarm.last_seen_ts == 1777511327999
    assert alarm.alarm_pending_ms == 60000
    assert alarm.is_rate_alarm is False
    assert alarm.messages.alarm.text == "{{agent_name}} hit {{value}}"
    assert alarm.messages.ok.notify is False
    assert alarm.messages.ok.text is None
    assert alarm.messages.pending is None


def test_alarm_parses_rate_fields():
    alarm = Alarm.from_dict(RATE_ALARM)

    assert alarm.is_rate_alarm is True
    assert alarm.value is None
    assert alarm.rate_threshold == -0.5
    assert alarm.rate_window_ms == 300000
    assert alarm.rate_baseline_value == 82.5
    assert alarm.rate_baseline_ts == 1777511320000


def test_alarm_defaults_fields_absent_from_legacy_payloads():
    alarm = Alarm.from_dict(LEGACY_ALARM)

    assert alarm.topic_name == ""
    assert alarm.notification_policy is NotificationPolicy.default
    assert alarm.channel_name == ""
    assert alarm.messages is None
    assert alarm.is_rate_alarm is False


def test_alarm_round_trips_through_dict():
    alarm = Alarm.from_dict(THRESHOLD_ALARM)
    again = Alarm.from_dict(alarm.to_dict())

    assert again.to_dict() == alarm.to_dict()
    assert again.messages.ok.notify is False


def test_alarm_pending_is_a_known_state():
    assert AlarmState("AlarmPending") is AlarmState.AlarmPending


# ── Alarm trigger events ───────────────────────────────────────────────────

ALARM_TRIGGER_PAYLOAD = {
    "channel": {"agent_id": "5551", "name": "tag_values"},
    "alarm": THRESHOLD_ALARM,
    "old_state": "AlarmPending",
    "new_state": "Alarm",
    "aggregate": {"data": {"sensors": {"temperature": 112.4}}},
    "request_data": {"data": {"sensors": {"temperature": 112.4}}},
    "organisation_id": "77",
}


def test_alarm_trigger_event_parses():
    event = AlarmTriggerEvent.from_dict(ALARM_TRIGGER_PAYLOAD)

    assert event.channel.name == "tag_values"
    assert event.channel.agent_id == 5551
    assert event.alarm.id == 3092
    assert event.old_state is AlarmState.AlarmPending
    assert event.new_state is AlarmState.Alarm
    assert event.is_alarm is True
    assert event.is_cleared is False
    assert event.value == 112.4
    assert event.organisation_id == "77"


def test_alarm_trigger_value_is_none_when_key_is_absent():
    payload = dict(ALARM_TRIGGER_PAYLOAD, aggregate={"data": {"sensors": {}}})
    assert AlarmTriggerEvent.from_dict(payload).value is None


def test_alarm_trigger_recovery_reports_cleared():
    payload = dict(ALARM_TRIGGER_PAYLOAD, old_state="Alarm", new_state="OK")
    event = AlarmTriggerEvent.from_dict(payload)

    assert event.is_cleared is True
    assert event.is_alarm is False


# ── Client payloads ────────────────────────────────────────────────────────


def _recording_client():
    client = DataClient(base_url="https://data.example", token="test-token")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return THRESHOLD_ALARM

    client._request = fake_request
    return client, calls


def test_create_alarm_sends_threshold_payload():
    client, calls = _recording_client()
    try:
        client.create_alarm(
            1,
            "tag_values",
            name="High Temperature",
            key="sensors.temperature",
            operator="gt",
            value=100,
            topic_name="high-temperature",
            notification_policy="opt-in",
            alarm_pending_ms=60000,
            messages=AlarmMessages(ok=AlarmStateMessage(notify=False)),
        )
    finally:
        client.close()

    method, path, kwargs = calls[0]
    assert (method, path) == ("POST", "/agents/1/channels/tag_values/alarms")
    assert kwargs["data"] == {
        "name": "High Temperature",
        "key": "sensors.temperature",
        "operator": "gt",
        "description": "",
        "enabled": True,
        "value": 100,
        "topic_name": "high-temperature",
        "notification_policy": "opt-in",
        "alarm_pending_ms": 60000,
        "messages": {"ok": {"notify": False}},
    }


def test_create_rate_alarm_omits_value():
    client, calls = _recording_client()
    try:
        client.create_alarm(
            1,
            "tag_values",
            name="Tank Draining",
            key="tank.level",
            operator="lt",
            rate_threshold=-0.5,
            rate_window_ms=300000,
        )
    finally:
        client.close()

    data = calls[0][2]["data"]
    assert "value" not in data
    assert data["rate_threshold"] == -0.5
    assert data["rate_window_ms"] == 300000


def test_update_alarm_omits_untouched_fields():
    client, calls = _recording_client()
    try:
        client.update_alarm(1, "tag_values", 3092, enabled=False)
    finally:
        client.close()

    assert calls[0][2]["data"] == {"enabled": False}


def test_update_alarm_distinguishes_clearing_from_leaving_alone():
    client, calls = _recording_client()
    try:
        client.update_alarm(
            1,
            "tag_values",
            3092,
            value=None,
            rate_threshold=-0.5,
            rate_window_ms=300000,
            expiry_mins=None,
            messages=None,
        )
    finally:
        client.close()

    assert calls[0][2]["data"] == {
        "value": None,
        "expiry_mins": None,
        "rate_threshold": -0.5,
        "rate_window_ms": 300000,
        "messages": None,
    }


@pytest.mark.asyncio
async def test_list_agent_alarms_hits_the_agent_wide_route():
    client = AsyncDataClient(base_url="https://data.example", token="test-token")
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return [THRESHOLD_ALARM, RATE_ALARM]

    client._request = fake_request

    try:
        alarms = await client.list_agent_alarms(1, organisation_id=77)
    finally:
        await client.close()

    assert calls == [("GET", "/agents/1/alarms", {"organisation_id": 77})]
    assert [a.channel_name for a in alarms] == ["tag_values", "tag_values"]
