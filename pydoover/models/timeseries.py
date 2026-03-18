from typing import Any


class DataPoint:
    def __init__(self, value: Any, message_id: int):
        self.value = value
        self.message_id = int(message_id)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            value=data["value"],
            message_id=int(data["message_id"]),
        )

    def to_dict(self):
        return {
            "value": self.value,
            "message_id": self.message_id,
        }


class TimeseriesResponse:
    def __init__(
        self,
        count: int,
        results: list[DataPoint],
        next: int | None = None,
    ):
        self.count = count
        self.results = results
        self.next = next

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            count=data["count"],
            results=[DataPoint.from_dict(r) for r in data["results"]],
            next=data.get("next"),
        )

    def to_dict(self):
        result = {
            "count": self.count,
            "results": [r.to_dict() for r in self.results],
        }
        if self.next is not None:
            result["next"] = self.next
        return result
