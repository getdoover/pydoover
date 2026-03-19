from __future__ import annotations

import inspect
import json
import keyword
import platform
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from ..auth import (
    AsyncDoover2AuthClient,
    AuthProfile,
    Doover2AuthClient,
)
from ..auth._base import (
    DEFAULT_CONTROL_BASE_URL,
    AsyncAuthClient,
    SyncAuthClient,
    _normalise_datetime,
)
from ... import __version__
from ...models import control as control_models
from ...models.data.exceptions import (
    ForbiddenError,
    HTTPError,
    NotFoundError,
    UnauthorizedError,
)

_python_version = platform.python_version()


def _build_user_agent(http_lib: str, http_lib_version: str) -> str:
    return (
        f"pydoover/{__version__} Python/{_python_version} {http_lib}/{http_lib_version}"
    )


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


def _normalize_control_base_url(base_url: str | None, control_base_url: str | None) -> str:
    if base_url and control_base_url and base_url.rstrip("/") != control_base_url.rstrip("/"):
        raise ValueError("`base_url` and `control_base_url` must match when both are provided.")
    return (control_base_url or base_url or DEFAULT_CONTROL_BASE_URL).rstrip("/")


def _validate_profile_input(profile: Any):
    if profile is None:
        return
    if not isinstance(profile, (str, AuthProfile)):
        raise TypeError("`profile` must be a profile name or AuthProfile instance.")


def _is_async_callable(value: Any) -> bool:
    return callable(value) and inspect.iscoroutinefunction(value)


def _validate_sync_auth(auth: Any) -> SyncAuthClient:
    missing = [
        name
        for name in ("token", "set_token", "get_auth_headers", "ensure_token")
        if not hasattr(auth, name)
    ]
    if missing:
        raise TypeError(
            "Sync control clients require an auth client with "
            + ", ".join(sorted(missing))
            + "."
        )
    ensure_token = getattr(auth, "ensure_token")
    close = getattr(auth, "close", None)
    if _is_async_callable(ensure_token) or _is_async_callable(close):
        raise TypeError("Sync control clients require a synchronous auth client.")
    return auth


def _validate_async_auth(auth: Any) -> AsyncAuthClient:
    missing = [
        name
        for name in ("token", "set_token", "get_auth_headers", "ensure_token")
        if not hasattr(auth, name)
    ]
    if missing:
        raise TypeError(
            "Async control clients require an auth client with "
            + ", ".join(sorted(missing))
            + "."
        )
    if not _is_async_callable(getattr(auth, "ensure_token")):
        raise TypeError("Async control clients require an asynchronous auth client.")
    return auth


_AUTH_KWARGS = (
    "auth",
    "profile",
    "control_base_url",
    "token",
    "token_expires",
    "refresh_token",
    "refresh_token_id",
    "auth_server_url",
    "auth_server_client_id",
)


def _consume_auth_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {name: kwargs.pop(name, None) for name in _AUTH_KWARGS}


def build_sync_control_auth(
    *,
    base_url: str | None = None,
    timeout: float,
    auth: SyncAuthClient | None = None,
    profile: str | AuthProfile | None = None,
    control_base_url: str | None = None,
    token: str | None = None,
    token_expires=None,
    refresh_token: str | None = None,
    refresh_token_id: str | None = None,
    auth_server_url: str | None = None,
    auth_server_client_id: str | None = None,
) -> tuple[SyncAuthClient, str, bool]:
    _validate_profile_input(profile)

    if auth is not None:
        auth_client = _validate_sync_auth(auth)
        resolved = _normalize_control_base_url(
            base_url,
            control_base_url or getattr(auth_client, "control_base_url", None),
        )
        return auth_client, resolved, False

    if profile is not None:
        auth_client = Doover2AuthClient.from_profile(profile, timeout=timeout)
        if token is not None:
            auth_client.set_token(token)
            auth_client.token_expires = _normalise_datetime(token_expires)
        if control_base_url is not None:
            auth_client.control_base_url = control_base_url.rstrip("/")
        if refresh_token is not None:
            auth_client.refresh_token = refresh_token
        if refresh_token_id is not None:
            auth_client.refresh_token_id = refresh_token_id
        if auth_server_url is not None:
            auth_client.auth_server_url = auth_server_url.rstrip("/")
        if auth_server_client_id is not None:
            auth_client.auth_server_client_id = auth_server_client_id
    else:
        auth_client = Doover2AuthClient(
            token=token,
            token_expires=token_expires,
            refresh_token=refresh_token,
            refresh_token_id=refresh_token_id,
            control_base_url=_normalize_control_base_url(base_url, control_base_url),
            auth_server_url=auth_server_url,
            auth_server_client_id=auth_server_client_id,
            timeout=timeout,
        )

    resolved = _normalize_control_base_url(
        base_url,
        control_base_url or auth_client.control_base_url,
    )
    auth_client.control_base_url = resolved
    return auth_client, resolved, True


