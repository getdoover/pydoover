import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

from .types import Channel

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
        self, method, endpoint, data: dict | str = None, organisation_id: int = None
    ):
        org_id = organisation_id or self.organisation_id
        async with self.session.request(
            method, endpoint, json=data, headers={"X-Doover-Organisation": str(org_id)}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_channel(
        self, agent_id: int, channel_name: str, organisation_id: int = None
    ):
        data = await self._request(
            "GET",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}",
            organisation_id=organisation_id,
        )
        return Channel.from_dict(data)

    async def publish_message(
        self,
        agent_id: int,
        channel_name: str,
        message: dict | str,
        timestamp: datetime | None = None,
        record_log: bool = True,
        organisation_id: int = None,
    ):
        if channel_name == self._invoking_channel_name:
            raise RuntimeError("Cannot publish to the invoking channel.")

        payload: dict[str, Any] = {
            "data": message,
            "record_log": record_log,
            "is_diff": True,
        }
        if timestamp is not None:
            payload["ts"] = (
                int(timestamp.timestamp()) * 1000
            )  # milliseconds since epoch

        return await self._request(
            "POST",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}/messages",
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
