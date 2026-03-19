from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import aiohttp

from ._base import (
    BaseControlClient,
    _build_user_agent,
    _consume_auth_kwargs,
    _raise_for_status,
    build_async_control_auth,
)
from ._generated_async import _attach_async_groups


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


class AsyncControlClient(BaseControlClient):
    def __init__(self, base_url: str | None = None, **kwargs):
        timeout = kwargs.get("timeout", 60.0)
        self._user_agent = _build_user_agent("aiohttp", aiohttp.__version__)
        auth, resolved_base_url, owns_auth = build_async_control_auth(
            base_url=base_url,
            timeout=timeout,
            **_consume_auth_kwargs(kwargs),
        )
        super().__init__(resolved_base_url, auth=auth, owns_auth=owns_auth, **kwargs)
        self._session: aiohttp.ClientSession | None = None
        _attach_async_groups(self)

    async def setup(self):
        if self._session and not self._session.closed:
            await self._session.close()
            await asyncio.sleep(0.05)
        self._session = aiohttp.ClientSession(
            headers={"User-Agent": self._user_agent},
        )

    async def close(self):
        if self._session:
            await self._session.close()
            await asyncio.sleep(0.05)
            self._session = None
        if self._owns_auth:
            await self.auth.close()

    async def __aenter__(self):
        await self.setup()
        return self

    async def __aexit__(self, *exc):
        await self.close()

    def _ensure_session(self):
        if not self._session or self._session.closed:
            raise RuntimeError(
                "Session not initialised. Call `await client.setup()` or use `async with`."
            )

    async def _execute(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        body_schema: str | None = None,
        body_mode: str = "json",
        binary_fields: set[str] | None = None,
        organisation_id: int | None = None,
        response_kind: str = "raw",
        response_schema: str | None = None,
        item_schema: str | None = None,
    ):
        self._ensure_session()
        assert self._session is not None
        await self.auth.ensure_token()
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
                        form = aiohttp.FormData()
                        for key, value in payload.items():
                            if value is None:
                                continue
                            if binary_fields and key in binary_fields:
                                filename, data, content_type = _coerce_file_value(key, value)
                                form.add_field(
                                    key,
                                    data,
                                    filename=filename,
                                    content_type=content_type,
                                )
                            elif isinstance(value, (dict, list)):
                                form.add_field(key, json.dumps(value))
                            elif isinstance(value, bool):
                                form.add_field(key, str(value).lower())
                            else:
                                form.add_field(key, str(value))
                        request_kwargs["data"] = form
                    else:
                        request_kwargs["json"] = payload

                async with self._session.request(method, url, **request_kwargs) as resp:
                    status = resp.status
                    if status >= 500:
                        if attempt == self.max_retries - 1:
                            _raise_for_status(status, await resp.text(), url)
                    elif 400 <= status < 500:
                        _raise_for_status(status, await resp.text(), url)
                    else:
                        return await self._parse_response(
                            resp,
                            response_kind=response_kind,
                            response_schema=response_schema,
                            item_schema=item_schema,
                        )
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise
            except aiohttp.ClientError:
                if attempt == self.max_retries - 1:
                    raise
            await asyncio.sleep(self.retry_delay * (2**attempt))

    async def _parse_response(
        self,
        response: aiohttp.ClientResponse,
        *,
        response_kind: str,
        response_schema: str | None,
        item_schema: str | None,
    ):
        if response_kind == "none":
            return None
        if response_kind == "bytes":
            return await response.read()
        text = await response.text()
        if not text:
            return None
        if response_kind == "raw":
            return json.loads(text)
        data = json.loads(text)
        if response_kind == "model" and response_schema is not None:
            return self._deserialize_model(response_schema, data)
        if response_kind == "page" and response_schema is not None:
            return self._deserialize_page(response_schema, data)
        if response_kind == "list_model" and item_schema is not None:
            return self._deserialize_list(item_schema, data)
        return data
