"""Synchronous Doover Data API client.

Usage::

    from pydoover.api import DataClient

    client = DataClient("https://data.doover.com/api", token="...")
    channel = client.fetch_channel(123, "my_channel")
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from datetime import datetime

from ._base import (
    UNSET,
    _build_user_agent,
    BaseClient,
    _consume_auth_kwargs,
    _raise_for_status,
    _to_snowflake,
    Unset,
    build_sync_auth,
)

from ._iterators import MessageIterator, MultiAgentMessageIterator
from ...models.data import (
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
    Attachment,
)
from ...models.data.alarm import AlarmOperator
from ...models.data.notification import (
    NotificationEndpoint,
    NotificationSeverity,
    NotificationSubscription,
    NotificationType,
)
from ...models.data.wss_connection import (
    ConnectionDetail,
    ConnectionSubscription,
    ConnectionSubscriptionLog,
)

log = logging.getLogger(__name__)


class DataClient(BaseClient):
    """Synchronous Doover Data API client using ``httpx``."""

    def __init__(self, base_url: str | None = None, **kwargs):
        timeout = kwargs.get("timeout", 60.0)
        self._user_agent = _build_user_agent("httpx", httpx.__version__)
        auth, resolved_base_url, owns_auth = build_sync_auth(
            base_url=base_url,
            timeout=timeout,
            **_consume_auth_kwargs(kwargs),
        )
        super().__init__(resolved_base_url, auth=auth, owns_auth=owns_auth, **kwargs)
        self._session = httpx.Client(timeout=self.timeout, follow_redirects=True)

    def close(self):
        self._session.close()
        if self._owns_auth:
            self.auth.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- Core request --------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        files: list[File] | None = None,
        params: dict[str, Any] | None = None,
        organisation_id: int | None = None,
    ) -> Any:
        self.auth.ensure_token()
        url = self._build_url(path)
        if params:
            url += self._build_query(params)
        headers = self._auth_headers(organisation_id)

        for attempt in range(self.max_retries):
            try:
                if files is not None:
                    json_str, file_fields = self._build_multipart_fields(
                        data or {}, files
                    )
                    httpx_files = {
                        "json_payload": (
                            "json_payload",
                            json_str.encode(),
                            "application/json",
                        ),
                    }
                    for field_name, (filename, fdata, content_type) in file_fields:
                        httpx_files[field_name] = (filename, fdata, content_type)
                    resp = self._session.request(
                        method,
                        url,
                        files=httpx_files,
                        headers=headers,
                    )
                elif data is not None:
                    resp = self._session.request(
                        method,
                        url,
                        json=data,
                        headers=headers,
                    )
                else:
                    resp = self._session.request(
                        method,
                        url,
                        headers=headers,
                    )

                status = resp.status_code
                if status >= 500:
                    log.info(
                        f"Server error {status} on {method} {url}: "
                        f"{resp.text[:200]} attempt={attempt + 1}/{self.max_retries}"
                    )
                    if attempt == self.max_retries - 1:
                        _raise_for_status(status, resp.text, url)
                    continue

                if 400 <= status < 500:
                    _raise_for_status(status, resp.text, url)

                return resp.json() if resp.content else None

            except httpx.TimeoutException:
                log.info(
                    f"Timeout on {method} {url} attempt={attempt + 1}/{self.max_retries}"
                )
                if attempt == self.max_retries - 1:
                    raise

            except httpx.HTTPError as e:
                log.info(
                    f"Request error on {method} {url}: {e} "
                    f"attempt={attempt + 1}/{self.max_retries}"
                )
                if attempt == self.max_retries - 1:
                    raise

            delay = self.retry_delay * (2**attempt)
            log.info(f"Retrying {method} {url} in {delay}s...")
            time.sleep(delay)

    # ── Channels ───────────────────────────────────────────────────────────

    def list_channels(
        self,
        agent_id: int,
        include_aggregate: bool = True,
        include_daily_summaries: bool = True,
        organisation_id: int | None = None,
    ) -> list[Channel]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/channels",
            params={
                "include_aggregate": include_aggregate,
                "include_daily_summaries": include_daily_summaries,
            },
            organisation_id=organisation_id,
        )
        return [Channel.from_dict(c) for c in data]

    def fetch_channel(
        self,
        agent_id: int,
        channel_name: str,
        include_aggregate: bool = True,
        organisation_id: int | None = None,
    ) -> Channel:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}",
            params={"include_aggregate": include_aggregate},
            organisation_id=organisation_id,
        )
        return Channel.from_dict(data)

    def create_channel(
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
        data = self._request(
            "POST",
            f"/agents/{agent_id}/channels/{channel_name}",
            data=payload,
            organisation_id=organisation_id,
        )
        return int(data["id"])

    def put_channel(
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
        data = self._request(
            "PUT",
            f"/agents/{agent_id}/channels/{channel_name}",
            data=payload,
            organisation_id=organisation_id,
        )
        return Channel.from_dict(data)

    def list_data_series(
        self,
        agent_id: int,
        field_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> dict[str, Any]:
        return self._request(
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

    def list_messages(
        self,
        agent_id: int,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
    ) -> list[Message]:
        data = self._request(
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
        page_size: int = 50,
        organisation_id: int | None = None,
    ) -> MessageIterator:
        """Return a paginating iterator over channel messages.

        Use as ``for msg in client.iter_messages(...)`` or call
        ``.collect()`` to load all matching messages into a list.
        """
        return MessageIterator(
            self,
            agent_id,
            channel_name,
            before=before,
            after=after,
            field_names=field_names,
            organisation_id=organisation_id,
            page_size=page_size,
        )

    def fetch_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        organisation_id: int | None = None,
    ) -> Message:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            organisation_id=organisation_id,
        )
        return Message.from_dict(data)

    def create_message(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        timestamp: int | None = None,
        files: list[File] | None = None,
        message_id: int | None = None,
        organisation_id: int | None = None,
    ) -> Message:
        payload: dict[str, Any] = {"data": data}
        if timestamp is not None:
            if isinstance(timestamp, datetime):
                timestamp = int(timestamp.timestamp() * 1000)
            payload["ts"] = timestamp

        if message_id is not None:
            path = f"/agents/{agent_id}/channels/{channel_name}/messages/{message_id}"
        else:
            path = f"/agents/{agent_id}/channels/{channel_name}/messages"

        result = self._request(
            "POST",
            path,
            data=payload,
            files=files,
            organisation_id=organisation_id,
        )
        return Message.from_dict(result)

    def update_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        data: dict[str, Any],
        replace_data: bool = False,
        files: list[File] | None = None,
        suppress_response: bool = False,
        clear_attachments: bool = False,
        organisation_id: int | None = None,
    ) -> Message | None:
        method = "PUT" if replace_data else "PATCH"
        result = self._request(
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

    def delete_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        organisation_id: int | None = None,
    ):
        self._request(
            "DELETE",
            f"/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            organisation_id=organisation_id,
        )

    def fetch_message_attachment(
        self,
        attachment: Attachment,
        organisation_id: int | None = None,
    ) -> bytes:
        """Download a message attachment. Follows the redirect to S3."""

        self.auth.ensure_token()

        resp = self._session.get(
            attachment.url,
            headers=self._auth_headers(organisation_id),
        )
        _raise_for_status(resp.status_code, resp.text, attachment.url)
        return resp.content

    def fetch_timeseries(
        self,
        agent_id: int,
        channel_name: str,
        field_names: list[str],
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> TimeseriesResponse:
        data = self._request(
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

    def fetch_channel_aggregate(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int | None = None,
    ) -> Aggregate:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/aggregate",
            organisation_id=organisation_id,
        )
        return Aggregate.from_dict(data)

    def update_channel_aggregate(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        replace_data: bool = False,
        files: list[File] | None = None,
        suppress_response: bool = False,
        clear_attachments: bool = False,
        log_update: bool = False,
        organisation_id: int | None = None,
    ) -> Aggregate | None:
        method = "PUT" if replace_data else "PATCH"
        result = self._request(
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

    def fetch_channel_aggregate_attachment(
        self,
        agent_id: int,
        channel_name: str,
        attachment_id: int,
        organisation_id: int | None = None,
    ) -> bytes:
        """Download an aggregate attachment. Follows the redirect to S3."""
        self.auth.ensure_token()
        url = self._build_url(
            f"/agents/{agent_id}/channels/{channel_name}"
            f"/aggregate/attachments/{attachment_id}"
        )
        resp = self._session.get(
            url,
            headers=self._auth_headers(organisation_id),
        )
        _raise_for_status(resp.status_code, resp.text, url)
        return resp.content

    # ── Multi-agent batch ──────────────────────────────────────────────────

    def fetch_multi_agent_messages(
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
        data = self._request(
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

    def iter_multi_agent_messages(
        self,
        channel_name: str,
        agent_ids: list[int],
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        agent_message_limit: int | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = 50,
    ) -> MultiAgentMessageIterator:
        """Return a paginating iterator over multi-agent channel messages.

        Use as ``for msg in client.iter_multi_agent_messages(...)`` or call
        ``.collect()`` to load all matching messages into a list.
        """
        return MultiAgentMessageIterator(
            self,
            channel_name,
            agent_ids,
            before=before,
            after=after,
            agent_message_limit=agent_message_limit,
            field_names=field_names,
            organisation_id=organisation_id,
            page_size=page_size,
        )

    def fetch_multi_agent_aggregates(
        self,
        channel_name: str,
        agent_ids: list[int],
        organisation_id: int | None = None,
    ) -> BatchAggregateResponse:
        data = self._request(
            "GET",
            f"/agents/channels/{channel_name}/aggregates",
            params={"agent_id": agent_ids},
            organisation_id=organisation_id,
        )
        return BatchAggregateResponse.from_dict(data)

    # ── Alarms ─────────────────────────────────────────────────────────────

    def list_alarms(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int | None = None,
    ) -> list[Alarm]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/alarms",
            organisation_id=organisation_id,
        )
        return [Alarm.from_dict(a) for a in data]

    def fetch_alarm(
        self,
        agent_id: int,
        channel_name: str,
        alarm_id: int,
        organisation_id: int | None = None,
    ) -> Alarm:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    def create_alarm(
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
        data = self._request(
            "POST",
            f"/agents/{agent_id}/channels/{channel_name}/alarms",
            data=payload,
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    def put_alarm(
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
        data = self._request(
            "PUT",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    def update_alarm(
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
        expiry_mins: float | None | Unset = UNSET,
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
        data = self._request(
            "PATCH",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return Alarm.from_dict(data)

    def delete_alarm(
        self,
        agent_id: int,
        channel_name: str,
        alarm_id: int,
        organisation_id: int | None = None,
    ):
        self._request(
            "DELETE",
            f"/agents/{agent_id}/channels/{channel_name}/alarms/{alarm_id}",
            organisation_id=organisation_id,
        )

    # ── Connections ────────────────────────────────────────────────────────

    def list_connections(
        self,
        agent_id: int,
        organisation_id: int | None = None,
    ) -> list[ConnectionDetail]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/wss_connections",
            organisation_id=organisation_id,
        )
        return [ConnectionDetail.from_dict(c) for c in data]

    def fetch_connection(
        self,
        connection_id: int,
        organisation_id: int | None = None,
    ) -> ConnectionDetail:
        data = self._request(
            "GET",
            f"/connections/{connection_id}",
            organisation_id=organisation_id,
        )
        return ConnectionDetail.from_dict(data)

    def fetch_connection_history(
        self,
        agent_id: int,
        default_connection: bool,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> list[ConnectionDetail]:
        data = self._request(
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

    def fetch_subscription_history(
        self,
        agent_id: int,
        channel_agent_id: int,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        organisation_id: int | None = None,
    ) -> list[ConnectionSubscriptionLog]:
        data = self._request(
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

    def fetch_channel_subscriptions(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int | None = None,
    ) -> list[ConnectionSubscription]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/channels/{channel_name}/subscriptions",
            organisation_id=organisation_id,
        )
        return [ConnectionSubscription.from_dict(s) for s in data]

    # ── Notifications ──────────────────────────────────────────────────────

    def fetch_notifications(
        self,
        agent_id: int,
        organisation_id: int | None = None,
    ) -> AgentNotificationResponse:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/notifications",
            organisation_id=organisation_id,
        )
        return AgentNotificationResponse.from_dict(data)

    def list_notification_endpoints(
        self,
        agent_id: int,
        name: str | None = None,
        organisation_id: int | None = None,
    ) -> list[NotificationEndpoint]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/notifications/endpoints",
            params={"name": name},
            organisation_id=organisation_id,
        )
        return [NotificationEndpoint.from_dict(e) for e in data["endpoints"]]

    def create_notification_endpoint(
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
        data = self._request(
            "POST",
            f"/agents/{agent_id}/notifications/endpoints",
            data=payload,
            organisation_id=organisation_id,
        )
        return int(data["id"])

    def update_notification_endpoint(
        self,
        agent_id: int,
        endpoint_id: int,
        name: str | None = None,
        extra_data: dict[str, Any] | None = None,
        priority: int | None | Unset = UNSET,
        organisation_id: int | None = None,
    ):
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if extra_data is not None:
            payload["extra_data"] = extra_data
        if priority is not UNSET:
            payload["priority"] = priority
        self._request(
            "PATCH",
            f"/agents/{agent_id}/notifications/endpoints/{endpoint_id}",
            data=payload,
            organisation_id=organisation_id,
        )

    def delete_notification_endpoint(
        self,
        agent_id: int,
        endpoint_id: int,
        organisation_id: int | None = None,
    ):
        self._request(
            "DELETE",
            f"/agents/{agent_id}/notifications/endpoints/{endpoint_id}",
            organisation_id=organisation_id,
        )

    def test_notification_endpoint(
        self,
        agent_id: int,
        endpoint_id: int,
        organisation_id: int | None = None,
    ) -> bool:
        data = self._request(
            "POST",
            f"/agents/{agent_id}/notifications/endpoints/{endpoint_id}/test",
            organisation_id=organisation_id,
        )
        return data["success"]

    def list_notification_subscriptions(
        self,
        agent_id: int,
        subscribed_to: int | None = None,
        organisation_id: int | None = None,
    ) -> list[NotificationSubscription]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/notifications/subscriptions",
            params={"subscribed_to": subscribed_to},
            organisation_id=organisation_id,
        )
        return [NotificationSubscription.from_dict(s) for s in data["subscriptions"]]

    def create_notification_subscription(
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
        data = self._request(
            "POST",
            f"/agents/{agent_id}/notifications/subscriptions",
            data=payload,
            organisation_id=organisation_id,
        )
        return [
            {"id": int(s["id"]), "endpoint_id": int(s["endpoint_id"])}
            for s in data["subscriptions"]
        ]

    def update_notification_subscription(
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
        self._request(
            "PATCH",
            f"/agents/{agent_id}/notifications/subscriptions/{subscription_id}",
            data=payload,
            organisation_id=organisation_id,
        )

    def delete_notification_subscription(
        self,
        agent_id: int,
        subscription_id: int,
        organisation_id: int | None = None,
    ):
        self._request(
            "DELETE",
            f"/agents/{agent_id}/notifications/subscriptions/{subscription_id}",
            organisation_id=organisation_id,
        )

    def list_default_notification_subscriptions(
        self,
        agent_id: int,
        subscribed_to: int | None = None,
        organisation_id: int | None = None,
    ) -> list[NotificationSubscription]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/notifications/subscriptions/default",
            params={"subscribed_to": subscribed_to},
            organisation_id=organisation_id,
        )
        return [NotificationSubscription.from_dict(s) for s in data["subscriptions"]]

    def delete_default_notification_subscription(
        self,
        agent_id: int,
        subscribed_to: int,
        organisation_id: int | None = None,
    ):
        self._request(
            "DELETE",
            f"/agents/{agent_id}/notifications/subscriptions/default/{subscribed_to}",
            organisation_id=organisation_id,
        )

    def list_notification_subscribers(
        self,
        agent_id: int,
        organisation_id: int | None = None,
    ) -> list[NotificationSubscription]:
        data = self._request(
            "GET",
            f"/agents/{agent_id}/notifications/subscribers",
            organisation_id=organisation_id,
        )
        return [NotificationSubscription.from_dict(s) for s in data["subscribers"]]

    def update_web_push_endpoint(
        self,
        old_endpoint: str,
        endpoint: str,
        key_p256dh: str,
        key_auth: str,
        expires_at: int,
        organisation_id: int | None = None,
    ):
        self._request(
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

    def fetch_subscription_info(
        self,
        subscription_id: int,
        organisation_id: int | None = None,
    ) -> SubscriptionInfo:
        data = self._request(
            "GET",
            f"/processors/subscriptions/{subscription_id}",
            organisation_id=organisation_id,
        )
        return SubscriptionInfo.from_dict(data)

    def fetch_schedule_info(
        self,
        schedule_id: int,
        organisation_id: int | None = None,
    ) -> SubscriptionInfo:
        data = self._request(
            "GET",
            f"/processors/schedules/{schedule_id}",
            organisation_id=organisation_id,
        )
        return SubscriptionInfo.from_dict(data)

    def put_schedule(
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
        data = self._request(
            "PUT",
            f"/agents/{agent_id}/processors/schedules/{schedule_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return ProcessorTokenResponse.from_dict(data)

    def put_subscription(
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
        self._request(
            "PUT",
            f"/agents/{agent_id}/processors/subscriptions/{subscription_id}",
            data=payload,
            organisation_id=organisation_id,
        )

    def put_ingestion_endpoint(
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
        data = self._request(
            "PUT",
            f"/agents/{agent_id}/processors/ingestions/{ingestion_id}",
            data=payload,
            organisation_id=organisation_id,
        )
        return ProcessorTokenResponse.from_dict(data)

    def delete_ingestion_endpoint(
        self,
        agent_id: int,
        ingestion_id: int,
        organisation_id: int | None = None,
    ) -> None:
        self._request(
            "DELETE",
            f"/agents/{agent_id}/processors/ingestions/{ingestion_id}",
            organisation_id=organisation_id,
        )

    # ── TURN ───────────────────────────────────────────────────────────────

    def fetch_turn_token(
        self,
        role: str,
        camera_name: str,
        device_id: int | None = None,
        organisation_id: int | None = None,
    ) -> TurnCredential:
        payload: dict[str, Any] = {"role": role, "camera_name": camera_name}
        if device_id is not None:
            payload["device_id"] = str(device_id)
        data = self._request(
            "POST",
            "/turn/token",
            data=payload,
            organisation_id=organisation_id,
        )
        return TurnCredential.from_dict(data)
