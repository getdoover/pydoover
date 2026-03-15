import base64
import io
import json
import logging
import os
import time
import sys
from datetime import datetime, timedelta, timezone

from typing import Any

from .types import (
    ManualInvokeEvent,
    MessageCreateEvent,
    Channel,
    DeploymentEvent,
    ScheduleEvent,
    IngestionEndpointEvent,
    ConnectionConfig,
    AggregateUpdateEvent,
    DooverConnectionStatus,
)
from .data_client import ProcessorDataClient
from ...models import ConnectionDetermination, ConnectionStatus, SubscriptionInfo
from ...ui import UIManager
from ...config import Schema


log = logging.getLogger(__name__)


DEFAULT_DATA_ENDPOINT = "https://data.doover.com/api"
DEFAULT_OFFLINE_AFTER = 60 * 60  # 1 hour

console_handler = logging.StreamHandler(sys.stdout)


class Application:
    def __init__(self, config: Schema | None):
        self.config = config

        self.received_deployment_config = None

        self._api_endpoint = (
            os.environ.get("DOOVER_DATA_ENDPOINT") or DEFAULT_DATA_ENDPOINT
        )

        self.api = ProcessorDataClient(self._api_endpoint)

        # set per-task
        self.agent_id: int = None
        self._initial_token: str = None
        self.ui_manager: UIManager = None
        self._tag_values: dict[str, Any] = None
        self._connection_config: dict[str, Any] = None

        self.log_capture_string = io.StringIO()
        self.string_stream_handler = logging.StreamHandler(self.log_capture_string)
        logging.getLogger().addHandler(self.string_stream_handler)
        logging.getLogger().addHandler(console_handler)

        self._record_tag_update: bool = True
        self._update_external_tags: bool = False

    async def _setup(self, initial_payload: dict[str, Any]):
        self._publish_tags = False

        # this is ok to setup because it doesn't store any state
        await self.api.setup()

        # this is essentially an oauth2 "upgrade" request with some more niceties.
        # we give it a minimal token provisioned from doover data, along with our subscription (uuid) ID
        # and we get back a full token, agent id, app key and a few common channels - ui state, ui cmds,
        # tag values and deployment config.
        self.api.set_token(self._initial_token)

        # Always prioritise the upgrade payload, otherwise get it from the normal method
        if initial_payload["d"].get("upgrade", None) is not None:
            info = SubscriptionInfo.from_dict(initial_payload["d"]["upgrade"])
        else:
            if self.subscription_id:
                info = await self.api.fetch_processor_info(self.subscription_id)
            elif self.schedule_id:
                info = await self.api.fetch_schedule_info(self.schedule_id)
            elif self.ingestion_id:
                # doover data invokes this directly so we can pre-load all required info here to save a call...
                info = SubscriptionInfo.from_dict(initial_payload["d"]["upgrade"])
            else:
                raise ValueError("No subscription or schedule ID provided.")

        self.agent_id = self.api.agent_id = info.agent_id
        self.api.set_token(info.token)

        # this should match the original organisation ID, but in case it doesn't, this should
        # probably be the source of truth
        self.api.organisation_id = info.organisation_id or self.organisation_id

        self.app_key = info.app_key
        self.api.app_key = self.app_key
        self._tag_values = info.tag_values

        connection_data = info.connection_data
        if not connection_data:
            # connection config isn't valid for org processors
            # but fresh-ly created devices also won't have connection config...
            self._connection_config = {}
            self.connection_config = None
        else:
            self._connection_config = connection_data.get("config", {})
            self._connection_status = connection_data.get("status", {})
            self.connection_config = ConnectionConfig.from_dict(self._connection_config)
            self.connection_status = DooverConnectionStatus.from_dict(
                self._connection_status
            )

        # it's probably better to recreate this one every time
        self.ui_manager: UIManager = UIManager(self.app_key, self.api)

        if info.ui_state is not None and info.ui_cmds is not None:
            self._ui_to_set = (info.ui_state, info.ui_cmds)
        else:
            self._ui_to_set = None

        if self.config is not None:
            # if there's no config defined this can legitimately be None in which case don't bother.
            self.config._inject_deployment_config(info.deployment_config)

        # Store the deployment config for later use
        self.received_deployment_config = info.deployment_config
        self.display_name = self.received_deployment_config.get("APP_DISPLAY_NAME")
        self.app_id = self.received_deployment_config.get("APP_ID")
        self.ui_manager.set_display_name(self.display_name)

    async def _close(self):
        await self.api.close()

    async def setup(self):
        """The setup function to be invoked before any processing of a message.

        This is designed to be overridden by a user to perform any setup required.

        You do **not** need to call `super().setup()` as this function ordinarily does nothing.
        """
        return NotImplemented

    async def close(self):
        """Override this method to change behaviour before a processor exits.

        This is invoked after the processing of a message is complete, and can be used to clean up resources or perform any final actions.

        You do **not** need to call `super().close()` as this function ordinarily does nothing.
        """
        return NotImplemented

    async def on_message_create(self, event: MessageCreateEvent):
        pass

    async def on_aggregate_update(self, event: AggregateUpdateEvent):
        pass

    async def on_deployment(self, event: DeploymentEvent):
        pass

    async def on_schedule(self, event: ScheduleEvent):
        pass

    async def on_ingestion_endpoint(self, event: IngestionEndpointEvent):
        pass

    async def on_manual_invoke(self, event: ManualInvokeEvent):
        pass

    def parse_ingestion_event_payload(self, payload: str):
        # by default, this **should** be base64 encoded json bytes
        # but it's not required to be, and the user should override this if e.g. it's a C-packed struct.
        # the important thing to note, however, is that doover data wraps the binary in b64 so you must decode that
        # first, and every time.
        as_bytes = base64.b64decode(payload)
        return json.loads(as_bytes)

    async def pre_hook_filter(self, event):
        """This is an early filter that can be used to reject events before they are processed.

        This is intended to be fast and cheap; to quickly discard unwanted events based on their payload.

        This is run before `setup` and any API setup.
        """
        return True

    async def post_setup_filter(self, event):
        """This is a filter that can be used to reject events after `setup` and API setup.

        If you don't require any API calls, config, etc. - use pre_hook_filter which is cheaper, faster and earlier in the process.
        """
        return True

    async def _handle_event(self, event: dict[str, Any], subscription_id: str = None):
        start_time = time.time()
        log.info("Initialising processor task")
        log.info(f"Started at {start_time}.")

        # self.app_key: str = event.get("app_key", os.environ.get("APP_KEY"))
        # self.agent_id: int = event["agent_id"]
        self.subscription_id = subscription_id

        try:
            self.schedule_id = event["d"]["schedule_id"]
        except KeyError:
            self.schedule_id = None

        try:
            self.ingestion_id = event["d"]["ingestion_id"]
        except KeyError:
            self.ingestion_id = None

        try:
            # org ID should be set in both schedules and subscriptions, but just in case it isn't...
            self.organisation_id = event["d"]["organisation_id"]
        except KeyError:
            self.organisation_id = None

        # this is the initial token provided. For a subscription, it will be a temporary token.
        # For a schedule, it will be a long-lived token.
        # Both have permission to access the info endpoint, only.
        self._initial_token = event["token"]
        # this can be set during testing. during normal operation it's signed in the JWT.
        self.agent_id = event.get("agent_id")

        func = None
        original_func = None
        payload = None
        match event["op"]:
            case "on_message_create":
                func = self.on_message_create
                payload = MessageCreateEvent.from_dict(event["d"])
                # prevent infinite loops
                self.api._invoking_channel_name = payload.channel_name
                original_func = Application.on_message_create

            case "on_deployment":
                func = self.on_deployment
                payload = DeploymentEvent.from_dict(event["d"])
                original_func = Application.on_deployment
            case "on_schedule":
                func = self.on_schedule
                payload = ScheduleEvent.from_dict(event["d"])
                original_func = Application.on_schedule
            case "on_ingestion_endpoint":
                func = self.on_ingestion_endpoint
                payload = IngestionEndpointEvent.from_dict(
                    event["d"], parser=self.parse_ingestion_event_payload
                )
                original_func = Application.on_ingestion_endpoint
            case "on_manual_invoke":
                func = self.on_manual_invoke
                payload = ManualInvokeEvent.from_dict(event["d"])
                original_func = Application.on_manual_invoke
            case "on_aggregate_update":
                func = self.on_aggregate_update
                payload = AggregateUpdateEvent.from_dict(event["d"])
                self.api._invoking_channel_name = payload.channel.name
                original_func = Application.on_aggregate_update

        if func == original_func:
            log.info(f"Skipping {func.__name__} event as no overridden handler found.")
            return None

        self._payload = payload

        if not await self.pre_hook_filter(payload):
            log.info("Pre-hook filter rejected event.")
            return None

        s = time.perf_counter()
        await self._setup(event)
        log.info(f"Setup took {time.perf_counter() - s} seconds.")

        if (
            isinstance(payload, AggregateUpdateEvent)
            and payload.channel.name == "tag_values"
            and self.app_key in payload.request_data.data
        ) or (
            isinstance(payload, MessageCreateEvent)
            and payload.channel.name == "tag_values"
            and self.app_key in payload.message.data
        ):
            log.info("Rejecting event publishing to tag_values within this app key.")
            return None

        s = time.perf_counter()
        try:
            await self.setup()
        except Exception as e:
            log.error(f"Error attempting to setup processor: {e} ", exc_info=e)
        log.info(f"user Setup took {time.perf_counter() - s} seconds.")

        if not await self.post_setup_filter(payload):
            log.info("Post-setup filter rejected event.")
            return None

        if self._ui_to_set:
            # not valid for org apps
            await self.ui_manager._processor_set_ui_channels(*self._ui_to_set)

        result = None
        if func is None:
            log.error(f"Unknown event type: {event['op']}")
        else:
            try:
                s = time.perf_counter()
                result = await func(payload)
                log.info(f"Processing event took {time.perf_counter() - s} seconds.")
            except Exception as e:
                log.error(f"Error attempting to process event: {e} ", exc_info=e)

        # fixme: publish UI if needed

        if self._publish_tags:
            try:
                update = self._tag_values[self.app_key]
            except KeyError:
                update = None

            if self._update_external_tags:
                update = self._tag_values
            else:
                update = update and {self.app_key: update}

            # only publish if there are tags to publish.
            # Only publish external tags if requested explicitly (can cause recursion issues)
            if update:
                await self.api.update_aggregate(self.agent_id, "tag_values", update)

                if self._record_tag_update:
                    await self.api.publish_message(self.agent_id, "tag_values", update)

        try:
            await self.close()
        except Exception as e:
            log.error(f"Error attempting to close processor: {e} ", exc_info=e)

        await self._close()

        end_time = time.time()
        log.info(
            f"Finished at {end_time}. Process took {end_time - start_time} seconds. result: {result}"
        )

        return result

    async def fetch_channel(self, channel_name: str) -> Channel:
        """Helper method to fetch a channel by its name.

        Parameters
        ----------
        channel_name : str
            The name of the channel to fetch.

        Returns
        -------
        :class:`pydoover.cloud.api.Channel`
            The channel object corresponding to the provided key.

        Raises
        -------
        :class:`pydoover.cloud.api.NotFound`
            If the channel with the specified key does not exist.
        """
        return await self.api.get_channel(self.agent_id, channel_name)

    async def get_tag(self, key: str, default: Any = None):
        try:
            return self._tag_values[self.app_key][key]
        except KeyError:
            return default

    async def set_tag(self, key: str, value: Any):
        try:
            current = self._tag_values[self.app_key][key]
        except KeyError:
            current = None

        if current == value:
            # don't publish if it hasn't changed
            return

        try:
            self._tag_values[self.app_key][key] = value
        except KeyError:
            self._tag_values[self.app_key] = {key: value}

        self._publish_tags = True

    async def ping_connection(
        self,
        online_at: datetime = None,
        connection_status: ConnectionStatus = ConnectionStatus.periodic_unknown,
        offline_at: datetime = None,
    ):
        if not online_at:
            online_at = datetime.now(tz=timezone.utc)

        # prefer the user's settings if they've set it.
        if offline_at:
            offline_after = (offline_at - online_at).total_seconds()
        else:
            offline_after = self._connection_config.get(
                "offline_after", DEFAULT_OFFLINE_AFTER
            )

        if datetime.now(tz=timezone.utc) - online_at > timedelta(seconds=offline_after):
            determination = ConnectionDetermination.offline
        else:
            determination = ConnectionDetermination.online

        await self.api.ping_connection_at(
            self.agent_id,
            online_at,
            connection_status=connection_status,
            determination=determination,
            user_agent=f"pydoover-processor,app_key={self.app_key}",
        )
