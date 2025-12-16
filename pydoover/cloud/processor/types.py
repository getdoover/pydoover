from datetime import datetime, timezone
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


class Message:
    def __init__(self, id: int, author_id: int, data: dict, diff: dict, timestamp: int):
        self.id = id
        self.author_id = author_id
        self.data = data
        self.diff = diff
        self.timestamp = timestamp

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["id"],
            data.get("author_id"),
            data.get("data"),
            data.get("diff"),
            data.get("timestamp"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "data": self.data,
            "diff": self.diff,
            "timestamp": self.timestamp,
        }


class Channel:
    def __init__(
        self,
        id: int,
        name: str,
        owner_id: int,
        is_private: bool,
        type_: str,
        last_updated: int,
        last_message: Message | None,
        data: dict,
    ):
        self.id = int(id)
        self.name = name
        self.owner_id = int(owner_id)
        self.is_private = is_private
        self.type = type_
        self.last_updated = last_updated or datetime.now(tz=timezone.utc).timestamp()
        self.last_message = last_message
        self.data = data
        self.aggregate = data

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        # #[derive(Serialize)]
        # pub struct Channel {
        #     id: SnowflakeID,
        #     pub name: String,
        #     pub owner_id: SnowflakeID,
        #     is_private: bool,
        #     channel_type: ChannelType,
        #     last_message: Option<LastMessage>,
        #     data: Value,
        # }
        try:
            last_message = data["last_message"] and Message.from_dict(
                data["last_message"]
            )
        except KeyError:
            last_message = None

        return cls(
            data["id"],
            data["name"],
            data["owner_id"],
            data["is_private"],
            data["channel_type"],
            data.get("last_updated"),
            last_message,
            data["data"],
        )


class MessageCreateEvent:
    owner_id: int
    channel_name: str
    author_id: int
    message: Message

    def __init__(
        self, owner_id: int, channel_name: str, author_id: int, message: Message
    ):
        self.owner_id = owner_id
        self.channel_name = channel_name
        self.author_id = author_id
        self.message = message

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["owner_id"],
            data["channel_name"],
            data["author_id"],
            Message.from_dict(data["message"]),
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
