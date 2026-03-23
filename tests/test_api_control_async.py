import json

import pytest

from pydoover.api import AsyncControlClient
from pydoover.api.control import ControlMethodUnavailableError
from pydoover.models.control import ControlPage, DeviceType, Theme


THEME_WITH_ID = {
    "id": 8,
    "accent_colour": "#223344",
    "brand_logo_colour": "#556677",
    "navbar_colour": "#8899aa",
    "navbar_text_colour": "#ffffff",
    "sidebar_colour": "#111111",
    "sidebar_text_colour": "#eeeeee",
}


class DummyAsyncAuth:
    def __init__(self):
        self.token = "test-token"
        self.control_base_url = "https://control.example"

    def set_token(self, token: str):
        self.token = token

    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    async def ensure_token(self):
        return None

    async def close(self):
        return None


class DummyAsyncResponse:
    def __init__(self, status: int, *, json_body=None, content: bytes | None = None):
        self.status = status
        if json_body is not None:
            self._json_body = json_body
            self._content = json.dumps(json_body).encode()
        else:
            self._json_body = None
            self._content = content or b""

    async def text(self):
        return self._content.decode("utf-8", errors="ignore")

    async def read(self):
        return self._content


class DummyAsyncRequestContext:
    def __init__(self, response: DummyAsyncResponse):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyAsyncSession:
    def __init__(self, response: DummyAsyncResponse):
        self.response = response
        self.calls: list[tuple[str, str, dict]] = []
        self.closed = False

    def request(self, method: str, url: str, **kwargs):
        self.calls.append((method, url, kwargs))
        return DummyAsyncRequestContext(self.response)

    async def close(self):
        self.closed = True


def make_client(response: DummyAsyncResponse) -> tuple[AsyncControlClient, DummyAsyncSession]:
    client = AsyncControlClient(
        auth=DummyAsyncAuth(),
        base_url="https://control.example",
    )
    session = DummyAsyncSession(response)
    client._session = session
    return client, session


@pytest.mark.asyncio
async def test_async_client_exposes_generated_groups():
    client, _ = make_client(DummyAsyncResponse(204))

    assert hasattr(client, "applications")
    assert hasattr(client.organisations.billing, "products")
    assert hasattr(client.organisations.pending_users, "approve")
    assert not hasattr(client, "public")
    assert not hasattr(client, "pwa")

    await client.close()


@pytest.mark.asyncio
async def test_async_client_parses_model_and_page_responses():
    model_client, model_session = make_client(DummyAsyncResponse(200, json_body=THEME_WITH_ID))
    page_client, page_session = make_client(
        DummyAsyncResponse(
            200,
            json_body={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [THEME_WITH_ID],
            },
        )
    )

    theme = await model_client.themes.retrieve("8", organisation_id=66)
    page = await page_client.themes.list(page=3)

    assert isinstance(theme, Theme)
    assert theme.id == 8
    assert model_session.calls[0][2]["headers"]["X-Doover-Organisation"] == "66"
    assert isinstance(page, ControlPage)
    assert isinstance(page.results[0], Theme)
    assert page_session.calls[0][1] == "https://control.example/themes/?page=3"

    await model_client.close()
    await page_client.close()


@pytest.mark.asyncio
async def test_async_client_handles_bytes_and_none_responses():
    bytes_client, _ = make_client(DummyAsyncResponse(200, content=b"archive-bytes"))
    none_client, _ = make_client(DummyAsyncResponse(204))

    assert await bytes_client.devices.installer_tarball("9") == b"archive-bytes"
    assert await none_client.permissions.sync() is None

    await bytes_client.close()
    await none_client.close()


@pytest.mark.asyncio
async def test_async_client_can_lookup_control_methods_by_model_name_or_class():
    client, _ = make_client(DummyAsyncResponse(204))

    by_name = client.get_control_methods("DeviceType")
    by_class = client.get_control_methods(DeviceType)

    assert by_name.model is DeviceType
    assert by_name.model_name == "DeviceType"
    assert by_name.available_operations() == ("get", "post", "patch", "put", "list")
    assert by_name.model is by_class.model
    assert by_name._get is not None
    assert by_name._post is not None
    assert by_name._patch is not None
    assert by_name._put is not None
    assert by_name._list is not None
    assert by_name._get.__name__ == "types_retrieve"
    assert by_name._post.__name__ == "types_create"
    assert by_name._patch.__name__ == "types_partial"
    assert by_name._put.__name__ == "types_update"
    assert by_name._list.__name__ == "types_list"
    assert client.get_control_method("DeviceType", "retrieve") == by_name._get
    assert client.get_control_method(DeviceType, "post") == by_name._post

    themes = client.get_control_methods(Theme)
    assert themes.available_operations() == ("get", "patch", "put", "list")
    with pytest.raises(ControlMethodUnavailableError):
        themes.post()

    await client.close()
