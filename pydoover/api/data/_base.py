import inspect
import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from ..auth import (
    AsyncDataServiceAuthClient,
    AsyncDoover2AuthClient,
    AuthProfile,
    DataServiceAuthClient,
    Doover2AuthClient,
)
from ..auth._base import (
    DEFAULT_DATA_BASE_URL,
    AsyncAuthClient,
    SyncAuthClient,
    _normalise_datetime,
)
from ...models.attachment import File
from ...utils.snowflake import generate_snowflake_id_at
from ...models.exceptions import (
    ForbiddenError,
    HTTPError,
    NotFoundError,
    UnauthorizedError,
)

log = logging.getLogger(__name__)


class Unset:
    """Sentinel for distinguishing 'not provided' from ``None``."""

    def __repr__(self):
        return "UNSET"

    def __bool__(self):
        return False


UNSET = Unset()


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
        *,
        auth: SyncAuthClient | AsyncAuthClient,
        owns_auth: bool = False,
        organisation_id: int | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.organisation_id: int | None = (
            int(organisation_id) if organisation_id else None
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._owns_auth = owns_auth

    @property
    def token(self) -> str | None:
        return self.auth.token

    def set_token(self, token: str):
        """Manually set the bearer token."""
        self.auth.set_token(token)

    def _auth_headers(self, organisation_id: int | None = None) -> dict[str, str]:
        headers = dict(self.auth.get_auth_headers())
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
            if v is None or isinstance(v, Unset):
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


_AUTH_KWARGS = (
    "auth",
    "profile",
    "data_base_url",
    "control_base_url",
    "token",
    "token_expires",
    "client_id",
    "client_secret",
    "refresh_token",
    "refresh_token_id",
    "auth_server_url",
    "auth_server_client_id",
)


def _consume_auth_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {name: kwargs.pop(name, None) for name in _AUTH_KWARGS}


def _normalize_data_base_url(
    base_url: str | None,
    data_base_url: str | None,
) -> str:
    if base_url and data_base_url and base_url.rstrip("/") != data_base_url.rstrip("/"):
        raise ValueError("`base_url` and `data_base_url` must match when both are provided.")
    return (data_base_url or base_url or DEFAULT_DATA_BASE_URL).rstrip("/")


def _has_value(value: Any) -> bool:
    return value is not None


def _is_async_callable(value: Any) -> bool:
    return callable(value) and inspect.iscoroutinefunction(value)


def _validate_profile_input(profile: Any):
    if profile is None:
        return
    if not isinstance(profile, (str, AuthProfile)):
        raise TypeError("`profile` must be a profile name or AuthProfile instance.")


def _validate_sync_auth(auth: Any) -> SyncAuthClient:
    missing = [
        name
        for name in ("token", "set_token", "get_auth_headers", "ensure_token")
        if not hasattr(auth, name)
    ]
    if missing:
        raise TypeError(
            "Sync data clients require an auth client with "
            + ", ".join(sorted(missing))
            + "."
        )
    ensure_token = getattr(auth, "ensure_token")
    close = getattr(auth, "close", None)
    if _is_async_callable(ensure_token) or _is_async_callable(close):
        raise TypeError("Sync data clients require a synchronous auth client.")
    return auth


def _validate_async_auth(auth: Any) -> AsyncAuthClient:
    missing = [
        name
        for name in ("token", "set_token", "get_auth_headers", "ensure_token")
        if not hasattr(auth, name)
    ]
    if missing:
        raise TypeError(
            "Async data clients require an auth client with "
            + ", ".join(sorted(missing))
            + "."
        )
    if not _is_async_callable(getattr(auth, "ensure_token")):
        raise TypeError("Async data clients require an asynchronous auth client.")
    return auth


def build_sync_auth(
    *,
    base_url: str | None = None,
    timeout: float,
    auth: SyncAuthClient | None = None,
    profile: str | AuthProfile | None = None,
    data_base_url: str | None = None,
    control_base_url: str | None = None,
    token: str | None = None,
    token_expires: datetime | float | int | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    refresh_token: str | None = None,
    refresh_token_id: str | None = None,
    auth_server_url: str | None = None,
    auth_server_client_id: str | None = None,
) -> tuple[SyncAuthClient, str, bool]:
    _validate_profile_input(profile)
    raw_inputs = {
        "profile": profile,
        "data_base_url": data_base_url,
        "control_base_url": control_base_url,
        "token": token,
        "token_expires": token_expires,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "refresh_token_id": refresh_token_id,
        "auth_server_url": auth_server_url,
        "auth_server_client_id": auth_server_client_id,
        "base_url": base_url,
    }

    if auth is not None:
        auth = _validate_sync_auth(auth)
        if any(_has_value(value) for value in raw_inputs.values()):
            raise ValueError("`auth` cannot be combined with other auth configuration.")
        return auth, getattr(auth, "data_base_url", resolved_data_base_url := _normalize_data_base_url(base_url, data_base_url)), False

    if profile is not None:
        auth_client = Doover2AuthClient.from_profile(profile, timeout=timeout)
        if token is not None or token_expires is not None:
            current_token = token if token is not None else auth_client.token
            if current_token is not None:
                auth_client._set_access_token(
                    current_token,
                    token_expires=token_expires,
                )
            else:
                auth_client.token_expires = _normalise_datetime(token_expires)
        if control_base_url is not None:
            auth_client.control_base_url = control_base_url.rstrip("/")
        if data_base_url is not None or base_url is not None:
            auth_client.data_base_url = _normalize_data_base_url(base_url, data_base_url)
        if refresh_token is not None:
            auth_client.refresh_token = refresh_token
        if refresh_token_id is not None:
            auth_client.refresh_token_id = refresh_token_id
        if auth_server_url is not None:
            auth_client.auth_server_url = auth_server_url.rstrip("/")
        if auth_server_client_id is not None:
            auth_client.auth_server_client_id = auth_server_client_id
        return auth_client, auth_client.data_base_url, True

    resolved_data_base_url = _normalize_data_base_url(base_url, data_base_url)
    doover2_inputs_present = any(
        _has_value(value)
        for value in (refresh_token, auth_server_url, auth_server_client_id)
    )
    data_service_inputs_present = bool(client_id and client_secret)

    if doover2_inputs_present:
        return (
            Doover2AuthClient(
                token=token,
                token_expires=token_expires,
                refresh_token=refresh_token,
                refresh_token_id=refresh_token_id,
                control_base_url=control_base_url,
                data_base_url=resolved_data_base_url,
                auth_server_url=auth_server_url,
                auth_server_client_id=auth_server_client_id,
                timeout=timeout,
            ),
            resolved_data_base_url,
            True,
        )

    if data_service_inputs_present:
        return (
            DataServiceAuthClient(
                token=token,
                token_expires=token_expires,
                data_base_url=resolved_data_base_url,
                client_id=client_id,
                client_secret=client_secret,
                timeout=timeout,
            ),
            resolved_data_base_url,
            True,
        )

    if control_base_url is not None:
        return (
            Doover2AuthClient(
                token=token,
                token_expires=token_expires,
                refresh_token=refresh_token,
                refresh_token_id=refresh_token_id,
                control_base_url=control_base_url,
                data_base_url=resolved_data_base_url,
                auth_server_url=auth_server_url or None,
                auth_server_client_id=auth_server_client_id,
                timeout=timeout,
            ),
            resolved_data_base_url,
            True,
        )

    return (
        DataServiceAuthClient(
            token=token,
            token_expires=token_expires,
            data_base_url=resolved_data_base_url,
            client_id=client_id,
            client_secret=client_secret,
            timeout=timeout,
        ),
        resolved_data_base_url,
        True,
    )


def build_async_auth(
    *,
    base_url: str | None = None,
    timeout: float,
    auth: AsyncAuthClient | None = None,
    profile: str | AuthProfile | None = None,
    data_base_url: str | None = None,
    control_base_url: str | None = None,
    token: str | None = None,
    token_expires: datetime | float | int | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    refresh_token: str | None = None,
    refresh_token_id: str | None = None,
    auth_server_url: str | None = None,
    auth_server_client_id: str | None = None,
) -> tuple[AsyncAuthClient, str, bool]:
    _validate_profile_input(profile)
    raw_inputs = {
        "profile": profile,
        "data_base_url": data_base_url,
        "control_base_url": control_base_url,
        "token": token,
        "token_expires": token_expires,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "refresh_token_id": refresh_token_id,
        "auth_server_url": auth_server_url,
        "auth_server_client_id": auth_server_client_id,
        "base_url": base_url,
    }

    if auth is not None:
        auth = _validate_async_auth(auth)
        if any(_has_value(value) for value in raw_inputs.values()):
            raise ValueError("`auth` cannot be combined with other auth configuration.")
        return auth, getattr(auth, "data_base_url", resolved_data_base_url := _normalize_data_base_url(base_url, data_base_url)), False

    if profile is not None:
        auth_client = AsyncDoover2AuthClient.from_profile(profile, timeout=timeout)
        if token is not None or token_expires is not None:
            current_token = token if token is not None else auth_client.token
            if current_token is not None:
                auth_client._set_access_token(
                    current_token,
                    token_expires=token_expires,
                )
            else:
                auth_client.token_expires = _normalise_datetime(token_expires)
        if control_base_url is not None:
            auth_client.control_base_url = control_base_url.rstrip("/")
        if data_base_url is not None or base_url is not None:
            auth_client.data_base_url = _normalize_data_base_url(base_url, data_base_url)
        if refresh_token is not None:
            auth_client.refresh_token = refresh_token
        if refresh_token_id is not None:
            auth_client.refresh_token_id = refresh_token_id
        if auth_server_url is not None:
            auth_client.auth_server_url = auth_server_url.rstrip("/")
        if auth_server_client_id is not None:
            auth_client.auth_server_client_id = auth_server_client_id
        return auth_client, auth_client.data_base_url, True

    resolved_data_base_url = _normalize_data_base_url(base_url, data_base_url)
    doover2_inputs_present = any(
        _has_value(value)
        for value in (refresh_token, auth_server_url, auth_server_client_id)
    )
    data_service_inputs_present = bool(client_id and client_secret)

    if doover2_inputs_present:
        return (
            AsyncDoover2AuthClient(
                token=token,
                token_expires=token_expires,
                refresh_token=refresh_token,
                refresh_token_id=refresh_token_id,
                control_base_url=control_base_url,
                data_base_url=resolved_data_base_url,
                auth_server_url=auth_server_url,
                auth_server_client_id=auth_server_client_id,
                timeout=timeout,
            ),
            resolved_data_base_url,
            True,
        )

    if data_service_inputs_present:
        return (
            AsyncDataServiceAuthClient(
                token=token,
                token_expires=token_expires,
                data_base_url=resolved_data_base_url,
                client_id=client_id,
                client_secret=client_secret,
                timeout=timeout,
            ),
            resolved_data_base_url,
            True,
        )

    if control_base_url is not None:
        return (
            AsyncDoover2AuthClient(
                token=token,
                token_expires=token_expires,
                refresh_token=refresh_token,
                refresh_token_id=refresh_token_id,
                control_base_url=control_base_url,
                data_base_url=resolved_data_base_url,
                auth_server_url=auth_server_url or None,
                auth_server_client_id=auth_server_client_id,
                timeout=timeout,
            ),
            resolved_data_base_url,
            True,
        )

    return (
        AsyncDataServiceAuthClient(
            token=token,
            token_expires=token_expires,
            data_base_url=resolved_data_base_url,
            client_id=client_id,
            client_secret=client_secret,
            timeout=timeout,
        ),
        resolved_data_base_url,
        True,
    )
