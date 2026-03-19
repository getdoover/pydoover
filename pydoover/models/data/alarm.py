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
        return result
