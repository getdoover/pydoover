from typing import Any

from .channel import ChannelID


class ConnectionSubscription:
    def __init__(
        self,
        channel: ChannelID,
        subscribed_at: int,
        connection_id: str,
    ):
        self.channel = channel
        self.subscribed_at = subscribed_at
        self.connection_id = connection_id

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            channel=ChannelID.from_dict(data["channel"]),
            subscribed_at=data["subscribed_at"],
            connection_id=int(data["connection_id"]),
        )

    def to_dict(self):
        return {
            "channel": self.channel.to_dict(),
            "subscribed_at": self.subscribed_at,
            "connection_id": self.connection_id,
        }


class ConnectionDetail:
    def __init__(
        self,
        agent_id: str,
        session_id: str,
        default_session: bool,
        address: str,
        status: int,
        subscriptions: list[ConnectionSubscription],
        last_ping: int | None = None,
        latency: float | None = None,
    ):
        self.agent_id = agent_id
        self.session_id = session_id
        self.default_session = default_session
        self.address = address
        self.status = status
        self.subscriptions = subscriptions
        self.last_ping = last_ping
        self.latency = latency

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            agent_id=int(data["agent_id"]),
            session_id=int(data["session_id"]),
            default_session=data["default_session"],
            address=data["address"],
            status=data["status"],
            subscriptions=[
                ConnectionSubscription.from_dict(s)
                for s in data.get("subscriptions", [])
            ],
            last_ping=data.get("last_ping"),
            latency=data.get("latency"),
        )

    def to_dict(self):
        result = {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "default_session": self.default_session,
            "address": self.address,
            "status": self.status,
            "subscriptions": [s.to_dict() for s in self.subscriptions],
        }
        if self.last_ping is not None:
            result["last_ping"] = self.last_ping
        if self.latency is not None:
            result["latency"] = self.latency
        return result


class ConnectionSubscriptionLog:
    def __init__(
        self,
        channel: ChannelID,
        connection_id: str,
        subscribed_at: int | None = None,
        unsubscribed_at: int | None = None,
    ):
        self.channel = channel
        self.connection_id = connection_id
        self.subscribed_at = subscribed_at
        self.unsubscribed_at = unsubscribed_at

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            channel=ChannelID.from_dict(data["channel"]),
            connection_id=int(data["connection_id"]),
            subscribed_at=data.get("subscribed_at"),
            unsubscribed_at=data.get("unsubscribed_at"),
        )

    def to_dict(self):
        result = {
            "channel": self.channel.to_dict(),
            "connection_id": self.connection_id,
        }
        if self.subscribed_at is not None:
            result["subscribed_at"] = self.subscribed_at
        if self.unsubscribed_at is not None:
            result["unsubscribed_at"] = self.unsubscribed_at
        return result
