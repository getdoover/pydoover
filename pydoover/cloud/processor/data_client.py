import json
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp
from urllib.parse import urlencode

from pydoover.utils.snowflake import generate_snowflake_id_at


from .types import Channel, Messages

log = logging.getLogger(__name__)


class ConnectionDetermination:
    online = "Online"
    offline = "Offline"


class ConnectionStatus:
    continuous_online = "ContinuousOnline"
    continuous_offline = "ContinuousOffline"
    continuous_pending = "ContinuousPending"

    periodic_unknown = "PeriodicUnknown"
    unknown = "Unknown"


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
            self.session = None

    async def _request(
        self,
        method,
        endpoint,
        data: dict | str | aiohttp.FormData | None = None,
        organisation_id: int = None,
    ):
        org_id = organisation_id or self.organisation_id
        if org_id:
            headers = {"X-Doover-Organisation": str(org_id)}
        else:
            headers = {}

        if isinstance(data, aiohttp.FormData):
            kwargs = {"data": data}
        else:
            kwargs = {"json": data}

        log.debug(f"request {method} {endpoint}")
        
        async with self.session.request(
            method, endpoint, **kwargs, headers=headers
        ) as resp:
            resp.raise_for_status()
            jsondata = await resp.json()
            return jsondata

    async def get_channel(
        self, agent_id: int, channel_name: str, organisation_id: int = None
    ):
        data = await self._request(
            "GET",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}",
            organisation_id=organisation_id,
        )
        return Channel.from_dict(data)

    async def get_channel_messages(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int = None,
        limit: int = None,
        before: int = None,
        after: int = None,
        chunk_size: int = None,
    ):
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
                log.debug(f"Received {len(messages.messages)} messages")
                for message in messages.messages:
                    if int(message.id) <= before:
                        all_messages.append(message)
                if not messages.messages or len(messages.messages) < chunk_size:
                    break
                last_message = messages.messages[-1]
                if int(last_message.id) >= before:
                    break
                after = int(messages.messages[-1].id)

            return Messages(all_messages)

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
    ) -> Messages:
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

        return Messages.from_dict(data)

    async def publish_message(
        self,
        agent_id: int,
        channel_name: str,
        message: dict | str,
        timestamp: datetime | None = None,
        record_log: bool = True,
        is_diff: bool = None,
        organisation_id: int = None,
        files: list[tuple[str, bytes, str]] = None,
    ):
        if channel_name == self._invoking_channel_name:
            raise RuntimeError("Cannot publish to the invoking channel.")

        payload: dict[str, Any] = {
            "data": message,
            "record_log": record_log,
            "is_diff": is_diff or (files is None),
        }
        if timestamp is not None:
            payload["ts"] = (
                int(timestamp.timestamp()) * 1000
            )  # milliseconds since epoch

        if files is not None:
            if type(files) is not list:
                files = [files]
            form = aiohttp.FormData()
            form.add_field("json_payload", json.dumps(payload), content_type="application/json")
            for i in range(len(files)):
                file = files[i]
                form.add_field(f"attachment-{i+1}", file[1], filename=file[0], content_type=file[2])
            return await self._request(
                "POST",
                f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/messages",
                data=form,
                organisation_id=organisation_id,
            )

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
        message: dict | str,
        timestamp: datetime | None = None,
        record_log: bool = True,
        organisation_id: int = None,
        files: list[tuple[str, bytes, str]] = None,
    ):
        if channel_name == self._invoking_channel_name:
            raise RuntimeError("Cannot update to the invoking channel.")

        payload: dict[str, Any] = {
            "data": message,
            "record_log": record_log,
            "is_diff": False,
        }
        if timestamp is not None:
            payload["ts"] = (
                int(timestamp.timestamp()) * 1000
            )  # milliseconds since epoch

        if files is not None:
            if type(files) is not list:
                files = [files]
            form = aiohttp.FormData()
            form.add_field("json_payload", json.dumps(payload), content_type="application/json")
            for i in range(len(files)):
                file = files[i]
                form.add_field(f"attachment-{i+1}", file[1], filename=file[0], content_type=file[2])
            return await self._request(
                "PATCH",
                f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/messages/{message_id}",
                data=form,
                organisation_id=organisation_id,
            )

        return await self._request(
            "PATCH",
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
        connection_status: str,
        determination: str,
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
        return await self.publish_message(
            agent_id,
            "doover_connection",
            {
                "status": {
                    "status": connection_status,
                    "last_online": int(online_at.timestamp() * 1000),
                    "last_ping": int(ping_at.timestamp() * 1000),
                    "user_agent": user_agent,
                    "ip": ip_address,
                },
                "determination": determination,
            },
            organisation_id=organisation_id,
        )
