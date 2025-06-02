import logging
import sys
import time

from typing import Any

from ..api import Client, Channel, Message
from ...ui import UIManager

# use the root logger since we want to pipe these logs to a channel.
log = logging.getLogger()


class LogHandler(logging.NullHandler):
    def __init__(self, *args, **kwargs):
        self.logs = []
        super().__init__(*args, **kwargs)

    def handle(self, record):
        if record.levelno < self.level:
            return

        fmt = self.format(record)
        self.logs.append(fmt)

    def emit(self, record):
        self.handle(record)

    def get_logs(self):
        return "\n".join(self.logs)


class ProcessorBase:
    """Base class for all Doover processors.

    Processors can be thought of as tiny lambda functions, and are run in response to messages processed through a channel.
    This base class is designed to be overridden by a user defined class

    In the doover_config.json file we have defined some of these subscriptions
    These are under 'processor_deployments' > 'tasks'

    Examples
    --------

    A simple processor that logs a message to a channel::

        from pydoover.cloud.processor import ProcessorBase

        class target(ProcessorBase):
            def setup(self):
                pass
            def process(self):
                logging.info("Processing message...")


    Attributes
    ----------
    agent_id  : str
        The Doover agent invoking the task
    app_key   : str
        The application key for the processor. This is currently blank.
    access_token : str
        A temporary token that can be used to interact with the Doover API
    log_channel_id : str
        A channel to publish any logs to. This is handled for you through the `logging` module.
    task_id : str
        The identifier string of the task channel which invoked this processor.
    api : :class:`pydoover.cloud.api.Client`
        The Doover API client used to interact with the Doover API.
    ui_manager : :class:`pydoover.ui.UIManager`
        A UI manager to manage the UI for this processor. This is optional and can be used to push updates to the UI.
    message: :class:`pydoover.cloud.api.Message`
        The message that triggered this processor. This is may be `None` depending on the trigger.
    deployment_config : dict[str, Any]
        A dictionary of the deployment configuration for this agent.
    package_config : dict[str, Any]
        A dictionary of the package configuration for this processor.
    """

    def __init__(self, **kwargs):
        self.app_key: str = kwargs.get("app_key", "app")
        self.access_token: str = kwargs["access_token"]

        self._log_handler = LogHandler()
        log.addHandler(self._log_handler)
        log.setLevel(level=logging.INFO)

        self.agent_id: str = kwargs["agent_id"]
        self.log_channel_id: str = kwargs["log_channel"]
        self.task_id: str = kwargs["task_id"]

        self.api: Client = Client(
            token=self.access_token, base_url=kwargs["api_endpoint"]
        )
        self.ui_manager: UIManager = UIManager(self.agent_id, self.app_key, self.api)

        self.deployment_config: dict[str, Any] = kwargs["agent_settings"].get(
            "deployment_config", {}
        )
        self.package_config: dict[str, Any] = kwargs.get("package_config", {})

        try:
            if kwargs["msg_obj"] is None:
                raise KeyError
            self.message = Message(
                client=self.api, data=kwargs["msg_obj"], channel_id=None
            )
        except KeyError:
            self.message = None

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

    def setup(self):
        """The setup function to be invoked before any processing of a message.

        This is designed to be overridden by a user to perform any setup required.

        You do **not** need to call `super().setup()` as this function ordinarily does nothing.
        """
        return NotImplemented

    def process(self):
        """Override this method to perform the actual processing of a message.

        This method is invoked after the setup method, and is where the main logic of the processor should be implemented.

        You do **not** need to call `super().process()` as this function ordinarily does nothing.

        You can optionally update the UI at the end of this method by calling `self.ui_manager.push()`.
        """
        return NotImplemented

    def close(self):
        """Override this method to change behaviour before a processor exits.

        This is invoked after the processing of a message is complete, and can be used to clean up resources or perform any final actions.

        You do **not** need to call `super().close()` as this function ordinarily does nothing.
        """
        return NotImplemented

    def execute(self):
        start_time = time.time()
        log.info(f"Initialising processor task for task channel {self.task_id}")
        log.info(f"Started at {start_time}.")

        try:
            self.import_modules()
            self.setup()

            try:
                self.process()
            except Exception as e:
                log.error(f"ERROR attempting to process message: {e} ", exc_info=e)

        except Exception as e:
            log.error(f"ERROR attempting to initialise process: {e}", exc_info=e)

        try:
            self.close()
        except Exception as e:
            log.error(f"ERROR attempting to close process: {e} ", exc_info=e)

        end_time = time.time()
        log.info(
            f"Finished at {end_time}. Process took {end_time - start_time} seconds."
        )

        if self._log_handler.get_logs() and self.log_channel_id is not None:
            self.api.publish_to_channel(
                self.log_channel_id, self._log_handler.get_logs()
            )

    @staticmethod
    def import_modules():
        """Remove all dangling instances of pydoover modules from the python path."""
        if "pydoover" in sys.modules:
            del sys.modules["pydoover"]
        try:
            del pydoover  # noqa: F821
        except NameError:
            pass
        try:
            del pd  # noqa: F821
        except NameError:
            pass

    def get_agent_config(self, filter_key: str = None) -> Any | None:
        """Fetch a config entry for the agent who owns (or invoked) this processor.

        Parameters
        ----------
        filter_key : str, optional
            If provided, will return only the value for this key in the config. Otherwise, returns the entire config dictionary.

        Returns
        -------
        dict or None
            The agent's deployment configuration dictionary, or None if no deployment config is set, or the key is not found.
        """
        if not self.deployment_config:
            return None
        if filter_key:
            return self.deployment_config.get(filter_key)
        return self.deployment_config

    def fetch_channel(self, channel_key: str) -> Channel:
        """Helper method to fetch a channel by its key.

        Parameters
        ----------
        channel_key : str
            The key of the channel to fetch.

        Returns
        -------
        :class:`pydoover.cloud.api.Channel`
            The channel object corresponding to the provided key.

        Raises
        -------
        :class:`pydoover.cloud.api.NotFound`
            If the channel with the specified key does not exist.
        """
        return self.api.get_channel(channel_key)

    def fetch_channel_named(self, channel_name: str) -> Channel:
        """Helper method to fetch a channel by its name, owned by the current agent.

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

        return self.api.get_channel_named(channel_name, self.agent_id)
