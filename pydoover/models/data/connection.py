from datetime import datetime, timezone
from enum import Enum


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
        connection_type = data.get("connection_type")
        return cls(
            connection_type and ConnectionType(connection_type),
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
            "connection_type": self.connection_type and self.connection_type.value,
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


class DooverConnectionStatus:
    # pub struct DooverConnectionStatus {
    #     pub status: ConnectionStatus,
    #     pub last_online: u64,
    #     pub last_ping: u64,
    #     pub user_agent: Option<String>,
    #     pub ip: Option<String>,
    #     pub latency_ms: Option<u64>,
    # }
    def __init__(
        self,
        status: ConnectionStatus,
        last_online: datetime,
        last_ping: datetime,
        user_agent: str | None = None,
        ip: str | None = None,
        latency_ms: int | None = None,
    ):
        self.status = status
        self.last_online = last_online
        self.last_ping = last_ping
        self.user_agent = user_agent
        self.ip = ip
        self.latency_ms = latency_ms

    @classmethod
    def from_dict(cls, data):
        last_ping = data.get("last_ping")
        last_online = data.get("last_online")
        return cls(
            ConnectionStatus(data.get("status")),
            last_online
            and datetime.fromtimestamp(last_online / 1000.0, tz=timezone.utc),
            last_ping and datetime.fromtimestamp(last_ping / 1000.0, tz=timezone.utc),
            data.get("user_agent"),
            data.get("ip"),
            data.get("latency_ms"),
        )

    def to_dict(self):
        result = {
            "status": self.status.value,
            "last_online": self.last_online.timestamp() * 1000,
            "last_ping": self.last_ping.timestamp() * 1000,
        }
        if self.user_agent is not None:
            result["user_agent"] = self.user_agent
        if self.ip is not None:
            result["ip"] = self.ip
        if self.latency_ms is not None:
            result["latency_ms"] = self.latency_ms
        return result

    def __eq__(self, other):
        if not isinstance(other, DooverConnectionStatus):
            return False

        return (
            self.status == other.status
            and self.last_online == other.last_online
            and self.last_ping == other.last_ping
            and self.user_agent == other.user_agent
            and self.ip == other.ip
            and self.latency_ms == other.latency_ms
        )
