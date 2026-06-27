"""Trusted-publisher auth: exchange a CI OIDC token for a Doover access token.

This is the client side of Doover "trusted publishing" (PyPI-style). A CI job
holds a short-lived OIDC token minted by its provider (GitHub Actions to start)
and exchanges it, with no stored Doover secret, for a short-lived Doover access
token scoped to a single application:

    POST {control_base_url}/publishers/mint-token/
        {"provider": "GH", "token": "<oidc jwt>"}
    -> {"token": "<doover bearer>", "expiry": "<iso8601>"}

The vended token is scoped to the publisher(s) matched from the OIDC token's
repository + workflow claims, and can act on any application that points at one of
them. The result is a normal Doover bearer, so this plugs in anywhere a
``SyncAuthClient`` / ``AsyncAuthClient`` is accepted (e.g. ``ControlClient(auth=...)``).
"""

from __future__ import annotations

import logging
import os
from typing import Awaitable, Callable

import aiohttp
import httpx

from ...models.data.exceptions import TokenRefreshError
from ._base import DEFAULT_CONTROL_BASE_URL, AsyncAuthBase, SyncAuthBase

log = logging.getLogger(__name__)

# Must match doover-control's settings.DOOVER_OIDC_AUDIENCE. The CI workflow must
# request its OIDC token with exactly this audience or the exchange is rejected.
DEFAULT_DOOVER_OIDC_AUDIENCE = "https://api.doover.com"

MINT_TOKEN_PATH = "/publishers/mint-token/"

# GitHub Actions exposes these to a job with `permissions: id-token: write`.
_GH_REQUEST_URL_ENV = "ACTIONS_ID_TOKEN_REQUEST_URL"
_GH_REQUEST_TOKEN_ENV = "ACTIONS_ID_TOKEN_REQUEST_TOKEN"


def fetch_github_actions_oidc_token(
    audience: str = DEFAULT_DOOVER_OIDC_AUDIENCE, *, timeout: float = 30.0
) -> str:
    """Fetch a GitHub Actions OIDC token for ``audience`` (sync).

    Only works inside a GitHub Actions job that has ``permissions: id-token: write``.
    Raises TokenRefreshError if the runtime variables are missing.
    """
    request_url = os.environ.get(_GH_REQUEST_URL_ENV)
    request_token = os.environ.get(_GH_REQUEST_TOKEN_ENV)
    if not (request_url and request_token):
        raise TokenRefreshError(
            "Not running in a GitHub Actions job with id-token permission "
            f"({_GH_REQUEST_URL_ENV}/{_GH_REQUEST_TOKEN_ENV} not set). Grant "
            "`permissions: id-token: write` to the workflow/job."
        )
    resp = httpx.get(
        request_url,
        params={"audience": audience},
        headers={"Authorization": f"Bearer {request_token}"},
        timeout=timeout,
    )
    if resp.is_error:
        raise TokenRefreshError(
            f"Failed to fetch GitHub OIDC token: {resp.status_code} {resp.text}"
        )
    return resp.json()["value"]


