"""Connection state over time for many agents.

``GET /agents/connection_history`` reports each agent's state at the
window's start and end and every change of state inside it, newest first
and paged, so a fleet chart or an uptime strip reads one timeline rather
than every agent's messages.
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


class ConnectionEvent:
    """One change of state in a fleet's timeline: the agent moved into ``state`` at ``t`` (epoch ms)."""

    def __init__(self, t: int, agent_id: int, state: ConnectionHistoryState):
        self.t = int(t)
        self.agent_id = int(agent_id)
        self.state = state

    def __repr__(self):
        return (
            f"<ConnectionEvent {self.state.value} agent_id={self.agent_id} t={self.t}>"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            t=data["t"],
            agent_id=int(data["agent_id"]),
            state=ConnectionHistoryState(data["state"]),
        )

    def to_dict(self):
        return {"t": self.t, "agent_id": str(self.agent_id), "state": self.state.value}


class AgentConnectionHistory:
    def __init__(
        self,
        agent_id: int,
        state_at_start: ConnectionHistoryState,
        state_at_end: ConnectionHistoryState,
        uptime: float | None,
        truncated: bool,
    ):
        self.agent_id = int(agent_id)
        self.state_at_start = state_at_start
        self.state_at_end = state_at_end
        #: Share of the known time the agent was up; ``None`` when nothing is known.
        self.uptime = uptime
        #: Some day in the window had more status changes than the server
        #: reads; its earliest stretch is unknown.
        self.truncated = truncated

    def __repr__(self):
        return (
            f"<AgentConnectionHistory agent_id={self.agent_id} "
            f"{self.state_at_start.value}->{self.state_at_end.value} uptime={self.uptime}>"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            agent_id=int(data["id"]),
            state_at_start=ConnectionHistoryState(data["state_at_start"]),
            state_at_end=ConnectionHistoryState(data["state_at_end"]),
            uptime=data.get("uptime"),
            truncated=bool(data.get("truncated", False)),
        )

    def to_dict(self):
        return {
            "id": str(self.agent_id),
            "state_at_start": self.state_at_start.value,
            "state_at_end": self.state_at_end.value,
            "uptime": self.uptime,
            "truncated": self.truncated,
        }


class ConnectionHistoryResponse:
    """One page of a fleet's connection timeline.

    ``start`` is inclusive and ``end`` exclusive, both epoch ms; ``end`` is
    the requested ``before`` clipped to now. ``agents`` carry the state each
    held at the window's start and end, the same on every page; ``events``
    are the changes of state inside it, newest first. ``next`` is the
    cursor for the next page of older events, to pass as ``cursor`` with
    the same ``before`` and ``after``, or ``None`` once drained.
    """

    def __init__(
        self,
        start: int,
        end: int,
        agents: list[AgentConnectionHistory],
        events: list[ConnectionEvent],
        count: int | None = None,
        next: int | None = None,
    ):
        self.start = int(start)
        self.end = int(end)
        self.agents = agents
        self.events = events
        self.count = len(events) if count is None else int(count)
        self.next = next

    def __repr__(self):
        return (
            f"<ConnectionHistoryResponse {self.start}-{self.end} "
            f"agents={len(self.agents)} events={len(self.events)} next={self.next}>"
        )

    @property
    def agents_by_id(self) -> dict[int, AgentConnectionHistory]:
        return {a.agent_id: a for a in self.agents}

    def segments_for(self, agent_id: int) -> list[ConnectionSegment]:
        """One agent's timeline as segments across the window, from its
        carried-in state and its events here.

        For every agent at once, :meth:`segments_by_agent` reads the events
        only once. Needs the whole timeline
        (``fetch_all_connection_history``): raises :class:`ValueError` on a
        page with ``next`` set, whose older events are not here to build on.
        """
        self._require_whole_timeline()
        agent = self.agents_by_id.get(agent_id)
        if agent is None:
            return []
        return self._build_segments(
            agent, [e for e in self.events if e.agent_id == agent_id]
        )

    def segments_by_agent(self) -> dict[int, list[ConnectionSegment]]:
        """Every agent's timeline as segments across the window, keyed by
        agent id, in one pass over the events. As with :meth:`segments_for`,
        the whole timeline and not one page of it."""
        self._require_whole_timeline()
        events_by_agent: dict[int, list[ConnectionEvent]] = {}
        for e in self.events:
            events_by_agent.setdefault(e.agent_id, []).append(e)
        return {
            a.agent_id: self._build_segments(a, events_by_agent.get(a.agent_id, []))
            for a in self.agents
        }

    def _require_whole_timeline(self) -> None:
        if self.next is not None:
            raise ValueError(
                "segments need the whole timeline, and this is one page of it "
                "(next is set); read it with fetch_all_connection_history."
            )

    def _build_segments(
        self, agent: AgentConnectionHistory, events: list[ConnectionEvent]
    ) -> list[ConnectionSegment]:
        if self.end <= self.start:
            return []
        segments: list[ConnectionSegment] = []
        start, state = self.start, agent.state_at_start
        for e in sorted(events, key=lambda e: e.t):
            if e.t > start:
                segments.append(ConnectionSegment(start, e.t, state))
            start, state = max(start, e.t), e.state
        if self.end > start:
            segments.append(ConnectionSegment(start, self.end, state))
        return segments

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        nxt = data.get("next")
        return cls(
            start=data["start"],
            end=data["end"],
            agents=[AgentConnectionHistory.from_dict(a) for a in data["agents"]],
            events=[ConnectionEvent.from_dict(e) for e in data.get("events", [])],
            count=data.get("count"),
            next=int(nxt) if nxt is not None else None,
        )

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "agents": [a.to_dict() for a in self.agents],
            "events": [e.to_dict() for e in self.events],
            "count": self.count,
            "next": str(self.next) if self.next is not None else None,
        }


def merge_connection_history(
    pages: list[ConnectionHistoryResponse],
) -> ConnectionHistoryResponse:
    """The pages of one request, or the chunks of a wide one, as a single
    response: agents from the first response they appear in (every page of
    one request carries the same ones), events concatenated newest first,
    ``next`` ``None``. A single response is returned as it is, cursor and
    all."""
    if not pages:
        return ConnectionHistoryResponse(0, 0, [], [])
    if len(pages) == 1:
        return pages[0]
    seen: set[int] = set()
    agents: list[AgentConnectionHistory] = []
    for page in pages:
        for a in page.agents:
            if a.agent_id not in seen:
                seen.add(a.agent_id)
                agents.append(a)
    agents.sort(key=lambda a: a.agent_id)
    events = sorted(
        (e for page in pages for e in page.events), key=lambda e: (-e.t, e.agent_id)
    )
    return ConnectionHistoryResponse(
        start=min(p.start for p in pages),
        end=max(p.end for p in pages),
        agents=agents,
        events=events,
    )
