from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest

from pydoover.api import AsyncDataClient, DataClient
from pydoover.api.auth import (
    AsyncDataServiceAuthClient,
    AsyncDoover2AuthClient,
    AuthProfile,
    ConfigManager,
    DataServiceAuthClient,
    Doover2AuthClient,
)
from pydoover.models.exceptions import TokenRefreshError


def make_jwt(expires_at: datetime) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": int(expires_at.timestamp())}).encode()
    ).rstrip(b"=")
    return f"{header.decode()}.{payload.decode()}.sig"


def future_token(minutes: int = 5) -> str:
    return make_jwt(datetime.now(timezone.utc) + timedelta(minutes=minutes))


def expired_token(minutes: int = 5) -> str:
    return make_jwt(datetime.now(timezone.utc) - timedelta(minutes=minutes))


class SyncResponse:
    def __init__(self, *, payload: dict[str, object], status_code: int = 200, text: str = ""):
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self.is_error = status_code >= 400

    def json(self) -> dict[str, object]:
        return self._payload


class AsyncResponse:
    def __init__(self, *, payload: dict[str, object], status: int = 200, text: str = ""):
        self._payload = payload
        self.status = status
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self) -> dict[str, object]:
        return self._payload

    async def text(self) -> str:
        return self._text


class AsyncSession:
    def __init__(self, response: AsyncResponse):
        self.response = response

    def post(self, *args, **kwargs):
        return self.response


class InjectedSyncAuth:
    def __init__(self, token: str = "sync-token", data_base_url: str = "https://example.test/api"):
        self.token = token
        self.data_base_url = data_base_url
        self.ensure_calls = 0
        self.closed = False

    def set_token(self, token: str | None) -> None:
        self.token = token

    def get_auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def ensure_token(self) -> None:
        self.ensure_calls += 1

    def close(self) -> None:
        self.closed = True


class InjectedAsyncAuth:
    def __init__(self, token: str = "async-token", data_base_url: str = "https://example.test/api"):
        self.token = token
        self.data_base_url = data_base_url
        self.ensure_calls = 0
        self.closed = False

    def set_token(self, token: str | None) -> None:
        self.token = token

    def get_auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def ensure_token(self) -> None:
        self.ensure_calls += 1

    async def close(self) -> None:
        self.closed = True


def configure_temp_config(monkeypatch: pytest.MonkeyPatch, tmp_path):
    config_dir = tmp_path / ".doover"
    monkeypatch.setattr(ConfigManager, "directory", str(config_dir))
    monkeypatch.setattr(ConfigManager, "filepath", str(config_dir / "config"))
    return config_dir


def test_config_manager_parses_reduced_profile_format():
    config = ConfigManager()
    config.parse(
        "\n".join(
            [
                "[profile=default]",
                "TOKEN=test-token",
                "TOKEN_EXPIRES=1710806400",
                "AGENT_ID=agent-1",
                "BASE_URL=https://api.doover.com",
                "REFRESH_TOKEN=refresh",
                "REFRESH_TOKEN_ID=refresh-id",
                "BASE_DATA_URL=https://data.doover.com/api",
                "AUTH_SERVER_URL=https://auth.doover.com",
                "AUTH_SERVER_CLIENT_ID=client-id",
            ]
        )
    )

    entry = config.get("default")
    assert entry is not None
    assert entry.control_base_url == "https://api.doover.com"
    assert entry.data_base_url == "https://data.doover.com/api"
    assert entry.auth_server_client_id == "client-id"


def test_config_manager_parses_legacy_doover2_profile_and_rewrites_reduced_format():
    legacy = "\n".join(
        [
            "[profile=dv2]",
            "USERNAME=user@example.com",
            f"PASSWORD={base64.b64encode(b'secret').decode()}",
            "TOKEN=test-token",
            "TOKEN_EXPIRES=1710806400",
            "AGENT_ID=agent-1",
            "BASE_URL=https://api.doover.com",
            "IS_DOOVER2=True",
            "REFRESH_TOKEN=refresh",
            "REFRESH_TOKEN_ID=refresh-id",
            "BASE_DATA_URL=https://data.doover.com/api",
            "AUTH_SERVER_URL=https://auth.doover.com",
            "AUTH_SERVER_CLIENT_ID=client-id",
        ]
    )

    config = ConfigManager()
    config.parse(legacy)

    dumped = config.dump()
    assert "USERNAME=" not in dumped
    assert "PASSWORD=" not in dumped
    assert "IS_DOOVER2=" not in dumped
    assert "REFRESH_TOKEN=refresh" in dumped


def test_config_manager_preserves_legacy_doover1_blocks_verbatim():
    legacy_v1 = "\n".join(
        [
            "[profile=legacy]",
            "USERNAME=legacy-user",
            f"PASSWORD={base64.b64encode(b'legacy-pass').decode()}",
            "TOKEN=",
            "TOKEN_EXPIRES=",
            "AGENT_ID=",
            "BASE_URL=https://my.doover.com",
            "IS_DOOVER2=False",
        ]
    )

    config = ConfigManager()
    config.parse(legacy_v1)

    assert config.entries == {}
    assert config.dump() == legacy_v1


