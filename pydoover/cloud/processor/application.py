import logging
import os
import time

from typing import Any

from .types import MessageCreateEvent, Channel, DeploymentEvent
from .data_client import DooverData
from ...ui import UIManager
from ...config import Schema


log = logging.getLogger()


DEFAULT_DATA_ENDPOINT = "https://data.sandbox.udoover.com/api"


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

        ### kwarg
        #     'agent_id' : The Doover agent id invoking the task e.g. '9843b273-6580-4520-bdb0-0afb7bfec049'
        #     'access_token' : A temporary token that can be used to interact with the Doover API .e.g 'ABCDEFGHJKLMNOPQRSTUVWXYZ123456890',
        #     'api_endpoint' : The API endpoint to interact with e.g. "https://my.doover.com",
        #     'package_config' : A dictionary object with configuration for the task - as stored in the task channel in Doover,
        #     'msg_obj' : A dictionary object of the msg that has invoked this task,
        #     'task_id' : The identifier string of the task channel used to run this processor,
        #     'log_channel' : The identifier string of the channel to publish any logs to
        #     'agent_settings' : {
        #       'deployment_config' : {} # a dictionary of the deployment config for this agent
        #     }

    async def _setup(self):
        self._publish_tags = False

        # this is ok to setup because it doesn't store any state
        await self.api.setup()

        # this is essentially an oauth2 "upgrade" request with some more niceties.
        # we give it a minimal token provisioned from doover data, along with our subscription (uuid) ID
        # and we get back a full token, agent id, app key and a few common channels - ui state, ui cmds,
        # tag values and deployment config.
        self.api.set_token(self._initial_token)
        data = await self.api.fetch_processor_info(self.subscription_id, self.agent_id)

        self.agent_id = self.api.agent_id = data["agent_id"]
        self.api.set_token(data["token"])

        self.app_key = data["app_key"]
        self._tag_values = data["tag_values"]

        # it's probably better to recreate this one every time
        self.ui_manager: UIManager = UIManager(self.app_key, self.api)
        self._ui_to_set = (data["ui_state"], data["ui_cmds"])

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

    async def _handle_event(self, event: dict[str, Any], subscription_id: str):
        start_time = time.time()
        log.info("Initialising processor task")
        log.info(f"Started at {start_time}.")

        # self.app_key: str = event.get("app_key", os.environ.get("APP_KEY"))
        # self.agent_id: int = event["agent_id"]
        self.subscription_id = subscription_id
        self._initial_token = event["token"]
        # this can be set during testing. during normal operation it's signed in the JWT.
        self.agent_id = event.get("agent_id")

        s = time.perf_counter()
        await self._setup()
        log.info(f"Setup took {time.perf_counter() - s} seconds.")

        s = time.perf_counter()
        try:
            await self.setup()
        except Exception as e:
            log.error(f"Error attempting to setup processor: {e} ", exc_info=e)
        log.info(f"user Setup took {time.perf_counter() - s} seconds.")

        await self.ui_manager._processor_set_ui_channels(*self._ui_to_set)

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

        if func is None:
            log.error(f"Unknown event type: {event['op']}")
        else:
            try:
                s = time.perf_counter()
                await func(payload)
                log.info(f"Processing event took {time.perf_counter() - s} seconds.")
            except Exception as e:
                log.error(f"Error attempting to process event: {e} ", exc_info=e)

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
