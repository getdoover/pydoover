import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp
from urllib.parse import urlencode

from ...utils.snowflake import generate_snowflake_id_at

from .types import (
    Channel,
    ConnectionConfig,
    ConnectionStatus,
    ConnectionDetermination,
    Message,
    Aggregate,
)

log = logging.getLogger(__name__)


class DooverData:
    def __init__(self, base_url: str):
        self.agent_id = None
        self.organisation_id = None
        self.base_url = base_url
        self.session: aiohttp.ClientSession = None

        self.has_persistent_connection = lambda: False
        self.is_processor_v2 = True

        # for onmessagecreate events this is set to the trigger channel
        # so that we don't publish to the same channel we're receiving from
        # and get in an infinite loop
        self._invoking_channel_name = None
        self.lookup_ip = True

    async def setup(self):
        if self.session:
            await self.close()

        self.session = aiohttp.ClientSession()

    def set_token(self, token: str):
        self.session.headers["Authorization"] = f"Bearer {token}"

    async def close(self):
        if self.session:
            await self.session.close()
            # Allow the event loop to process the underlying connection
            # cleanup (SSL transports, connectors, etc.) that session.close()
            # schedules but doesn't complete synchronously.
            await asyncio.sleep(0.05)
            self.session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | str | aiohttp.FormData | None = None,
        organisation_id: int | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        org_id = organisation_id or self.organisation_id
        headers = {"X-Doover-Organisation": str(org_id)} if org_id else {}

        kwargs = (
            {"data": data} if isinstance(data, aiohttp.FormData) else {"json": data}
        )

        log.debug(f"Starting request: {method} {endpoint} (org_id={org_id})")

        for attempt in range(max_retries):
            try:
                async with self.session.request(
                    method, endpoint, **kwargs, headers=headers
                ) as resp:
                    status = resp.status

                    log.debug(
                        f"Response received: {method} {endpoint} "
                        f"status={status} attempt={attempt + 1}/{max_retries}"
                    )

                    if status >= 500:
                        response_text = await resp.text()
                        log.info(
                            f"Server error {status} on {method} {endpoint}: "
                            f"{response_text[:200]} attempt={attempt + 1}/{max_retries}"
                        )
                        if attempt == max_retries - 1:
                            resp.raise_for_status()
                        continue  # Retry

                    elif 400 <= status < 500:
                        # Client errors - don't retry
                        response_text = await resp.text()
                        log.error(
                            f"Client error {status} on {method} {endpoint}: "
                            f"{response_text[:200]}"
                        )
                        resp.raise_for_status()

                    elif 200 <= status < 300:
                        # Success
                        result = await resp.json()
                        log.debug(
                            f"Request successful: {method} {endpoint} "
                            f"status={status} attempt={attempt + 1}"
                        )
                        return result

                    else:
                        log.warning(
                            f"Unexpected status {status} on {method} {endpoint}"
                        )
                        resp.raise_for_status()

            except aiohttp.ClientError as e:
                log.info(
                    f"Client error on {method} {endpoint}: "
                    f"{str(e)} attempt={attempt + 1}/{max_retries}",
                    exc_info=e,
                )

            except asyncio.TimeoutError:
                log.info(
                    f"Timeout on {method} {endpoint} attempt={attempt + 1}/{max_retries}"
                )

            except Exception as e:
                log.info(
                    f"Unexpected error on {method} {endpoint}: {str(e)} attempt={attempt + 1}/{max_retries}",
                    exc_info=e,
                )

            if attempt < max_retries - 1:
                delay = retry_delay * (2**attempt)
                log.info(f"Retrying {method} {endpoint} in {delay}s...")
                await asyncio.sleep(delay)

        raise

    async def get_channel(
        self, agent_id: int, channel_name: str, organisation_id: int = None
    ):
        data = await self._request(
            "GET",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}",
            organisation_id=organisation_id,
        )
        return Channel.from_dict(data)

    async def get_channel_aggregate(self, agent_id: int, channel_name: str):
        data = await self._request(
            "GET",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/aggregate",
        )
        return Aggregate.from_dict(data)

    async def get_channel_messages(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int = None,
        limit: int = None,
        before: datetime | None = None,
        after: datetime | None = None,
        chunk_size: int | None = None,
    ) -> list[Message]:
        before = generate_snowflake_id_at(before) if before else None
        after = generate_snowflake_id_at(after) if after else None

        if chunk_size is not None and before is not None and after is not None:
            log.debug(f"Splitting messages into chunks of {chunk_size}")
            all_messages = []

            while True:
                log.debug(f"Fetching messages from {after} with limit {chunk_size}")
                messages = await self._get_channel_messages(
                    agent_id,
                    channel_name,
                    organisation_id,
                    limit=chunk_size,
                    after=after,
                )
                log.debug(f"Received {len(messages)} messages")
                for message in messages:
                    if int(message.id) <= before:
                        all_messages.append(message)
                if not messages or len(messages) < chunk_size:
                    break
                last_message = messages[-1]
                if int(last_message.id) >= before:
                    break
                after = int(messages[-1].id)

            return [Message.from_dict(m) for m in all_messages]

        return await self._get_channel_messages(
            agent_id, channel_name, organisation_id, limit, before, after
        )

    async def _get_channel_messages(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int = None,
        limit: int = None,
        before: datetime = None,
        after: datetime = None,
    ) -> list[Message]:
        params = {}
        if limit:
            params["limit"] = limit
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        query = f"?{urlencode(params)}" if params else ""
        url = (
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/messages{query}"
        )

        data = await self._request(
            "GET",
            url,
            organisation_id=organisation_id,
        )

        return [Message.from_dict(m) for m in data]

    async def update_aggregate(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        files: list[tuple[str, bytes, str]] = None,
        replace: bool = False,
        organisation_id: int = None,
    ):
        if channel_name == self._invoking_channel_name:
            raise RuntimeError("Cannot publish to the invoking channel.")

        operation = "PUT" if replace else "PATCH"
        url = f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/aggregate"

        if files is not None:
            if not isinstance(files, list):
                files = [files]
            form = aiohttp.FormData()
            form.add_field(
                "json_payload", json.dumps(data), content_type="application/json"
            )
            for i, (filename, data, content_type) in enumerate(files, start=1):
                form.add_field(
                    f"attachment-{i}",
                    data,
                    filename=filename,
                    content_type=content_type,
                )

            return await self._request(
                operation,
                url,
                data=form,
                organisation_id=organisation_id,
            )

        return await self._request(
            operation,
            url,
            data=data,
            organisation_id=organisation_id,
        )

    async def publish_message(
        self,
        agent_id: int,
        channel_name: str,
        message: dict | str,
        timestamp: datetime | None = None,
        files: list[tuple[str, bytes, str]] = None,
        organisation_id: int = None,
    ):
        if channel_name == self._invoking_channel_name:
            raise RuntimeError("Cannot publish to the invoking channel.")

        payload: dict[str, Any] = {
            "data": message,
        }
        if timestamp is not None:
            payload["ts"] = (
                int(timestamp.timestamp()) * 1000
            )  # milliseconds since epoch

        if files is not None:
            if not isinstance(files, list):
                files = [files]
            form = aiohttp.FormData()
            form.add_field(
                "json_payload", json.dumps(payload), content_type="application/json"
            )
            for i, (filename, data, content_type) in enumerate(files, start=1):
                form.add_field(
                    f"attachment-{i}",
                    data,
                    filename=filename,
                    content_type=content_type,
                )

            payload = form

        return await self._request(
            "POST",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/messages",
            data=payload,
            organisation_id=organisation_id,
        )

    async def update_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: str,
        data: dict | str,
        organisation_id: int = None,
        files: list[tuple[str, bytes, str]] = None,
        replace: bool = True,
    ):
        if channel_name == self._invoking_channel_name:
            raise RuntimeError("Cannot update to the invoking channel.")

        payload: dict[str, Any] = {"data": data}

        if files is not None:
            if not isinstance(files, list):
                files = [files]
            form = aiohttp.FormData()
            form.add_field(
                "json_payload", json.dumps(payload), content_type="application/json"
            )
            for i, (filename, data, content_type) in enumerate(files):
                form.add_field(
                    f"attachment-{i + 1}",
                    data,
                    filename=filename,
                    content_type=content_type,
                )
            payload = form

        return await self._request(
            "PUT" if replace else "PATCH",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            data=payload,
            organisation_id=organisation_id,
        )

    async def fetch_processor_info(
        self, subscription_id: str, organisation_id: int = None
    ):
        return await self._request(
            "GET",
            f"{self.base_url}/processors/subscriptions/{subscription_id}",
            organisation_id=organisation_id,
        )

    async def fetch_schedule_info(self, schedule_id: int, organisation_id: int = None):
        return await self._request(
            "GET",
            f"{self.base_url}/processors/schedules/{schedule_id}",
            organisation_id=organisation_id,
        )

    async def ping_connection_at(
        self,
        agent_id: int,
        online_at: datetime,
        connection_status: ConnectionStatus,
        determination: ConnectionDetermination,
        ping_at: datetime = None,
        user_agent: str = None,
        ip_address: str = None,
        organisation_id: int = None,
    ):
        user_agent = user_agent or "pydoover-processor, aiohttp"
        if not ip_address and self.lookup_ip:
            async with self.session.get("https://checkip.amazonaws.com") as resp:
                ip_address = await resp.text()

        ping_at = ping_at or datetime.now(tz=timezone.utc)

        payload = {
            "status": {
                "status": connection_status.value,
                "last_online": int(online_at.timestamp() * 1000),
                "last_ping": int(ping_at.timestamp() * 1000),
                "user_agent": user_agent,
                "ip": ip_address,
            },
            "determination": determination.value,
        }

        await self.publish_message(
            agent_id,
            "doover_connection",
            payload,
            organisation_id=organisation_id,
        )

        await self.update_aggregate(
            agent_id, "doover_connection", payload, organisation_id=organisation_id
        )

    async def update_connection_config(
        self, agent_id: int, config: ConnectionConfig, organisation_id: int = None
    ):
        payload = {"config": config.to_dict()}
        await self.publish_message(
            agent_id, "doover_connection", payload, organisation_id=organisation_id
        )
        await self.update_aggregate(
            agent_id, "doover_connection", payload, organisation_id=organisation_id
        )

    async def get_channel_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: str,
        organisation_id: int = None,
    ):
        return await self._request(
            "GET",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
            organisation_id=organisation_id,
        )
