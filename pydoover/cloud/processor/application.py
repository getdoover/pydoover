import base64
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

from typing import Any

from .types import (
    MessageCreateEvent,
    Channel,
    DeploymentEvent,
    ScheduleEvent,
    IngestionEndpointEvent,
    ConnectionConfig,
)
from .data_client import DooverData, ConnectionDetermination, ConnectionStatus
from ...ui import UIManager
from ...config import Schema


log = logging.getLogger()


DEFAULT_DATA_ENDPOINT = "https://data.doover.com/api"
DEFAULT_OFFLINE_AFTER = 60 * 60  # 1 hour


class Application:
    def __init__(self, config: Schema | None):
        self.config = config

        self._api_endpoint = (
            os.environ.get("DOOVER_DATA_ENDPOINT") or DEFAULT_DATA_ENDPOINT
        )

        self.api = DooverData(self._api_endpoint)

        # set per-task
        self.agent_id: int = None
        self._initial_token: str = None
        self.ui_manager: UIManager = None
        self._tag_values: dict[str, Any] = None
        self._connection_config: dict[str, Any] = None

    async def _setup(self, initial_payload: dict[str, Any]):
        self._publish_tags = False

        # this is ok to setup because it doesn't store any state
        await self.api.setup()

        # this is essentially an oauth2 "upgrade" request with some more niceties.
        # we give it a minimal token provisioned from doover data, along with our subscription (uuid) ID
        # and we get back a full token, agent id, app key and a few common channels - ui state, ui cmds,
        # tag values and deployment config.
        self.api.set_token(self._initial_token)

        if self.subscription_id:
            data = await self.api.fetch_processor_info(self.subscription_id)
        elif self.schedule_id:
            data = await self.api.fetch_schedule_info(self.schedule_id)
        elif self.ingestion_id:
            # doover data invokes this directly so we can pre-load all required info here to save a call...
            data = initial_payload["d"]["upgrade"]
        else:
            raise ValueError("No subscription or schedule ID provided.")

        self.agent_id = self.api.agent_id = data["agent_id"]
        self.api.set_token(data["token"])

        # this should match the original organisation ID, but in case it doesn't, this should
        # probably be the source of truth
        self.api.organisation_id = data["organisation_id"]

        self.app_key = data["app_key"]
        self._tag_values = data["tag_values"]

        if data["connection_data"]:
            self._connection_config = data["connection_data"].get("config", {})
            self.connection_config = ConnectionConfig.from_dict(self._connection_config)
        else:
            # connection config isn't valid for org processors
            # but fresh-ly created devices also won't have connection config...
            self._connection_config = {}
            self.connection_config = None

        # it's probably better to recreate this one every time
        self.ui_manager: UIManager = UIManager(self.app_key, self.api)

        if data["ui_state"] is not None and data["ui_cmds"] is not None:
            self._ui_to_set = (data["ui_state"], data["ui_cmds"])
        else:
            self._ui_to_set = None

        if self.config is not None:
            # if there's no config defined this can legitimately be None in which case don't bother.
            self.config._inject_deployment_config(data["deployment_config"])

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

    async def on_deployment(self, event: DeploymentEvent):
        pass

    async def on_schedule(self, event: ScheduleEvent):
        pass

    async def on_ingestion_endpoint(self, event: IngestionEndpointEvent):
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
        payload = None
        match event["op"]:
            case "on_message_create":
                func = self.on_message_create
                payload = MessageCreateEvent.from_dict(event["d"])
                # prevent infinite loops
                self.api._invoking_channel_name = payload.channel_name
            case "on_deployment":
                func = self.on_deployment
                payload = DeploymentEvent.from_dict(event["d"])
            case "on_schedule":
                func = self.on_schedule
                payload = ScheduleEvent.from_dict(event["d"])
            case "on_ingestion_endpoint":
                func = self.on_ingestion_endpoint
                payload = IngestionEndpointEvent.from_dict(
                    event["d"], parser=self.parse_ingestion_event_payload
                )

        if not await self.pre_hook_filter(payload):
            log.info("Pre-hook filter rejected event.")
            return

        s = time.perf_counter()
        await self._setup(event)
        log.info(f"Setup took {time.perf_counter() - s} seconds.")

        s = time.perf_counter()
        try:
            await self.setup()
        except Exception as e:
            log.error(f"Error attempting to setup processor: {e} ", exc_info=e)
        log.info(f"user Setup took {time.perf_counter() - s} seconds.")

        if self._ui_to_set:
            # not valid for org apps
            await self.ui_manager._processor_set_ui_channels(*self._ui_to_set)

        if func is None:
            log.error(f"Unknown event type: {event['op']}")
        else:
            try:
                s = time.perf_counter()
                await func(payload)
                log.info(f"Processing event took {time.perf_counter() - s} seconds.")
            except Exception as e:
                log.error(f"Error attempting to process event: {e} ", exc_info=e)

        # fixme: publish UI if needed

        if self._publish_tags:
            await self.api.publish_message(
                self.agent_id, "tag_values", self._tag_values
            )

        try:
            await self.close()
        except Exception as e:
            log.error(f"Error attempting to close processor: {e} ", exc_info=e)

        await self._close()

        end_time = time.time()
        log.info(
            f"Finished at {end_time}. Process took {end_time - start_time} seconds."
        )

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

    async def ping_connection(self, online_at: datetime = None):
        if online_at:
            online_at = online_at.replace(tzinfo=timezone.utc)
        else:
            online_at = datetime.now(tz=timezone.utc)

        if datetime.now(tz=timezone.utc) - online_at > timedelta(
            seconds=self._connection_config.get("offline_after", DEFAULT_OFFLINE_AFTER)
        ):
            determination = ConnectionDetermination.offline
        else:
            determination = ConnectionDetermination.online

        await self.api.ping_connection_at(
            self.agent_id,
            online_at,
            connection_status=ConnectionStatus.periodic_unknown,
            determination=determination,
            user_agent=f"pydoover-processor,app_key={self.app_key}",
        )
