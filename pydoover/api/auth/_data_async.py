from __future__ import annotations

import logging
from base64 import b64encode

import aiohttp

from ...models.exceptions import TokenRefreshError
from ._base import AsyncAuthBase, DEFAULT_DATA_BASE_URL

log = logging.getLogger(__name__)


class AsyncDataServiceAuthClient(AsyncAuthBase):
    def __init__(
        self,
        *,
        token: str | None = None,
        token_expires=None,
        data_base_url: str = DEFAULT_DATA_BASE_URL,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 60.0,
    ):
        super().__init__(
            token=token,
            token_expires=token_expires,
            timeout=timeout,
        )
        self.data_base_url = data_base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret

    async def refresh_access_token(self):
        if not (self.client_id and self.client_secret):
            raise TokenRefreshError(
                "Token expired and no client credentials configured for refresh."
            )

        credentials = b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        session = await self._get_session()
        async with session.post(
            f"{self.data_base_url}/oauth2/token",
            data={"grant_type": "client_credentials", "scope": ""},
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
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
