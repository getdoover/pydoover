from __future__ import annotations

import json
import time
from collections.abc import Collection
from pathlib import Path
from typing import Any

import httpx

from ..auth._base import SyncAuthClient
from ._base import (
    BaseControlClient,
    _build_user_agent,
    _consume_auth_kwargs,
    _raise_for_status,
    build_sync_control_auth,
)
from ._generated_sync import ControlClientGroups, _attach_sync_groups


def _coerce_file_value(field_name: str, value: Any) -> tuple[str, bytes, str]:
    if isinstance(value, Path):
        return value.name, value.read_bytes(), "application/octet-stream"
    if isinstance(value, (bytes, bytearray)):
        return f"{field_name}.bin", bytes(value), "application/octet-stream"
    if isinstance(value, str):
        path = Path(value)
        if path.exists():
            return path.name, path.read_bytes(), "application/octet-stream"
        return f"{field_name}.txt", value.encode(), "text/plain"
    return f"{field_name}.bin", json.dumps(value).encode(), "application/json"


class ControlClient(ControlClientGroups, BaseControlClient):
    auth: SyncAuthClient

    def __init__(self, base_url: str | None = None, **kwargs):
        timeout = kwargs.get("timeout", 60.0)
        self._user_agent = _build_user_agent("httpx", httpx.__version__)
        auth, resolved_base_url, owns_auth = build_sync_control_auth(
            base_url=base_url,
            timeout=timeout,
            **_consume_auth_kwargs(kwargs),
        )
        super().__init__(resolved_base_url, auth=auth, owns_auth=owns_auth, **kwargs)
        self.auth = auth
        self._session = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": self._user_agent},
        )
        _attach_sync_groups(self)

    def close(self):
        self._session.close()
        if self._owns_auth:
            self.auth.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _execute(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        body_schema: str | None = None,
        body_mode: str = "json",
        binary_fields: Collection[str] | None = None,
        organisation_id: int | None = None,
        response_kind: str = "raw",
        response_schema: str | None = None,
        item_schema: str | None = None,
    ):
        self.auth.ensure_token()
        url = self._build_url(path)
        if params:
            url += self._build_query(params)
        headers = self._auth_headers(organisation_id)
        payload = self._serialize_body(body, body_schema, method)

        for attempt in range(self.max_retries):
            try:
                request_kwargs: dict[str, Any] = {"headers": headers}

                if payload is not None:
                    if body_mode == "multipart":
                        data: dict[str, str] = {}
                        files: dict[str, tuple[str, bytes, str]] = {}
                        for key, value in payload.items():
                            if value is None:
                                continue
                            if binary_fields and key in binary_fields:
                                files[key] = _coerce_file_value(key, value)
                            elif isinstance(value, (dict, list)):
                                data[key] = json.dumps(value)
                            elif isinstance(value, bool):
                                data[key] = str(value).lower()
                            else:
                                data[key] = str(value)
                        request_kwargs["data"] = data
                        if files:
                            request_kwargs["files"] = files
                    else:
                        request_kwargs["json"] = payload

                resp = self._session.request(method, url, **request_kwargs)
                status = resp.status_code
                if status >= 500:
                    if attempt == self.max_retries - 1:
                        _raise_for_status(status, resp.text, url)
                elif 400 <= status < 500:
                    _raise_for_status(status, resp.text, url)
                else:
                    return self._parse_response(
                        resp,
                        response_kind=response_kind,
                        response_schema=response_schema,
                        item_schema=item_schema,
                    )
            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise
            except httpx.HTTPError:
                if attempt == self.max_retries - 1:
                    raise
            time.sleep(self.retry_delay * (2**attempt))

    def _parse_response(
        self,
        response: httpx.Response,
        *,
        response_kind: str,
        response_schema: str | None,
        item_schema: str | None,
    ):
        if response_kind == "none":
            return None
        if response_kind == "bytes":
            return response.content
        if not response.content:
            return None
        if response_kind == "raw":
            return response.json()
        data = response.json()
        if response_kind == "model" and response_schema is not None:
            return self._deserialize_model(response_schema, data)
        if response_kind == "page" and response_schema is not None:
            return self._deserialize_page(response_schema, data)
        if response_kind == "list_model" and item_schema is not None:
            return self._deserialize_list(item_schema, data)
        return data
