from __future__ import annotations

import logging

import aiohttp

from ...models.exceptions import TokenRefreshError
from ._base import (
    DEFAULT_AUTH_SERVER_URL,
    DEFAULT_CONTROL_BASE_URL,
    DEFAULT_DATA_BASE_URL,
    AsyncAuthBase,
    AuthProfile,
)
from ._config import ConfigManager

log = logging.getLogger(__name__)


class AsyncDoover2AuthClient(AsyncAuthBase):
    def __init__(
        self,
        *,
        token: str | None = None,
        token_expires=None,
        refresh_token: str | None = None,
        refresh_token_id: str | None = None,
        control_base_url: str | None = DEFAULT_CONTROL_BASE_URL,
        data_base_url: str = DEFAULT_DATA_BASE_URL,
        auth_server_url: str | None = DEFAULT_AUTH_SERVER_URL,
        auth_server_client_id: str | None = None,
        timeout: float = 60.0,
    ):
        super().__init__(
            token=token,
            token_expires=token_expires,
            timeout=timeout,
        )
        self.refresh_token = refresh_token
        self.refresh_token_id = refresh_token_id
        self.control_base_url = (control_base_url or DEFAULT_CONTROL_BASE_URL).rstrip("/")
        self.data_base_url = (data_base_url or DEFAULT_DATA_BASE_URL).rstrip("/")
        self.auth_server_url = (auth_server_url or DEFAULT_AUTH_SERVER_URL).rstrip("/")
        self.auth_server_client_id = auth_server_client_id

    @classmethod
    def from_profile(
        cls,
        profile: str | AuthProfile,
        *,
        timeout: float = 60.0,
        config_manager: ConfigManager | None = None,
    ) -> "AsyncDoover2AuthClient":
        if isinstance(profile, AuthProfile):
            profile_data = profile
        else:
            manager = config_manager or ConfigManager(profile)
            profile_data = manager.get(profile)
            if profile_data is None:
                raise RuntimeError(f"No configuration found for profile {profile}.")

        return cls(
            token=profile_data.token,
            token_expires=profile_data.token_expires,
            refresh_token=profile_data.refresh_token,
            refresh_token_id=profile_data.refresh_token_id,
            control_base_url=profile_data.control_base_url or DEFAULT_CONTROL_BASE_URL,
            data_base_url=profile_data.data_base_url or DEFAULT_DATA_BASE_URL,
            auth_server_url=profile_data.auth_server_url or DEFAULT_AUTH_SERVER_URL,
            auth_server_client_id=profile_data.auth_server_client_id,
            timeout=timeout,
        )

    async def refresh_access_token(self):
        if not (
            self.refresh_token and self.auth_server_url and self.auth_server_client_id
        ):
            raise TokenRefreshError(
                "Token expired and Doover 2 refresh configuration is incomplete."
            )

        session = await self._get_session()
        async with session.post(
            f"{self.auth_server_url}/oauth2/token",
            params={
                "grant_type": "refresh_token",
                "access_token": self.token,
                "refresh_token": self.refresh_token,
                "client_id": self.auth_server_client_id,
            },
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise TokenRefreshError(f"Token refresh failed: {resp.status} {text}")
            data = await resp.json()

        self._set_access_token(
            data["access_token"],
            expires_in=data.get("expires_in"),
        )
        log.info("Refreshed access token.")
