"""Declarative notification schemas.

An application declares the notifications it can send, the same way it
declares its tags, config and UI. Two things fall out of that declaration:

* a canonical topic per notification, so the notification lands in the
  structured hierarchy rather than the temporary ``legacy/default`` bucket;
* a schema, exported at publish time and loaded onto the device at deploy,
  which is what lets the Doover site offer a per-notification opt-out
  instead of an all-or-nothing switch.

Examples
--------

>>> from pydoover import notifications
>>> class MyNotifications(notifications.Notifications):
...     low_battery = notifications.Notification("The battery is low")
...     maintenance_due = notifications.Notification(
...         "Maintenance is due",
...         policy=notifications.NotificationPolicy.opt_in,
...     )

Then, from the application::

    await self.notifications.low_battery.send()
    await self.notifications.low_battery.send("Battery at 10.2V")
"""

import json
import pathlib
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, NoReturn, overload

from ..models.data.alarm import NotificationPolicy
from ..models.data.notification import (
    NotificationSeverity,
    NotificationTopic,
    _validate_topic_segment,
)

if TYPE_CHECKING:
    from ..models.data.message import Message

__all__ = (
    "BoundNotification",
    "Notification",
    "NotificationPolicy",
    "NotificationSeverity",
    "Notifications",
)


