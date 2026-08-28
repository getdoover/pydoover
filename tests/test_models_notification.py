"""Tests for notification models, especially the JSON wire format.

Both notification enums serialise server-side as the variant *name*, so
responses carry ``"Info"`` / ``"Email"`` rather than integers. On input the
two differ: ``NotificationSeverity`` has a hand-written deserialiser that also
accepts its integers (3-7), while ``NotificationType`` accepts names only.

Names are matched exactly, and on the ``notifications`` channel a rejected
payload is not an error anyone sees — the handler falls back to using the raw
JSON as the notification text. These tests pin the encoding.
"""

import pytest

from pydoover.models.data import (
    DEFAULT_NOTIFICATION_TOPIC_FILTERS,
    Notification,
    NotificationEndpoint,
    NotificationPolicy,
    NotificationSeverity,
    NotificationSubscription,
    NotificationSubscriptionEndpoint,
    NotificationTopic,
    NotificationType,
    TopicFilterMode,
)


# Exactly the variant names accepted by the server enums.
SERVER_SEVERITIES = {"Trace", "Debug", "Info", "Warn", "Critical"}
SERVER_TYPES = {"Email", "Sms", "WebPush", "Http", "Placeholder", "FirebasePush"}


class TestWireEncoding:
    def test_enums_match_the_server(self):
        assert {s.wire for s in NotificationSeverity} == SERVER_SEVERITIES
        assert {t.wire for t in NotificationType} == SERVER_TYPES

    def test_type_to_dict_sends_name_not_int(self):
        # NotificationType has no integer deserialiser server-side, so the
        # name is the only form that parses.
        endpoint = NotificationEndpoint(
            id=1,
            agent_id=2,
            type=NotificationType.WebPush,
            name="phone",
            default=True,
            extra_data={},
        )
        assert endpoint.to_dict()["type"] == "WebPush"

    def test_notification_to_dict(self):
        payload = Notification(
            message="Drain VSD motor stopped",
            title="Drain VSD stopped",
            severity=NotificationSeverity.Info,
        ).to_dict()

        assert payload == {
            "message": "Drain VSD motor stopped",
            "title": "Drain VSD stopped",
            "severity": 5,
        }

    def test_optional_fields_omitted(self):
        assert Notification(message="m").to_dict() == {"message": "m"}

    def test_topic_included_when_set(self):
        assert Notification(message="m", topic="pumps").to_dict()["topic"] == "pumps"

    def test_structured_application_topic(self):
        topic = NotificationTopic.application(
            "pump-controller",
            "low-pressure",
            NotificationPolicy.ExplicitOptIn,
        )

        assert topic == "dev/applications/opt-in/pump-controller/low-pressure"
        assert Notification(message="m", topic=topic).to_dict()["topic"] == str(topic)


