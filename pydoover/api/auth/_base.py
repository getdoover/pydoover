from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable

import aiohttp

from ._utils import decode_jwt_exp_datetime, token_needs_refresh

DEFAULT_CONTROL_BASE_URL = "https://api.doover.com"
DEFAULT_DATA_BASE_URL = "https://data.doover.com/api"
DEFAULT_AUTH_SERVER_URL = "https://auth.doover.com"


def _normalise_datetime(value: datetime | float | int | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


@dataclass(slots=True)
class AuthProfile:
    profile: str
    token: str | None = None
    token_expires: datetime | None = None
    agent_id: str | None = None
    control_base_url: str | None = None
    data_base_url: str | None = None
    refresh_token: str | None = None
    refresh_token_id: str | None = None
    auth_server_url: str | None = None
    auth_server_client_id: str | None = None

    def __post_init__(self):
        self.token = self.token or None
        self.token_expires = _normalise_datetime(self.token_expires)
        self.agent_id = self.agent_id or None
        self.control_base_url = self.control_base_url or None
        self.data_base_url = self.data_base_url or None
        self.refresh_token = self.refresh_token or None
        self.refresh_token_id = self.refresh_token_id or None
        self.auth_server_url = self.auth_server_url or None
        self.auth_server_client_id = self.auth_server_client_id or None

    @property
    def base_url(self) -> str | None:
        return self.control_base_url

    @base_url.setter
    def base_url(self, value: str | None):
        self.control_base_url = value or None

    @property
    def base_data_url(self) -> str | None:
        return self.data_base_url

    @base_data_url.setter
    def base_data_url(self, value: str | None):
        self.data_base_url = value or None

    @property
    def is_doover2(self) -> bool:
        return True

    def format(self) -> str:
        return (
            f"[profile={self.profile}]\n"
            f"TOKEN={self.token or ''}\n"
            f"TOKEN_EXPIRES={self.token_expires.timestamp() if self.token_expires else ''}\n"
            f"AGENT_ID={self.agent_id or ''}\n"
            f"BASE_URL={self.control_base_url or ''}\n"
            f"REFRESH_TOKEN={self.refresh_token or ''}\n"
            f"REFRESH_TOKEN_ID={self.refresh_token_id or ''}\n"
            f"BASE_DATA_URL={self.data_base_url or ''}\n"
            f"AUTH_SERVER_URL={self.auth_server_url or ''}\n"
            f"AUTH_SERVER_CLIENT_ID={self.auth_server_client_id or ''}\n"
        )


@runtime_checkable
class SyncAuthClient(Protocol):
    @property
    def token(self) -> str | None: ...

    def set_token(self, token: str | None) -> None: ...

    def get_auth_headers(self) -> dict[str, str]: ...

    def ensure_token(self) -> None: ...

    def close(self) -> None: ...


@runtime_checkable
class AsyncAuthClient(Protocol):
    @property
    def token(self) -> str | None: ...

    def set_token(self, token: str | None) -> None: ...

    def get_auth_headers(self) -> dict[str, str]: ...

    async def ensure_token(self) -> None: ...

    async def close(self) -> None: ...


class SyncAuthBase:
    def __init__(
        self,
        *,
        token: str | None = None,
        token_expires: datetime | float | int | None = None,
        timeout: float = 60.0,
    ):
        self.timeout = timeout
        self._token: str | None = token
        self.token_expires: datetime | None = _normalise_datetime(token_expires)
        if self._token and self.token_expires is None:
            self.token_expires = decode_jwt_exp_datetime(self._token)

    @property
    def token(self) -> str | None:
        return self._token

    def set_token(self, token: str | None) -> None:
        self._token = token or None
        self.token_expires = (
            decode_jwt_exp_datetime(self._token) if self._token else None
        )

    def get_auth_headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    def _set_access_token(
        self,
        token: str,
        *,
        token_expires: datetime | float | int | None = None,
        expires_in: float | int | None = None,
    ) -> None:
        self._token = token
        self.token_expires = _normalise_datetime(token_expires)
        if self.token_expires is None:
            self.token_expires = decode_jwt_exp_datetime(token)
        if self.token_expires is None and expires_in is not None:
            self.token_expires = datetime.now(timezone.utc).replace(
                microsecond=0
            ) + timedelta(seconds=float(expires_in))

    def ensure_token(self) -> None:
        if token_needs_refresh(self._token, self.token_expires):
            self.refresh_access_token()

    def refresh_access_token(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        return None


class AsyncAuthBase:
    def __init__(
        self,
        *,
        token: str | None = None,
        token_expires: datetime | float | int | None = None,
        timeout: float = 60.0,
    ):
        self.timeout = timeout
        self._token: str | None = token
        self.token_expires: datetime | None = _normalise_datetime(token_expires)
        if self._token and self.token_expires is None:
            self.token_expires = decode_jwt_exp_datetime(self._token)
        self._session: aiohttp.ClientSession | None = None

    @property
    def token(self) -> str | None:
        return self._token

    def set_token(self, token: str | None) -> None:
        self._token = token or None
        self.token_expires = (
            decode_jwt_exp_datetime(self._token) if self._token else None
        )

    def get_auth_headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    def _set_access_token(
        self,
        token: str,
        *,
        token_expires: datetime | float | int | None = None,
        expires_in: float | int | None = None,
    ) -> None:
        self._token = token
        self.token_expires = _normalise_datetime(token_expires)
        if self.token_expires is None:
            self.token_expires = decode_jwt_exp_datetime(token)
        if self.token_expires is None and expires_in is not None:
            self.token_expires = datetime.now(timezone.utc).replace(
                microsecond=0
            ) + timedelta(seconds=float(expires_in))

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def ensure_token(self) -> None:
        if token_needs_refresh(self._token, self.token_expires):
            await self.refresh_access_token()

    async def refresh_access_token(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
