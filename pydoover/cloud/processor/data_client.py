import logging
from datetime import datetime, timezone
from typing import Any

from ...api import AsyncDataClient
from ...models import (
    File,
    Message,
)
from ...models.connection import (
    ConnectionConfig,
    ConnectionDetermination,
    ConnectionStatus,
)

log = logging.getLogger(__name__)


class ProcessorDataClient(AsyncDataClient):
    """Processor-layer extension of :class:`AsyncDataClient`.

    Adds anti-recursion checks for invoking channels, datetime-to-snowflake
    conversion, chunked message fetching, and connection helpers.
    """

    def __init__(self, base_url: str):
        super().__init__(base_url)
        self.agent_id: int | None = None

        self.has_persistent_connection = lambda: False
        self.is_processor_v2 = True

        # for onmessagecreate events this is set to the trigger channel
        # so that we don't publish to the same channel we're receiving from
        # and get in an infinite loop
        self._invoking_channel_name: str | None = None
        self.lookup_ip = True
        self.app_key: str | None = None

    # -- Anti-recursion checks -----------------------------------------------

    def _check_invoking_channel(self, channel_name, data, allow_invoking_channel):
        if allow_invoking_channel:
            log.warning(
                "Publishing to invoking channel with override to allow. "
                "Be careful - this will cause recursion issues if not handled correctly."
            )
            return True

        if channel_name != "tag_values":
            raise RuntimeError("Cannot publish to the invoking channel.")

        if any(k != self.app_key for k in data.keys()):
            raise RuntimeError(
                "Cannot publish to tag_values outside the scope of this app "
                "without explicit enable."
            )

        return True

    # -- Convenience: chunked message fetching with datetime support ----------

    # -- Overrides with anti-recursion ---------------------------------------

    async def create_message(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        ts: int | None = None,
        files: list[File] = None,
        organisation_id: int = None,
        allow_invoking_channel: bool = False,
    ) -> Message:
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, data, allow_invoking_channel)

        return await super().create_message(
            agent_id,
            channel_name,
            data=data,
            ts=ts,
            files=files,
            organisation_id=organisation_id or self.organisation_id,
        )

    async def update_aggregate(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        files: list[File] = None,
        replace: bool = False,
        organisation_id: int = None,
        allow_invoking_channel: bool = False,
        **kwargs,
    ):
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, data, allow_invoking_channel)

        return await super().update_aggregate(
            agent_id,
            channel_name,
            data,
            replace=replace,
            files=files,
            organisation_id=organisation_id or self.organisation_id,
            **kwargs,
        )

    async def update_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        data: dict | str,
        replace: bool = True,
        files: list[File] = None,
        organisation_id: int = None,
        allow_invoking_channel: bool = False,
        **kwargs,
    ):
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, data, allow_invoking_channel)

        return await super().update_message(
            agent_id,
            channel_name,
            message_id,
            data=data,
            replace=replace,
            files=files,
            organisation_id=organisation_id or self.organisation_id,
            **kwargs,
        )

    # -- Connection helpers --------------------------------------------------

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
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get("https://checkip.amazonaws.com") as resp:
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

        org = organisation_id or self.organisation_id
        await self.create_message(
            agent_id,
            "doover_connection",
            payload,
            organisation_id=org,
        )
        await self.update_aggregate(
            agent_id,
            "doover_connection",
            payload,
            organisation_id=org,
        )

    async def update_connection_config(
        self, agent_id: int, config: ConnectionConfig, organisation_id: int = None
    ):
        payload = {"config": config.to_dict()}
        org = organisation_id or self.organisation_id
        await self.create_message(
            agent_id,
            "doover_connection",
            payload,
            organisation_id=org,
        )
        await self.update_aggregate(
            agent_id,
            "doover_connection",
            payload,
            organisation_id=org,
        )