class TestCoercion:
    """The server matches names exactly, so near-misses must resolve here."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Info", NotificationSeverity.Info),
            ("info", NotificationSeverity.Info),
            ("  WARN  ", NotificationSeverity.Warn),
            ("warning", NotificationSeverity.Warn),  # logging-module spelling
            ("error", NotificationSeverity.Critical),
            ("fatal", NotificationSeverity.Critical),
            (5, NotificationSeverity.Info),
            (NotificationSeverity.Trace, NotificationSeverity.Trace),
        ],
    )
    def test_severity_accepts_sensible_spellings(self, value, expected):
        assert NotificationSeverity(value) is expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Email", NotificationType.Email),
            ("email", NotificationType.Email),
            ("FirebasePush", NotificationType.FirebasePush),
            (3, NotificationType.WebPush),
        ],
    )
    def test_type_accepts_names_and_ints(self, value, expected):
        assert NotificationType(value) is expected

    def test_coerced_severity_is_a_real_member(self):
        # "warning" is rejected by the server; it must not reach the wire.
        assert Notification(message="m", severity="warning").severity is (
            NotificationSeverity.Warn
        )

    def test_unknown_severity_raises_with_valid_options(self):
        with pytest.raises(ValueError) as exc:
            NotificationSeverity("urgent")
        assert "Trace, Debug, Info, Warn, Critical" in str(exc.value)

    def test_out_of_range_int_raises(self):
        # e.g. logging.WARNING (30) — no silent nearest-match.
        with pytest.raises(ValueError):
            NotificationSeverity(30)

    def test_severity_ordering_preserved(self):
        # Subscriptions filter by severity, so ordering must hold.
        assert NotificationSeverity.Trace < NotificationSeverity.Info
        assert NotificationSeverity.Critical > NotificationSeverity.Warn


class TestValidation:
    """A payload the server can't parse becomes a wall of JSON on someone's
    phone, so bad input fails here instead."""

    def test_non_string_message_raises(self):
        with pytest.raises(TypeError, match="message must be a str"):
            Notification(message={"body": "Motor stopped"})

    def test_none_message_raises(self):
        with pytest.raises(TypeError):
            Notification(message=None)

    def test_empty_message_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            Notification(message="   ")

    def test_non_string_title_raises(self):
        with pytest.raises(TypeError, match="title must be a str"):
            Notification(message="m", title=123)

    def test_non_string_topic_raises(self):
        with pytest.raises(TypeError, match="topic must be a str"):
            Notification(message="m", topic=["pumps"])

    @pytest.mark.parametrize(
        ("app_key", "event"),
        [
            ("Pump Controller", "low-pressure"),
            ("pump/controller", "low-pressure"),
            ("pump-controller", "Low Pressure"),
            ("pump-controller", "low/pressure"),
            ("", "low-pressure"),
        ],
    )
    def test_structured_topic_rejects_invalid_segments(self, app_key, event):
        with pytest.raises(ValueError, match="must match"):
            NotificationTopic.application(app_key, event)


class TestParsingResponses:
    """The API returns names for both enums — plain IntEnum lookup would raise."""

    def test_subscription_response_uses_severity_name(self):
        payload = {
            "id": "1",
            "subscriber": "2",
            "subscribed_to": "3",
            "severity": "Info",
            "topic_filter": ["*"],
            "endpoints": [{"id": "4", "name": "phone", "default": True}],
        }
        sub = NotificationSubscription.from_dict(payload)

        assert sub.severity is NotificationSeverity.Info
        assert sub.topic_filter_mode is TopicFilterMode.Exact
        assert isinstance(sub.endpoints[0], NotificationSubscriptionEndpoint)

    def test_subscription_response_parses_regex_mode(self):
        payload = {
            "id": "1",
            "subscriber": "2",
            "subscribed_to": "3",
            "severity": "Info",
            "topic_filter": list(DEFAULT_NOTIFICATION_TOPIC_FILTERS),
            "topic_filter_mode": "regex",
        }

        sub = NotificationSubscription.from_dict(payload)

        assert sub.topic_filter_mode is TopicFilterMode.Regex
        assert sub.to_dict()["topic_filter_mode"] == "regex"

    def test_endpoint_response_uses_type_name(self):
        payload = {
            "id": "1",
            "agent_id": "2",
            "type": "Sms",
            "name": "phone",
            "default": True,
            "extra_data": {"number": "+61400000000"},
        }
        endpoint = NotificationEndpoint.from_dict(payload)

        assert endpoint.type is NotificationType.Sms
        assert endpoint.to_dict()["type"] == "Sms"

    def test_notification_round_trip(self):
        original = Notification(
            message="m", title="t", severity=NotificationSeverity.Warn, topic="pumps"
        )
        restored = Notification.from_dict(original.to_dict())

        assert restored.message == original.message
        assert restored.title == original.title
        assert restored.severity is NotificationSeverity.Warn
        assert restored.topic == original.topic

    def test_notification_from_dict_accepts_either_encoding(self):
        assert (
            Notification.from_dict({"message": "m", "severity": "Critical"}).severity
            is NotificationSeverity.Critical
        )
        assert (
            Notification.from_dict({"message": "m", "severity": 6}).severity
            is NotificationSeverity.Warn
        )
