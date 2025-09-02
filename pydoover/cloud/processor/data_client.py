import logging
from datetime import datetime
from typing import Any

import aiohttp

from .types import Channel

log = logging.getLogger(__name__)


class DooverData:
    def __init__(self, base_url: str):
        self.agent_id = None
        self.base_url = base_url
        self.session: aiohttp.ClientSession = None

        self.has_persistent_connection = lambda: False
        self.is_processor_v2 = True

    async def setup(self, agent_id: int):
        self.agent_id = agent_id

        if self.session:
            await self.close()

        self.session = aiohttp.ClientSession()

    def set_token(self, token: str):
        self.session.headers["Authorization"] = f"Bearer {token}"

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(self, method, endpoint, data: dict | str = None):
        async with self.session.request(method, endpoint, json=data) as resp:
            log.info(resp.content)
            resp.raise_for_status()
            return await resp.json()

    async def get_channel(self, agent_id: int, channel_name: str):
        data = await self._request(
            "GET", f"{self.base_url}/agents/{agent_id}/channels/{channel_name}"
        )
        return Channel.from_dict(data)

    async def publish_message(
        self,
        agent_id: int,
        channel_name: str,
        message: dict | str,
        timestamp: datetime | None = None,
        record_log: bool = True,
    ):
        payload: dict[str, Any] = {
            "data": message,
            "record_log": record_log,
        }
        if timestamp is not None:
            payload["timestamp"] = int(timestamp.timestamp())

        return await self._request(
            "POST",
            f"{self.base_url}/agents/{agent_id}/channels/{channel_name}",
            data=payload,
        )
