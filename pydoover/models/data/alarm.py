from enum import Enum
from typing import Any


class AlarmOperator(str, Enum):
    eq = "eq"
    ge = "ge"
    gt = "gt"
    le = "le"
    lt = "lt"


class AlarmState(str, Enum):
    NoData = "NoData"
    OK = "OK"
    Alarm = "Alarm"
    AlarmPending = "AlarmPending"


class NotificationPolicy(str, Enum):
    """Whether broad default notification subscriptions include this alarm."""

    default = "default"
    opt_in = "opt-in"


class AlarmStateMessage:
    """Notification override for one alarm state.

    ``notify`` and ``text`` are independent: switching notifications off keeps
    any text already configured, so it is restored when they are switched back
    on. ``text=None`` means "use the auto-generated wording".
    """

    def __init__(self, notify: bool = True, text: str | None = None):
        self.notify = notify
        self.text = text

    def __repr__(self):
        return f"AlarmStateMessage(notify={self.notify!r}, text={self.text!r})"

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(notify=data.get("notify", True), text=data.get("text"))

    def to_dict(self):
        result: dict[str, Any] = {"notify": self.notify}
        if self.text is not None:
            result["text"] = self.text
        return result


class AlarmMessages:
    """Per-state notification overrides, keyed by the state being entered.

    A state that is absent behaves entirely by default. States are keyed by
    their destination, so an ``ok`` override applies to recoveries from both
    ``Alarm`` and ``AlarmPending``.
    """

    def __init__(
        self,
        alarm: AlarmStateMessage | None = None,
        ok: AlarmStateMessage | None = None,
        pending: AlarmStateMessage | None = None,
        no_data: AlarmStateMessage | None = None,
    ):
        self.alarm = alarm
        self.ok = ok
        self.pending = pending
        self.no_data = no_data

    def __repr__(self):
        return (
            f"AlarmMessages(alarm={self.alarm!r}, ok={self.ok!r}, "
            f"pending={self.pending!r}, no_data={self.no_data!r})"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        def maybe(key):
            value = data.get(key)
            return AlarmStateMessage.from_dict(value) if value is not None else None

        return cls(
            alarm=maybe("alarm"),
            ok=maybe("ok"),
            pending=maybe("pending"),
            no_data=maybe("no_data"),
        )

    def to_dict(self):
        result = {}
        for key in ("alarm", "ok", "pending", "no_data"):
            value = getattr(self, key)
            if value is not None:
                result[key] = value.to_dict()
        return result


class Alarm:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        enabled: bool,
        key: str,
        operator: AlarmOperator,
        value: Any,
        state: AlarmState,
        entered_state_ts: int,
        expiry_mins: float | None = None,
        topic_name: str = "",
        notification_policy: NotificationPolicy = NotificationPolicy.default,
        channel_name: str = "",
        last_seen_ts: int | None = None,
        alarm_pending_ms: int | None = None,
        messages: AlarmMessages | None = None,
        rate_threshold: float | None = None,
        rate_window_ms: int | None = None,
        rate_baseline_value: float | None = None,
        rate_baseline_ts: int | None = None,
    ):
        self.id = int(id)
        self.name = name
        self.topic_name = topic_name
        self.notification_policy = notification_policy
        self.description = description
        self.channel_name = channel_name
        self.enabled = enabled
        self.key = key
        self.operator = operator
        self.value = value
        self.state = state
        self.entered_state_ts = entered_state_ts
        self.expiry_mins = expiry_mins
        self.last_seen_ts = last_seen_ts
        self.alarm_pending_ms = alarm_pending_ms
        self.messages = messages
        self.rate_threshold = rate_threshold
        self.rate_window_ms = rate_window_ms
        self.rate_baseline_value = rate_baseline_value
        self.rate_baseline_ts = rate_baseline_ts

    def __repr__(self):
        return (
            f"Alarm(id={self.id!r}, name={self.name!r}, key={self.key!r}, "
            f"state={self.state!r})"
        )

    @property
    def is_rate_alarm(self) -> bool:
        """Whether this is a rate-of-change alarm rather than a threshold alarm.

        The presence of ``rate_window_ms`` is what makes an alarm a rate alarm.
        """
        return self.rate_window_ms is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        messages = data.get("messages")
        return cls(
            id=int(data["id"]),
            name=data["name"],
            description=data["description"],
            enabled=data["enabled"],
            key=data["key"],
            operator=AlarmOperator(data["operator"]),
            value=data["value"],
            state=AlarmState(data["state"]),
            entered_state_ts=data["entered_state_ts"],
            expiry_mins=data.get("expiry_mins"),
            # These are defaulted server-side for rows written before they
            # existed, so a payload in flight can legitimately omit them.
            topic_name=data.get("topic_name", ""),
            notification_policy=NotificationPolicy(
                data.get("notification_policy", "default")
            ),
            channel_name=data.get("channel_name", ""),
            last_seen_ts=data.get("last_seen_ts"),
            alarm_pending_ms=data.get("alarm_pending_ms"),
            messages=AlarmMessages.from_dict(messages)
            if messages is not None
            else None,
            rate_threshold=data.get("rate_threshold"),
            rate_window_ms=data.get("rate_window_ms"),
            rate_baseline_value=data.get("rate_baseline_value"),
            rate_baseline_ts=data.get("rate_baseline_ts"),
        )

    def to_dict(self):
        result = {
            "id": self.id,
            "name": self.name,
            "topic_name": self.topic_name,
            "notification_policy": self.notification_policy.value,
            "description": self.description,
            "channel_name": self.channel_name,
            "enabled": self.enabled,
            "key": self.key,
            "operator": self.operator.value,
            "value": self.value,
            "state": self.state.value,
            "entered_state_ts": self.entered_state_ts,
        }
        optional = {
            "expiry_mins": self.expiry_mins,
            "last_seen_ts": self.last_seen_ts,
            "alarm_pending_ms": self.alarm_pending_ms,
            "rate_threshold": self.rate_threshold,
            "rate_window_ms": self.rate_window_ms,
            "rate_baseline_value": self.rate_baseline_value,
            "rate_baseline_ts": self.rate_baseline_ts,
        }
        for key, value in optional.items():
            if value is not None:
                result[key] = value
        if self.messages is not None:
            result["messages"] = self.messages.to_dict()
        return result
