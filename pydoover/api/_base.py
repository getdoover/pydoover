import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from ._auth import decode_jwt_exp, token_needs_refresh
from ..models.attachment import File
from ..utils.snowflake import generate_snowflake_id_at
from .exceptions import (
    ForbiddenError,
    HTTPError,
    NotFoundError,
    UnauthorizedError,
)

log = logging.getLogger(__name__)


def _to_snowflake(value: int | datetime | None) -> int | None:
    """Coerce a datetime or snowflake int to a snowflake int."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return generate_snowflake_id_at(value)
    return int(value)


def _raise_for_status(status: int, text: str, url: str):
    if 200 <= status < 300:
        return
    if status == 401:
        raise UnauthorizedError(text, url)
    if status == 403:
        raise ForbiddenError(text, url)
    if status == 404:
        raise NotFoundError(text, url)
    raise HTTPError(status, text, url)


class BaseClient:
    """Shared logic for sync and async Doover API clients.

    Not intended to be instantiated directly — use :class:`DataClient`
    or :class:`AsyncDataClient` instead.
    """

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        organisation_id: int | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._token: str | None = token
        self._token_expires_at: float | None = decode_jwt_exp(token) if token else None
        self._client_id = client_id
        self._client_secret = client_secret
        self.organisation_id: str | None = (
            str(organisation_id) if organisation_id else None
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    @property
    def token(self) -> str | None:
        return self._token

    def set_token(self, token: str):
        """Manually set the bearer token."""
        self._token = token
        self._token_expires_at = decode_jwt_exp(token)

    @property
    def _needs_refresh(self) -> bool:
        return token_needs_refresh(self._token, self._token_expires_at)

    @property
    def _can_refresh(self) -> bool:
        return bool(self._client_id and self._client_secret)

    def _auth_headers(self, organisation_id: int | None = None) -> dict[str, str]:
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        org = organisation_id or self.organisation_id
        if org:
            headers["X-Org-Id"] = str(org)
        return headers

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def _build_query(params: dict[str, Any]) -> str:
        """Build a query string, filtering out None values and handling lists."""
        filtered = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                filtered[k] = str(v).lower()
            elif isinstance(v, list):
                filtered[k] = v
            else:
                filtered[k] = v
        if not filtered:
            return ""
        return "?" + urlencode(filtered, doseq=True)

    @staticmethod
    def _build_multipart_fields(
        payload: dict[str, Any],
        files: list[File],
    ) -> tuple[str, list[tuple[str, tuple[str, bytes, str]]]]:
        """Return (json_payload_str, file_fields) for multipart uploads."""
        json_str = json.dumps(payload)
        file_fields = []
        for i, f in enumerate(files, start=1):
            file_fields.append(
                (f"attachment-{i}", (f.filename, f.data, f.content_type))
            )
        return json_str, file_fields
