import asyncio
import argparse
import json
import os
import logging
import time
from collections import deque

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING, Callable

from pydoover.tags import Tags
from pydoover.tags.manager import TagsManagerDocker
from collections.abc import Coroutine

from ..ui import UICommandsManager

try:
    from aiohttp.web import Response, Server, ServerRunner, TCPSite
except ImportError:
    RUN_HEALTHCHECK = False
else:
    RUN_HEALTHCHECK = True

from .device_agent.device_agent import DeviceAgentInterface
from .modbus import ModbusInterface
from .platform import PlatformInterface

from ..models import (
    Aggregate,
    AggregateUpdateEvent,
    EventSubscription,
    File,
    Message,
    MessageCreateEvent,
    MessageUpdateEvent,
    OneShotMessage,
)
from ..rpc import RPCManager
from ..ui import UI
from ..utils import (
    setup_logging as utils_setup_logging,
    apply_diff,
    generate_diff,
)

if TYPE_CHECKING:
    from ..config import Schema

log = logging.getLogger(__name__)


class Application:
    """Base class for a Doover application. All apps will inherit from this class, and override the setup and main_loop methods.

    You generally don't need to worry about initiating parameters to this class as that will be done through `run_app`.

    Examples
    --------

    The following is an incredibly simple example of a Doover application that shows how to initiate this Application class.
    However, in practice, it is suggested to use the template application repository for a more structured, complex scaffold
    for building apps.

    A basic application::

        from pydoover.docker import Application, run_app
        from pydoover.config import Schema
        from pydoover import ui
        from pydoover.tags import Tag, Tags

        class MyTags(Tags):
            ready = Tag("boolean", default=False)

        class MyUI(ui.UI):
            ready = ui.BooleanVariable("ready", "Ready", curr_val=MyTags.ready)

        class MyApp(Application):
            config_class = Schema
            tags_class = MyTags
            ui_class = MyUI

            def setup(self):
                self.tags.ready.set(True)

            def main_loop(self):
                # Your main loop logic here
                pass

        if __name__ == "__main__":
            run_app(MyApp())


    Attributes
    ----------
    config : Schema
        The configuration schema for the application. See [] for more information about config schemas.
    device_agent : DeviceAgentInterface
        The interface to the Doover Device Agent, which allows the app to communicate with the Doover cloud and other devices.
    platform_iface : PlatformInterface
        The interface to the Doover Platform, which allows the app to interact with the device's hardware.
    modbus_iface : ModbusInterface
        The interface to the Modbus communication protocol, allowing the app to read and write Modbus registers.
    ui_manager : UIManager
        The UI manager for the application, which handles the user interface elements and commands.
    app_key : str
        The application key for the app, used to identify it in the Doover cloud. This is globally unique.
    """

    config_class: type["Schema"] | None = None
    ui_class: type[UI] | None = None
    tags_class: type[Tags] | None = None

    def __init__(
        self,
        app_key: str = None,
        device_agent: DeviceAgentInterface = None,
        platform_iface: PlatformInterface = None,
        modbus_iface: ModbusInterface = None,
        name: str = None,
        test_mode: bool = False,
        config_fp: str = None,
        healthcheck_port: int = None,
    ):
        self.config: "Schema" = self.__class__.config_class()

        self._tags: Tags | None = None
        self._ui: UI | None = None
        self.app_key = app_key
        self.app_display_name = ""

        if config_fp:
            path = Path(config_fp)
            if not path.exists() or not path.is_file():
                raise RuntimeError(f"Config file {config_fp} does not exist")
            self._config_fp = path
        else:
            self._config_fp = None

        self.device_agent = device_agent or DeviceAgentInterface(app_key, "")
        self.platform_iface = platform_iface or PlatformInterface(app_key, "")
        self.modbus_iface = modbus_iface or ModbusInterface(
            app_key, "", config=self.config
        )

        self.tag_manager = TagsManagerDocker(
            client=self.device_agent,
        )
        self.tags = self.__class__.tags_class(
            self.app_key, self.tag_manager, self.config
        )
        self.ui = self.__class__.ui_class(self.config, self.tags)

        self._ready = asyncio.Event()

        self.rpc = RPCManager(self)
        self.ui_manager = UICommandsManager(self)

        self.app_key = app_key
        self.app_display_name = ""

        self._ready = asyncio.Event()

        self._shutdown_at = None
        self.force_log_on_shutdown = False

        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name

        self.loop_target_period = 1
        self._error_wait_period = 10
        self.dda_startup_timeout: int = 300

        self._last_interval_time: float | None = None
        self._last_loop_time_warning: float | None = None
        self._loop_times = deque(maxlen=20)

        self._test_next_event = asyncio.Event()
        self._test_next_loop_done = asyncio.Event()
        self.test_mode = test_mode

        self._is_healthy = False
        self._healthcheck_port = healthcheck_port

    async def _handle_healthcheck(self, _request):
        if self._is_healthy:
            return Response(text="OK", status=200)
        else:
            return Response(text="ERROR", status=503)

    async def _on_deployment_config_update(self, config: dict[str, Any]):
        try:
            app_config = config["applications"][self.app_key]
        except KeyError:
            log.warning(
                f"Application key {self.app_key} not found in deployment config"
            )
            app_config = {}

        self.device_agent.agent_id = app_config.get("AGENT_ID")
        log.info(f"Agent ID set: {self.device_agent.agent_id}")

        self.app_display_name = app_config.get("APP_DISPLAY_NAME", "")
        log.info(f"Application display name set: {self.app_display_name}")

        log.info(f"Deployment Config Updated: {app_config}")
        if self.config is not None:
            self.config._inject_deployment_config(app_config)

    async def __aenter__(self):
        # any more setup here...
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_type, (KeyboardInterrupt, asyncio.CancelledError)):
            log.info("Exiting app manager")
        else:
            log.error(f"Error in main loop: {exc_val}", exc_info=exc_tb)

        self._ready.clear()
        await self.close()

    async def next(self):
        """Increment a main loop iteration. This is only available in test mode.

        Normally, the main loop runs in an infinite cycle every `loop_target_period` seconds.

        During testing, it is helpful to be able to control the flow of the main loop, so this method allows you to
        increment the main loop iteration manually. Simply call this method to run the next iteration of the main loop.

        Examples
        --------

        A simple example::

            from pydoover.docker import Application, run_app
            from pydoover.config import Schema

            async def test_app():
                class MyApp(Application):
                    config_class = Schema

                app = MyApp(test_mode=True)
                asyncio.create_task(run_app(app, start=False))

                # wait for app to start
                await app.wait_until_ready()

                # increment the main loop once
                await app.next()

        Raises
        -------
        RuntimeError
            If this method is called when the app is not in test mode. This method is only available in test mode.
        """
        if not self.test_mode:
            raise RuntimeError("You can only use `app.next()` in test mode.")

        self._test_next_event.set()
        self._test_next_loop_done.clear()
        await self._test_next_loop_done.wait()

    async def _run(self):
        if RUN_HEALTHCHECK:
            try:
                log.info(
                    f"Starting healthcheck server on http://127.0.0.1:{self._healthcheck_port}"
                )
                server = Server(self._handle_healthcheck, access_log=None)
                runner = ServerRunner(server)
                await runner.setup()
                site = TCPSite(runner, "127.0.0.1", self._healthcheck_port)
                await site.start()
            except Exception as e:
                log.error(f"Error starting healthcheck server: {e}", exc_info=e)
        else:
            log.info("`aiohttp` not installed, skipping healthcheck server.")

        log.info(
            f"Waiting for DDA to start with a timeout of {self.dda_startup_timeout} seconds."
        )
        await self.device_agent.wait_until_healthy(self.dda_startup_timeout)

        if self._config_fp is not None:
            if self.config is not None:
                data = json.loads(self._config_fp.read_text())
                self.config._inject_deployment_config(data)
        else:
            self.device_agent.add_event_callback(
                "deployment_config",
                self._wrap_aggregate_callback(self._on_deployment_config_update),
                EventSubscription.aggregate_update,
            )
            await self.device_agent.wait_for_channels_sync(["deployment_config"])
            # Fetch initial deployment config from the aggregate cache
            try:
                config_agg = await self.device_agent.fetch_channel_aggregate(
                    "deployment_config"
                )
                await self._on_deployment_config_update(config_agg.data)
            except Exception:
                log.warning("No initial deployment config available from DDA")

        # await self._resolve_tags()
        # await self._resolve_ui()

        await self.modbus_iface.setup()

        try:
            await self._setup()
            await self.setup()
        except Exception as e:
            log.error(f"Error in setup function: {e}", exc_info=e)
            log.warning(
                f"\n\nWaiting {self._error_wait_period} seconds before restarting app\n\n"
            )
            await asyncio.sleep(self._error_wait_period)
            return

        self._ready.set()

        try:
            shutdown_at = self.tag_manager.get_tag("shutdown_at", raise_key_error=True)
        except KeyError:
            pass
        else:
            await self._check_shutdown_at(shutdown_at)

        self.tag_manager.subscribe_to_tag("shutdown_at", self._on_shutdown_at)

        ## allow for other async tasks to run between setup and loop
        await asyncio.sleep(0.2)

        while True:
            if self.test_mode:
                await self._test_next_event.wait()
                self._test_next_event.clear()  # clear it for the next iteration...

            try:
                await self._main_loop()
                await self.main_loop()
                await self.tag_manager.commit_tags()
            except Exception as e:
                log.error(f"Error in loop function: {e}", exc_info=e)
                log.warning(
                    f"\n\n\nWaiting {self._error_wait_period} seconds before restarting app\n\n"
                )
                self._is_healthy = False
                await asyncio.sleep(self._error_wait_period)
                break
            else:
                if self.test_mode is False:
                    # slow down the loop in live mode.
                    # await asyncio.sleep(self.loop_target_period)
                    await self.wait_for_interval(self.loop_target_period)
                else:
                    # allow other async tasks to run if the user has done a doozy and chained a whole heap of .next()s
                    await asyncio.sleep(0.01)

                self._is_healthy = True

            if self.test_mode is True:
                # signal that the loop is done.
                self._test_next_loop_done.set()

    async def wait_for_interval(self, target_time: float):
        """
        Waits for the necessary amount of time to maintain a consistent interval
        of `target_time` seconds between calls to this method.
        """
        if target_time is None or target_time <= 0:
            return

        current_time = time.time()
        if self._last_interval_time is None:
            self._last_interval_time = current_time
            ## Wait for half the target time on the first call
            await asyncio.sleep(target_time / 2)
            return

        elapsed = current_time - self._last_interval_time
        await self._assess_loop_time(
            elapsed, target_time
        )  ## This will display a warning if the loop is running slower than target
        elapsed = current_time - self._last_interval_time
        remaining = target_time - elapsed
        log.debug(f"Last loop time: {elapsed}, target_time: {target_time}")
        if remaining > 0:
            log.debug(f"Sleeping for {remaining} seconds to maintain target loop time")
            await asyncio.sleep(remaining)
        self._last_interval_time = time.time()

    async def _assess_loop_time(self, last_loop_time: float, target_time: float):
        """
        Assess the loop time and adjust the target time if necessary.
        """
        self._loop_times.append(last_loop_time)
        average_loop_time = sum(self._loop_times) / len(self._loop_times)
        log.debug(f"Average loop time: {average_loop_time}, target_time: {target_time}")

        ## If the loop time is greater than 20% above the target time, display a warning every 6 seconds or so
        if average_loop_time > (target_time * 1.2):
            if (
                not hasattr(self, "_last_loop_time_warning")
                or self._last_loop_time_warning is None
            ):
                self._last_loop_time_warning = time.time()
            elif time.time() - self._last_loop_time_warning > 6:
                log.warning(
                    f"Loop is running slower than target. Average loop time: {average_loop_time}, target_time: {target_time}"
                )
                self._last_loop_time_warning = time.time()

    async def close(self):
        log.info(
            "\n########################################"
            "\n\nClosing app manager...\n\n"
            "########################################\n"
        )

        await self.device_agent.close()
        await self.platform_iface.close()
        await self.modbus_iface.close()

        for task in asyncio.all_tasks():
            task.cancel()

    @property
    def is_ready(self) -> bool:
        """Check if the application is ready.

        The application is ready when all initialization tasks have completed and the UI is set up.
        In practice, this means your `setup` method has completed and the application is connected to the cloud.

        Returns
        -------
        bool
            True if the application is ready, False otherwise.
        """
        return self._ready.is_set()

    async def wait_until_ready(self):
        """Wait until the application is ready.

        This method waits (blocks) the current loop until the application is ready.
        """
        await self._ready.wait()

    ## Agent Interface Functions (DDA)

    async def on_message_create(self, event: MessageCreateEvent):
        """Called when a new message is created on a subscribed channel.

        Override this method in your application to handle message creation events.

        You do **not** need to call ``super().on_message_create()`` — this method does nothing by default.

        Parameters
        ----------
        event : MessageCreateEvent
            The message creation event.
        """
        pass

    async def on_message_update(self, event: MessageUpdateEvent):
        """Called when a message is updated on a subscribed channel.

        Override this method in your application to handle message update events.

        You do **not** need to call ``super().on_message_update()`` — this method does nothing by default.

        Parameters
        ----------
        event : MessageUpdateEvent
            The message update event.
        """
        pass

    async def on_oneshot_message(self, event: OneShotMessage):
        """Called when a one-shot message is received on a subscribed channel.

        Override this method in your application to handle one-shot message events.

        You do **not** need to call ``super().on_oneshot_message()`` — this method does nothing by default.

        Parameters
        ----------
        event : OneShotMessage
            The one-shot message event.
        """
        pass

    async def on_aggregate_update(self, event: AggregateUpdateEvent):
        """Called when the aggregate is updated on a subscribed channel.

        Override this method in your application to handle aggregate update events.

        You do **not** need to call ``super().on_aggregate_update()`` — this method does nothing by default.

        Parameters
        ----------
        event : AggregateUpdateEvent
            The aggregate update event.
        """
        pass

    async def subscribe(
        self,
        channel_name: str,
        events: EventSubscription = EventSubscription.all,
    ):
        """Subscribe to events on a channel.

        When events are received on the channel, the appropriate ``on_*`` callback methods
        will be called (e.g. :meth:`on_message_create`, :meth:`on_aggregate_update`).

        You can subscribe to specific event types using the ``events`` parameter, or
        subscribe to all events (the default).

        Examples
        --------

        Subscribe to all events on a channel::

            async def setup(self):
                await self.subscribe("my_channel")

        Subscribe to only message creation events::

            async def setup(self):
                await self.subscribe("my_channel", EventSubscription.message_create)

        Combine event types::

            async def setup(self):
                await self.subscribe(
                    "my_channel",
                    EventSubscription.message_create | EventSubscription.aggregate_update,
                )

        Parameters
        ----------
        channel_name : str
            The name of the channel to subscribe to.
        events : EventSubscription, optional
            Which event types to subscribe to. Defaults to ``EventSubscription.all``.
        """
        self.device_agent.add_event_callback(channel_name, self._dispatch_event, events)

    @staticmethod
    def _wrap_aggregate_callback(callback):
        """Wrap a ``(data_dict)`` callback for use with ``add_event_callback``."""

        async def _wrapper(event):
            data = event.aggregate.data if event.aggregate else {}
            await callback(data)

        return _wrapper

    async def _dispatch_event(self, event):
        """Dispatch an event to the appropriate user-facing handler."""
        if isinstance(event, OneShotMessage):
            await self.on_oneshot_message(event)
        elif isinstance(event, MessageCreateEvent):
            await self.on_message_create(event)
        elif isinstance(event, MessageUpdateEvent):
            await self.on_message_update(event)
        elif isinstance(event, AggregateUpdateEvent):
            await self.on_aggregate_update(event)

    def get_is_dda_available(self):
        return self.device_agent.get_is_dda_available()

    def get_is_dda_online(self):
        return self.device_agent.get_is_dda_online()

    def get_has_dda_been_online(self):
        return self.device_agent.get_has_dda_been_online()

    async def create_message(
        self,
        channel_name: str,
        data: dict[str, Any],
        files: list[File] = None,
        timestamp: datetime = None,
    ) -> int:
        """Create a new message on a channel.

        Parameters
        ----------
        channel_name : str
            The name of the channel to create the message on.
        data : dict
            The message data.
        files : list[File], optional
            Files to attach to the message.
        timestamp : datetime, optional
            The timestamp for the message. Defaults to now (UTC).

        Returns
        -------
        int
            The ID of the created message.
        """
        return await self.device_agent.create_message(
            channel_name, data, files=files, timestamp=timestamp
        )

    async def update_message(
        self,
        channel_name: str,
        message_id: int,
        data: dict[str, Any],
        files: list[File] = None,
        replace_data: bool = False,
        clear_attachments: bool = False,
    ) -> Message:
        """Update an existing message on a channel.

        Parameters
        ----------
        channel_name : str
            The name of the channel the message belongs to.
        message_id : int
            The ID of the message to update.
        data : dict
            The updated message data. By default this is merged with existing data.
        files : list[File], optional
            Files to attach to the message.
        replace_data : bool, optional
            If True, replace the message data entirely instead of merging. Defaults to False.
        clear_attachments : bool, optional
            If True, clear existing attachments before adding new ones. Defaults to False.

        Returns
        -------
        Message
            The updated message.
        """
        return await self.device_agent.update_message(
            channel_name,
            message_id,
            data,
            files=files,
            replace_data=replace_data,
            clear_attachments=clear_attachments,
        )

    async def update_channel_aggregate(
        self,
        channel_name: str,
        data: dict[str, Any],
        files: list[File] = None,
        clear_attachments: bool = False,
        replace_data: bool = False,
        max_age_secs: float = None,
    ) -> Aggregate:
        """Update the aggregate data on a channel.

        Parameters
        ----------
        channel_name : str
            The name of the channel to update the aggregate on.
        data : dict
            The aggregate data. By default this is merged with existing data.
        files : list[File], optional
            Files to attach to the aggregate.
        clear_attachments : bool, optional
            If True, clear existing attachments before adding new ones. Defaults to False.
        replace_data : bool, optional
            If True, replace the aggregate data entirely instead of merging. Defaults to False.
        max_age_secs : float, optional
            Maximum age in seconds before the aggregate is published to the cloud.

        Returns
        -------
        Aggregate
            The updated aggregate.
        """
        return await self.device_agent.update_channel_aggregate(
            channel_name,
            data,
            files=files,
            clear_attachments=clear_attachments,
            replace_data=replace_data,
            max_age_secs=max_age_secs,
        )

    ## Platform Interface Functions

    def fetch_di(self, di):
        return self.platform_iface.fetch_di(di)

    def fetch_ai(self, ai):
        return self.platform_iface.fetch_ai(ai)

    def fetch_do(self, do):
        return self.platform_iface.fetch_do(do)

    def set_do(self, do, value):
        return self.platform_iface.set_do(do, value)

    def schedule_do(self, do, value, delay_secs):
        return self.platform_iface.schedule_do(do, value, delay_secs)

    def fetch_ao(self, ao):
        return self.platform_iface.fetch_ao(ao)

    def set_ao(self, ao, value):
        return self.platform_iface.set_ao(ao, value)

    def schedule_ao(self, ao, value, delay_secs):
        return self.platform_iface.schedule_ao(ao, value, delay_secs)

    ## Modbus Interface Functions

    def read_modbus_registers(
        self, address, count, register_type, modbus_id=None, bus_id=None
    ):
        return self.modbus_iface.read_registers(
            bus_id=bus_id,
            modbus_id=modbus_id,
            start_address=address,
            num_registers=count,
            register_type=register_type,
        )

    def write_modbus_registers(
        self, address, values, register_type, modbus_id=None, bus_id=None
    ):
        return self.modbus_iface.write_registers(
            bus_id=bus_id,
            modbus_id=modbus_id,
            start_address=address,
            values=values,
            register_type=register_type,
        )

    def add_new_modbus_read_subscription(
        self,
        address,
        count,
        register_type,
        callback,
        poll_secs=None,
        modbus_id=None,
        bus_id=None,
    ):
        return self.modbus_iface.add_read_register_subscription(
            bus_id=bus_id,
            modbus_id=modbus_id,
            start_address=address,
            num_registers=count,
            register_type=register_type,
            poll_secs=poll_secs,
            callback=callback,
        )

    # state

    @property
    def _shutdown_requested(self):
        return self.tag_manager.get_tag("shutdown_requested")

    async def _on_shutdown_at(self, _, shutdown_at):
        if shutdown_at is None:
            return
        await self._check_shutdown_at(shutdown_at)

    async def _check_shutdown_at(self, shutdown_at):
        if not self.is_ready:
            log.info("Ignoring check shutdown request, app not ready yet.")
            return

        dt = datetime.fromtimestamp(shutdown_at, tz=timezone.utc)
        if self._shutdown_at is None or (
            dt > self._shutdown_at and dt > datetime.now(tz=timezone.utc)
        ):
            # shutdown should be in the future and not already scheduled
            log.info(f"Shutdown scheduled at {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            self._shutdown_at = dt
            await self.on_shutdown_at(dt)

    def subscribe_to_tag(
        self,
        tag_key: str,
        callback: Callable[[str, Any], Coroutine],
        app_key: str = None,
        global_tag: bool = False,
    ):
        if global_tag:
            self.tag_manager.subscribe_to_tag(tag_key, callback=callback)
        else:
            self.tag_manager.subscribe_to_tag(
                tag_key, callback=callback, app_key=app_key or self.app_key
            )

    def get_tag(
        self, tag_key: str, app_key: str = None, default: Any = None
    ) -> Any | None:
        """Get a tag value for a specific app.

        If you want to get a global tag, use :meth:`get_global_tag` instead.

        Examples
        --------

        >>> tag_value = self.get_tag("other_tag", "some-other-app-1234")
        >>> print(f"other-tag is {tag_value} for app some-other-app-1234")

        >>> tag_value = self.get_tag("my_tag")
        >>> print(f"my-tag is {tag_value} for current app {self.app_key}")


        Parameters
        ----------
        tag_key: str
            The tag to fetch.
        app_key: str, optional
            The app key to get the tag for. This defaults to the current app.
        default: Any, optional
            The default value to return if the tag does not exist. Defaults to None.


        Returns
        -------
        Any
            The value of the tag, or None if the tag does not exist.
        """

        return self.tag_manager.get_tag(
            tag_key, default=default, app_key=app_key or self.app_key
        )

    def get_global_tag(self, tag_key: str, default: Any = None) -> Any | None:
        """Get a global tag value.

        Global tags are tags that are not specific to an app, but are shared across all apps.

        Warnings
        --------
        Due to namespacing concerns, it's best practice to use global tags sparingly and only for values that are truly global in nature.
        For example, you might use a global tag for a shutdown request or a system-wide status indicator.
        If you need to get a tag for a specific app, use :meth:`get_tag` instead.

        Examples
        --------
        >>> is_flag_set = self.get_global_tag("my_global_flag")
        >>> print(f"Global flag my_global_flag is set to {is_flag_set}")

        Parameters
        ----------
        tag_key: str
            The global tag to fetch.
        default: Any, optional
            The default value to return if the tag does not exist. Defaults to None.

        Returns
        -------
        Any
            The value of the global tag, or None if the tag does not exist.
        """
        return self.tag_manager.get_tag(tag_key, default=default, app_key=None)

    async def set_tag(
        self,
        tag_key: str,
        value: Any,
        app_key: str = None,
        only_if_changed: bool = True,
    ) -> None:
        """Set a tag value.

        This method sets a tag value for a specific app. If you want to set a global tag, use :meth:`set_global_tag` instead.

        Tag updates are accumulated and flushed to the aggregate once per main loop cycle.
        Call :meth:`flush_tags` to force an immediate flush.

        Examples
        --------
        >>> self.set_tag("my_tag", "my_value")
        >>> self.set_tag("other_tag", "other_value", app_key="some-other-app-1234")

        Parameters
        ----------
        tag_key: str
            The tag to set.
        value: Any
            The value to set the tag to.
        app_key: str, optional
            The app key to set the tag for. This defaults to the current app's key.
        only_if_changed: bool, optional
            If True, the tag will only be set if the value is different from the current value. Defaults to True.
        """
        await self.tag_manager.set_tag(
            tag_key,
            value,
            app_key=app_key or self.app_key,
            only_if_changed=only_if_changed,
        )

    async def set_tags(
        self, tags: dict[str, Any], app_key: str = None, only_if_changed: bool = True
    ) -> None:
        """Set multiple tags at once."""
        await self.tag_manager.set_tags(
            tags,
            app_key=app_key or self.app_key,
            only_if_changed=only_if_changed,
        )

    async def set_global_tag(
        self, tag_key: str, value: Any, only_if_changed: bool = True
    ) -> None:
        """Set a global tag value.

        As in :meth:`get_global_tag`, global tags are not specific to an app, but are shared across all apps and should be used sparingly as such.

        Examples
        --------
        >>> self.set_global_tag("my_global_flag", True)
        >>> self.set_global_tag("system_status", "operational")

        Parameters
        ----------
        tag_key: str
            The global tag to set.
        value: Any
            The value to set the global tag to.
        only_if_changed: bool, optional
            If True, the tag will only be set if the value is different from the current value. Defaults to True.
        """
        await self.tag_manager.set_tag(
            tag_key,
            value,
            app_key=None,
            only_if_changed=only_if_changed,
        )

    def _do_set_tags(
        self,
        tags: dict[str, Any],
        app_key: str | None,
        is_global: bool = False,
        only_if_changed: bool = True,
    ):
        if is_global:
            data = tags
        else:
            if app_key is None:
                app_key = self.app_key
            data = {app_key: tags}

        # Always track for logging (even if value unchanged)
        apply_diff(self._pending_tag_log, data, clone=False)

        if only_if_changed:
            diff = generate_diff(self._tag_values, data, do_delete=False)
            if len(diff) == 0:
                return

        apply_diff(self._tag_values, data, clone=False)
        apply_diff(self._pending_tag_aggregate, data, clone=False)
        self._tags_dirty = True

    ## Power Manager Functions
    async def request_shutdown(self) -> None:
        """Request a system shutdown."""
        log.info("Requesting shutdown")
        await self.set_global_tag("shutdown_requested", True)

    async def on_shutdown_at(self, dt: datetime) -> None:
        """Callback for when a shutdown is scheduled.

        See [https://docs.doover.com/docker/shutdown-behaviour] for a detailed explanation of the shutdown behaviour.

        This method is called when a shutdown is scheduled, and can be overridden by an application to perform
        specific actions before the imminent system shutdown.

        By default, this method does nothing.

        Examples
        --------

        Simple logging example::

            class MyApplication(Application):
                # setup, main_loop, etc...

                async def on_shutdown_at(self, dt: datetime):
                    log.info(f"Shutdown scheduled at {dt}. Performing cleanup...")


        Parameters
        ----------
        dt : datetime
            The datetime when the shutdown is scheduled.
        """
        pass
        # if self.force_log_on_shutdown:
        #     await self._update_ui(force_log=True)
        # fixme: this should probs update tags?

    async def check_can_shutdown(self) -> bool:
        """Check if the application can shutdown.

        This method is called when the application is requested to shutdown,
        and should be overridden by an application if specific logic is required when a shutdown is requested.

        See [https://docs.doover.com/docker/shutdown-behaviour] for a detailed explanation of the shutdown behaviour.

        This must be implemented as an asynchronous function, take no parameters and return a boolean value.

        A return value of `True` indicates that the application can shutdown, while `False` indicates that it cannot.

        By default, this method always returns `True`, meaning the application can shutdown without any checks.

        Examples
        --------
        Simple example that checks if Digital Output 0 (maybe an engine or fan) is Low before returning True::

            class MyApplication(Application):
                # setup, main_loop, etc...

                async def check_can_shutdown(self) -> bool:
                    if await self.platform_iface.fetch_do(0) == 0:
                        log.info("Digital Output 0 is Low. Can shutdown.")
                        return True
                    else:
                        log.warning("Digital Output 0 is High. Cannot shutdown.")
                        return False

        """
        return True

    ## App Functions

    async def _setup(self):
        log.info(f"Setting up internal app: {self.name}")
        self.rpc.register_handlers(self)
        self.ui_manager.register_handlers(self)

        await self.tags.setup()
        await self.ui.setup()
        self.ui_manager._set_interactions(self.ui.get_interactions())

        # bit of a cheeky double publish to ensure the old schema is cleared before we set it.
        # ideally I'd like to have a `clear_set_keys` parameter or something to PUT to the `self.app_key` key.
        if not self.ui.is_static:
            log.info("Updating ui_state with runtime-generated schema.")
            schema = self.ui.to_schema()
            await self.update_channel_aggregate(
                "ui_state", {"state": {self.app_key: None}}, max_age_secs=-1
            )
            await self.update_channel_aggregate(
                "ui_state", {"state": {self.app_key: schema}}, max_age_secs=-1
            )

        if self.test_mode:
            ## Quit out of setup if we are in test mode.
            await self.tag_manager.setup(skip_sync=True)
            return

        # Fetch initial tag values from the aggregate cache (seeded by _run_channel_stream)
        try:
            # wait for tag values to sync from DDA - but only for 10sec.
            await asyncio.wait_for(self.tag_manager.setup(), timeout=10.0)
        except TimeoutError:
            log.warning("Timed out waiting for tag values to be set")

    async def _main_loop(self):
        log.debug(f"Running internal main_loop: {self.name}")
        if self._shutdown_requested:
            try:
                resp = await self.check_can_shutdown()
            except Exception as e:
                log.error(
                    f"Error checking if we can shutdown: {e}. Assuming False.",
                    exc_info=e,
                )
                resp = False

            await self.set_tag("shutdown_check_ok", resp)

    async def setup(self):
        """The main setup function for the application.

        Your application should override this method to perform any setup tasks that need to be done before the main loop starts.

        Generally, that involves setting up UI, registering callbacks, starting state machines, etc.

        This function can be asynchronous or synchronous, depending on your needs.

        You do **not** need to call `super()` inside your setup method; this function does nothing by default.
        """
        return NotImplemented

    async def main_loop(self):
        """The main loop function for the application.

        Your application should override this method to perform the main logic of your application.

        Generally, this involves running and checking any state machines, setting tags, reading sensors, etc. depending on your application.

        This function is called in a continuous loop, so it should generally not perform any long blocking calls, instead deferring to
        checking if a result is ready to be processed in a future loop.

        You can control the speed at which this loop runs by setting the `loop_target_period` attribute of the application instance.
        By default, this is set to a target invocation period of 1 second.

        This function can be asynchronous or synchronous, depending on your needs.

        You do **not** need to call `super()` inside your setup method; this function does nothing by default.
        """
        return NotImplemented


def parse_args():
    parser = argparse.ArgumentParser(description="Doover Docker App Manager")

    parser.add_argument("--app-key", type=str, default=None, help="App Key")
    parser.add_argument(
        "--remote-dev", type=str, default=None, help="Remote device URI"
    )
    parser.add_argument(
        "--dda-uri", type=str, default=None, help="Doover Device Agent URI"
    )
    parser.add_argument(
        "--plt-uri", type=str, default="localhost:50053", help="Platform Interface URI"
    )
    parser.add_argument(
        "--modbus-uri", type=str, default="localhost:50054", help="Modbus Interface URI"
    )
    parser.add_argument(
        "--config-fp",
        type=str,
        default=None,
        help="Config file path to override app config",
    )
    parser.add_argument(
        "--healthcheck-port",
        type=int,
        default=None,
        help="Port for the healthcheck server (default: 49200). This must be overidden per-app to avoid conflicts.",
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help="Debug Mode"
    )

    args = parser.parse_args()

    app_key = args.app_key or os.environ.get("APP_KEY")
    dda_uri = args.dda_uri or os.environ.get("DDA_URI") or "localhost:50051"
    plt_uri = args.plt_uri or os.environ.get("PLT_URI") or "localhost:50053"
    modbus_uri = args.modbus_uri or os.environ.get("MODBUS_URI") or "localhost:50054"
    healthcheck_port = int(
        args.healthcheck_port or os.environ.get("HEALTHCHECK_PORT") or 49200
    )
    config_fp = args.config_fp or os.environ.get("CONFIG_FP")

    remote_dev = args.remote_dev or os.environ.get("REMOTE_DEV")
    if remote_dev is not None:
        dda_uri = dda_uri.replace("localhost", remote_dev)
        plt_uri = plt_uri.replace("localhost", remote_dev)
        modbus_uri = modbus_uri.replace("localhost", remote_dev)

    debug = args.debug or os.environ.get("DEBUG") == "1"
    return (
        app_key,
        dda_uri,
        plt_uri,
        modbus_uri,
        remote_dev,
        config_fp,
        debug,
        healthcheck_port,
    )


def run_app(
    app: Application,
    start: bool = True,
    setup_logging: bool = True,
    log_formatter: logging.Formatter = None,
    log_filters: logging.Filter | list[logging.Filter] = None,
):
    """Run the application.

    This function initializes the application, sets up the interfaces, and runs the main loop.
    If `start` is True, it will run the application in a blocking manner, otherwise it will return an async runner function.
    This is useful for testing or when you want to run the application in an event loop without blocking the main thread, but not recommended for production use.

    Examples
    --------

    The general recommended structure for starting applications in the `__init__.py` file::

        from pydoover.docker import run_app

        from .application import SampleApplication
        from .app_config import SampleConfig

        def main():
            run_app(SampleApplication())


    Parameters
    ----------
    app : Application
        The application instance to run.
    start : bool, optional
        If True, the application will run in a blocking manner. If False, it will return an async runner function.
        Defaults to True.
    setup_logging : bool, optional
        If True, the logging will be set up. Defaults to True. You can pass a custom logging formatter to the `log_formatter` parameter.
    log_formatter : logging.Formatter, optional
        The logging formatter to use. Defaults to None, which will use a simple custom formatter defined in `pydoover.utils.LogFormatter`.
    log_filters : logging.Filter | list[logging.Filter], optional
        The logging filters to use. Defaults to None, which will not apply any filters.
    """
    (
        app_key,
        dda_uri,
        plt_uri,
        modbus_uri,
        remote_dev,
        config_fp,
        debug,
        healthcheck_port,
    ) = parse_args()

    if setup_logging:
        utils_setup_logging(debug=debug, formatter=log_formatter, filters=log_filters)

    for inst in (
        app,
        app.platform_iface,
        app.modbus_iface,
        app.device_agent,
        # app.ui_manager,
        app.tag_manager,
    ):
        inst.app_key = app_key

    app.platform_iface.uri = plt_uri
    app.modbus_iface.uri = modbus_uri
    app.device_agent.uri = dda_uri
    app._config_fp = config_fp and Path(config_fp)
    app._healthcheck_port = healthcheck_port

    async def runner():
        async with app:
            await app._run()

    if start:
        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            pass
    else:
        return runner()


def run_app2(
    app_cls: type[Application],
    dda_iface_cls: type[DeviceAgentInterface] = DeviceAgentInterface,
    plt_iface_cls: type[PlatformInterface] = PlatformInterface,
    mb_iface_cls: type[ModbusInterface] = ModbusInterface,
):
    (
        app_key,
        dda_uri,
        plt_uri,
        modbus_uri,
        remote_dev,
        config_fp,
        debug,
        healthcheck_port,
    ) = parse_args()

    utils_setup_logging(debug)
    config = app_cls.config_class() if app_cls.config_class is not None else None

    app = app_cls(
        app_key,
        platform_iface=plt_iface_cls(app_key, plt_uri),
        modbus_iface=mb_iface_cls(app_key, modbus_uri, config=config),
        device_agent=dda_iface_cls(app_key, dda_uri),
        config_fp=config_fp,
        healthcheck_port=healthcheck_port,
    )
    app.config = config

    async def runner():
        async with app:
            await app._run()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        pass
