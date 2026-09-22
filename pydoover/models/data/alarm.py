import datetime
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


class ConditionType(str, Enum):
    """What one alarm condition tests."""

    #: A reading against a constant. Covers status equality too.
    threshold = "threshold"
    #: Rate of change, in units per *second*, over ``rate_window_ms``.
    rate = "rate"
    compare = "compare"
    #: A window in milliseconds since **UTC** midnight.
    time_of_day = "time_of_day"


MS_PER_DAY = 24 * 60 * 60 * 1000


def _time_to_ms(value: "datetime.time | int") -> int:
    """Milliseconds since UTC midnight, from a naive (UTC) ``datetime.time``.

    A tz-aware time is rejected rather than converted: without a date there is
    no way to know which side of a DST boundary it falls on.
    """
    if isinstance(value, int):
        return value
    if value.tzinfo is not None:
        raise ValueError(
            "time-of-day windows are stored in UTC and a tz-aware time cannot "
            "be converted without a date (DST) — convert to UTC yourself and "
            "pass from_ms/to_ms"
        )
    return (
        value.hour * 3_600_000
        + value.minute * 60_000
        + value.second * 1000
        + value.microsecond // 1000
    )


class Condition:
    """One condition in an alarm's AND-ed set.

    An alarm is in alarm when **every** condition holds. There is no nesting
    and no ``OR`` — an OR alarm is a second alarm — so a condition set is
    always a flat list.

    Build them with the constructors rather than by hand::

        Condition.threshold("sensors.temperature", "gt", 30)
        Condition.rate("tank.level", "lt", rate_threshold=-0.5, rate_window_ms=300_000)
        Condition.compare("battery_temp", "gt", "ambient_temp", offset=15)
        Condition.time_between(time(5, 0), time(21, 0))

    ``id`` is assigned by the server and keys the condition's runtime state.
    Send it back when editing an existing alarm — that is what stops an edit to
    one condition resetting another's rate baseline. A new condition leaves it
    ``None``.
    """

    __slots__ = (
        "from_ms",
        "id",
        "invert",
        "key",
        "offset",
        "operator",
        "other_key",
        "rate_threshold",
        "rate_window_ms",
        "to_ms",
        "type",
        "value",
    )

    def __init__(
        self,
        type: ConditionType | str,
        *,
        id: str | None = None,
        key: str | None = None,
        operator: AlarmOperator | str | None = None,
        value: Any = None,
        other_key: str | None = None,
        offset: float | None = None,
        rate_threshold: float | None = None,
        rate_window_ms: int | None = None,
        from_ms: int | None = None,
        to_ms: int | None = None,
        invert: bool = False,
    ):
        self.type = ConditionType(type)
        self.id = id
        self.key = key
        self.operator = AlarmOperator(operator) if operator is not None else None
        self.value = value
        self.other_key = other_key
        self.offset = offset
        self.rate_threshold = rate_threshold
        self.rate_window_ms = rate_window_ms
        self.from_ms = from_ms
        self.to_ms = to_ms
        self.invert = invert

    @classmethod
    def threshold(
        cls,
        key: str,
        operator: AlarmOperator | str,
        value: Any,
        *,
        id: str | None = None,
    ) -> "Condition":
        return cls(
            ConditionType.threshold, id=id, key=key, operator=operator, value=value
        )

    @classmethod
    def rate(
        cls,
        key: str,
        operator: AlarmOperator | str,
        rate_threshold: float,
        rate_window_ms: int,
        *,
        id: str | None = None,
    ) -> "Condition":
        """Rate of change in units per **second**.

        ``eq`` is not valid — use ``gt``/``ge`` for a rising rate and
        ``lt``/``le`` for a falling one (with a negative threshold).
        """
        return cls(
            ConditionType.rate,
            id=id,
            key=key,
            operator=operator,
            rate_threshold=rate_threshold,
            rate_window_ms=rate_window_ms,
        )

    @classmethod
    def compare(
        cls,
        key: str,
        operator: AlarmOperator | str,
        other_key: str,
        offset: float | None = None,
        *,
        id: str | None = None,
    ) -> "Condition":
        """``key <operator> other_key + offset``."""
        return cls(
            ConditionType.compare,
            id=id,
            key=key,
            operator=operator,
            other_key=other_key,
            offset=offset,
        )

    @classmethod
    def time_of_day(
        cls,
        from_ms: int,
        to_ms: int,
        *,
        invert: bool = False,
        id: str | None = None,
    ) -> "Condition":
        """A window in milliseconds since **UTC** midnight.

        ``from_ms > to_ms`` wraps midnight; ``invert=True`` means "only
        *outside* these hours".
        """
        return cls(
            ConditionType.time_of_day,
            id=id,
            from_ms=from_ms,
            to_ms=to_ms,
            invert=invert,
        )

    @classmethod
    def time_between(
        cls,
        start: "datetime.time | int",
        end: "datetime.time | int",
        *,
        invert: bool = False,
        id: str | None = None,
    ) -> "Condition":
        """A window between two **UTC** times; ``start > end`` wraps midnight.

        The server stores windows in UTC only, so a local window has to be
        converted by the caller.
        """
        return cls.time_of_day(
            _time_to_ms(start), _time_to_ms(end), invert=invert, id=id
        )

    @property
    def keys(self) -> list[str]:
        """The aggregate keys this condition reads (empty for a time window)."""
        if self.type is ConditionType.compare:
            return [k for k in (self.key, self.other_key) if k]
        if self.key:
            return [self.key]
        return []

    def __repr__(self):
        return f"Condition(type={self.type.value!r}, id={self.id!r})"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Condition":
        return cls(
            data["type"],
            id=data.get("id"),
            key=data.get("key"),
            operator=data.get("operator"),
            value=data.get("value"),
            other_key=data.get("other_key"),
            offset=data.get("offset"),
            rate_threshold=data.get("rate_threshold"),
            rate_window_ms=data.get("rate_window_ms"),
            from_ms=data.get("from_ms"),
            to_ms=data.get("to_ms"),
            invert=data.get("invert", False),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type.value}
        if self.id is not None:
            result["id"] = self.id
        if self.operator is not None:
            result["operator"] = self.operator.value
        if self.key is not None:
            result["key"] = self.key
        if self.type is ConditionType.threshold:
            result["value"] = self.value
        elif self.type is ConditionType.rate:
            result["rate_threshold"] = self.rate_threshold
            result["rate_window_ms"] = self.rate_window_ms
        elif self.type is ConditionType.compare:
            result["other_key"] = self.other_key
            if self.offset is not None:
                result["offset"] = self.offset
        elif self.type is ConditionType.time_of_day:
            result["from_ms"] = self.from_ms
            result["to_ms"] = self.to_ms
            if self.invert:
                result["invert"] = True
        return result


