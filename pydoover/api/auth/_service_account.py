"""Act as a service account from CI, with no stored secret.

A service account can trust an outside identity, such as a GitHub repository's
workflow. Inside that workflow (``permissions: id-token: write``) this fetches
the runner's OIDC token and exchanges it on doover-data's ``/oauth2/token``
(RFC 8693 token exchange) for a token acting as the account, re-exchanging when
it expires:

    POST {data_base_url}/oauth2/token
        grant_type=urn:ietf:params:oauth:grant-type:token-exchange
        subject_token_type=urn:ietf:params:oauth:token-type:jwt
        subject_token=<oidc jwt>
        client_id=<service account id>

The result is a normal Doover bearer, accepted by both data and control.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

import aiohttp
import httpx

from ...models.data.exceptions import TokenRefreshError
from ._base import DEFAULT_DATA_BASE_URL, AsyncAuthBase, SyncAuthBase
from ._trusted_publisher import (
    async_fetch_github_actions_oidc_token,
    fetch_github_actions_oidc_token,
)

log = logging.getLogger(__name__)

# The audience a trusted identity expects by default.
DEFAULT_SERVICE_ACCOUNT_AUDIENCE = "doover"

TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"
JWT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:jwt"


def _exchange_form(service_account_id: str, oidc_token: str) -> dict[str, str]:
    return {
        "grant_type": TOKEN_EXCHANGE_GRANT,
        "subject_token_type": JWT_TOKEN_TYPE,
        "subject_token": oidc_token,
        "client_id": str(service_account_id),
    }


class ServiceAccountAuthClient(SyncAuthBase):
    """A service account's token, exchanged (and re-exchanged on expiry) from
    an outside identity's OIDC token.

    The OIDC token comes from ``oidc_token_provider`` if given, else from the
    GitHub Actions runtime for ``audience``.
    """

    def __init__(
        self,
        service_account_id: str | int,
        *,
        oidc_token_provider: Callable[[], str] | None = None,
        audience: str = DEFAULT_SERVICE_ACCOUNT_AUDIENCE,
        data_base_url: str | None = DEFAULT_DATA_BASE_URL,
        control_base_url: str | None = None,
        timeout: float = 60.0,
    ):
        super().__init__(token=None, timeout=timeout)
        self.service_account_id = str(service_account_id)
        # Where ControlClient(auth=...) sends requests; its default if None.
        self.control_base_url = (
            control_base_url.rstrip("/") if control_base_url else None
        )
        self.audience = audience
        self._oidc_token_provider = oidc_token_provider
        self.data_base_url = (data_base_url or DEFAULT_DATA_BASE_URL).rstrip("/")

    def _get_oidc_token(self) -> str:
        if self._oidc_token_provider is not None:
            return self._oidc_token_provider()
        return fetch_github_actions_oidc_token(self.audience, timeout=self.timeout)

    def refresh_access_token(self) -> None:
        resp = httpx.post(
            f"{self.data_base_url}/oauth2/token",
            data=_exchange_form(self.service_account_id, self._get_oidc_token()),
            timeout=self.timeout,
        )
        if resp.is_error:
            raise TokenRefreshError(
                f"Service account token exchange failed: {resp.status_code} {resp.text}"
            )
        body = resp.json()
        self._set_access_token(body["access_token"], expires_in=body.get("expires_in"))
        log.info(
            "Exchanged an OIDC token for service account %s.", self.service_account_id
        )


class AsyncServiceAccountAuthClient(AsyncAuthBase):
    """Async counterpart of :class:`ServiceAccountAuthClient`."""

    def __init__(
        self,
        service_account_id: str | int,
        *,
        oidc_token_provider: Callable[[], str | Awaitable[str]] | None = None,
        audience: str = DEFAULT_SERVICE_ACCOUNT_AUDIENCE,
        data_base_url: str | None = DEFAULT_DATA_BASE_URL,
        control_base_url: str | None = None,
        timeout: float = 60.0,
    ):
        super().__init__(token=None, timeout=timeout)
        self.service_account_id = str(service_account_id)
        # Where ControlClient(auth=...) sends requests; its default if None.
        self.control_base_url = (
            control_base_url.rstrip("/") if control_base_url else None
        )
        self.audience = audience
        self._oidc_token_provider = oidc_token_provider
        self.data_base_url = (data_base_url or DEFAULT_DATA_BASE_URL).rstrip("/")

    async def _get_oidc_token(self) -> str:
        if self._oidc_token_provider is not None:
            result = self._oidc_token_provider()
            if isinstance(result, Awaitable):
                return await result
            return result
        return await async_fetch_github_actions_oidc_token(
            self.audience, timeout=self.timeout
        )

    async def refresh_access_token(self) -> None:
        form = _exchange_form(self.service_account_id, await self._get_oidc_token())
        session = await self._get_session()
        async with session.post(
            f"{self.data_base_url}/oauth2/token",
            data=form,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise TokenRefreshError(
                    f"Service account token exchange failed: {resp.status} {text}"
                )
            data = await resp.json()
        self._set_access_token(data["access_token"], expires_in=data.get("expires_in"))
        log.info(
            "Exchanged an OIDC token for service account %s.", self.service_account_id
        )
