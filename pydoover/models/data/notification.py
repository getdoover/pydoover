from enum import IntEnum
from typing import Any


class _NameWireEnum(IntEnum):
    """An ``IntEnum`` the API represents by member *name* in JSON.

    Both notification enums serialise server-side as the variant name —
    ``"Info"``, ``"Email"`` — so responses carry names, not the integer
    discriminants (which are internal database storage). Plain ``IntEnum``
    lookup raises on those names, hence :meth:`_missing_`.

    The two enums differ on input: ``NotificationSeverity`` has a hand-written
    deserialiser server-side that also accepts its integers, while
    ``NotificationType`` does not, so anything sent as a type must be a name.
    :attr:`wire` gives the always-correct form for both.
    """

    @classmethod
    def _aliases(cls) -> dict[str, str]:
        """Extra lowercase spellings accepted on input, mapped to member names."""
        return {}

    @property
    def wire(self) -> str:
        """The value to put on the wire for this member."""
        return self.name

    @classmethod
    def _missing_(cls, value: Any):
        # Accept names case-insensitively (plus a few common misspellings).
        # The server matches names exactly, so a near-miss like "warning" is
        # rejected there — and on the notifications channel that rejection is
        # silent, the payload being replaced by its own raw JSON. Resolving it
        # here is what stops that reaching a subscriber.
        if isinstance(value, str):
            key = value.strip().lower()
            by_name = {member.name.lower(): member for member in cls}
            if key in by_name:
                return by_name[key]
            alias = cls._aliases().get(key)
            if alias is not None:
                return cls[alias]
            raise ValueError(
                f"{value!r} is not a valid {cls.__qualname__} — "
                f"expected one of {', '.join(m.name for m in cls)}"
            )
        return None


class NotificationType(_NameWireEnum):
    Email = 1
    Sms = 2
    WebPush = 3
    Http = 4
    Placeholder = 5
    FirebasePush = 6


class NotificationSeverity(_NameWireEnum):
    Trace = 3
    Debug = 4
    Info = 5
    Warn = 6
    Critical = 7

    @classmethod
    def _aliases(cls) -> dict[str, str]:
        # `Warn` and `Critical` are the two that get guessed wrong most often,
        # since Python's logging module spells them `warning` and `critical`
        # and most people reach for `error`. The server rejects all three.
        return {
            "warning": "Warn",
            "error": "Critical",
            "err": "Critical",
            "fatal": "Critical",
            "crit": "Critical",
        }


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
            "type": self.type.wire,
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
        The notification body. Required, and must be a non-empty string.
    title : str, optional
        An optional title / headline for the notification. Defaults
        server-side to the agent's display name.
    severity : NotificationSeverity | str | int, optional
        The severity level. Subscribers only receive notifications at or
        above their subscription severity. Accepts the enum, a member name
        (``"warn"``, case-insensitive) or the integer value.
    topic : str, optional
        An optional topic string used to filter subscriptions by
        ``topic_filter``.

    Raises
    ------
    TypeError
        If any field is of the wrong type.
    ValueError
        If ``message`` is empty, or ``severity`` is not a recognised level.

    Notes
    -----
    Fields are validated eagerly, and deliberately so. A payload the server
    cannot deserialise is not rejected — it is quietly replaced by one whose
    message is the raw JSON, which surfaces as an unreadable notification on
    a subscriber's phone long after the fact. Failing here instead keeps that
    mistake in the application, where it is visible.
    """

    NOTIFICATIONS_CHANNEL: str = "notifications"

    def __init__(
        self,
        message: str,
        title: str | None = None,
        severity: NotificationSeverity | str | int | None = None,
        topic: str | None = None,
    ):
        if not isinstance(message, str):
            raise TypeError(
                f"notification message must be a str, "
                f"got {type(message).__name__}: {message!r}"
            )
        if not message.strip():
            raise ValueError("notification message must not be empty")
        for name, value in (("title", title), ("topic", topic)):
            if value is not None and not isinstance(value, str):
                raise TypeError(
                    f"notification {name} must be a str or None, "
                    f"got {type(value).__name__}: {value!r}"
                )

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
            # The server accepts either the name or the integer for severity
            # (unlike NotificationType), so the historical int is kept.
            result["severity"] = self.severity.value
        if self.topic is not None:
            result["topic"] = self.topic
        return result
