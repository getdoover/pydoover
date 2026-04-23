from enum import IntEnum
from typing import Any


class NotificationType(IntEnum):
    Email = 1
    Sms = 2
    WebPush = 3
    Http = 4
    Placeholder = 5


class NotificationSeverity(IntEnum):
    Trace = 3
    Debug = 4
    Info = 5
    Warn = 6
    Critical = 7


class NotificationEndpoint:
    def __init__(
        self,
        id: str,
        agent_id: str,
        type: NotificationType,
        name: str,
        default: bool,
        extra_data: dict[str, Any],
        priority: int | None = None,
    ):
        self.id = id
        self.agent_id = agent_id
        self.type = type
        self.name = name
        self.default = default
        self.extra_data = extra_data
        self.priority = priority

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            id=int(data["id"]),
            agent_id=int(data["agent_id"]),
            type=NotificationType(data["type"]),
            name=data["name"],
            default=data["default"],
            extra_data=data["extra_data"],
            priority=data.get("priority"),
        )

    def to_dict(self):
        result = {
            "id": self.id,
            "agent_id": self.agent_id,
            "type": self.type.value,
            "name": self.name,
            "default": self.default,
            "extra_data": self.extra_data,
        }
        if self.priority is not None:
            result["priority"] = self.priority
        return result


class NotificationSubscriptionEndpoint:
    def __init__(self, id: str, name: str, default: bool):
        self.id = id
        self.name = name
        self.default = default

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            id=int(data["id"]),
            name=data["name"],
            default=data["default"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "default": self.default,
        }


class NotificationSubscription:
    def __init__(
        self,
        id: str,
        subscriber: str,
        subscribed_to: str,
        severity: NotificationSeverity,
        topic_filter: list[str],
        endpoints: list[NotificationSubscriptionEndpoint],
    ):
        self.id = id
        self.subscriber = subscriber
        self.subscribed_to = subscribed_to
        self.severity = severity
        self.topic_filter = topic_filter
        self.endpoints = endpoints

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            id=int(data["id"]),
            subscriber=int(data["subscriber"]),
            subscribed_to=int(data["subscribed_to"]),
            severity=NotificationSeverity(data["severity"]),
            topic_filter=data["topic_filter"],
            endpoints=[
                NotificationSubscriptionEndpoint.from_dict(e)
                for e in data.get("endpoints", [])
            ],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "subscriber": self.subscriber,
            "subscribed_to": self.subscribed_to,
            "severity": self.severity.value,
            "topic_filter": self.topic_filter,
            "endpoints": [e.to_dict() for e in self.endpoints],
        }


class Notification:
    """A notification message sent via the ``notifications`` channel.

    Mirrors the server-side ``NotificationChannelMessagePayload``. Publishing a
    message with this payload to an agent's ``notifications`` channel causes
    the Doover cloud to fan the notification out to matching subscriptions.

    Parameters
    ----------
    message : str
        The notification body. Required.
    title : str, optional
        An optional title / headline for the notification.
    severity : NotificationSeverity, optional
        The severity level. Subscribers only receive notifications at or
        above their subscription severity.
    topic : str, optional
        An optional topic string used to filter subscriptions by
        ``topic_filter``.
    """

    NOTIFICATIONS_CHANNEL: str = "notifications"

    def __init__(
        self,
        message: str,
        title: str | None = None,
        severity: NotificationSeverity | int | None = None,
        topic: str | None = None,
    ):
        self.message = message
        self.title = title
        self.severity = NotificationSeverity(severity) if severity is not None else None
        self.topic = topic

    def __repr__(self) -> str:
        return (
            f"Notification(message={self.message!r}, title={self.title!r}, "
            f"severity={self.severity!r}, topic={self.topic!r})"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Notification":
        severity = data.get("severity")
        return cls(
            message=data["message"],
            title=data.get("title"),
            severity=NotificationSeverity(severity) if severity is not None else None,
            topic=data.get("topic"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"message": self.message}
        if self.title is not None:
            result["title"] = self.title
        if self.severity is not None:
            result["severity"] = self.severity.value
        if self.topic is not None:
            result["topic"] = self.topic
        return result
