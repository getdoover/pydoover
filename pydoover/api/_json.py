"""JSON helpers that transparently use orjson when available.

``orjson`` (installed via the ``speedups`` extra) is a significantly faster JSON
parser, which helps when deserialising the large channel/aggregate payloads the
data API returns. When it is not installed we fall back to the standard library
``json`` module, so the clients work either way.
"""

import json
from typing import Any

try:
    import orjson
except ImportError:  # pragma: no cover - exercised by environments without the extra
    orjson = None


def loads(data: str | bytes) -> Any:
    """Deserialise a JSON ``str``/``bytes`` payload, preferring orjson."""
    if orjson is not None:
        return orjson.loads(data)
    return json.loads(data)


def dumps(obj: Any) -> bytes:
    """Serialise *obj* to compact JSON ``bytes``, preferring orjson."""
    if orjson is not None:
        return orjson.dumps(obj)
    return json.dumps(obj, separators=(",", ":")).encode()
