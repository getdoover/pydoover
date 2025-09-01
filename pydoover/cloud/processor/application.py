import logging
import os
import time

from typing import Any, TYPE_CHECKING

from .types import MessageCreateEvent, Channel, DeploymentEvent
from .data_client import DooverData
from ...ui import UIManager


log = logging.getLogger()

try:
    import boto3
except ImportError:
    boto3 = None
    AWS_BOTO3_SUPPORT = False
else:
    AWS_BOTO3_SUPPORT = True

if TYPE_CHECKING:
    from ...config import Schema


if AWS_BOTO3_SUPPORT:
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    session = boto3.Session()
    credentials = session.get_credentials()


DEFAULT_TOKEN_ENDPOINT = "https://proc-auth.u.sandbox.udoover.com/token"
DEFAULT_DATA_ENDPOINT = "https://data.sandbox.udoover.com/api"


class Application:
    def __init__(self, config: "Schema"):
        self.config = config

        self._token_endpoint = (
            os.environ.get("DOOVER_TOKEN_ENDPOINT") or DEFAULT_TOKEN_ENDPOINT
        )
        self._api_endpoint = (
            os.environ.get("DOOVER_DATA_ENDPOINT") or DEFAULT_DATA_ENDPOINT
        )

        self.api = DooverData(self._api_endpoint)
        self.is_processor_v2 = True

        # set per-task
        self.agent_id: int = None
        self.ui_manager: UIManager = None
        self._tags: dict[str, Any] = None

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
        self._has_fetched_tags = False
        self._publish_tags = False
        self._tags = None

        # this is ok to setup because it doesn't store any state
        token = await self.fetch_token()
        await self.api.setup(token, self.agent_id)

        # it's probably better to recreate this one every time
        self.ui_manager: UIManager = UIManager(self.app_key, self.api)

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

    async def fetch_token(self):
        if not AWS_BOTO3_SUPPORT:
            raise RuntimeError("AWS Boto3 support not available")

        endpoint = f"{self._token_endpoint}/{self.agent_id}"
        # Prepare the request
        request = AWSRequest(method="GET", url=endpoint)

        # Sign the request
        SigV4Auth(credentials, "execute-api", os.environ.get("AWS_REGION")).add_auth(
            request
        )

        # Convert to requests format and execute
        prepared_request = request.prepare()

        async with self.api.session.get(
            endpoint, headers=prepared_request.headers
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        return data["token"]

    async def on_message_create(self, event: MessageCreateEvent):
        pass

    async def on_deployment(self, event: DeploymentEvent):
        pass

    async def _handle_event(self, event: dict[str, Any], context):
        start_time = time.time()
        log.info("Initialising processor task")
        log.info(f"Started at {start_time}.")

        self.app_key: str = event.get("app_key", os.environ.get("APP_KEY"))
        self.agent_id: int = event["agent_id"]

        try:
            await self.setup()
        except Exception as e:
            log.error(f"Error attempting to setup processor: {e} ", exc_info=e)

        func = None
        payload = None
        match event["EVENT_TYPE"]:
            case "on_message_create":
                func = self.on_message_create
                payload = MessageCreateEvent.from_dict(event)
            case "on_deployment":
                func = self.on_deployment
                payload = DeploymentEvent.from_dict(event)

        if func is None:
            log.error(f"Unknown event type: {event['EVENT_TYPE']}")
        else:
            try:
                await func(payload)
            except Exception as e:
                log.error(f"Error attempting to process event: {e} ", exc_info=e)

        if self._publish_tags:
            await self.api.publish_message(self.agent_id, "tag_values", self._tags)

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
        if not self._has_fetched_tags:
            tags = await self.api.get_channel(self.agent_id, "tag_values")
            self._tags = tags.get(self.app_key, {})
            self._has_fetched_tags = True

        try:
            return self._tags[key]
        except KeyError:
            return default

    async def set_tag(self, key: str, value: Any):
        if not self._has_fetched_tags:
            self._tags = await self.api.get_channel(self.agent_id, "tag_values")

        try:
            self._tags[self.app_key][key] = value
        except KeyError:
            self._tags[self.app_key] = {key: value}

        self._publish_tags = True
