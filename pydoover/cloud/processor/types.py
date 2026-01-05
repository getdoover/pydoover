from datetime import datetime
from enum import Enum
from typing import Any, Callable


class ConnectionDetermination(Enum):
    online = "Online"
    offline = "Offline"


class ConnectionStatus(Enum):
    continuous_online = "ContinuousOnline"
    continuous_online_no_ping = "ContinuousOnlineNoPing"
    continuous_offline = "ContinuousOffline"
    continuous_pending = "ContinuousPending"

    periodic_unknown = "PeriodicUnknown"
    unknown = "Unknown"


class ConnectionType(Enum):
    continuous = "Continuous"
    periodic_continuous = "PeriodicContinuous"
    periodic = "Periodic"

    @classmethod
    def from_v1(cls, data):
        match data:
            case "constant" | "continuous":
                return cls.continuous
            case "periodic":
                return cls.periodic
            case "periodic_continuous":
                return cls.periodic_continuous
            case _:
                raise ValueError(f"Unknown connection type: {data}")


class ConnectionConfig:
    # pub struct ConnectionConfig {
    #     pub connection_type: Option<ConnectionType>,
    #     pub expected_interval: Option<u64>, // in seconds
    #     pub offline_after: Option<u64>,     // in seconds
    #     pub sleep_time: Option<u64>,
    #     pub next_wake_time: Option<u64>,
    # }
    def __init__(
        self,
        connection_type: ConnectionType,
        expected_interval: float | None,
        offline_after: float | None,
        sleep_time: float | None,
        next_wake_time: float | None,
    ):
        self.connection_type = connection_type
        self.expected_interval = expected_interval
        self.offline_after = offline_after
        self.sleep_time = sleep_time
        self.next_wake_time = next_wake_time

    @classmethod
    def from_dict(cls, data):
        return cls(
            data.get("connection_type"),
            data.get("expected_interval"),
            data.get("offline_after"),
            data.get("sleep_time"),
            data.get("next_wake_time"),
        )

    @classmethod
    def from_v1(cls, data):
        return cls(
            ConnectionType.from_v1(data["connectionType"]),
            data.get("connectionPeriod"),
            data.get("offlineAfter"),
            data.get("connectionPeriod"),  # not 100% accurate but close enough?
            # as above... although I think the original intention was for this timestamp
            None,  # this is a seconds value in doover 1.0 but should be a timestamp in doover 2.0
        )

    def to_dict(self):
        return {
            "connection_type": self.connection_type.value,
            "expected_interval": self.expected_interval,
            "offline_after": self.offline_after,
            "sleep_time": self.sleep_time,
            "next_wake_time": self.next_wake_time,
        }

    def __eq__(self, other):
        if not isinstance(other, ConnectionConfig):
            return False

        return (
            self.connection_type == other.connection_type
            and self.expected_interval == other.expected_interval
            and self.offline_after == other.offline_after
            and self.sleep_time == other.sleep_time
            and self.next_wake_time == other.next_wake_time
        )


class ChannelID:
    def __init__(self, agent_id: int, name: str):
        self.agent_id = agent_id
        self.name = name

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["agent_id"],
            data["name"],
        )


