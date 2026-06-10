"""Helpers for the dual ``data`` / ``data_json`` payload fields on device-agent protos.

``google.protobuf.Struct`` stores every number as a double, so integers lose
their type (``42`` -> ``42.0``) and values above 2**53 silently lose precision
— fatal for snowflake IDs embedded in payloads. The ``data_json`` proto fields
carry the same payload as a JSON string instead, which round-trips integers
exactly and is several times faster to encode/decode.

Writers populate both fields so either side of an app/agent version skew keeps
working; readers prefer ``data_json`` whenever it is set. Once the fleet is on
versions that read ``data_json``, the ``data`` Struct writes can be dropped.
"""

import json
from typing import Any

try:
    import orjson
except ImportError:  # pragma: no cover - exercised by environments without the extra
    orjson = None

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct


def dumps_payload(data: Any) -> str:
    """Serialise a payload to a compact JSON string, preferring orjson."""
    if orjson is not None:
        return orjson.dumps(data).decode()
    return json.dumps(data, separators=(",", ":"))


def loads_payload(raw: str | bytes) -> Any:
    """Deserialise a JSON payload, preferring orjson."""
    if orjson is not None:
        return orjson.loads(raw)
    return json.loads(raw)


def encode_data_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Return kwargs carrying *data* in both wire formats.

    ``{"data": Struct, "data_json": str}`` — splat into a proto constructor.
    """
    struct = Struct()
    json_format.ParseDict(data, struct)
    return {"data": struct, "data_json": dumps_payload(data)}


def decode_data_fields(message) -> dict[str, Any]:
    """Read a payload from a proto message, preferring the lossless ``data_json``."""
    if message.data_json:
        return loads_payload(message.data_json)
    return json_format.MessageToDict(message.data)