def _humanise(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").strip().capitalize()


class Notification:
    """One declared notification an application can send.

    Parameters
    ----------
    message : str
        The default body. :meth:`BoundNotification.send` sends this when it
        is not given a message of its own.
    display_name : str, optional
        Human label for the Doover site's notification picker. Defaults to a
        humanised form of the attribute name.
    description : str, optional
        Longer explanation of when this notification fires, shown alongside
        the label.
    severity : NotificationSeverity | str | int, optional
        Severity of the sent notification. Defaults to
        :attr:`~pydoover.models.NotificationSeverity.Info`.

        Note that severity is matched *before* topic: a subscriber whose
        subscription severity is above this never receives the notification,
        however they have set their topics.
    title : str, optional
        Title / headline. Defaults server-side to the agent's display name.
    policy : NotificationPolicy | str, optional
        Whether broad default subscriptions include this notification
        (``default``) or a subscriber has to ask for it (``opt_in``). It is
        part of the topic, so changing it on a published app changes the
        topic and orphans any exclusion a subscriber had written against the
        old one.
    name : str, optional
        Event name, forming the last topic segment. Defaults to the
        attribute name, matching the tags convention.
    """

    def __init__(
        self,
        message: str,
        *,
        display_name: str | None = None,
        description: str | None = None,
        severity: NotificationSeverity | str | int = NotificationSeverity.Info,
        title: str | None = None,
        policy: NotificationPolicy | str = NotificationPolicy.default,
        name: str | None = None,
    ):
        if not isinstance(message, str) or not message.strip():
            raise ValueError(
                f"notification message must be a non-empty str, got {message!r}"
            )

        self.message = message
        self.display_name = display_name
        self.description = description
        self.severity = NotificationSeverity(severity)
        self.title = title
        self.policy = NotificationPolicy(policy)
        self.name = _validate_topic_segment("name", name) if name else None
        self._declared_attr_name: str | None = None

    def __repr__(self) -> str:
        return (
            f"Notification(name={self.name!r}, severity={self.severity!r}, "
            f"policy={self.policy!r})"
        )

    def to_schema(self) -> dict[str, Any]:
        """The schema entry for this notification.

        The topic is deliberately absent: it needs the app *install* key,
        which differs per device, so it is assembled by whoever reads the
        schema from the install it is filed under.
        """
        name = self.name or self._declared_attr_name or ""
        result: dict[str, Any] = {
            "event": name,
            "display_name": self.display_name or _humanise(name),
            "message": self.message,
            "severity": self.severity.wire,
            "policy": self.policy.value,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.title is not None:
            result["title"] = self.title
        return result

    def _raise_unbound_error(self) -> NoReturn:
        raise RuntimeError(
            "Declared Notification definitions are not sendable. "
            "Send notifications through a Notifications instance."
        )

    async def send(self, *args: Any, **kwargs: Any) -> NoReturn:
        del args, kwargs
        self._raise_unbound_error()


class BoundNotification:
    """A declared notification bound to a running application."""

    def __init__(self, owner: "Notifications", declaration: "_DeclaredNotification"):
        self._owner = owner
        self._declaration = declaration

    @property
    def template(self) -> Notification:
        return self._declaration.template

    @property
    def name(self) -> str:
        return self._declaration.name

    @property
    def topic(self) -> NotificationTopic:
        """The canonical topic this notification is sent on."""
        return self._owner.topic_for(self.name)

    def __repr__(self) -> str:
        return f"BoundNotification(name={self.name!r})"

    async def send(
        self,
        message: str | None = None,
        *,
        title: str | None = None,
        severity: NotificationSeverity | str | int | None = None,
        **kwargs: Any,
    ) -> "int | Message":
        """Send this notification.

        Every argument falls back to the declaration, so the common case is
        ``await self.notifications.low_battery.send()``.
        """
        template = self.template
        return await self._owner._send(
            message if message is not None else template.message,
            title=title if title is not None else template.title,
            severity=severity if severity is not None else template.severity,
            topic=self.topic,
            **kwargs,
        )


class _DeclaredNotification:
    def __init__(self, attr_name: str, template: Notification):
        self.attr_name = attr_name
        self.template = template

    @property
    def name(self) -> str:
        return self.template.name or self.attr_name

    @overload
    def __get__(self, instance: None, owner: type["Notifications"]) -> Notification: ...

    @overload
    def __get__(
        self, instance: "Notifications", owner: type["Notifications"]
    ) -> BoundNotification: ...

    def __get__(
        self, instance: "Notifications | None", owner: type["Notifications"]
    ) -> "Notification | BoundNotification":
        if instance is None:
            return self.template
        return BoundNotification(instance, self)


class Notifications:
    """Base class for declarative notification definitions.

    Subclasses declare the notifications an application can send as class
    attributes. Instances expose :class:`BoundNotification` proxies that
    actually send.
    """

    __notification_declarations__: "dict[str, _DeclaredNotification]" = dict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        declarations: dict[str, _DeclaredNotification] = dict()
        for base in reversed(cls.__mro__[1:]):
            declarations.update(getattr(base, "__notification_declarations__", {}))

        for attr_name, value in list(cls.__dict__.items()):
            if not isinstance(value, Notification):
                continue

            # Validated here rather than at declaration time: the attribute
            # name is the event name unless one was given, and an attribute
            # like `lowBattery` would otherwise only fail much later, when
            # the first notification is sent from a device in the field.
            _validate_topic_segment("name", value.name or attr_name)

            value._declared_attr_name = attr_name
            declaration = _DeclaredNotification(attr_name, value)
            declarations[attr_name] = declaration
            setattr(cls, attr_name, declaration)

        seen: dict[str, str] = {}
        for attr_name, declaration in declarations.items():
            clash = seen.get(declaration.name)
            if clash is not None:
                raise ValueError(
                    f"Duplicate notification event name {declaration.name!r} "
                    f"declared by both {clash!r} and {attr_name!r}."
                )
            seen[declaration.name] = attr_name

        cls.__notification_declarations__ = declarations

    def __init__(self, app_key: str | None = None, application: Any = None):
        self.app_key = app_key
        self._application = application
        self._notification_declarations = dict(
            self.__class__.__notification_declarations__
        )

    async def setup(self):
        """Mutate this notification set before it is used."""

    def topic_for(self, name: str) -> NotificationTopic:
        """The canonical topic for one declared notification."""
        declaration = self._find(name)
        if declaration is None:
            raise KeyError(f"No notification declared with name {name!r}")
        if not self.app_key:
            raise RuntimeError(
                "Application key has not been set, so a notification topic "
                "cannot be built. This is set from the APP_KEY environment "
                "variable by the device runtime, so it is normally only "
                "missing in local development or tests."
            )
        return NotificationTopic.application(
            self.app_key, declaration.name, declaration.template.policy
        )

    async def _send(self, message: str, **kwargs: Any) -> "int | Message":
        if self._application is None:
            raise RuntimeError(
                "Notifications are not attached to an application, so nothing "
                "can be sent. Access them as `self.notifications` from within "
                "your application."
            )
        return await self._application.send_notification(message, **kwargs)

    def _find(self, name: str) -> _DeclaredNotification | None:
        declaration = self._notification_declarations.get(name)
        if declaration is not None:
            return declaration
        return next(
            (
                candidate
                for candidate in self._notification_declarations.values()
                if candidate.name == name
            ),
            None,
        )

    def get(self, name: str) -> BoundNotification | None:
        """The bound notification called ``name``, or ``None``."""
        declaration = self._find(name)
        return BoundNotification(self, declaration) if declaration else None

    def to_schema(self) -> dict[str, Any]:
        """The schema for every declared notification, keyed by event name."""
        return {
            declaration.name: declaration.template.to_schema()
            for declaration in self._notification_declarations.values()
        }

    @classmethod
    def export(cls, fp: pathlib.Path, app_name: str):
        """Export the notification schema to a JSON file.

        Writes the ``notification_schema`` field of ``app_name`` in the
        ``doover_config.json`` at ``fp``, alongside ``config_schema`` and
        ``ui_schema``.
        """
        schema = cls().to_schema()

        data = json.loads(fp.read_text()) if fp.exists() else {}
        data.setdefault(app_name, {})["notification_schema"] = schema
        fp.write_text(json.dumps(data, indent=4))

    def __iter__(self) -> Iterator[BoundNotification]:
        for attr_name in self._notification_declarations:
            yield BoundNotification(self, self._notification_declarations[attr_name])

    def __len__(self) -> int:
        return len(self._notification_declarations)

    def __getitem__(self, item: str) -> BoundNotification:
        notification = self.get(item)
        if notification is None:
            raise KeyError(item)
        return notification

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._notification_declarations)})"