class Message:
    def __init__(self, id: int, author_id: int, data: dict, timestamp: int):
        self.id = id
        self.author_id = author_id
        self.data = data
        self.timestamp = timestamp

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["id"],
            data.get("author_id"),
            data.get("data"),
            data.get("timestamp"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class Attachment:
    #     pub filename: String,
    #     pub content_type: Option<String>,
    #     pub size: u64,
    #     pub url: String,
    def __init__(self, filename: str, content_type: str, size: int, url: str):
        self.filename = filename
        self.content_type = content_type
        self.size = size
        self.url = url

    @classmethod
    def from_dict(cls, payload: dict[str, Any]):
        return cls(
            payload["filename"],
            payload.get("content_type"),
            payload["size"],
            payload["url"],
        )


class Aggregate:
    def __init__(
        self,
        data: dict[str, Any],
        attachments: list[Attachment],
        last_updated: datetime | None,
    ):
        self.data: dict[str, Any] = data
        self.attachments = attachments
        self.last_updated: datetime | None = last_updated

    @classmethod
    def from_dict(cls, payload):
        return cls(
            payload["data"],
            [Attachment.from_dict(a) for a in payload.get("attachments", [])],
            payload.get("last_updated"),
        )


class Channel:
    def __init__(
        self,
        id: int,
        name: str,
        owner_id: int,
        is_private: bool,
        aggregate_schema: dict[str, Any],
        message_schema: dict[str, Any],
        aggregate: Aggregate,
    ):
        self.id = int(id)
        self.name = name
        self.owner_id = int(owner_id)
        self.is_private = is_private
        self.aggregate_schema = aggregate_schema
        self.message_schema = message_schema
        self.aggregate = aggregate

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        # #[derive(Serialize)]
        # pub struct Channel {
        #     pub name: String,
        #     pub owner_id: SnowflakeID,
        #     pub is_private: bool,
        #     pub aggregate_schema: Option<Value>,
        #     pub message_schema: Option<Value>,
        #     // pub last_updated: Option<u64>,
        #     #[serde(skip_serializing_if = "Option::is_none")]
        #     pub aggregate: Option<ChannelAggregate>,
        #     #[serde(skip_serializing_if = "Option::is_none")]
        #     pub daily_message_summaries: Option<Vec<ChannelMessageSummary>>,
        # }
        return cls(
            data["id"],
            data["name"],
            data["owner_id"],
            data["is_private"],
            data["aggregate_schema"],
            data["message_schema"],
            Aggregate.from_dict(data["aggregate"]),
        )


class MessageCreateEvent:
    owner_id: int
    channel_name: str
    author_id: int
    organisation_id: int
    message: Message

    def __init__(
        self,
        owner_id: int,
        channel_name: str,
        author_id: int,
        message: Message,
        organisation_id: int,
    ):
        self.owner_id = owner_id
        self.channel_name = channel_name
        self.author_id = author_id
        self.message = message
        self.organisation_id = organisation_id

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["owner_id"],
            data["channel_name"],
            data["author_id"],
            Message.from_dict(data["message"]),
            data["organisation_id"],
        )


class DeploymentEvent:
    agent_id: int
    app_id: int
    app_install_id: int

    def __init__(self, agent_id: int, app_id: int, app_install_id: int):
        self.agent_id = agent_id
        self.app_id = app_id
        self.app_install_id = app_install_id

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["agent_id"],
            data["app_id"],
            data["app_install_id"],
        )


class ScheduleEvent:
    def __init__(self, schedule_id: int):
        self.schedule_id = schedule_id

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["schedule_id"],
        )


class IngestionEndpointEvent:
    def __init__(
        self,
        ingestion_id: int,
        agent_id: int,
        organisation_id: int,
        payload: str,
        parser: Callable[[str], Any],
    ):
        self.ingestion_id = ingestion_id
        self.agent_id = agent_id
        self.organisation_id = organisation_id
        self.payload = parser(payload)

    @classmethod
    def from_dict(cls, data: dict[str, Any], parser: Callable[[str], Any]):
        return cls(
            data["ingestion_id"],
            data["agent_id"],
            data["organisation_id"],
            data["payload"],
            parser,
        )


class ManualInvokeEvent:
    def __init__(
        self,
        organisation_id: int,
        payload: str,
    ):
        self.organisation_id = organisation_id
        self.payload = payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["organisation_id"],
            data["payload"],
        )


class AggregateUpdateEvent:
    # pub struct AggregateUpdatePayload {
    #     pub author_id: SnowflakeID,
    #     pub channel: ChannelID,
    #     pub aggregate: ChannelAggregate,
    #     pub request_data: ChannelAggregate,
    #     pub organisation_id: SnowflakeID,
    # }
    def __init__(
        self,
        author_id: int,
        channel: ChannelID,
        aggregate: Aggregate,
        request_data: Aggregate,
        organisation_id: int,
    ):
        self.author_id = author_id
        self.channel = channel
        self.aggregate = aggregate
        self.request_data = request_data
        self.organisation_id = organisation_id

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["author_id"],
            ChannelID.from_dict(data["channel"]),
            Aggregate.from_dict(data["aggregate"]),
            Aggregate.from_dict(data["request_data"]),
            data["organisation_id"],
        )