class ConditionState:
    """Read-only runtime state the server keeps for one condition, keyed by
    :attr:`Condition.id` on :attr:`Alarm.condition_state`."""

    __slots__ = ("baseline_ts", "baseline_value", "last_seen_ts", "last_verdict")

    def __init__(
        self,
        baseline_value: float | None = None,
        baseline_ts: int | None = None,
        last_seen_ts: int | None = None,
        last_verdict: bool | None = None,
    ):
        self.baseline_value = baseline_value
        self.baseline_ts = baseline_ts
        self.last_seen_ts = last_seen_ts
        self.last_verdict = last_verdict

    def __repr__(self):
        return (
            f"ConditionState(baseline_value={self.baseline_value!r}, "
            f"last_verdict={self.last_verdict!r})"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConditionState":
        return cls(
            baseline_value=data.get("baseline_value"),
            baseline_ts=data.get("baseline_ts"),
            last_seen_ts=data.get("last_seen_ts"),
            last_verdict=data.get("last_verdict"),
        )

    def to_dict(self) -> dict[str, Any]:
        fields = {
            "baseline_value": self.baseline_value,
            "baseline_ts": self.baseline_ts,
            "last_seen_ts": self.last_seen_ts,
            "last_verdict": self.last_verdict,
        }
        return {key: value for key, value in fields.items() if value is not None}


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
        conditions: "list[Condition] | None" = None,
        condition_state: "dict[str, ConditionState] | None" = None,
        condition_summary: str = "",
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
        self.conditions = conditions if conditions is not None else []
        self.condition_state = condition_state or {}
        self.condition_summary = condition_summary
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
    def primary_condition(self) -> "Condition | None":
        """The condition :attr:`key`, :attr:`operator` and :attr:`value`
        describe: the first measurement condition, preferring a threshold."""
        return _primary_condition(self.conditions)

    @property
    def is_rate_alarm(self) -> bool:
        """Whether the alarm's primary condition is a rate-of-change one."""
        return self.rate_window_ms is not None

    @property
    def has_time_window(self) -> bool:
        return any(c.type is ConditionType.time_of_day for c in self.conditions)

    @property
    def is_multi_condition(self) -> bool:
        """Whether more than one condition has to hold.

        :attr:`key` / :attr:`operator` / :attr:`value` describe only the
        primary condition, so anything reasoning about *why* such an alarm
        fired should read :attr:`conditions` or :attr:`condition_summary`.
        """
        return len(self.conditions) > 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        messages = data.get("messages")
        conditions = [Condition.from_dict(c) for c in data.get("conditions") or []]
        # An alarm stored before conditions existed reports only the
        # single-condition fields; synthesise the set it describes so callers
        # never have to know which era a payload is from.
        if not conditions:
            conditions = _conditions_from_legacy_fields(data)
        primary = _primary_condition(conditions)
        # ``key``/``operator``/``value`` are derived from the primary condition
        # server-side and may eventually stop being sent, so fall back to it
        # rather than subscripting the payload.
        key = data.get("key")
        if key is None:
            key = primary.key if primary else ""
        operator = data.get("operator")
        if operator is None and primary is not None:
            operator = primary.operator
        return cls(
            id=int(data["id"]),
            name=data["name"],
            description=data["description"],
            enabled=data["enabled"],
            key=key,
            operator=AlarmOperator(operator) if operator is not None else None,
            value=data.get("value")
            if "value" in data
            else (primary.value if primary else None),
            state=AlarmState(data["state"]),
            entered_state_ts=data["entered_state_ts"],
            conditions=conditions,
            condition_state={
                condition_id: ConditionState.from_dict(state)
                for condition_id, state in (data.get("condition_state") or {}).items()
            },
            condition_summary=data.get("condition_summary", ""),
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
            rate_threshold=data.get("rate_threshold")
            if "rate_threshold" in data
            else (primary.rate_threshold if primary else None),
            rate_window_ms=data.get("rate_window_ms")
            if "rate_window_ms" in data
            else (primary.rate_window_ms if primary else None),
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
            "operator": self.operator.value if self.operator else None,
            "value": self.value,
            "state": self.state.value,
            "entered_state_ts": self.entered_state_ts,
            "conditions": [c.to_dict() for c in self.conditions],
        }
        if self.condition_summary:
            result["condition_summary"] = self.condition_summary
        if self.condition_state:
            result["condition_state"] = {
                condition_id: state.to_dict()
                for condition_id, state in self.condition_state.items()
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


def _primary_condition(conditions: "list[Condition]") -> "Condition | None":
    """Mirrors the server's own choice, so ``key``/``value`` mean the same
    thing here as in a notification template."""
    for wanted in (ConditionType.threshold, ConditionType.rate, ConditionType.compare):
        for condition in conditions:
            if condition.type is wanted:
                return condition
    return None


def _conditions_from_legacy_fields(data: dict[str, Any]) -> "list[Condition]":
    """The single condition a pre-conditions alarm payload describes."""
    key = data.get("key")
    operator = data.get("operator")
    if key is None or operator is None:
        return []
    # ``rate_window_ms`` was the discriminator between the two legacy shapes.
    if data.get("rate_window_ms") is not None:
        return [
            Condition.rate(
                key,
                operator,
                rate_threshold=data.get("rate_threshold"),
                rate_window_ms=data["rate_window_ms"],
                id="c1",
            )
        ]
    return [Condition.threshold(key, operator, data.get("value"), id="c1")]
