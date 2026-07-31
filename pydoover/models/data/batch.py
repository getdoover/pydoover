from datetime import datetime
from typing import Any

from .aggregate import Aggregate
from .message import Message

#: Maximum number of items the batch mutation endpoints accept per request.
MAX_BATCH_MUTATIONS = 50


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


class BatchMutationItem:
    """One entry in a batch mutation request.

    Every item names its own agent and channel, so a single batch can span
    both.  ``message_id`` is required for update and delete items; supplying it
    on a create makes the create idempotent, since a retry writes to the same
    id rather than generating a second message.
    """

    def __init__(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any] | None = None,
        message_id: int | None = None,
        timestamp: int | datetime | None = None,
        ttl: int | None = None,
        replace: list[str] | None = None,
        suppress_hooks: bool | None = None,
    ):
        self.agent_id = int(agent_id)
        self.channel_name = channel_name
        self.data = data
        self.message_id = int(message_id) if message_id is not None else None
        self.timestamp = timestamp
        self.ttl = ttl
        self.replace = replace
        self.suppress_hooks = suppress_hooks

    def to_dict(self) -> dict[str, Any]:
        item: dict[str, Any] = {
            "agent_id": str(self.agent_id),
            "channel_name": self.channel_name,
        }
        if self.data is not None:
            item["data"] = self.data
        if self.message_id is not None:
            item["message_id"] = str(self.message_id)
        if self.timestamp is not None:
            ts = self.timestamp
            if isinstance(ts, datetime):
                ts = int(ts.timestamp() * 1000)
            item["ts"] = int(ts)
        if self.ttl is not None:
            item["ttl"] = self.ttl
        if self.replace is not None:
            item["replace"] = self.replace
        if self.suppress_hooks is not None:
            item["suppress_hooks"] = self.suppress_hooks
        return item


class BatchMutationResult:
    """The outcome of a single item in a batch mutation."""

    def __init__(
        self,
        agent_id: int,
        channel_name: str,
        success: bool,
        message_id: int | None = None,
        error: str | None = None,
    ):
        self.agent_id = int(agent_id)
        self.channel_name = channel_name
        self.success = success
        self.message_id = int(message_id) if message_id is not None else None
        self.error = error

    def __repr__(self):
        state = "ok" if self.success else f"failed: {self.error}"
        return (
            f"<BatchMutationResult agent_id={self.agent_id} "
            f"channel={self.channel_name!r} {state}>"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            agent_id=int(data["agent_id"]),
            channel_name=data["channel_name"],
            success=data["success"],
            message_id=data.get("message_id"),
            error=data.get("error"),
        )

    def to_dict(self):
        result: dict[str, Any] = {
            "agent_id": self.agent_id,
            "channel_name": self.channel_name,
            "success": self.success,
        }
        if self.message_id is not None:
            result["message_id"] = self.message_id
        if self.error is not None:
            result["error"] = self.error
        return result


class BatchMutationResponse:
    """Per-item results of a batch mutation, in request order.

    A batch can partially succeed - successful items are not rolled back - so
    callers should retry only the items in :attr:`failures`.
    """

    def __init__(
        self,
        items: list[BatchMutationResult],
        count: int,
        succeeded: int,
        failed: int,
    ):
        self.items = items
        self.count = count
        self.succeeded = succeeded
        self.failed = failed

    def __repr__(self):
        return (
            f"<BatchMutationResponse count={self.count} "
            f"succeeded={self.succeeded} failed={self.failed}>"
        )

    @property
    def failures(self) -> list[BatchMutationResult]:
        """The items that failed, for selective retry."""
        return [item for item in self.items if not item.success]

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            items=[BatchMutationResult.from_dict(i) for i in data["items"]],
            count=data["count"],
            succeeded=data["succeeded"],
            failed=data["failed"],
        )

    def to_dict(self):
        return {
            "items": [i.to_dict() for i in self.items],
            "count": self.count,
            "succeeded": self.succeeded,
            "failed": self.failed,
        }
