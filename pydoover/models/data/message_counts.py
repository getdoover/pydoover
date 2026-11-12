"""Messages stored per day on a channel, for many agents.

``GET /agents/channels/{channel}/messages/counts`` reads the channel's daily
message summaries, so no message is fetched and a quarter for a fleet is one
small request.
"""

from typing import Any


class DayCount:
    """Messages stored on a channel for one UTC day.

    ``count`` is what is retained now: a deleted message counts down.
    """

    def __init__(self, start: int, count: int):
        #: UTC day start, epoch ms.
        self.start = int(start)
        self.count = int(count)

    def __repr__(self):
        return f"<DayCount start={self.start} count={self.count}>"

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(start=data["start"], count=data["count"])

    def to_dict(self):
        return {"start": self.start, "count": self.count}


class AgentMessageCounts:
    def __init__(self, agent_id: int, days: list[DayCount]):
        self.agent_id = int(agent_id)
        #: Oldest first; days with no messages are absent.
        self.days = days

    def __repr__(self):
        return f"<AgentMessageCounts agent_id={self.agent_id} days={len(self.days)}>"

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            agent_id=int(data["id"]),
            days=[DayCount.from_dict(d) for d in data["days"]],
        )

    def to_dict(self):
        return {"id": str(self.agent_id), "days": [d.to_dict() for d in self.days]}


class MessageCountsResponse:
    """What ``fetch_multi_agent_message_counts`` returns.

    ``totals`` is every agent's counts summed, by day, oldest first.
    """

    def __init__(
        self,
        start: int,
        end: int,
        agents: list[AgentMessageCounts],
        totals: list[DayCount],
    ):
        self.start = int(start)
        self.end = int(end)
        self.agents = agents
        self.totals = totals

    def __repr__(self):
        return (
            f"<MessageCountsResponse {self.start}-{self.end} "
            f"agents={len(self.agents)} days={len(self.totals)}>"
        )

    @property
    def days_by_agent(self) -> dict[int, list[DayCount]]:
        return {a.agent_id: a.days for a in self.agents}

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            start=data["start"],
            end=data["end"],
            agents=[AgentMessageCounts.from_dict(a) for a in data["agents"]],
            totals=[DayCount.from_dict(d) for d in data["totals"]],
        )

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "agents": [a.to_dict() for a in self.agents],
            "totals": [d.to_dict() for d in self.totals],
        }
