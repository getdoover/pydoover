"""Opt-in gzip compression for request bodies.

Compressing request bodies is opt-in (the ``compress=`` argument on the client)
because the ingest server has to be able to decode the ``Content-Encoding``.
gzip is stdlib and universally understood. (zstd support was removed for
simplicity — re-add a codec here and to ``SUPPORTED_ENCODINGS`` if needed.)
"""

from __future__ import annotations

import gzip
from typing import Optional

SUPPORTED_ENCODINGS = ("gzip",)
MIN_COMPRESS_SIZE = 50
_DEFAULT_LEVELS = {"gzip": 6}


def compress_body(
    data: bytes,
    encoding: str,
    level: Optional[int] = None,
) -> bytes:
    """Compress *data* with *encoding* (currently only ``"gzip"``)."""
    if encoding not in SUPPORTED_ENCODINGS:
        raise ValueError(
            f"Unsupported compression encoding {encoding!r}; "
            f"expected one of {SUPPORTED_ENCODINGS}."
        )
    if level is None:
        level = _DEFAULT_LEVELS[encoding]
    return gzip.compress(data, compresslevel=level)
