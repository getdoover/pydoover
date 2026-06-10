"""Tests for the dual data/data_json payload encoding on device-agent protos.

google.protobuf.Struct stores all numbers as doubles, so integers passed
through the legacy ``data`` field lose their type and — above 2**53 — their
value. The ``data_json`` field must round-trip them exactly, while readers
stay compatible with old peers that only populate ``data``.
"""

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct

from pydoover.models.data import Aggregate, Attachment, Message
from pydoover.models.data.channel import ChannelID
from pydoover.models.data._proto_json import (
    decode_data_fields,
    encode_data_fields,
)
from pydoover.models.generated.device_agent import device_agent_pb2

SNOWFLAKE = 1918273645261234177  # > 2**53, unrepresentable as a double
PAYLOAD = {"count": 42, "ratio": 1.5, "snowflake_id": SNOWFLAKE, "name": "x"}


def test_encode_populates_both_fields():
    req = device_agent_pb2.UpdateAggregateRequest(
        channel_name="c", **encode_data_fields(PAYLOAD)
    )
    assert req.data_json
    assert req.data.fields["count"].number_value == 42


def test_decode_prefers_data_json_and_preserves_ints():
    req = device_agent_pb2.UpdateAggregateRequest(
        channel_name="c", **encode_data_fields(PAYLOAD)
    )
    decoded = decode_data_fields(req)
    assert decoded == PAYLOAD
    assert isinstance(decoded["count"], int)
    assert decoded["snowflake_id"] == SNOWFLAKE


def test_decode_falls_back_to_struct_for_old_peers():
    struct = Struct()
    json_format.ParseDict({"count": 42}, struct)
    req = device_agent_pb2.UpdateAggregateRequest(channel_name="c", data=struct)
    assert decode_data_fields(req) == {"count": 42.0}


def test_message_round_trips_through_proto():
    msg = Message(
        id=SNOWFLAKE,
        author_id=2,
        channel=ChannelID(3, "chan"),
        data=PAYLOAD,
        attachments=[],
    )
    restored = Message.from_proto(msg.to_proto())
    assert restored.data == PAYLOAD
    assert restored.data["snowflake_id"] == SNOWFLAKE


def test_aggregate_round_trips_through_proto():
    agg = Aggregate(data=PAYLOAD, attachments=[], last_updated=None)
    restored = Aggregate.from_proto(agg.to_proto())
    assert restored.data == PAYLOAD
    assert isinstance(restored.data["count"], int)


def test_attachments_still_round_trip():
    agg = Aggregate(
        data={"a": 1},
        attachments=[
            Attachment.from_dict(
                {"filename": "f.bin", "content_type": "b/b", "size": 1, "url": "u"}
            )
        ],
        last_updated=None,
    )
    restored = Aggregate.from_proto(agg.to_proto())
    assert restored.attachments[0].filename == "f.bin"
