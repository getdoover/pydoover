"""Connection state over time for many agents.

``GET /agents/connection_history`` returns each agent's connection state
as a timeline, so a fleet chart or an uptime strip is one small request
rather than a page through every agent's messages.
"""

from enum import Enum
from typing import Any


class ConnectionHistoryState(Enum):
    """Coarse connection state over time.

    ``sleeping`` is a periodic-continuous device between check-ins and counts
    as up; ``unknown`` is before the agent's first message, or earlier than a
    truncated read reached.
    """

    online = "Online"
    sleeping = "Sleeping"
    offline = "Offline"
    unknown = "Unknown"

    @property
    def is_up(self) -> bool:
        return self in (ConnectionHistoryState.online, ConnectionHistoryState.sleeping)


class ConnectionSegment:
    """A stretch of one state. ``start`` inclusive, ``end`` exclusive, epoch ms."""

    def __init__(self, start: int, end: int, state: ConnectionHistoryState):
        self.start = int(start)
        self.end = int(end)
        self.state = state

    def __repr__(self):
        return f"<ConnectionSegment {self.state.value} {self.start}-{self.end}>"

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            start=data["start"],
            end=data["end"],
            state=ConnectionHistoryState(data["state"]),
        )

    def to_dict(self):
        return {"start": self.start, "end": self.end, "state": self.state.value}


class ConnectionBucket:
    """The fleet in one time slot.

    Counts are by the state each agent held for most of the slot;
    :attr:`came_up` and :attr:`went_down` name the agents that changed inside
    it (an agent that flapped is in both).
    """

    def __init__(
        self,
        start: int,
        end: int,
        online: int,
        sleeping: int,
        offline: int,
        unknown: int,
        came_up: list[int],
        went_down: list[int],
    ):
        self.start = int(start)
        self.end = int(end)
        self.online = online
        self.sleeping = sleeping
        self.offline = offline
        self.unknown = unknown
        self.came_up = came_up
        self.went_down = went_down

    def __repr__(self):
        return (
            f"<ConnectionBucket {self.start}-{self.end} up={self.up} "
            f"offline={self.offline} unknown={self.unknown}>"
        )

    @property
    def up(self) -> int:
        """Online plus sleeping: what a "devices online" chart plots."""
        return self.online + self.sleeping

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            start=data["start"],
            end=data["end"],
            online=data["online"],
            sleeping=data["sleeping"],
            offline=data["offline"],
            unknown=data["unknown"],
            came_up=[int(a) for a in data.get("came_up", [])],
            went_down=[int(a) for a in data.get("went_down", [])],
        )

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "online": self.online,
            "sleeping": self.sleeping,
            "offline": self.offline,
            "unknown": self.unknown,
            "came_up": [str(a) for a in self.came_up],
            "went_down": [str(a) for a in self.went_down],
        }


class AgentConnectionHistory:
    def __init__(
        self,
        agent_id: int,
        state_at_start: ConnectionHistoryState,
        state_at_end: ConnectionHistoryState,
        uptime: float | None,
        truncated: bool,
        segments: list[ConnectionSegment] | None = None,
    ):
        self.agent_id = int(agent_id)
        self.state_at_start = state_at_start
        self.state_at_end = state_at_end
        #: Share of the known time the agent was up; ``None`` when nothing is known.
        self.uptime = uptime
        #: Some day in the window had more status changes than the server
        #: reads; its earliest stretch is unknown.
        self.truncated = truncated
        #: Only present when requested with ``include_segments``.
        self.segments = segments

    def __repr__(self):
        return (
            f"<AgentConnectionHistory agent_id={self.agent_id} "
            f"{self.state_at_start.value}->{self.state_at_end.value} uptime={self.uptime}>"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        segments = data.get("segments")
        return cls(
            agent_id=int(data["id"]),
            state_at_start=ConnectionHistoryState(data["state_at_start"]),
            state_at_end=ConnectionHistoryState(data["state_at_end"]),
            uptime=data.get("uptime"),
            truncated=bool(data.get("truncated", False)),
            segments=[ConnectionSegment.from_dict(s) for s in segments]
            if segments is not None
            else None,
        )

    def to_dict(self):
        result: dict[str, Any] = {
            "id": str(self.agent_id),
            "state_at_start": self.state_at_start.value,
            "state_at_end": self.state_at_end.value,
            "uptime": self.uptime,
            "truncated": self.truncated,
        }
        if self.segments is not None:
            result["segments"] = [s.to_dict() for s in self.segments]
        return result


class ConnectionHistoryResponse:
    """What ``fetch_connection_history`` returns.

    ``start`` is inclusive and ``end`` exclusive, both epoch ms; ``end`` is
    the requested ``before`` clipped to now. Agents the caller cannot read are
    absent. ``buckets`` is only present when ``bucket_ms`` was given.
    """

    def __init__(
        self,
        start: int,
        end: int,
        agents: list[AgentConnectionHistory],
        buckets: list[ConnectionBucket] | None = None,
    ):
        self.start = int(start)
        self.end = int(end)
        self.agents = agents
        self.buckets = buckets

    def __repr__(self):
        return (
            f"<ConnectionHistoryResponse {self.start}-{self.end} "
            f"agents={len(self.agents)} buckets={len(self.buckets or [])}>"
        )

    @property
    def agents_by_id(self) -> dict[int, AgentConnectionHistory]:
        return {a.agent_id: a for a in self.agents}

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        buckets = data.get("buckets")
        return cls(
            start=data["start"],
            end=data["end"],
            agents=[AgentConnectionHistory.from_dict(a) for a in data["agents"]],
            buckets=[ConnectionBucket.from_dict(b) for b in buckets]
            if buckets is not None
            else None,
        )

    def to_dict(self):
        result: dict[str, Any] = {
            "start": self.start,
            "end": self.end,
            "agents": [a.to_dict() for a in self.agents],
        }
        if self.buckets is not None:
            result["buckets"] = [b.to_dict() for b in self.buckets]
        return result
