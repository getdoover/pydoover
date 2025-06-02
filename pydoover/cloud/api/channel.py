import base64
import os
import shutil
import uuid
import mimetypes
import logging
import sys
import importlib
from datetime import datetime
from os import PathLike

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .client import Client
    from .agent import Agent
    from .message import Message


class Channel:
    """Base class for Doover channels.

    Channels are used to store state between applications, UI, tasks, processors and more in the Doover system.


    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.



    Attributes
    ----------
    key: str
        The unique identifier for the channel.
    name: str
        The name of the channel.
    agent_id: str
        The agent that owns the channel.
    """

    def __init__(self, *, client, data):
        self.client: "Client" = client
        self._aggregate = None
        self._messages = None

        self._from_data(data)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def _from_data(self, data):
        self.id = data["channel"]
        self.key = data["channel"]
        self.name = data["name"]
        # from the get_agent endpoint this is `agent`, from the get_channel endpoint this is `owner`.
        self.agent_id = data.get("owner") or data.get("agent")
        self._agent = None

        try:
            self._aggregate = data["aggregate"]["payload"]
        except KeyError:
            self._aggregate = None

    @property
    def aggregate(self) -> Any:
        """Returns the aggregate data for the channel."""
        return self._aggregate

    def update(self):
        """Updates the channel data from the server."""
        res = self.client._get_channel_raw(self.id)
        self._from_data(res)

    def get_tunnel_url(self, address: str) -> str | None:
        """Returns the tunnel URL for a given address if it exists in the channel's aggregate.

        Parameters
        ----------
        address : str
            The address to look for in the tunnels.

        Returns
        -------
        str or None
            The tunnel URL if found, otherwise None.

        Raises
        -------
        RuntimeError
            If the channel name is not "tunnels".
        """
        if self.name != "tunnels":
            raise RuntimeError("Tunnels are only valid in the `tunnels` channel.")

        agg = self.fetch_aggregate()
        try:
            tunnels = agg["open"]
        except KeyError:
            return

        found = [t for t in tunnels if t["address"] == address]
        if found:
            return found[0]["url"]

    def fetch_agent(self) -> "Agent":
        """Fetches the agent that owns this channel.

        Returns
        -------
        :class:`pydoover.cloud.api.Agent`
            The agent object that owns this channel.

        Raises
        ------
        :class:`pydoover.cloud.api.NotFound`
            If the agent with the specified ID does not exist or you don't have permission to view it.
        """
        if self._agent is not None:
            return self._agent

        self._agent = self.client.get_agent(self.agent_id)
        return self._agent

    def fetch_aggregate(self) -> dict | str:
        """Fetches the aggregate data for the channel.

        Returns
        -------
        Any
            The aggregate data for the channel, or None if not available.
            This is generally a dictionary for JSON channels, or a string for text channels.
        """
        if self._aggregate is not None:
            return self._aggregate

        self.update()
        return self._aggregate

    def fetch_messages(self, num_messages: int = 10) -> list["Message"]:
        """Fetches the latest messages from the channel.

        Parameters
        ----------
        num_messages : int, optional
            The number of messages to fetch, by default 10.

        Returns
        -------
        list[Message]
            A list of messages from the channel

        """
        if self._messages is not None and len(self._messages) >= num_messages:
            return self._messages

        self._messages = self.client.get_channel_messages(
            self.id, num_messages=num_messages
        )
        return self._messages

    def fetch_messages_in_window(
        self, window_start: datetime, window_end: datetime
    ) -> list["Message"]:
        """Fetches messages from the channel within a specific time window.

        Parameters
        ----------
        window_start : datetime
            The start of the time window.
        window_end : datetime
            The end of the time window.

        Returns
        -------
        list[Message]
            A list of messages from the channel within the specified time window.
        """

        return self.client.get_channel_messages_in_window(
            self.id, window_start, window_end
        )

    def publish(
        self,
        data: Any,
        save_log: bool = True,
        log_aggregate: bool = False,
        override_aggregate: bool = False,
        timestamp: Optional[datetime] = None,
    ):
        """Publishes data to the channel.

        Parameters
        ----------
        data : Any
            The data to publish to the channel. This can be any JSON-serializable object.
        save_log : bool, optional
            Whether to save the published data in the channel's log, by default True.
        log_aggregate : bool, optional
            Whether to log the aggregate data after publishing, by default False.
        override_aggregate : bool, optional
            Whether to override the existing aggregate data with the published data, by default False.
        timestamp : datetime, optional
            The timestamp to use for the published data. If not provided, the current time is used.

        """
        return self.client.publish_to_channel(
            self.id, data, save_log, log_aggregate, override_aggregate, timestamp
        )

    @property
    def last_message(self) -> Optional["Message"]:
        """:class:`pydoover.cloud.api.Message` : Returns the last message published to the channel."""
        messages = self.fetch_messages(num_messages=1)
        if messages is None or len(messages) == 0:
            return None
        return messages[0]

    @property
    def last_update_age(self) -> float | None:
        """Returns the age of the last message in seconds, or None if there are no messages."""
        last_message = self.last_message
        if last_message is None:
            return None
        return last_message.get_age()

    def update_from_file(
        self, file_path: str | PathLike, mime_type: str = None
    ) -> None:
        """Updates the channel with the contents of a file.

        Parameters
        ----------
        file_path : str or PathLike
            The path to the file to read and publish.
        mime_type : str, optional
            The MIME type of the file. If not provided, it will be guessed based on the file extension.
        """

        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(file_path)
            # mime_type = "application/octet-stream"

        with open(file_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode()

        msg = {"output_type": mime_type, "output": b64_data}
        self.publish(msg)


class Processor(Channel):
    """Represents a Doover processor channel.

    Processors are lambda-like functions which run on a trigger.

    A processor channel contains a base64 encoded .zip file of the code
    required to run a processor - either a zip of the source code, or a docker-compose file.
    """

    def update_from_package(self, package_dir: PathLike) -> None:
        """Updates the processor channel with a package directory.

        This method zips the contents of the package directory and publishes it to the channel.

        Parameters
        ----------
        package_dir : str or PathLike
            The path to the directory containing the package files.
        """
        fp = f"/tmp/{uuid.uuid4()}"
        shutil.make_archive(fp, "zip", package_dir)

        with open(f"{fp}.zip", "rb") as f:
            zip_bytes = f.read()
            b64_package = base64.b64encode(zip_bytes).decode()

        self.publish(b64_package)
        os.remove(f"{fp}.zip")

    def invoke_locally(
        self,
        package_dir: str | PathLike,
        agent_id: str,
        access_token: str,
        api_endpoint: str = "https://my.doover.dev",
        package_config: dict = None,
        msg_obj: dict = None,
        task_id: str = None,
        log_channel: str = None,
        agent_settings: dict = None,
    ):
        """Invokes the processor locally with the given parameters.

        This method loads the processor code from the specified package directory and executes it.

        This is very similar to the execution process called from the `doover-task-sandbox`

        Parameters
        ----------
        package_dir : str or PathLike
            The path to the directory containing the processor code.
        agent_id : str
            The agent ID to assume to be the owner of this invocation  / channel
        access_token : str
            The access token to use for API interactions.
        api_endpoint : str, optional
            The API endpoint to use for interactions, by default "https://my.doover.dev".
        package_config : dict, optional
            The config for the trigger
        msg_obj : dict, optional
            The message object that triggered this processor, by default an empty dictionary.
        task_id : str, optional
            The ID of the task channel that invoked this processor, by default None.
        log_channel : str, optional
            The key of the channel to publish logs to, by default None.
        agent_settings : dict, optional
            Settings for the agent, including deployment configuration, by default an empty dictionary.
        """
        package_config = package_config or {}
        msg_obj = msg_obj or {}
        agent_settings = agent_settings or {}

        logging.basicConfig(level=logging.DEBUG)
        sys.path.append(package_dir)

        # Construct the full path to "target.py" within package_dir
        target_path = os.path.join(package_dir, "target.py")

        ## import the loaded generator file
        spec = importlib.util.spec_from_file_location("target", target_path)
        target_task = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(target_task)

        # from .target import generator
        target_task = getattr(target_task, "target")

        #     'agent_id' : The Doover agent id invoking the task e.g. '9843b273-6580-4520-bdb0-0afb7bfec049'
        #     'access_token' : A temporary token that can be used to interact with the Doover API .e.g 'ABCDEFGHJKLMNOPQRSTUVWXYZ123456890',
        #     'api_endpoint' : The API endpoint to interact with e.g. "https://my.doover.com",
        #     'package_config' : A dictionary object with configuration for the task - as stored in the task channel in Doover,
        #     'msg_obj' : A dictionary object of the msg that has invoked this task,
        #     'task_id' : The identifier string of the task channel used to run this processor,
        #     'log_channel' : The identifier string of the channel to publish any logs to
        #     'agent_settings' : {
        #       'deployment_config' : {} # a dictionary of the deployment config for this agent
        task_obj = target_task(
            agent_id=agent_id,
            access_token=access_token,
            api_endpoint=api_endpoint,
            package_config=package_config,
            msg_obj=msg_obj,
            task_id=task_id,
            log_channel=log_channel,
            agent_settings=agent_settings,
            # *args, **kwargs,
        )

        task_obj.execute()


class Task(Channel):
    """Represents a Doover task channel.

    Tasks are channels that trigger a processor when a message is published to them.

    Attributes
    ----------
    processor_key : str
        The key of the processor that this task triggers.
    """

    def _from_data(self, data):
        super()._from_data(data)
        self.processor_key: str = data.get("processor")
        self.processor_id = self.processor_key
        self._processor: Processor = None

    def fetch_processor(self) -> Processor | None:
        """Fetches the processor channel associated with this task.

        Returns
        -------
        Processor or None
            The processor channel that this task triggers, or None if there is no processor attached.
        """
        if self._processor is not None:
            return self._processor
        if self.processor_id is None:
            return

        self._processor = self.client.get_channel(self.processor_id)
        return self._processor

    def subscribe_to_channel(self, channel_id: str):
        """Subscribes this task to a channel.

        Parameters
        ----------
        channel_id : str
            The channel to subscribe this task to.
        """
        return self.client.subscribe_to_channel(channel_id, self.id)

    def unsubscribe_from_channel(self, channel_id: str):
        """Unsubscribes this task from a channel.

        Parameters
        ----------
        channel_id : str
            The channel to unsubscribe this task from.
        """
        return self.client.unsubscribe_from_channel(channel_id, self.id)

    def invoke_locally(
        self,
        package_dir: str | PathLike,
        msg_obj: dict | str,
        agent_settings: dict,
        agent_id: str = None,
    ):
        """Invokes the task locally with the given parameters.

        This method loads the processor code from the specified package directory and executes it.

        Parameters
        ----------
        package_dir : str or PathLike
            The path to the directory containing the processor code.
        msg_obj : dict or str
            The message to invoke the processor with
        agent_settings : dict
            Settings for the agent, including deployment configuration.
        agent_id : str, optional
            The agent ID to assume to be the owner of this invocation / channel, by default None.
        """
        processor = self.fetch_processor()
        if processor is None:
            return

        agent_id = agent_id or self.client.agent_id
        access_token = self.client.access_token.token
        api_endpoint = self.client.base_url
        package_config = self.fetch_aggregate()
        task_id = self.id

        log_channel = None

        processor.invoke_locally(
            package_dir,
            agent_id,
            access_token,
            api_endpoint,
            package_config,
            msg_obj,
            task_id,
            log_channel,
            agent_settings,
        )
