from typing import Any

from .grpc_stubs.device_agent_pb2 import (
    TurnCredentialResponse,
    File as ProtoFile,
    Attachment as ProtoAttachment,
    Message as ProtoMessage,
    ChannelID as ProtoChannelID,
)


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
        self.agent_id = agent_id
        self.name = name

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data["agent_id"],
            data["name"],
        )

    @classmethod
    def from_proto(cls, response: ProtoChannelID):
        return cls(
            response.agent_id,
            response.name,
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
        self.id = id
        self.author_id = author_id
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

    @classmethod
    def from_proto(cls, response: ProtoMessage):
        return cls(
            response.message_id,
            response.author_id,
            ChannelID.from_proto(response.channel),
            response.data.MessageToDict(),
            [Attachment.from_proto(a) for a in response.attachments],
        )


class TurnCredentials:
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
    def from_proto(cls, response: TurnCredentialResponse):
        return cls(
            response.username,
            response.credential,
            response.ttl,
            response.expires_at,
            list(response.uris),
        )
