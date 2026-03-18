"""Asynchronous Doover Data API client.

Usage::

    from pydoover.api import AsyncDataClient

    async with AsyncDataClient("https://data.doover.com/api", token="...") as client:
        channel = await client.fetch_channel(agent_id, "my_channel")
"""

import asyncio
import json
import logging
import time
from typing import Any
from base64 import b64encode

import aiohttp

from datetime import datetime

from ._auth import decode_jwt_exp
from ._base import UNSET, BaseClient, _raise_for_status, _to_snowflake
from ._iterators import AsyncMessageIterator
from ..models.exceptions import TokenRefreshError
from ..models import (
    Aggregate,
    AgentNotificationResponse,
    Alarm,
    BatchAggregateResponse,
    BatchMessageResponse,
    Channel,
    File,
    Message,
    ProcessorTokenResponse,
    SubscriptionInfo,
    TimeseriesResponse,
    TurnCredential,
)
from ..models.alarm import AlarmOperator
from ..models.notification import (
    NotificationEndpoint,
    NotificationSeverity,
    NotificationSubscription,
    NotificationType,
)
from ..models.wss_connection import (
    ConnectionDetail,
    ConnectionSubscription,
    ConnectionSubscriptionLog,
)

log = logging.getLogger(__name__)


class AsyncDataClient(BaseClient):
    """Asynchronous Doover Data API client using ``aiohttp``."""

    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self._session: aiohttp.ClientSession | None = None
        self._token_session: aiohttp.ClientSession | None = None

    async def setup(self):
        """Create the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self.close()
        self._session = aiohttp.ClientSession()

    async def close(self):
        """Close the underlying aiohttp sessions."""
        if self._token_session:
            await self._token_session.close()
            self._token_session = None
        if self._session:
            await self._session.close()
            await asyncio.sleep(0.05)  # let SSL cleanup finish
            self._session = None

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

    # -- Token refresh -------------------------------------------------------

    async def _refresh_token(self):
        if not self._can_refresh:
            raise TokenRefreshError(
                "Token expired and no client credentials configured for refresh."
            )
        self._ensure_session()
        url = self._build_url("/oauth2/token")
        credentials = b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()
        if not self._token_session or self._token_session.closed:
            self._token_session = aiohttp.ClientSession()
        async with self._token_session.post(
            url,
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
        self._token = data["access_token"]
        self._token_expires_at = decode_jwt_exp(self._token)
        if self._token_expires_at is None and "expires_in" in data:
            self._token_expires_at = time.time() + data["expires_in"]
        log.info("Refreshed access token.")

    async def _ensure_token(self):
        if self._needs_refresh:
            await self._refresh_token()

    # -- Core request --------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        files: list[File] | None = None,
        params: dict[str, Any] | None = None,
        organisation_id: int | None = None,
    ) -> Any:
        self._ensure_session()
        assert self._session is not None
        await self._ensure_token()
        url = self._build_url(path)
        if params:
            url += self._build_query(params)
        headers = self._auth_headers(organisation_id)

        def _session_broken() -> bool:
            if not self._session or self._session.closed:
                return True
            connector = self._session.connector
            return connector is None or connector.closed

        for attempt in range(self.max_retries):
            try:
                if _session_broken():
                    log.warning("Session/connector closed. Reinitialising.")
                    await self.setup()

                kwargs: dict[str, Any] = {"headers": headers}

                if files is not None:
                    form = aiohttp.FormData()
                    form.add_field(
                        "json_payload",
                        json.dumps(data or {}),
                        content_type="application/json",
                    )
                    for i, f in enumerate(files, start=1):
                        form.add_field(
                            f"attachment-{i}",
                            f.data,
                            filename=f.filename,
                            content_type=f.content_type,
                        )
                    kwargs["data"] = form
                elif data is not None:
                    kwargs["json"] = data

                async with self._session.request(method, url, **kwargs) as resp:
                    status = resp.status

                    if status >= 500:
                        text = await resp.text()
                        log.info(
                            f"Server error {status} on {method} {url}: "
                            f"{text[:200]} attempt={attempt + 1}/{self.max_retries}"
                        )
                        if attempt == self.max_retries - 1:
                            _raise_for_status(status, text, url)
                        continue

                    if 400 <= status < 500:
                        text = await resp.text()
                        _raise_for_status(status, text, url)

                    if resp.content_length == 0:
                        return None
                    return await resp.json()

            except aiohttp.ClientError as e:
                if _session_broken() or (
                    isinstance(e, aiohttp.ClientConnectionError)
                    and "connector is closed" in str(e).lower()
                ):
                    log.warning("Detected closed session/connector. Reinitialising.")
                    await self.setup()
                log.info(
                    f"Client error on {method} {url}: {e} "
                    f"attempt={attempt + 1}/{self.max_retries}",
                    exc_info=e,
                )
                if attempt == self.max_retries - 1:
                    raise

            except asyncio.TimeoutError:
                log.info(
                    f"Timeout on {method} {url} attempt={attempt + 1}/{self.max_retries}"
                )
                if attempt == self.max_retries - 1:
                    raise

            delay = self.retry_delay * (2**attempt)
            log.info(f"Retrying {method} {url} in {delay}s...")
            await asyncio.sleep(delay)

    # ── Channels ───────────────────────────────────────────────────────────

    async def list_channels(
        self,
        agent_id: int,
        include_aggregate: bool = True,
        include_daily_summaries: bool = True,
        organisation_id: int | None = None,
    ) -> list[Channel]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels",
            params={
                "include_aggregate": include_aggregate,
                "include_daily_summaries": include_daily_summaries,
            },
            organisation_id=organisation_id,
        )
        return [Channel.from_dict(c) for c in data]

    async def fetch_channel(
        self,
        agent_id: int,
        channel_name: str,
        include_aggregate: bool = True,
        organisation_id: int | None = None,
    ) -> Channel:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}",
            params={"include_aggregate": include_aggregate},
            organisation_id=organisation_id,
        )
        return Channel.from_dict(data)

    async def create_channel(
        self,
        agent_id: int,
        channel_name: str,
        is_private: bool = False,
        message_schema: dict | None = None,
        aggregate_schema: dict | None = None,
        organisation_id: int | None = None,
    ) -> int:
        """Create a channel. Returns the new channel's snowflake ID."""
        payload: dict[str, Any] = {"is_private": is_private}
        if message_schema is not None:
            payload["message_schema"] = message_schema
        if aggregate_schema is not None:
            payload["aggregate_schema"] = aggregate_schema
        data = await self._request(
            "POST",
            f"/agents/{agent_id}/channels/{channel_name}",
            data=payload,
            organisation_id=organisation_id,
        )
        return int(data["id"])

    async def put_channel(
        self,
        agent_id: int,
        channel_name: str,
        is_private: bool,
        message_schema: dict | None = None,
        aggregate_schema: dict | None = None,
        organisation_id: int | None = None,
    ) -> Channel:
        payload: dict[str, Any] = {"is_private": is_private}
        if message_schema is not None:
            payload["message_schema"] = message_schema
        if aggregate_schema is not None:
            payload["aggregate_schema"] = aggregate_schema
        data = await self._request(
            "PUT",
            f"/agents/{agent_id}/channels/{channel_name}",
            data=payload,
            organisation_id=organisation_id,
        )
        return Channel.from_dict(data)

    async def list_data_series(
        self,
        agent_id: int,
        field_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/agents/{agent_id}/data_series",
            params={
                "field_name": field_name,
                "before": _to_snowflake(before),
                "after": _to_snowflake(after),
                "limit": limit,
            },
            organisation_id=organisation_id,
        )

    # ── Messages ───────────────────────────────────────────────────────────

    async def list_messages(
        self,
        agent_id: int,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
    ) -> list[Message]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/messages",
            params={
                "before": _to_snowflake(before),
                "after": _to_snowflake(after),
                "limit": limit,
                "field_name": field_names,
            },
            organisation_id=organisation_id,
        )
        return [Message.from_dict(m) for m in data]

    def iter_messages(
        self,
        agent_id: int,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = 50,
    ) -> AsyncMessageIterator:
        """Return an async paginating iterator over channel messages.

        Use as ``async for msg in client.iter_messages(...)`` or call
        ``await .collect()`` to load all matching messages into a list.
        """
        return AsyncMessageIterator(
            self,
            agent_id,
            channel_name,
            before=before,
            after=after,
            field_names=field_names,
            organisation_id=organisation_id,
            page_size=page_size,
        )

    async def fetch_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        organisation_id: int | None = None,
    ) -> Message:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            organisation_id=organisation_id,
        )
        return Message.from_dict(data)

    async def create_message(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        ts: int | None = None,
        files: list[File] | None = None,
        message_id: int = None,
        organisation_id: int | None = None,
    ) -> Message:
        payload: dict[str, Any] = {"data": data}
        if ts is not None:
            payload["ts"] = ts

        if message_id is not None:
            method, path = (
                "PUT",
                f"/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            )
        else:
            method, path = (
                "POST",
                f"/agents/{agent_id}/channels/{channel_name}/messages",
            )
        result = await self._request(
            method,
            path,
            data=payload,
            files=files,
            organisation_id=organisation_id,
        )
        return Message.from_dict(result)

    async def update_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        data: dict[str, Any],
        replace: bool = True,
        files: list[File] | None = None,
        suppress_response: bool = False,
        clear_attachments: bool = False,
        organisation_id: int | None = None,
    ) -> Message | None:
        method = "PUT" if replace else "PATCH"
        result = await self._request(
            method,
            f"/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            data={"data": data},
            files=files,
            params={
                "suppress_response": suppress_response if suppress_response else None,
                "clear_attachments": clear_attachments if clear_attachments else None,
            },
            organisation_id=organisation_id,
        )
        if suppress_response or not result:
            return None
        return Message.from_dict(result)

    async def delete_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        organisation_id: int | None = None,
    ):
        await self._request(
            "DELETE",
            f"/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            organisation_id=organisation_id,
        )

    async def fetch_message_attachment(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        attachment_id: int,
        organisation_id: int | None = None,
    ) -> bytes:
        """Download a message attachment. Follows the redirect to S3."""
        self._ensure_session()
        assert self._session is not None
        await self._ensure_token()
        url = self._build_url(
            f"/agents/{agent_id}/channels/{channel_name}"
            f"/messages/{message_id}/attachments/{attachment_id}"
        )
        async with self._session.get(
            url,
            headers=self._auth_headers(organisation_id),
            allow_redirects=True,
        ) as resp:
            text = await resp.text() if resp.status >= 400 else ""
            _raise_for_status(resp.status, text, url)
            return await resp.read()

    async def fetch_timeseries(
        self,
        agent_id: int,
        channel_name: str,
        field_names: list[str],
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> TimeseriesResponse:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/messages/timeseries",
            params={
                "field_name": field_names,
                "before": _to_snowflake(before),
                "after": _to_snowflake(after),
                "limit": limit,
            },
            organisation_id=organisation_id,
        )
        return TimeseriesResponse.from_dict(data)

    # ── Aggregates ─────────────────────────────────────────────────────────

    async def fetch_channel_aggregate(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int | None = None,
    ) -> Aggregate:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/aggregate",
            organisation_id=organisation_id,
        )
        return Aggregate.from_dict(data)

    async def update_channel_aggregate(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        replace: bool = False,
        files: list[File] | None = None,
        suppress_response: bool = False,
        clear_attachments: bool = False,
        log_update: bool = False,
        organisation_id: int | None = None,
    ) -> Aggregate | None:
        method = "PUT" if replace else "PATCH"
        result = await self._request(
            method,
            f"/agents/{agent_id}/channels/{channel_name}/aggregate",
            data=data,
            files=files,
            params={
                "suppress_response": suppress_response if suppress_response else None,
                "clear_attachments": clear_attachments if clear_attachments else None,
                "log_update": log_update if log_update else None,
            },
            organisation_id=organisation_id,
        )
        if suppress_response or not result:
            return None
        return Aggregate.from_dict(result)

    async def fetch_channel_aggregate_attachment(
        self,
        agent_id: int,
        channel_name: str,
        attachment_id: int,
        organisation_id: int | None = None,
    ) -> bytes:
        """Download an aggregate attachment. Follows the redirect to S3."""
        self._ensure_session()
        assert self._session is not None
        await self._ensure_token()
        url = self._build_url(
            f"/agents/{agent_id}/channels/{channel_name}"
            f"/aggregate/attachments/{attachment_id}"
        )
        async with self._session.get(
            url,
            headers=self._auth_headers(organisation_id),
            allow_redirects=True,
        ) as resp:
            text = await resp.text() if resp.status >= 400 else ""
            _raise_for_status(resp.status, text, url)
            return await resp.read()

    # ── Multi-agent batch ──────────────────────────────────────────────────

    async def fetch_multi_agent_messages(
        self,
        channel_name: str,
        agent_ids: list[int],
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        agent_message_limit: int | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
    ) -> BatchMessageResponse:
        data = await self._request(
            "GET",
            f"/agents/channels/{channel_name}/messages",
            params={
                "agent_id": agent_ids,
                "before": _to_snowflake(before),
                "after": _to_snowflake(after),
                "limit": limit,
                "agent_message_limit": agent_message_limit,
                "field_name": field_names,
            },
            organisation_id=organisation_id,
        )
        return BatchMessageResponse.from_dict(data)

    async def fetch_multi_agent_aggregates(
        self,
        channel_name: str,
        agent_ids: list[int],
        organisation_id: int | None = None,
    ) -> BatchAggregateResponse:
        data = await self._request(
            "GET",
            f"/agents/channels/{channel_name}/aggregates",
            params={"agent_id": agent_ids},
            organisation_id=organisation_id,
        )
        return BatchAggregateResponse.from_dict(data)

    # ── Alarms ─────────────────────────────────────────────────────────────

    async def list_alarms(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int | None = None,
    ) -> list[Alarm]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/alarms",
            organisation_id=organisation_id,
        )
        return [Alarm.from_dict(a) for a in data]

    async def fetch_alarm(
        self,
        agent_id: int,
        channel_name: str,
        alarm_id: int,
        organisation_id: int | None = None,
    ) -> Alarm:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    async def create_alarm(
        self,
        agent_id: int,
        channel_name: str,
        name: str,
        key: str,
        operator: AlarmOperator | str,
        value: Any,
        description: str = "",
        enabled: bool = True,
        expiry_mins: float | None = None,
        organisation_id: int | None = None,
    ) -> Alarm:
        payload: dict[str, Any] = {
            "name": name,
            "key": key,
            "operator": AlarmOperator(operator).value,
            "value": value,
            "description": description,
            "enabled": enabled,
        }
        if expiry_mins is not None:
            payload["expiry_mins"] = expiry_mins
        data = await self._request(
            "POST",
            f"/agents/{agent_id}/channels/{channel_name}/alarms",
            data=payload,
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    async def put_alarm(
        self,
        agent_id: int,
        channel_name: str,
        alarm_id: int,
        name: str,
        key: str,
        operator: AlarmOperator | str,
        value: Any,
        description: str = "",
        enabled: bool = True,
        expiry_mins: float | None = None,
        organisation_id: int | None = None,
    ) -> Alarm:
        payload: dict[str, Any] = {
            "name": name,
            "key": key,
            "operator": AlarmOperator(operator).value,
            "value": value,
            "description": description,
            "enabled": enabled,
        }
        if expiry_mins is not None:
            payload["expiry_mins"] = expiry_mins
        data = await self._request(
            "PUT",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    async def update_alarm(
        self,
        agent_id: int,
        channel_name: str,
        alarm_id: int,
        name: str | None = None,
        key: str | None = None,
        operator: AlarmOperator | str | None = None,
        value: Any = None,
        description: str | None = None,
        enabled: bool | None = None,
        expiry_mins: float | None = UNSET,
        organisation_id: int | None = None,
    ) -> Alarm:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if key is not None:
            payload["key"] = key
        if operator is not None:
            payload["operator"] = AlarmOperator(operator).value
        if value is not None:
            payload["value"] = value
        if description is not None:
            payload["description"] = description
        if enabled is not None:
            payload["enabled"] = enabled
            if expiry_mins is not UNSET:
                payload["expiry_mins"] = expiry_mins
        data = await self._request(
            "PATCH",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    async def delete_alarm(
        self,
        agent_id: int,
        channel_name: str,
        alarm_id: int,
        organisation_id: int | None = None,
    ):
        await self._request(
            "DELETE",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            organisation_id=organisation_id,
        )

    # ── Connections ────────────────────────────────────────────────────────

    async def list_connections(
        self,
        agent_id: int,
        organisation_id: int | None = None,
    ) -> list[ConnectionDetail]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/wss_connections",
            organisation_id=organisation_id,
        )
        return [ConnectionDetail.from_dict(c) for c in data]

    async def fetch_connection(
        self,
        connection_id: int,
        organisation_id: int | None = None,
    ) -> ConnectionDetail:
        data = await self._request(
            "GET",
            f"/connections/{connection_id}",
            organisation_id=organisation_id,
        )
        return ConnectionDetail.from_dict(data)

    async def fetch_connection_history(
        self,
        agent_id: int,
        default_connection: bool,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> list[ConnectionDetail]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/wss_connections/history",
            params={
                "default_connection": default_connection,
                "before": _to_snowflake(before),
                "after": _to_snowflake(after),
                "limit": limit,
            },
            organisation_id=organisation_id,
        )
        return [ConnectionDetail.from_dict(c) for c in data]

    async def fetch_subscription_history(
        self,
        agent_id: int,
        channel_agent_id: int,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> list[ConnectionSubscriptionLog]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/wss_connections/subscriptions/history",
            params={
                "channel": json.dumps(
                    {"agent_id": str(channel_agent_id), "name": channel_name}
                ),
                "before": _to_snowflake(before),
                "after": _to_snowflake(after),
                "limit": limit,
            },
            organisation_id=organisation_id,
        )
        return [ConnectionSubscriptionLog.from_dict(s) for s in data]

    async def fetch_channel_subscriptions(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int | None = None,
    ) -> list[ConnectionSubscription]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/subscriptions",
            organisation_id=organisation_id,
        )
        return [ConnectionSubscription.from_dict(s) for s in data]

    # ── Notifications ──────────────────────────────────────────────────────

    async def fetch_notifications(
        self,
        agent_id: int,
        organisation_id: int | None = None,
    ) -> AgentNotificationResponse:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/notifications",
            organisation_id=organisation_id,
        )
        return AgentNotificationResponse.from_dict(data)

    async def list_notification_endpoints(
        self,
        agent_id: int,
        name: str | None = None,
        organisation_id: int | None = None,
    ) -> list[NotificationEndpoint]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/notifications/endpoints",
            params={"name": name},
            organisation_id=organisation_id,
        )
        return [NotificationEndpoint.from_dict(e) for e in data["endpoints"]]

    async def create_notification_endpoint(
        self,
        agent_id: int,
        name: str,
        type: NotificationType | int,
        extra_data: dict[str, Any],
        default: bool,
        priority: int | None = None,
        organisation_id: int | None = None,
    ) -> int:
        """Create a notification endpoint. Returns the new endpoint's snowflake ID."""
        payload: dict[str, Any] = {
            "name": name,
            "type": NotificationType(type).value,
            "extra_data": extra_data,
            "default": default,
        }
        if priority is not None:
            payload["priority"] = priority
        data = await self._request(
            "POST",
            f"/agents/{agent_id}/notifications/endpoints",
            data=payload,
            organisation_id=organisation_id,
        )
        return int(data["id"])

    async def update_notification_endpoint(
        self,
        agent_id: int,
        endpoint_id: int,
        name: str | None = None,
        extra_data: dict[str, Any] | None = None,
        priority: int | None = UNSET,
        organisation_id: int | None = None,
    ):
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if extra_data is not None:
            payload["extra_data"] = extra_data
        if priority is not UNSET:
            payload["priority"] = priority
        await self._request(
            "PATCH",
            f"/agents/{agent_id}/notifications/endpoints/{endpoint_id}",
            data=payload,
            organisation_id=organisation_id,
        )

    async def delete_notification_endpoint(
        self,
        agent_id: int,
        endpoint_id: int,
        organisation_id: int | None = None,
    ):
        await self._request(
            "DELETE",
            f"/agents/{agent_id}/notifications/endpoints/{endpoint_id}",
            organisation_id=organisation_id,
        )

    async def test_notification_endpoint(
        self,
        agent_id: int,
        endpoint_id: int,
        organisation_id: int | None = None,
    ) -> bool:
        data = await self._request(
            "POST",
            f"/agents/{agent_id}/notifications/endpoints/{endpoint_id}/test",
            organisation_id=organisation_id,
        )
        return data["success"]

    async def list_notification_subscriptions(
        self,
        agent_id: int,
        subscribed_to: int | None = None,
        organisation_id: int | None = None,
    ) -> list[NotificationSubscription]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/notifications/subscriptions",
            params={"subscribed_to": subscribed_to},
            organisation_id=organisation_id,
        )
        return [NotificationSubscription.from_dict(s) for s in data["subscriptions"]]

    async def create_notification_subscription(
        self,
        agent_id: int,
        subscribe_to: int,
        severity: NotificationSeverity | int,
        topic_filter: list[str],
        endpoint_id: int | None = None,
        organisation_id: int | None = None,
    ) -> list[dict[str, int]]:
        """Returns a list of created subscriptions, each with ``id`` and ``endpoint_id``."""
        payload: dict[str, Any] = {
            "subscribe_to": str(subscribe_to),
            "severity": NotificationSeverity(severity).value,
            "topic_filter": topic_filter,
        }
        if endpoint_id is not None:
            payload["endpoint_id"] = str(endpoint_id)
        data = await self._request(
            "POST",
            f"/agents/{agent_id}/notifications/subscriptions",
            data=payload,
            organisation_id=organisation_id,
        )
        return [
            {"id": int(s["id"]), "endpoint_id": int(s["endpoint_id"])}
            for s in data["subscriptions"]
        ]

    async def update_notification_subscription(
        self,
        agent_id: int,
        subscription_id: int,
        severity: NotificationSeverity | int | None = None,
        topic_filter: list[str] | None = None,
        organisation_id: int | None = None,
    ):
        payload: dict[str, Any] = {}
        if severity is not None:
            payload["severity"] = NotificationSeverity(severity).value
        if topic_filter is not None:
            payload["topic_filter"] = topic_filter
        await self._request(
            "PATCH",
            f"/agents/{agent_id}/notifications/subscriptions/{subscription_id}",
            data=payload,
            organisation_id=organisation_id,
        )

    async def delete_notification_subscription(
        self,
        agent_id: int,
        subscription_id: int,
        organisation_id: int | None = None,
    ):
        await self._request(
            "DELETE",
            f"/agents/{agent_id}/notifications/subscriptions/{subscription_id}",
            organisation_id=organisation_id,
        )

    async def list_default_notification_subscriptions(
        self,
        agent_id: int,
        subscribed_to: int | None = None,
        organisation_id: int | None = None,
    ) -> list[NotificationSubscription]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/notifications/subscriptions/default",
            params={"subscribed_to": subscribed_to},
            organisation_id=organisation_id,
        )
        return [NotificationSubscription.from_dict(s) for s in data["subscriptions"]]

    async def delete_default_notification_subscription(
        self,
        agent_id: int,
        subscribed_to: int,
        organisation_id: int | None = None,
    ):
        await self._request(
            "DELETE",
            f"/agents/{agent_id}/notifications/subscriptions/default/{subscribed_to}",
            organisation_id=organisation_id,
        )

    async def list_notification_subscribers(
        self,
        agent_id: int,
        organisation_id: int | None = None,
    ) -> list[NotificationSubscription]:
        data = await self._request(
            "GET",
            f"/agents/{agent_id}/notifications/subscribers",
            organisation_id=organisation_id,
        )
        return [NotificationSubscription.from_dict(s) for s in data["subscribers"]]

    async def update_web_push_endpoint(
        self,
        old_endpoint: str,
        endpoint: str,
        key_p256dh: str,
        key_auth: str,
        expires_at: int,
        organisation_id: int | None = None,
    ):
        await self._request(
            "POST",
            "/agents/me/notifications/update_web_push",
            data={
                "old_endpoint": old_endpoint,
                "endpoint": endpoint,
                "key_p256dh": key_p256dh,
                "key_auth": key_auth,
                "expires_at": expires_at,
            },
            organisation_id=organisation_id,
        )

    # ── Processors ─────────────────────────────────────────────────────────

    async def fetch_subscription_info(
        self,
        subscription_id: int,
        organisation_id: int | None = None,
    ) -> SubscriptionInfo:
        data = await self._request(
            "GET",
            f"/processors/subscriptions/{subscription_id}",
            organisation_id=organisation_id,
        )
        return SubscriptionInfo.from_dict(data)

    async def fetch_schedule_info(
        self,
        schedule_id: int,
        organisation_id: int | None = None,
    ) -> SubscriptionInfo:
        data = await self._request(
            "GET",
            f"/processors/schedules/{schedule_id}",
            organisation_id=organisation_id,
        )
        return SubscriptionInfo.from_dict(data)

    async def put_schedule(
        self,
        agent_id: int,
        schedule_id: int,
        app_key: str,
        permissions: list[dict[str, str]],
        is_org: bool | None = None,
        organisation_id: int | None = None,
    ) -> ProcessorTokenResponse:
        payload: dict[str, Any] = {
            "app_key": app_key,
            "permissions": permissions,
        }
        if is_org is not None:
            payload["is_org"] = is_org
        data = await self._request(
            "PUT",
            f"/agents/{agent_id}/processors/schedules/{schedule_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return ProcessorTokenResponse.from_dict(data)

    async def put_subscription(
        self,
        agent_id: int,
        subscription_id: int,
        subscription_arn: str,
        app_key: str,
        permissions: list[dict[str, str]],
        is_org: bool | None = None,
        organisation_id: int | None = None,
    ):
        payload: dict[str, Any] = {
            "subscription_arn": subscription_arn,
            "app_key": app_key,
            "permissions": permissions,
        }
        if is_org is not None:
            payload["is_org"] = is_org
        await self._request(
            "PUT",
            f"/agents/{agent_id}/processors/subscriptions/{subscription_id}",
            data=payload,
            organisation_id=organisation_id,
        )

    async def create_ingestion_endpoint(
        self,
        agent_id: int,
        ingestion_id: int,
        lambda_arn: str,
        cidr_ranges: list[str],
        throttle_limit: int,
        app_key: str,
        permissions: list[dict[str, str]],
        signing_key: str | None = None,
        signing_key_hash_header: str | None = None,
        never_replace_token: bool = False,
        mini_token: bool = False,
        is_org: bool | None = None,
        organisation_id: int | None = None,
    ) -> ProcessorTokenResponse:
        payload: dict[str, Any] = {
            "lambda_arn": lambda_arn,
            "cidr_ranges": cidr_ranges,
            "throttle_limit": throttle_limit,
            "app_key": app_key,
            "permissions": permissions,
            "never_replace_token": never_replace_token,
            "mini_token": mini_token,
        }
        if signing_key is not None:
            payload["signing_key"] = signing_key
        if signing_key_hash_header is not None:
            payload["signing_key_hash_header"] = signing_key_hash_header
        if is_org is not None:
            payload["is_org"] = is_org
        data = await self._request(
            "PUT",
            f"/agents/{agent_id}/processors/ingestion/{ingestion_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return ProcessorTokenResponse.from_dict(data)

    # ── TURN ───────────────────────────────────────────────────────────────

    async def fetch_turn_token(
        self,
        role: str,
        camera_name: str,
        device_id: int | None = None,
        organisation_id: int | None = None,
    ) -> TurnCredential:
        payload: dict[str, Any] = {"role": role, "camera_name": camera_name}
        if device_id is not None:
            payload["device_id"] = str(device_id)
        data = await self._request(
            "POST",
            "/turn/token",
            data=payload,
            organisation_id=organisation_id,
        )
        return TurnCredential.from_dict(data)
