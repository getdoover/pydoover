from datetime import datetime
from enum import Flag, auto
from typing import Any

from google.protobuf.json_format import MessageToDict

from .grpc_stubs.device_agent_pb2 import (
    File as ProtoFile,
    Attachment as ProtoAttachment,
    Message as ProtoMessage,
    ChannelID as ProtoChannelID,
    TurnCredential as ProtoTurnCredential,
    Aggregate as ProtoAggregate,
)

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct


class EventSubscription(Flag):
    message_create = auto()
    message_update = auto()
    aggregate_update = auto()
    oneshot_message = auto()
    all = message_create | message_update | aggregate_update | oneshot_message


class Attachment:
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

    @classmethod
    def from_proto(cls, response: ProtoAttachment):
        return cls(
            response.filename,
            response.content_type,
            response.size_bytes,
            response.url,
        )

    def to_proto(self):
        return ProtoAttachment(
            filename=self.filename,
            content_type=self.content_type,
            size_bytes=self.size,
            url=self.url,
        )

    def to_dict(self):
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
            "url": self.url,
        }


class File:
    def __init__(self, filename: str, content_type: str, size: int, data: bytes):
        self.filename = filename
        self.content_type = content_type
        self.size = size
        self.data = data

    @classmethod
    def from_proto(cls, response: ProtoFile):
        return cls(
            response.filename,
            response.content_type,
            response.size_bytes,
            response.data,
        )

    def to_proto(self):
        return ProtoFile(
            filename=self.filename,
            content_type=self.content_type,
            size_bytes=self.size,
            data=self.data,
        )


class ChannelID:
    def __init__(self, agent_id: int, name: str):
        self.agent_id = int(agent_id)
        self.name = name

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["agent_id"],
            data["name"],
        )

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "name": self.name,
        }

    @classmethod
    def from_proto(cls, response: ProtoChannelID):
        return cls(
            response.agent_id,
            response.name,
        )

    def to_proto(self):
        return ProtoChannelID(
            agent_id=self.agent_id,
            name=self.name,
        )


class Message:
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["id"],
            data["author_id"],
            ChannelID.from_dict(data["channel"]),
            data["data"],
            [Attachment.from_dict(d) for d in data["attachments"]],
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
    def from_proto(cls, response: ProtoMessage):
        return cls(
            response.message_id,
            response.author_id,
            ChannelID.from_proto(response.channel),
            MessageToDict(response.data),
            [Attachment.from_proto(a) for a in response.attachments],
        )

    def to_proto(self):
        data = Struct()
        json_format.ParseDict(self.data, data)

        return ProtoMessage(
            message_id=self.id,
            author_id=self.author_id,
            channel=self.channel.to_proto(),
            data=data,
            attachments=[a.to_proto() for a in self.attachments],
        )


class MessageCreateEvent:
    # #[derive(Serialize, Event)]
    # pub struct MessageCreate {
    #     pub id: Option<SnowflakeID>,
    #     pub author_id: SnowflakeID,
    #     pub channel: ChannelID,
    #     pub data: Value,
    # }
    def __init__(
        self, id: int, author_id: int, channel: ChannelID, data: dict[str, Any]
    ):
        self.id = id
        self.author_id = author_id
        self.channel = channel
        self.data = data

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["id"],
            data["author_id"],
            ChannelID.from_dict(data["channel"]),
            data["data"],
        )


class OneShotMessage(MessageCreateEvent):
    # just to support isinstance checks and really highlight that this isn't a real message.
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
        owner_id: int,
        channel_name: str,
        author_id: int,
        organisation_id: int,
        message: Message,
        request_data: dict[str, Any],
    ):
        self.owner_id = owner_id
        self.channel_name = channel_name
        self.author_id = author_id
        self.organisation_id = organisation_id
        self.message = message
        self.request_data = request_data

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["owner_id"],
            data["channel_name"],
            data["author_id"],
            data["organisation_id"],
            Message.from_dict(data["message"]),
            data.get("request_data", {}),
        )


class TurnCredential:
    # pub struct TurnTokenResponse {
    #     username: String,
    #     credential: String,
    #     ttl: u64,
    #     expires_at: u64,
    #     uris: Vec<String>,
    # }
    def __init__(
        self, username: str, credential: str, ttl: int, expires_at: int, uris: list[str]
    ):
        self.username = username
        self.credential = credential
        self.ttl = ttl
        self.expires_at = expires_at
        self.uris = uris

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["username"],
            data["credential"],
            data["ttl"],
            data["expires_at"],
            data["uris"],
        )

    @classmethod
    def from_proto(cls, resp: ProtoTurnCredential):
        return cls(
            resp.username,
            resp.credential,
            resp.ttl,
            resp.expires_at,
            list(resp.uris),
        )

    def to_proto(self):
        return ProtoTurnCredential(
            username=self.username,
            credential=self.credential,
            ttl=self.ttl,
            expires_at=self.expires_at,
            uris=self.uris,
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
        ts = payload.get("last_updated")
        dt = ts and datetime.fromtimestamp(ts / 1000.0)
        return cls(
            payload["data"],
            [Attachment.from_dict(a) for a in payload.get("attachments", [])],
            dt,
        )

    @classmethod
    def from_proto(cls, response: ProtoAggregate):
        return cls(
            MessageToDict(response.data),
            [Attachment.from_proto(a) for a in response.attachments],
            response.last_updated
            and datetime.fromtimestamp(response.last_updated / 1000.0),
        )

    def to_proto(self):
        data = Struct()
        json_format.ParseDict(self.data, data)

        return ProtoAggregate(
            data=data,
            attachments=[a.to_proto() for a in self.attachments],
            last_updated=self.last_updated
            and int(self.last_updated.timestamp() * 1000.0),
        )

    def to_dict(self):
        return {
            "data": self.data,
            "attachments": [a.to_dict() for a in self.attachments],
            "last_updated": self.last_updated and self.last_updated.timestamp() * 1000,
        }
