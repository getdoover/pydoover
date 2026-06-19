from typing import Any


class MessageLogEntry:
    """Processor invocation log entry for a channel message."""

    def __init__(self, timestamp: int, type: str, **fields: Any):
        self.timestamp = int(timestamp)
        self.type = type
        self.fields = fields

    @property
    def message(self) -> Any:
        return self.fields.get("message")

    @property
    def level(self) -> str | None:
        return self.fields.get("level")

    @property
    def logger(self) -> str | None:
        return self.fields.get("logger")

    @property
    def request_id(self) -> str | None:
        return self.fields.get("requestId")

    @property
    def record(self) -> dict[str, Any] | None:
        return self.fields.get("record")

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        fields = dict(data)
        timestamp = fields.pop("timestamp")
        entry_type = fields.pop("type")
        return cls(timestamp=timestamp, type=entry_type, **fields)

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "type": self.type,
            **self.fields,
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()
