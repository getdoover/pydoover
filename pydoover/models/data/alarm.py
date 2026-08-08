from enum import Enum
from typing import Any

from .notification import NotificationPolicy


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
        last_seen_ts: int | None = None,
        alarm_pending_ms: int | None = None,
        notification_policy: NotificationPolicy | str = (
            NotificationPolicy.IncludedByDefault
        ),
        topic_name: str | None = None,
    ):
        self.id = int(id)
        self.name = name
        self.description = description
        self.enabled = enabled
        self.key = key
        self.operator = operator
        self.value = value
        self.state = state
        self.entered_state_ts = entered_state_ts
        self.expiry_mins = expiry_mins
        self.last_seen_ts = last_seen_ts
        self.alarm_pending_ms = alarm_pending_ms
        self.notification_policy = NotificationPolicy(notification_policy)
        self.topic_name = topic_name

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
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
            last_seen_ts=data.get("last_seen_ts"),
            alarm_pending_ms=data.get("alarm_pending_ms"),
            notification_policy=data.get(
                "notification_policy", NotificationPolicy.IncludedByDefault
            ),
            topic_name=data.get("topic_name"),
        )

    def to_dict(self):
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "key": self.key,
            "operator": self.operator.value,
            "value": self.value,
            "state": self.state.value,
            "entered_state_ts": self.entered_state_ts,
        }
        if self.expiry_mins is not None:
            result["expiry_mins"] = self.expiry_mins
        if self.last_seen_ts is not None:
            result["last_seen_ts"] = self.last_seen_ts
        if self.alarm_pending_ms is not None:
            result["alarm_pending_ms"] = self.alarm_pending_ms
        result["notification_policy"] = self.notification_policy.value
        if self.topic_name is not None:
            result["topic_name"] = self.topic_name
        return result
