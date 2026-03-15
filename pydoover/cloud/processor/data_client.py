import logging
from datetime import datetime, timezone
from typing import Any

from ...api import AsyncDataClient
from ...models import (
    Aggregate,
    Channel,
    File,
    Message,
    SubscriptionInfo,
)
from ...models.connection import (
    ConnectionConfig,
    ConnectionDetermination,
    ConnectionStatus,
)
from ...utils.snowflake import generate_snowflake_id_at

log = logging.getLogger(__name__)


class ProcessorDataClient:
    """Processor-layer wrapper around :class:`AsyncDataClient`.

    Adds anti-recursion checks for invoking channels, datetime-to-snowflake
    conversion, chunked message fetching, and connection helpers.
    """

    def __init__(self, base_url: str):
        self.agent_id: int | None = None
        self.organisation_id: int | None = None
        self._client = AsyncDataClient(base_url)

        self.has_persistent_connection = lambda: False
        self.is_processor_v2 = True

        # for onmessagecreate events this is set to the trigger channel
        # so that we don't publish to the same channel we're receiving from
        # and get in an infinite loop
        self._invoking_channel_name: str | None = None
        self.lookup_ip = True
        self.app_key: str | None = None

    async def setup(self):
        await self._client.setup()

    def set_token(self, token: str):
        self._client.set_token(token)

    async def close(self):
        await self._client.close()

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

    # -- Channel operations --------------------------------------------------

    async def get_channel(
        self, agent_id: int, channel_name: str, organisation_id: int = None
    ) -> Channel:
        return await self._client.get_channel(
            agent_id,
            channel_name,
            organisation_id=organisation_id or self.organisation_id,
        )

    async def get_channel_aggregate(
        self, agent_id: int, channel_name: str
    ) -> Aggregate:
        return await self._client.get_aggregate(
            agent_id,
            channel_name,
            organisation_id=self.organisation_id,
        )

    async def get_channel_messages(
        self,
        agent_id: int,
        channel_name: str,
        organisation_id: int = None,
        limit: int = None,
        before: datetime | None = None,
        after: datetime | None = None,
        chunk_size: int | None = None,
        field_names: list[str] = None,
    ) -> list[Message]:
        before_sf = generate_snowflake_id_at(before) if before else None
        after_sf = generate_snowflake_id_at(after) if after else None
        org = organisation_id or self.organisation_id

        if chunk_size is not None and before_sf is not None and after_sf is not None:
            log.debug(f"Splitting messages into chunks of {chunk_size}")
            all_messages = []

            while True:
                log.debug(f"Fetching messages from {after_sf} with limit {chunk_size}")
                messages = await self._client.list_messages(
                    agent_id,
                    channel_name,
                    limit=chunk_size,
                    after=after_sf,
                    field_names=field_names,
                    organisation_id=org,
                )
                log.debug(f"Received {len(messages)} messages")
                for message in messages:
                    if int(message.id) <= before_sf:
                        all_messages.append(message)
                if not messages or len(messages) < chunk_size:
                    break
                last_message = messages[-1]
                if int(last_message.id) >= before_sf:
                    break
                after_sf = int(messages[-1].id)

            return all_messages

        return await self._client.list_messages(
            agent_id,
            channel_name,
            before=before_sf,
            after=after_sf,
            limit=limit,
            field_names=field_names,
            organisation_id=org,
        )

    async def get_channel_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        organisation_id: int = None,
    ) -> Message:
        return await self._client.get_message(
            agent_id,
            channel_name,
            message_id,
            organisation_id=organisation_id or self.organisation_id,
        )

    # -- Publishing ----------------------------------------------------------

    async def update_aggregate(
        self,
        agent_id: int,
        channel_name: str,
        data: dict[str, Any],
        files: list[File] = None,
        replace: bool = False,
        organisation_id: int = None,
        allow_invoking_channel: bool = False,
    ):
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, data, allow_invoking_channel)

        return await self._client.update_aggregate(
            agent_id,
            channel_name,
            data,
            replace=replace,
            files=files,
            organisation_id=organisation_id or self.organisation_id,
        )

    async def publish_message(
        self,
        agent_id: int,
        channel_name: str,
        message: dict | str,
        timestamp: datetime | None = None,
        files: list[File] = None,
        organisation_id: int = None,
        allow_invoking_channel: bool = False,
    ):
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, message, allow_invoking_channel)

        ts = None
        if timestamp is not None:
            ts = int(timestamp.timestamp()) * 1000  # milliseconds since epoch

        return await self._client.create_message(
            agent_id,
            channel_name,
            data=message,
            ts=ts,
            files=files,
            organisation_id=organisation_id or self.organisation_id,
        )

    async def update_message(
        self,
        agent_id: int,
        channel_name: str,
        message_id: int,
        data: dict | str,
        organisation_id: int = None,
        files: list[File] = None,
        replace: bool = True,
        allow_invoking_channel: bool = False,
    ):
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, data, allow_invoking_channel)

        return await self._client.update_message(
            agent_id,
            channel_name,
            message_id,
            data=data,
            replace=replace,
            files=files,
            organisation_id=organisation_id or self.organisation_id,
        )

    # -- Processor info ------------------------------------------------------

    async def fetch_processor_info(
        self, subscription_id: int, organisation_id: int = None
    ) -> SubscriptionInfo:
        return await self._client.get_subscription_info(
            subscription_id,
            organisation_id=organisation_id or self.organisation_id,
        )

    async def fetch_schedule_info(
        self, schedule_id: int, organisation_id: int = None
    ) -> SubscriptionInfo:
        return await self._client.get_schedule_info(
            schedule_id,
            organisation_id=organisation_id or self.organisation_id,
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
        await self.publish_message(
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
        await self.publish_message(
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