def build_async_control_auth(
    *,
    base_url: str | None = None,
    timeout: float,
    auth: AsyncAuthClient | None = None,
    profile: str | AuthProfile | None = None,
    control_base_url: str | None = None,
    token: str | None = None,
    token_expires=None,
    refresh_token: str | None = None,
    refresh_token_id: str | None = None,
    auth_server_url: str | None = None,
    auth_server_client_id: str | None = None,
) -> tuple[AsyncAuthClient, str, bool]:
    _validate_profile_input(profile)

    if auth is not None:
        auth_client = _validate_async_auth(auth)
        resolved = _normalize_control_base_url(
            base_url,
            control_base_url or getattr(auth_client, "control_base_url", None),
        )
        return auth_client, resolved, False

    if profile is not None:
        auth_client = AsyncDoover2AuthClient.from_profile(profile, timeout=timeout)
        if token is not None:
            auth_client.set_token(token)
            auth_client.token_expires = _normalise_datetime(token_expires)
        if control_base_url is not None:
            auth_client.control_base_url = control_base_url.rstrip("/")
        if refresh_token is not None:
            auth_client.refresh_token = refresh_token
        if refresh_token_id is not None:
            auth_client.refresh_token_id = refresh_token_id
        if auth_server_url is not None:
            auth_client.auth_server_url = auth_server_url.rstrip("/")
        if auth_server_client_id is not None:
            auth_client.auth_server_client_id = auth_server_client_id
    else:
        auth_client = AsyncDoover2AuthClient(
            token=token,
            token_expires=token_expires,
            refresh_token=refresh_token,
            refresh_token_id=refresh_token_id,
            control_base_url=_normalize_control_base_url(base_url, control_base_url),
            auth_server_url=auth_server_url,
            auth_server_client_id=auth_server_client_id,
            timeout=timeout,
        )

    resolved = _normalize_control_base_url(
        base_url,
        control_base_url or auth_client.control_base_url,
    )
    auth_client.control_base_url = resolved
    return auth_client, resolved, True


class BaseControlClient:
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
        self.organisation_id = int(organisation_id) if organisation_id else None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._owns_auth = owns_auth

    @property
    def token(self) -> str | None:
        return self.auth.token

    def set_token(self, token: str):
        self.auth.set_token(token)

    def _auth_headers(self, organisation_id: int | None = None) -> dict[str, str]:
        headers = dict(self.auth.get_auth_headers())
        org = organisation_id or self.organisation_id
        if org:
            headers["X-Doover-Organisation"] = str(org)
        return headers

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def _build_query(params: dict[str, Any]) -> str:
        filtered = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                filtered[key] = str(value).lower()
            elif isinstance(value, list):
                filtered[key] = value
            else:
                filtered[key] = value
        if not filtered:
            return ""
        return "?" + urlencode(filtered, doseq=True)

    def _serialize_body(self, body: Any, schema_name: str | None, method: str) -> Any:
        if body is None:
            return None
        if isinstance(body, control_models.ControlModel):
            if schema_name is None:
                return body.to_dict()
            return body.to_version(schema_name, method=method)
        if isinstance(body, dict):
            return body
        raise TypeError("Control request bodies must be dicts or ControlModel instances.")

    def _deserialize_model(self, schema_name: str, data: dict[str, Any]):
        info = control_models.resolve_control_schema(schema_name)
        model_cls = getattr(control_models, info["model"])
        return model_cls.from_version(info["version"], data)

    def _deserialize_page(self, schema_name: str, data: dict[str, Any]):
        info = control_models.resolve_control_schema(schema_name)
        model_cls = getattr(control_models, info["model"])
        results = [
            model_cls.from_version(info["version"], item)
            for item in data.get("results") or []
        ]
        return control_models.ControlPage(
            count=data.get("count", 0),
            next=data.get("next"),
            previous=data.get("previous"),
            results=results,
        )

    def _deserialize_list(self, item_schema: str, data: list[dict[str, Any]]):
        info = control_models.resolve_control_schema(item_schema)
        model_cls = getattr(control_models, info["model"])
        return [model_cls.from_version(info["version"], item) for item in data]


class _ControlGroupBase:
    def __init__(self, root: BaseControlClient):
        self._root = root
