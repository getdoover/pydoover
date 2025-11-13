from datetime import datetime, timezone
from typing import Any


class Message:
    def __init__(self, id: int, author_id: int, data: dict, diff: dict, timestamp: int):
        self.id = id
        self.author_id = author_id
        self.data = data
        self.diff = (diff,)
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
        
class Messages:
    def __init__(self, messages: list[Message]):
        self.messages = messages

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            [Message.from_dict(m) for m in data]
        )
        
    def __str__(self):
        return str(self.messages)
    
    def __repr__(self):
        return f"Messages({self.messages!r})"
    
    def to_dict(self):
        return [m.to_dict() for m in self.messages]
    
    

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
