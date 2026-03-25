from datetime import datetime, timezone
from typing import Any

from .attachment import Attachment

try:
    from google.protobuf import json_format
    from google.protobuf.json_format import MessageToDict
    from google.protobuf.struct_pb2 import Struct
    from ..generated.device_agent.device_agent_pb2 import (
        Aggregate as ProtoAggregate,
    )

    _HAS_PROTO = True
except ImportError:
    _HAS_PROTO = False


class Aggregate:
    # pub struct ChannelAggregate {
    #     pub data: Value,
    #     pub attachments: Vec<Attachment>,
    #     pub last_updated: Option<u64>,
    # }
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
        dt = ts and datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
        return cls(
            payload["data"],
            [Attachment.from_dict(a) for a in payload.get("attachments", [])],
            dt,
        )

    @classmethod
    def from_proto(cls, response):
        return cls(
            MessageToDict(response.data),
            [Attachment.from_proto(a) for a in response.attachments],
            response.last_updated
            and datetime.fromtimestamp(response.last_updated / 1000.0, tz=timezone.utc),
        )

    def to_proto(self):
        if not _HAS_PROTO:
            raise RuntimeError("Proto stubs not available")
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
