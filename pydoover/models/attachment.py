from typing import Any

try:
    from .generated.device_agent.device_agent_pb2 import (
        Attachment as ProtoAttachment,
        File as ProtoFile,
    )

    _HAS_PROTO = True
except ImportError:
    _HAS_PROTO = False


class Attachment:
    #     pub filename: String,
    #     pub content_type: Option<String>,
    #     pub size: u64,
    #     pub url: String,
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
    def from_proto(cls, response):
        return cls(
            response.filename,
            response.content_type,
            response.size_bytes,
            response.url,
        )

    def to_proto(self):
        if not _HAS_PROTO:
            raise RuntimeError("Proto stubs not available")
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
    def from_proto(cls, response):
        return cls(
            response.filename,
            response.content_type,
            response.size_bytes,
            response.data,
        )

    def to_proto(self):
        if not _HAS_PROTO:
            raise RuntimeError("Proto stubs not available")
        return ProtoFile(
            filename=self.filename,
            content_type=self.content_type,
            size_bytes=self.size,
            data=self.data,
        )