async def async_fetch_github_actions_oidc_token(
    audience: str = DEFAULT_DOOVER_OIDC_AUDIENCE, *, timeout: float = 30.0
) -> str:
    """Fetch a GitHub Actions OIDC token for ``audience`` (async)."""
    request_url = os.environ.get(_GH_REQUEST_URL_ENV)
    request_token = os.environ.get(_GH_REQUEST_TOKEN_ENV)
    if not (request_url and request_token):
        raise TokenRefreshError(
            "Not running in a GitHub Actions job with id-token permission "
            f"({_GH_REQUEST_URL_ENV}/{_GH_REQUEST_TOKEN_ENV} not set). Grant "
            "`permissions: id-token: write` to the workflow/job."
        )
    async with aiohttp.ClientSession() as session:
        async with session.get(
            request_url,
            params={"audience": audience},
            headers={"Authorization": f"Bearer {request_token}"},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise TokenRefreshError(
                    f"Failed to fetch GitHub OIDC token: {resp.status} {text}"
                )
            data = await resp.json()
    return data["value"]


def _missing_oidc_token() -> str:
    raise TokenRefreshError(
        "No OIDC token available to exchange. Pass oidc_token=, an "
        "oidc_token_provider= callable, or run inside GitHub Actions with "
        "provider='GH' and id-token permission."
    )


class TrustedPublisherAuthClient(SyncAuthBase):
    """Mints (and re-mints on expiry) a Doover token from a CI OIDC token.

    Provide the OIDC token one of three ways:
      * ``oidc_token`` — a pre-fetched OIDC JWT (single use; can't be re-minted
        once both it and the Doover token expire);
      * ``oidc_token_provider`` — a zero-arg callable returning a fresh OIDC JWT
        (enables transparent re-minting);
      * nothing, with ``provider="GH"`` — auto-fetch from the GitHub Actions
        runtime each time (the recommended path inside a workflow).
    """

    def __init__(
        self,
        *,
        provider: str = "GH",
        oidc_token: str | None = None,
        oidc_token_provider: Callable[[], str] | None = None,
        audience: str = DEFAULT_DOOVER_OIDC_AUDIENCE,
        control_base_url: str | None = DEFAULT_CONTROL_BASE_URL,
        timeout: float = 60.0,
    ):
        super().__init__(token=None, timeout=timeout)
        self.provider = provider
        self.audience = audience
        self._oidc_token = oidc_token
        self._oidc_token_provider = oidc_token_provider
        self.control_base_url = (control_base_url or DEFAULT_CONTROL_BASE_URL).rstrip(
            "/"
        )

    def _get_oidc_token(self) -> str:
        if self._oidc_token_provider is not None:
            return self._oidc_token_provider()
        if self._oidc_token is not None:
            return self._oidc_token
        if self.provider == "GH":
            return fetch_github_actions_oidc_token(self.audience, timeout=self.timeout)
        return _missing_oidc_token()

    def refresh_access_token(self) -> None:
        oidc_token = self._get_oidc_token()
        resp = httpx.post(
            f"{self.control_base_url}{MINT_TOKEN_PATH}",
            json={"provider": self.provider, "token": oidc_token},
            timeout=self.timeout,
        )
        if resp.is_error:
            raise TokenRefreshError(
                f"Trusted publisher token exchange failed: {resp.status_code} {resp.text}"
            )
        # Token is a JWT; SyncAuthBase derives the expiry from its `exp` claim.
        self._set_access_token(resp.json()["token"])
        log.info("Exchanged %s OIDC token for a Doover token.", self.provider)


class AsyncTrustedPublisherAuthClient(AsyncAuthBase):
    """Async counterpart of :class:`TrustedPublisherAuthClient`."""

    def __init__(
        self,
        *,
        provider: str = "GH",
        oidc_token: str | None = None,
        oidc_token_provider: Callable[[], str | Awaitable[str]] | None = None,
        audience: str = DEFAULT_DOOVER_OIDC_AUDIENCE,
        control_base_url: str | None = DEFAULT_CONTROL_BASE_URL,
        timeout: float = 60.0,
    ):
        super().__init__(token=None, timeout=timeout)
        self.provider = provider
        self.audience = audience
        self._oidc_token = oidc_token
        self._oidc_token_provider = oidc_token_provider
        self.control_base_url = (control_base_url or DEFAULT_CONTROL_BASE_URL).rstrip(
            "/"
        )

    async def _get_oidc_token(self) -> str:
        if self._oidc_token_provider is not None:
            result = self._oidc_token_provider()
            if isinstance(result, Awaitable):
                return await result
            return result
        if self._oidc_token is not None:
            return self._oidc_token
        if self.provider == "GH":
            return await async_fetch_github_actions_oidc_token(
                self.audience, timeout=self.timeout
            )
        return _missing_oidc_token()

    async def refresh_access_token(self) -> None:
        oidc_token = await self._get_oidc_token()
        session = await self._get_session()
        async with session.post(
            f"{self.control_base_url}{MINT_TOKEN_PATH}",
            json={"provider": self.provider, "token": oidc_token},
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise TokenRefreshError(
                    f"Trusted publisher token exchange failed: {resp.status} {text}"
                )
            data = await resp.json()
        self._set_access_token(data["token"])
        log.info("Exchanged %s OIDC token for a Doover token.", self.provider)
