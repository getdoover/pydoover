from collections.abc import Callable
from enum import Flag, IntEnum, auto
from typing import Any

from .aggregate import Aggregate
from .alarm import Alarm, AlarmState
from .channel import ChannelID
from .message import Message


class EventSubscription(Flag):
    message_create = auto()
    message_update = auto()
    aggregate_update = auto()
    oneshot_message = auto()
    channel_sync = auto()
    all = (
        message_create
        | message_update
        | aggregate_update
        | oneshot_message
        | channel_sync
    )


class WireFormat(IntEnum):
    """Requested delivery format for channel-event payloads.

    Values mirror the ``WireFormat`` proto enum. The SDK decodes events via
    ``data_json`` (see ``decode_data_fields``), so ``json_only`` is the safe
    default — it lets the device agent skip the costly protobuf ``Struct`` build.
    A device agent that predates the field ignores it and returns both formats,
    so requesting ``json_only`` is always safe against any agent version.
    """

    both = 0
    json_only = 1
    struct_only = 2


class MessageCreateEvent:
    # #[derive(Serialize, Event)]
    # pub struct MessageCreate {
    #     pub id: Option<SnowflakeID>,
    #     pub author_id: SnowflakeID,
    #     pub channel: ChannelID,
    #     pub data: Value,
    # }
    def __init__(
        self,
        channel: ChannelID,
        message: Message,
    ):
        self.channel = channel
        self.message = message

    def to_dict(self):
        return {
            "channel": self.channel.to_dict(),
            "message": self.message.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):
        try:
            message = data["message"]
        except KeyError:
            message = Message.from_dict(data)
        else:
            message = Message.from_dict(message)

        channel = message.channel

        return cls(
            channel,
            message,
        )


class OneShotMessage(MessageCreateEvent):
    """A one-shot message that is not persisted. Supports isinstance checks."""

    pass


