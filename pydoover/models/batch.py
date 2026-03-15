from typing import Any

from .aggregate import Aggregate
from .message import Message


class BatchMessageResponse:
    def __init__(
        self,
        results: list[Message],
        count: int,
        next: int | None = None,
    ):
        self.results = results
        self.count = count
        self.next = next

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            results=[Message.from_dict(m) for m in data["results"]],
            count=data["count"],
            next=int(data["next"]) if data.get("next") is not None else None,
        )

    def to_dict(self):
        result = {
            "results": [m.to_dict() for m in self.results],
            "count": self.count,
        }
        if self.next is not None:
            result["next"] = self.next
        return result


class AgentAggregate:
    def __init__(self, agent_id: int, aggregate: Aggregate):
        self.agent_id = int(agent_id)
        self.aggregate = aggregate

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            agent_id=int(data["agent_id"]),
            aggregate=Aggregate.from_dict(data),
        )

    def to_dict(self):
        result = {"agent_id": self.agent_id}
        result.update(self.aggregate.to_dict())
        return result


class BatchAggregateResponse:
    def __init__(self, results: list[AgentAggregate], count: int):
        self.results = results
        self.count = count

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            results=[AgentAggregate.from_dict(r) for r in data["results"]],
            count=data["count"],
        )

    def to_dict(self):
        return {
            "results": [r.to_dict() for r in self.results],
            "count": self.count,
        }
