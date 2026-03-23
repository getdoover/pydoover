import json

import pytest

from pydoover.api import ControlClient
from pydoover.api.control import ControlMethodUnavailableError
from pydoover.models.control import ControlPage, DeviceType, Theme


THEME_WITH_ID = {
    "id": 7,
    "accent_colour": "#112233",
    "brand_logo_colour": "#445566",
    "navbar_colour": "#778899",
    "navbar_text_colour": "#ffffff",
    "sidebar_colour": "#101010",
    "sidebar_text_colour": "#eeeeee",
}


class DummySyncAuth:
    def __init__(self):
        self.token = "test-token"
        self.control_base_url = "https://control.example"

    def set_token(self, token: str):
        self.token = token

    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def ensure_token(self):
        return None

    def close(self):
        return None


class DummyResponse:
    def __init__(self, status_code: int, *, json_body=None, content: bytes | None = None):
        self.status_code = status_code
        if json_body is not None:
            self._json_body = json_body
            self.content = json.dumps(json_body).encode()
            self.text = self.content.decode()
        else:
            self._json_body = None
            self.content = content or b""
            self.text = self.content.decode("utf-8", errors="ignore")

    def json(self):
        if self._json_body is None:
            raise ValueError("No JSON body configured")
        return self._json_body


class DummySession:
    def __init__(self, response: DummyResponse):
        self.response = response
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method: str, url: str, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response

    def close(self):
        return None


def make_client(response: DummyResponse) -> tuple[ControlClient, DummySession]:
    client = ControlClient(
        auth=DummySyncAuth(),
        base_url="https://control.example",
    )
    session = DummySession(response)
    client._session = session
    return client, session


def test_sync_client_exposes_generated_groups():
    client, _ = make_client(DummyResponse(204))

    assert hasattr(client, "applications")
    assert hasattr(client, "devices")
    assert hasattr(client, "organisations")
    assert hasattr(client.organisations, "billing")
    assert hasattr(client.organisations.billing, "products")
    assert hasattr(client.organisations.pending_users, "approve")
    assert not hasattr(client, "public")
    assert not hasattr(client, "pwa")

    client.close()


def test_sync_client_parses_model_response_and_builds_headers():
    client, session = make_client(DummyResponse(200, json_body=THEME_WITH_ID))

    theme = client.themes.retrieve("7", organisation_id=55)

    assert isinstance(theme, Theme)
    assert theme.id == 7
    assert session.calls[0][0] == "GET"
    assert session.calls[0][1] == "https://control.example/themes/7/"
    assert session.calls[0][2]["headers"]["X-Doover-Organisation"] == "55"

    client.close()


def test_sync_client_parses_paginated_response():
    client, session = make_client(
        DummyResponse(
            200,
            json_body={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [THEME_WITH_ID],
            },
        )
    )

    page = client.themes.list(page=2)

    assert isinstance(page, ControlPage)
    assert isinstance(page.results[0], Theme)
    assert session.calls[0][1] == "https://control.example/themes/?page=2"

    client.close()


def test_sync_client_handles_bytes_and_none_responses():
    bytes_client, _ = make_client(DummyResponse(200, content=b"archive-bytes"))
    none_client, _ = make_client(DummyResponse(204))

    assert bytes_client.devices.installer_tarball("9") == b"archive-bytes"
    assert none_client.permissions.sync() is None

    bytes_client.close()
    none_client.close()


def test_sync_client_can_deserialize_model_lists():
    client, _ = make_client(DummyResponse(204))

    items = client._deserialize_list("ThemeSerializerWithIdList", [THEME_WITH_ID])

    assert len(items) == 1
    assert isinstance(items[0], Theme)

    client.close()


def test_sync_client_can_lookup_control_methods_by_model_name_or_class():
    client, _ = make_client(DummyResponse(204))

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

    client.close()
