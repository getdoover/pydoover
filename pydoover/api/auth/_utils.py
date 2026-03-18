import base64
import json
import time
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# Refresh tokens 30 seconds before they expire.
_EXPIRY_BUFFER_SECS = 30


def decode_jwt_exp(token: str) -> float | None:
    """Extract the `exp` claim from a JWT without verification.

    Returns the expiry as a unix timestamp, or None if the token
    has no exp claim or cannot be decoded.
    """
    try:
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return float(payload["exp"])
    except Exception:
        return None


def decode_jwt_exp_datetime(token: str) -> datetime | None:
    exp = decode_jwt_exp(token)
    if exp is None:
        return None
    return datetime.fromtimestamp(exp, tz=timezone.utc)


def token_needs_refresh(
    token: str | None, expires_at: datetime | float | None
) -> bool:
    """Return True if the token is missing or expired (or about to expire)."""
    if token is None:
        return True
    if expires_at is None:
        return False  # No expiry info — assume valid
    if isinstance(expires_at, datetime):
        expires_at = expires_at.timestamp()
    return time.time() >= (expires_at - _EXPIRY_BUFFER_SECS)