def test_config_manager_round_trips_mixed_managed_and_preserved_blocks():
    legacy_v1 = "\n".join(
        [
            "[profile=legacy]",
            "USERNAME=legacy-user",
            f"PASSWORD={base64.b64encode(b'legacy-pass').decode()}",
            "TOKEN=",
            "TOKEN_EXPIRES=",
            "AGENT_ID=",
            "BASE_URL=https://my.doover.com",
            "IS_DOOVER2=False",
        ]
    )
    reduced = "\n".join(
        [
            "[profile=default]",
            "TOKEN=test-token",
            "TOKEN_EXPIRES=1710806400",
            "AGENT_ID=agent-1",
            "BASE_URL=https://api.doover.com",
            "REFRESH_TOKEN=refresh",
            "REFRESH_TOKEN_ID=refresh-id",
            "BASE_DATA_URL=https://data.doover.com/api",
            "AUTH_SERVER_URL=https://auth.doover.com",
            "AUTH_SERVER_CLIENT_ID=client-id",
        ]
    )

    config = ConfigManager()
    config.parse(f"{legacy_v1}\n\n{reduced}")

    dumped = config.dump()
    assert legacy_v1 in dumped
    assert "[profile=default]" in dumped
    assert "USERNAME=legacy-user" in dumped


def test_doover2_auth_client_uses_valid_token_without_refresh(monkeypatch):
    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: pytest.fail("unexpected refresh"))
    auth = Doover2AuthClient(
        token=future_token(),
        refresh_token="refresh",
        auth_server_client_id="client-id",
    )

    auth.ensure_token()

    assert auth.token is not None


def test_doover2_auth_client_refreshes_expired_token(monkeypatch):
    refreshed = future_token()
    calls = []

    def fake_post(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        return SyncResponse(payload={"access_token": refreshed, "expires_in": 600})

    monkeypatch.setattr("httpx.post", fake_post)
    auth = Doover2AuthClient(
        token=expired_token(),
        refresh_token="refresh",
        refresh_token_id="refresh-id",
        auth_server_url="https://auth.doover.com",
        auth_server_client_id="client-id",
    )

    auth.ensure_token()

    assert auth.token == refreshed
    assert calls[0][0] == "https://auth.doover.com/oauth2/token"
    assert calls[0][1]["grant_type"] == "refresh_token"


def test_doover2_auth_client_requires_refresh_inputs():
    auth = Doover2AuthClient(token=expired_token())

    with pytest.raises(TokenRefreshError):
        auth.ensure_token()


@pytest.mark.asyncio
async def test_async_doover2_auth_client_refreshes_expired_token(monkeypatch):
    refreshed = future_token()
    auth = AsyncDoover2AuthClient(
        token=expired_token(),
        refresh_token="refresh",
        refresh_token_id="refresh-id",
        auth_server_url="https://auth.doover.com",
        auth_server_client_id="client-id",
    )
    session = AsyncSession(
        AsyncResponse(payload={"access_token": refreshed, "expires_in": 600})
    )

    async def fake_get_session():
        return session

    monkeypatch.setattr(
        auth,
        "_get_session",
        fake_get_session,
    )

    await auth.ensure_token()

    assert auth.token == refreshed


def test_doover2_auth_client_from_profile_name(monkeypatch, tmp_path):
    configure_temp_config(monkeypatch, tmp_path)
    profile = AuthProfile(
        profile="default",
        token=future_token(),
        control_base_url="https://api.doover.com",
        data_base_url="https://data.doover.com/api",
        refresh_token="refresh",
        refresh_token_id="refresh-id",
        auth_server_url="https://auth.doover.com",
        auth_server_client_id="client-id",
    )
    config = ConfigManager("default")
    config.create(profile)
    config.write()

    auth = Doover2AuthClient.from_profile("default")

    assert auth.data_base_url == "https://data.doover.com/api"
    assert auth.auth_server_client_id == "client-id"


def test_doover2_auth_client_from_profile_object():
    profile = AuthProfile(
        profile="default",
        token=future_token(),
        control_base_url="https://api.doover.com",
        data_base_url="https://data.doover.com/api",
        refresh_token="refresh",
        refresh_token_id="refresh-id",
        auth_server_url="https://auth.doover.com",
        auth_server_client_id="client-id",
    )

    auth = Doover2AuthClient.from_profile(profile)

    assert auth.control_base_url == "https://api.doover.com"
    assert auth.refresh_token == "refresh"


def test_data_service_auth_client_uses_valid_token_without_refresh(monkeypatch):
    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: pytest.fail("unexpected refresh"))
    auth = DataServiceAuthClient(
        token=future_token(),
        client_id="client-id",
        client_secret="secret",
    )

    auth.ensure_token()

    assert auth.token is not None


