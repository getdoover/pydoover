from typing import Any

from ...utils.snowflake import get_datetime_from_snowflake

from .attachment import Attachment
from .channel import ChannelID

try:
    from google.protobuf import json_format
    from google.protobuf.json_format import MessageToDict
    from google.protobuf.struct_pb2 import Struct
    from ..generated.device_agent.device_agent_pb2 import (
        Message as ProtoMessage,
    )

    _HAS_PROTO = True
except ImportError:
    _HAS_PROTO = False


class Message:
    # pub struct Message {
    #     pub id: SnowflakeID,
    #     pub author_id: SnowflakeID,
    #     pub channel: ChannelID,
    #     pub data: Value,
    #     pub attachments: Vec<Attachment>,
    # }
    def __init__(
        self,
        id: int,
        author_id: int,
        channel: ChannelID,
        data: dict,
        attachments: list[Attachment],
    ):
        self.id = int(id)
        self.author_id = int(author_id)
        self.channel = channel
        self.data = data
        self.attachments = attachments

    @property
    def timestamp(self):
        return get_datetime_from_snowflake(self.id)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["id"],
            data["author_id"],
            ChannelID.from_dict(data["channel"]),
            data["data"],
            [Attachment.from_dict(d) for d in data.get("attachments", [])],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "channel": self.channel.to_dict(),
            "data": self.data,
            "attachments": [a.to_dict() for a in self.attachments],
        }

    @classmethod
    def from_proto(cls, response):
        return cls(
            response.message_id,
            response.author_id,
            ChannelID.from_proto(response.channel),
            MessageToDict(response.data),
            [Attachment.from_proto(a) for a in response.attachments],
        )

    def to_proto(self):
        if not _HAS_PROTO:
            raise RuntimeError("Proto stubs not available")
        data = Struct()
        json_format.ParseDict(self.data, data)

        return ProtoMessage(
            message_id=self.id,
            author_id=self.author_id,
            channel=self.channel.to_proto(),
            data=data,
            attachments=[a.to_proto() for a in self.attachments],
        )
