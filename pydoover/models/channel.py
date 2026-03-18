from typing import Any

from .aggregate import Aggregate

try:
    from .generated.device_agent.device_agent_pb2 import (
        ChannelID as ProtoChannelID,
    )

    _HAS_PROTO = True
except ImportError:
    _HAS_PROTO = False


class ChannelID:
    def __init__(self, agent_id: int, name: str):
        self.agent_id = int(agent_id)
        self.name = name

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["agent_id"],
            data["name"],
        )

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "name": self.name,
        }

    @classmethod
    def from_proto(cls, response):
        return cls(
            response.agent_id,
            response.name,
        )

    def to_proto(self):
        if not _HAS_PROTO:
            raise RuntimeError("Proto stubs not available")
        return ProtoChannelID(
            agent_id=self.agent_id,
            name=self.name,
        )


class Channel:
    # #[derive(Serialize)]
    # pub struct Channel {
    #     pub name: String,
    #     pub owner_id: SnowflakeID,
    #     pub is_private: bool,
    #     pub aggregate_schema: Option<Value>,
    #     pub message_schema: Option<Value>,
    #     pub alarms_enabled: bool,
    #     pub aggregate: Option<ChannelAggregate>,
    #     pub daily_message_summaries: Option<Vec<ChannelMessageSummary>>,
    #     pub alarms: Option<Vec<Alarm>>,
    # }
    def __init__(
        self,
        name: str,
        owner_id: int,
        is_private: bool,
        aggregate_schema: dict[str, Any],
        message_schema: dict[str, Any],
        aggregate: Aggregate,
    ):
        self.name = name
        self.owner_id = int(owner_id)
        self.is_private = is_private
        self.aggregate_schema = aggregate_schema
        self.message_schema = message_schema
        self.aggregate = aggregate

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["name"],
            data["owner_id"],
            data["is_private"],
            data.get("aggregate_schema"),
            data.get("message_schema"),
            Aggregate.from_dict(data["aggregate"]) if data.get("aggregate") else None,
        )

    def to_dict(self):
        result = {
            "name": self.name,
            "owner_id": self.owner_id,
            "is_private": self.is_private,
            "aggregate_schema": self.aggregate_schema,
            "message_schema": self.message_schema,
        }
        if self.aggregate is not None:
            result["aggregate"] = self.aggregate.to_dict()
        return result