def test_data_service_auth_client_refreshes_expired_token(monkeypatch):
    refreshed = future_token()

    def fake_post(url, data=None, headers=None, timeout=None):
        assert url == "https://data.doover.com/api/oauth2/token"
        assert data == {"grant_type": "client_credentials", "scope": ""}
        assert headers["Authorization"].startswith("Basic ")
        return SyncResponse(payload={"access_token": refreshed, "expires_in": 600})

    monkeypatch.setattr("httpx.post", fake_post)
    auth = DataServiceAuthClient(
        token=expired_token(),
        client_id="client-id",
        client_secret="secret",
    )

    auth.ensure_token()

    assert auth.token == refreshed


def test_data_service_auth_client_requires_client_credentials():
    auth = DataServiceAuthClient(token=expired_token())

    with pytest.raises(TokenRefreshError):
        auth.ensure_token()


@pytest.mark.asyncio
async def test_async_data_service_auth_client_refreshes_expired_token(monkeypatch):
    refreshed = future_token()
    auth = AsyncDataServiceAuthClient(
        token=expired_token(),
        client_id="client-id",
        client_secret="secret",
    )
    session = AsyncSession(
        AsyncResponse(payload={"access_token": refreshed, "expires_in": 600})
    )

    async def fake_get_session():
        return session

    monkeypatch.setattr(
        auth,
        "_get_session",
        fake_get_session,
    )

    await auth.ensure_token()

    assert auth.token == refreshed


def test_data_client_accepts_injected_sync_auth_without_owning_lifecycle():
    auth = InjectedSyncAuth()
    client = DataClient(auth=auth)

    try:
        assert client.auth is auth
        assert client.base_url == auth.data_base_url
        assert client.token == "sync-token"
        client.set_token("updated")
        assert auth.token == "updated"
    finally:
        client.close()

    assert auth.closed is False


@pytest.mark.asyncio
async def test_async_data_client_accepts_injected_async_auth_without_owning_lifecycle():
    auth = InjectedAsyncAuth()
    client = AsyncDataClient(auth=auth)

    await client.setup()
    try:
        assert client.auth is auth
        assert client.base_url == auth.data_base_url
        assert client.token == "async-token"
        client.set_token("updated")
        assert auth.token == "updated"
    finally:
        await client.close()

    assert auth.closed is False


def test_data_client_profile_builds_doover2_auth(monkeypatch, tmp_path):
    configure_temp_config(monkeypatch, tmp_path)
    config = ConfigManager("default")
    config.create(
        AuthProfile(
            profile="default",
            token=future_token(),
            control_base_url="https://api.doover.com",
            data_base_url="https://data.doover.com/api",
        )
    )
    config.write()

    client = DataClient(profile="default")
    try:
        assert isinstance(client.auth, Doover2AuthClient)
        assert client.base_url == "https://data.doover.com/api"
    finally:
        client.close()


def test_data_client_profile_object_builds_doover2_auth():
    client = DataClient(
        profile=AuthProfile(
            profile="default",
            token=future_token(),
            control_base_url="https://api.doover.com",
            data_base_url="https://data.doover.com/api",
        )
    )

    try:
        assert isinstance(client.auth, Doover2AuthClient)
    finally:
        client.close()


def test_data_client_base_url_token_is_backward_compatible():
    client = DataClient(base_url="https://data.doover.com/api", token=future_token())

    try:
        assert isinstance(client.auth, DataServiceAuthClient)
        assert client.base_url == "https://data.doover.com/api"
    finally:
        client.close()


def test_data_client_token_with_control_base_url_defaults_to_doover2_auth():
    client = DataClient(
        token=future_token(),
        control_base_url="https://api.doover.com",
        data_base_url="https://data.doover.com/api",
    )

    try:
        assert isinstance(client.auth, Doover2AuthClient)
    finally:
        client.close()


def test_data_client_token_with_client_credentials_builds_data_service_auth():
    client = DataClient(
        token=future_token(),
        data_base_url="https://data.doover.com/api",
        client_id="client-id",
        client_secret="secret",
    )

    try:
        assert isinstance(client.auth, DataServiceAuthClient)
    finally:
        client.close()


def test_data_client_rejects_conflicting_base_url_alias():
    with pytest.raises(ValueError):
        DataClient(
            base_url="https://data-1.doover.com/api",
            data_base_url="https://data-2.doover.com/api",
            token=future_token(),
        )


def test_data_client_auth_is_mutually_exclusive_with_raw_auth_kwargs():
    with pytest.raises(ValueError):
        DataClient(auth=InjectedSyncAuth(), token=future_token())


def test_data_client_rejects_async_auth():
    with pytest.raises(TypeError):
        DataClient(auth=InjectedAsyncAuth())


@pytest.mark.asyncio
async def test_async_data_client_rejects_sync_auth():
    with pytest.raises(TypeError):
        AsyncDataClient(auth=InjectedSyncAuth())


def test_data_client_org_header_behavior_is_unchanged():
    client = DataClient(
        auth=InjectedSyncAuth(),
        organisation_id=123,
    )

    try:
        assert client._auth_headers() == {
            "Authorization": "Bearer sync-token",
            "X-Org-Id": "123",
        }
        assert client._auth_headers(456) == {
            "Authorization": "Bearer sync-token",
            "X-Org-Id": "456",
        }
    finally:
        client.close()