class MessageUpdateEvent:
    # #[derive(Serialize, Deserialize, Clone)]
    # pub struct MessageUpdatePayload {
    #     pub owner_id: SnowflakeID,
    #     pub channel_name: String,
    #     pub author_id: SnowflakeID,
    #     pub organisation_id: SnowflakeID,
    #     pub message: Message,
    #     pub request_data: Value,
    # }
    def __init__(
        self,
        channel: ChannelID,
        author_id: int,
        organisation_id: int,
        message: Message,
        request_data: dict[str, Any],
    ):
        self.channel = channel
        self.author_id = author_id
        self.organisation_id = organisation_id
        self.message = message
        self.request_data = request_data

    def to_dict(self):
        return {
            "channel": self.channel.to_dict(),
            "author_id": self.author_id,
            "organisation_id": self.organisation_id,
            "message": self.message.to_dict(),
            "request_data": self.request_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            ChannelID.from_dict(data["channel"]),
            data["author_id"],
            data.get("organisation_id"),
            Message.from_dict(data["message"]),
            data.get("request_data", {}),
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

    def to_dict(self):
        return {
            "author_id": self.author_id,
            "channel": self.channel.to_dict(),
            "aggregate": self.aggregate.to_dict(),
            "request_data": self.request_data.to_dict(),
            "organisation_id": self.organisation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["author_id"],
            ChannelID.from_dict(data["channel"]),
            Aggregate.from_dict(data["aggregate"]),
            Aggregate.from_dict(data["request_data"]),
            data["organisation_id"],
        )


class AlarmTriggerEvent:
    # pub struct AlarmTriggerPayload {
    #     pub channel: ChannelID,
    #     pub alarm: Alarm,
    #     pub old_state: AlarmState,
    #     pub new_state: AlarmState,
    #     pub aggregate: ChannelAggregate,
    #     pub request_data: ChannelAggregate,
    #     pub organisation_id: SnowflakeID,
    # }
    """An alarm on a channel changed state.

    Fired for every transition, including the ones whose user-facing
    notification is suppressed by the alarm's ``messages`` overrides — the
    processor fan-out is independent of notification delivery.
    """

    def __init__(
        self,
        channel: ChannelID,
        alarm: Alarm,
        old_state: AlarmState,
        new_state: AlarmState,
        aggregate: Aggregate,
        request_data: Aggregate,
        organisation_id: int,
    ):
        self.channel = channel
        self.alarm = alarm
        self.old_state = old_state
        self.new_state = new_state
        self.aggregate = aggregate
        self.request_data = request_data
        self.organisation_id = organisation_id

    def __repr__(self):
        return (
            f"AlarmTriggerEvent(alarm={self.alarm!r}, "
            f"old_state={self.old_state!r}, new_state={self.new_state!r})"
        )

    @property
    def is_alarm(self) -> bool:
        """Whether the alarm has just entered the (fully debounced) alarm state."""
        return self.new_state is AlarmState.Alarm

    @property
    def is_cleared(self) -> bool:
        """Whether the alarm has just recovered to OK."""
        return self.new_state is AlarmState.OK

    @property
    def value(self) -> Any:
        """The value at the alarm's ``key`` in the aggregate at trigger time."""
        current = self.aggregate.data
        for part in self.alarm.key.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def to_dict(self):
        return {
            "channel": self.channel.to_dict(),
            "alarm": self.alarm.to_dict(),
            "old_state": self.old_state.value,
            "new_state": self.new_state.value,
            "aggregate": self.aggregate.to_dict(),
            "request_data": self.request_data.to_dict(),
            "organisation_id": self.organisation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            ChannelID.from_dict(data["channel"]),
            Alarm.from_dict(data["alarm"]),
            AlarmState(data["old_state"]),
            AlarmState(data["new_state"]),
            Aggregate.from_dict(data["aggregate"]),
            Aggregate.from_dict(data["request_data"]),
            data["organisation_id"],
        )


class ChannelSyncEvent:
    """Fired once per channel when the initial aggregate is fetched on subscription.

    This allows subscribers to process the initial channel state on boot,
    before any live aggregate_update events arrive.
    """

    def __init__(self, aggregate: Aggregate):
        self.aggregate = aggregate


class DeploymentEvent:
    def __init__(
        self,
        agent_id: int,
        app_id: int,
        app_install_id: int,
        app_key: str,
        app_display_name: str,
    ):
        self.agent_id = agent_id
        self.app_id = app_id
        self.app_install_id = app_install_id
        self.app_key = app_key
        self.app_display_name = app_display_name

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "app_id": self.app_id,
            "app_install_id": self.app_install_id,
            "app_key": self.app_key,
            "app_display_name": self.app_display_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["agent_id"],
            data["app_id"],
            data["app_install_id"],
            data["app_key"],
            data["app_display_name"],
        )


class ScheduleEvent:
    def __init__(self, schedule_id: int):
        self.schedule_id = schedule_id

    def to_dict(self):
        return {
            "schedule_id": self.schedule_id,
        }

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
        invocation_url: str | None = None,
        content_type: str | None = None,
    ):
        self.ingestion_id = ingestion_id
        self.agent_id = agent_id
        self.organisation_id = organisation_id
        self.payload = parser(payload)
        self.invocation_url = invocation_url
        self.content_type = content_type

    def to_dict(self):
        return {
            "ingestion_id": self.ingestion_id,
            "agent_id": self.agent_id,
            "organisation_id": self.organisation_id,
            "payload": self.payload,
            "invocation_url": self.invocation_url,
            "content_type": self.content_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], parser: Callable[[str], Any]):
        return cls(
            data["ingestion_id"],
            data["agent_id"],
            data["organisation_id"],
            data["payload"],
            parser,
            invocation_url=data.get("invocation_url"),
            content_type=data.get("content_type"),
        )


class ManualInvokeEvent:
    def __init__(
        self,
        organisation_id: int,
        payload: dict[str, Any],
    ):
        self.organisation_id = organisation_id
        self.payload = payload

    def to_dict(self):
        return {
            "organisation_id": self.organisation_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["organisation_id"],
            data["payload"],
        )
