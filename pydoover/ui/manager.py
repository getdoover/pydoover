import copy
import inspect
import logging
import re
import time
import json
from datetime import datetime

from typing import Union, Any, Optional, TypeVar, TYPE_CHECKING

from .element import Element
from .interaction import SlimCommand, Interaction, NotSet
from .misc import ApplicationVariant
from .submodule import Container, NAME_VALIDATOR, Application as UIApplication
from .variable import Variable

from ..cloud.api import Client

from ..utils import call_maybe_async, get_is_async, maybe_async, find_object_with_key

if TYPE_CHECKING:
    from ..docker.device_agent.device_agent import DeviceAgentInterface

log = logging.getLogger(__name__)
ElementT = TypeVar("ElementT", bound=Element)
InteractionT = TypeVar("InteractionT", bound=Interaction)


class UIManager:
    def __init__(
        self,
        app_key: str = None,
        client: Union["Client", "DeviceAgentInterface"] = None,
        auto_start: bool = False,
        min_ui_update_period: int = 600,
        min_observed_update_period: int = 4,
        is_async: bool = None,
    ):
        self._is_async = get_is_async(is_async)
        self.client = client
        # to determine whether we can use event-based logic. some reason we can't
        self._has_persistent_connection = client and client.has_persistent_connection()
        self._subscriptions_ready = False

        self.app_key = app_key

        self.last_ui_state = (
            dict()
        )  # A python dictionary of the full state from the cloud
        self.last_ui_state_update = None

        self.last_ui_state_wss_connections = dict()
        self.last_ui_state_wss_connections_update = None

        self.last_ui_cmds = dict()
        self.last_ui_cmds_update = None

        self._base_container = UIApplication(name=self.app_key)
        self._interactions: dict[str, Interaction] = dict()

        self._has_critical_interaction_pending: bool = False
        # self._has_critical_ui_state_pending: bool = False
        self._critical_values = dict()  # legacy

        self.min_ui_update_period = min_ui_update_period
        self.min_observed_update_period = min_observed_update_period
        self._last_pushed_time = None
        self._last_push_and_log_time = None

        # legacy, list of subscriptions to call when we have a command update.
        self._cmds_subscriptions = []

        # to allow for @ui.callback("pattern") decorators
        self._command_callbacks = []

        # to keep track of which interactions / ui_cmds to change
        self._changed_interactions = set()

        if auto_start:
            self.start_comms()

    def start_comms(self):
        self._setup_subscriptions()

    def _is_conn_ready(self, setup: bool = False) -> bool:
        if not self._has_persistent_connection:
            return self.client is not None

        if self._subscriptions_ready:
            return True
        elif setup:
            self._setup_subscriptions()
            return self._is_conn_ready(setup=False)  # don't setup for a second time
        else:
            log.error(
                "Attempted use of dda_iface in ui_manager without dda_iface being ready"
            )
            return False

    def is_connected(self) -> bool:
        if not self._has_persistent_connection:
            return self._is_conn_ready()

        if not self._is_conn_ready():
            return False

        return self.client.get_is_dda_online()

    get_is_connected = is_connected

    def is_being_observed(self):
        if not self.last_ui_state_wss_connections:
            return False

        try:
            if not isinstance(self.last_ui_state_wss_connections, dict):
                self.last_ui_state_wss_connections = json.loads(
                    self.last_ui_state_wss_connections
                )
            connections = set(self.last_ui_state_wss_connections["connections"].keys())

            # agent ID will get set on startup in processor Client and on config load in apps.
            if self.client.agent_id and len(connections - {self.client.agent_id}) > 0:
                return True

            # if there is more than one connection, then we are being observed
            return len(connections) > 1
        except Exception as e:
            log.error(f"Error checking if being observed: {e}")
            return False

    def has_been_connected(self):
        if self._has_persistent_connection and self.client is not None:
            return self.client.get_has_dda_been_online()
        return self.last_ui_state is not None

    get_has_been_connected = has_been_connected

    def _setup_subscriptions(self):
        if not self._has_persistent_connection:
            log.error(
                "Attempted to setup subscriptions without valid connection client."
            )
            return

        if self.client is None:
            log.warning("Attempted to setup subscriptions without client being set")
            return

        log.info("Setting up dda subscriptions")
        self.client.add_subscription("ui_state", self.on_state_update)
        self.client.add_subscription(
            "ui_state@wss_connections", self.on_state_wss_update
        )
        self.client.add_subscription("ui_cmds", self.on_command_update_async)

        self._subscriptions_ready = True

    async def await_comms_sync(self, timeout: int = 5) -> bool:
        if not self._has_persistent_connection:
            return False

        if not hasattr(self.client, "wait_for_channels_sync_async"):
            log.error("Attempted to await comms sync without valid connection client.")
            return False
        return await self.client.wait_for_channels_sync_async(
            channel_names=["ui_state", "ui_cmds"],
            timeout=timeout,
        )

    async def on_state_update(self, _, aggregate: dict[str, Any]):
        self._set_new_ui_state(aggregate)

    async def on_state_wss_update(self, _, aggregate: dict[str, Any]):
        self.last_ui_state_wss_connections = aggregate
        self.last_ui_state_wss_connections_update = time.time()

    def _on_command_update_common(self, aggregate: dict[str, Any]):
        aggregate = self._set_new_ui_cmds(aggregate)

        # add commands that don't currently exist
        to_add = {k: v for k, v in aggregate.items() if k not in self._interactions}
        for name, current_value in to_add.items():
            self._interactions[name] = SlimCommand(name, current_value)

        return aggregate

    def on_command_update(self, _, aggregate: dict[str, Any]):
        log.debug(f"running on command update, {aggregate}")
        self._on_command_update_common(aggregate)

        changed = {c: v for c, v in aggregate.items()}

        ## Iterate through all the commands that we have locally, and call the callback if it exists
        for command_name, command in self._interactions.items():
            if command_name in changed:
                new_value = changed[command_name]
            else:
                new_value = None
                if hasattr(command, "default") and command.default is not None:
                    new_value = command.default

            if not command._is_new_value(new_value):
                continue

            command._handle_new_value(new_value)

            for pattern, callback in self._command_callbacks:
                if pattern.match(command_name):
                    callback(command, new_value)

    async def on_command_update_async(self, _, aggregate: dict[str, Any]):
        log.debug("Running on_command_update_async")
        prev_agg = copy.deepcopy(self.last_ui_cmds)
        aggregate = self._on_command_update_common(aggregate)

        # call all subscribed to cmds updates
        for c in self._cmds_subscriptions:
            log.debug(f"Invoking command subscription: {c}")
            await call_maybe_async(c)

        # work out command diff and call individual commands
        changed = {c: v for c, v in aggregate.items()}

        log.debug(f"Prev Agg ({self.last_ui_cmds_update}): {prev_agg}")
        log.debug(f"New/Current Agg: {aggregate}")
        # log.debug(f"Changed: {changed}")

        ## Iterate through all the commands that we have locally, and call the callback if it exists
        for command_name, command in self._interactions.items():
            if command_name in changed:
                new_value = changed[command_name]
            else:
                new_value = None
                if hasattr(command, "default") and command.default is not None:
                    new_value = command.default

            if not command._is_new_value(new_value):
                continue

            await command._handle_new_value_async(new_value)

            for pattern, callback in self._command_callbacks:
                if pattern.match(command_name):
                    await call_maybe_async(callback, command, new_value)

    def _set_new_ui_cmds(self, payload: dict[str, Any]):
        if not payload:
            log.info("Received empty UI commands payload.")
            payload = {}

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                log.error(f"Failed to decode UI commands: {payload}")
                payload = {}

        try:
            payload = payload["cmds"]
        except KeyError:
            pass

        self.last_ui_cmds = copy.deepcopy(payload)
        self.last_ui_cmds_update = time.time()
        return payload

    def _set_new_ui_state(self, payload: dict[str, Any]):
        if not isinstance(payload, dict):
            payload = {}

        try:
            payload = payload["state"]
        except KeyError:
            pass

        try:
            payload = payload["children"][self.app_key]
        except KeyError:
            payload = {}

        self.last_ui_state = payload
        self.last_ui_state_update = time.time()

        ## TODO: Implement this ????
        # if self._base_container is not None:
        #     self._base_container.from_dict(payload)

        ## Iterate through the payload and update anything that needs updating
        # define a function to recursively trawl through each element of the last ui state and allow the element to update itself
        def update_elements_from_ui_state(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    element = self.get_element(k)
                    if element is not None:
                        element.recv_ui_state_update(v)
                    else:
                        update_elements_from_ui_state(v)

        update_elements_from_ui_state(payload)

    def get_full_interaction_key(self, name: str) -> str:
        # Get the complete name of the key for the interaction
        if self.app_key in name:
            return name
        return f"{self.app_key}_{name.strip()}"

    def _transform_interaction_name(self, name):
        # inject the app key (unique) into the interaction name
        # so we don't have namespace collisions between apps.
        if self.app_key in name:
            return name
        return f"{self.app_key}_{name.strip()}"

    def _add_interaction(self, interaction: Interaction):
        # inject the app key (unique) into the interaction name
        # so we don't have namespace collisions between apps.
        name = self._transform_interaction_name(interaction.name)
        interaction.name = name

        if not NAME_VALIDATOR.match(name):
            raise RuntimeError(
                f"Invalid name '{name}' for interaction '{interaction}'. "
                f"Valid characters include letters, numbers, and underscores."
            )

        if name in self._interactions:
            ## If the interaction already exists, we should preserve the current value if it exists
            if (
                hasattr(self._interactions[name], "_current_value")
                and self._interactions[name]._current_value is not NotSet
            ):
                interaction.current_value = self._interactions[name]._current_value

        self._interactions[name] = interaction
        interaction._manager = self

    def _remove_interaction(self, interaction_name: str) -> None:
        try:
            del self._interactions[interaction_name]
        except KeyError:
            return

    def add_interaction(self, interaction: InteractionT):
        if not isinstance(interaction, Interaction) and hasattr(
            interaction, "_ui_type"
        ):
            interaction = self._register_interaction(interaction, interaction.__self__)

        self._add_interaction(interaction)
        self._base_container.add_children(interaction)

    @staticmethod
    def _register_interaction(func, parent) -> InteractionT:
        item = func._ui_type(**func._ui_kwargs)
        item.callback = func

        try:
            setattr(parent, func.__name__, item)
        except AttributeError:
            pass  # maybe they've initialised the function w/o a class

        return item

    def register_interactions(self, obj_to_search):
        for name, func in inspect.getmembers(
            obj_to_search,
            predicate=lambda f: inspect.ismethod(f) and hasattr(f, "_ui_type"),
        ):
            self._register_interaction(func, obj_to_search)

    def register_callbacks(self, obj_to_search):
        for name, func in inspect.getmembers(
            obj_to_search,
            predicate=lambda f: inspect.ismethod(f) and hasattr(f, "_is_ui_callback"),
        ):
            if isinstance(func._ui_callback_pattern, str):
                p = func._ui_callback_pattern
                if func._is_ui_global_interaction:
                    pattern = re.compile(p)
                else:
                    pattern = re.compile(self._transform_interaction_name(p))

            elif isinstance(func._ui_callback_pattern, re.Pattern):
                pattern = func._ui_callback_pattern
                if func._is_ui_global_interaction is False:
                    pattern = re.compile(
                        self._transform_interaction_name(pattern.pattern)
                    )

            else:
                raise ValueError(
                    "Invalid pattern type for UI callback. Must be a string or re.Pattern."
                )

            log.info(f"Registering UI callback ({func}) with pattern {pattern.pattern}")
            self._command_callbacks.append((pattern, func))

    def get_interaction(self, name: str) -> Optional[Interaction]:
        try:
            return self._interactions[self._transform_interaction_name(name)]
        except KeyError:
            return None

    def update_interaction(self, name: str, updated: Interaction) -> bool:
        name = self._transform_interaction_name(name)
        if name not in self._interactions:
            return False

        self._interactions[name] = updated
        return True

    add_command = add_interaction
    get_command = get_interaction

    def coerce_command(
        self, command_name: str, value: Any, critical: bool = False
    ) -> None:
        command = self.get_command(command_name)
        if command is None:
            log.info(f"Tried to coerce command {command_name} that doesn't exist.")
            return

        command.coerce(value, critical=critical)

    def get_element(self, element_name: str) -> Optional[ElementT]:
        return self._base_container.get_element(element_name)

    def get_from_ui_state(self, element_name: str) -> Optional[dict]:
        return find_object_with_key(self.last_ui_state, element_name)

    def update_variable(
        self, variable_name: str, value: Any, critical: bool = False
    ) -> bool:
        element = self._base_container.get_element(variable_name)
        if not (element and isinstance(element, Variable)):
            log.info(
                f"PyDoover: Tried to update variable '{variable_name}' that doesn't exist."
            )
            return False

        if critical is True and element.current_value != value:
            self._has_critical_interaction_pending = True

        element.current_value = value
        return True

    def add_cmds_update_subscription(self, callback):
        # fixme: create alias or something
        self._cmds_subscriptions.append(callback)

    def get_all_interactions(self) -> list[Interaction]:
        return list(self._interactions.values())

    def get_all_interaction_names(self) -> list[str]:
        return list(self._interactions.keys())

    def get_all_variables(self) -> list[Variable]:
        if self._base_container is None:
            return []
        return self._base_container.get_all_elements(type_filter=Variable)

    get_available_commands = get_all_interaction_names

    def record_critical_value(self, name, value):
        log.warning(
            "this function is deprecated. use the critical=True parameter of another appropriate function."
        )
        if self._critical_values.get(name) == value:
            return

        self._critical_values[name] = value
        self._has_critical_interaction_pending = True
        # self._has_critical_ui_state_pending = True

    def _assess_pending_log_requests(self):
        ## Iterate through all variables and check if they have a pending log request
        log_requested = False
        for variable in self.get_all_variables():
            if variable.has_pending_log_request():
                log.debug(f"Variable {variable.name} has a pending log request")
                variable.clear_log_request()
                log_requested = True
        return log_requested

    def _get_max_age(self, force_update: bool = False) -> tuple[bool, int]:
        period = (
            self.min_observed_update_period
            if self.is_being_observed()
            else self.min_ui_update_period
        )

        if force_update:
            return True, 1

        if self._has_critical_interaction_pending:
            return True, 1
        if self._last_pushed_time is None or self._last_push_and_log_time is None:
            return True, 1

        since_last_push_and_log = time.time() - self._last_push_and_log_time
        if since_last_push_and_log > self.min_ui_update_period:
            return True, period

        return False, period

    @maybe_async()
    def handle_comms(self, force_log: bool = False):
        log_requested = self._assess_pending_log_requests()
        force_log, max_age = self._get_max_age(force_log or log_requested)
        self.push(force_log, max_age)

    async def handle_comms_async(self, force_log: bool = False):
        log_requested = self._assess_pending_log_requests()
        force_log, max_age = self._get_max_age(force_log or log_requested)
        await self.push_async(force_log, max_age)

    @maybe_async()
    def send_notification(self, message: str, record_activity: bool = True):
        self.publish_to_channel(
            "significantEvent",
            {
                "notification_msg": message,
            },
            record_log=True,
            max_age=1,
        )
        if record_activity:
            self.record_activity(message)

    async def send_notification_async(self, message: str, record_activity: bool = True):
        await self._publish_to_channel_async(
            "significantEvent",
            {
                "notification_msg": message,
            },
            record_log=True,
            max_age=1,
        )
        if record_activity:
            await self.record_activity_async(message)

    async def record_activity_async(self, message: str):
        await self._publish_to_channel_async(
            "activity_log",
            {
                "action_string": message,
            },
            record_log=True,
        )

    def publish_to_channel(
        self,
        channel_name: str,
        data: dict[str, Any],
        record_log: bool = True,
        max_age: int = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ):
        return self._publish_to_channel(
            channel_name,
            data,
            record_log=record_log,
            timestamp=timestamp,
            max_age=max_age,
            **kwargs,
        )

    def _publish_to_channel(
        self,
        channel_name: str,
        data: dict[str, Any],
        record_log: bool = True,
        timestamp: Optional[datetime] = None,
        max_age: int = None,
        **kwargs,
    ):
        # this purely exists to provide cross-compatibility between clients (hence private method).
        if isinstance(self.client, Client):
            channel = self.client.get_channel_named(channel_name, self.agent_id)
            return channel.publish(
                data, save_log=record_log, timestamp=timestamp, **kwargs
            )
        else:
            # fixme: allow for timestamp in DDA message publishing...
            return self.client.publish_to_channel(
                channel_name, data, record_log=record_log, max_age=max_age
            )

    async def _publish_to_channel_async(
        self,
        channel_name: str,
        data: dict[str, Any],
        record_log: bool = True,
        timestamp: Optional[datetime] = None,
        max_age: int = None,
        **kwargs,
    ):
        if isinstance(self.client, Client):
            # in theory this works but lets just discourage this behaviour...
            raise RuntimeError("Cannot push async with a Client object")

        return await self.client.publish_to_channel_async(
            channel_name, data, record_log=record_log, max_age=max_age
        )

    @maybe_async()
    def pull(self):
        print("pulling...")
        if isinstance(self.client, Client):
            ui_cmds = self.client.get_channel_named("ui_cmds", self.agent_id)
            ui_state = self.client.get_channel_named("ui_state", self.agent_id)

            ui_cmds_agg = ui_cmds.fetch_aggregate()
            ui_state_agg = ui_state.fetch_aggregate()
        else:
            ui_cmds_agg = self.client.get_channel_aggregate("ui_cmds")
            ui_state_agg = self.client.get_channel_aggregate("ui_state")

        self._set_new_ui_state(ui_state_agg)

        # self._set_new_ui_cmds(ui_cmds_agg)
        try:
            ui_cmds_agg = ui_cmds_agg["cmds"]
        except Exception as e:
            log.warning(f"Failed to get UI commands: {e}")
            ui_cmds_agg = {}

        self.on_command_update(None, ui_cmds_agg)

    async def pull_async(self):
        if isinstance(self.client, Client):
            raise RuntimeError("Cannot pull async with a Client object")

        ui_cmds_agg = await self.client.get_channel_aggregate_async("ui_cmds")
        ui_state_agg = await self.client.get_channel_aggregate_async("ui_state")
        self._set_new_ui_state(ui_state_agg)
        # self._set_new_ui_cmds(ui_cmds_agg)
        await self.on_command_update_async(None, ui_cmds_agg)

    def _check_dda_ready(self):
        if not self._is_conn_ready():
            log.warning("Attempted to push config without ready connection client.")
            return False
        elif not self.client.get_has_dda_been_online():
            # for a persistent connection, don't push if we haven't first pulled last data
            # HTTP-based connections will do a pull before pushing so that is fine.
            log.warning("Attempted to push config without DDA being online.")
            return False
        elif self.last_ui_state_update is None:
            log.warning("Waiting for UI state update to be pulled before pushing...")
            return False
        elif self.last_ui_cmds_update is None:
            log.warning("Waiting for UI commands to be pulled before pushing...")
            return False
        return True

    def _wrap_ui_state(
        self, data: dict[str, Any] | None, clear: bool = False
    ) -> dict[str, Any]:
        if clear is False and not data:
            data = {}

        return {"state": {"children": {self.app_key: data}}}

    @maybe_async()
    def push(
        self,
        record_log: bool = True,
        max_age: Optional[int] = None,
        should_remove: bool = True,
        timestamp: Optional[datetime] = None,
        even_if_empty: bool = False,
        only_channels: Optional[list] = None,
        publish_fields: Optional[list] = None,
    ) -> bool:
        publish_fields = publish_fields or []

        # self.check_dda()
        if self._has_persistent_connection:
            if not self._check_dda_ready():
                return False
        else:
            self.pull()  # do a pull before HTTP client pushes anything...

        print("pushing sync...")

        commands_update = self._get_commands_update(publish_fields=publish_fields)
        if commands_update is not None and (
            only_channels is None or "ui_cmds" in only_channels
        ):
            self._publish_to_channel(
                "ui_cmds",
                {"cmds": commands_update},
                timestamp=timestamp,
                max_age=1,
                record_log=True,
            )

        ui_state_update = self._get_ui_state_update(
            should_remove=should_remove, retain_fields=publish_fields
        )
        if even_if_empty or (
            ui_state_update is not None
            and (only_channels is None or "ui_state" in only_channels)
        ):
            self._publish_to_channel(
                "ui_state",
                ui_state_update or {},
                record_log=record_log,
                timestamp=timestamp,
                max_age=max_age,
            )
        else:
            print("not pushing empty ui state")

        self._last_pushed_time = time.time()
        if record_log:
            self._last_push_and_log_time = time.time()

        self._has_critical_interaction_pending = False
        return True

    async def push_async(
        self,
        record_log: bool = True,
        max_age: Optional[int] = None,
        should_remove: bool = True,
        timestamp: Optional[datetime] = None,
        even_if_empty: bool = False,
        only_channels: Optional[list] = None,
        publish_fields: Optional[list] = None,
    ) -> bool:
        publish_fields = publish_fields or []

        # self.check_dda()
        if self._has_persistent_connection:
            if not self._check_dda_ready():
                return False
        else:
            self.pull()  # do a pull before HTTP client pushes anything...

        commands_update = self._get_commands_update(publish_fields=publish_fields)
        if commands_update is not None and (
            only_channels is None or "ui_cmds" in only_channels
        ):
            log.debug("Pushing UI commands")
            await self._publish_to_channel_async(
                "ui_cmds",
                {"cmds": commands_update},
                timestamp=timestamp,
                max_age=1,
                record_log=True,
            )

        ui_state_update = self._get_ui_state_update(
            should_remove=should_remove, retain_fields=publish_fields
        )
        if even_if_empty or (
            ui_state_update is not None
            and (only_channels is None or "ui_state" in only_channels)
        ):
            log.debug("Pushing UI state")
            await self._publish_to_channel_async(
                "ui_state",
                self._wrap_ui_state(ui_state_update),
                record_log=record_log,
                timestamp=timestamp,
                max_age=max_age,
            )

        self._last_pushed_time = time.time()
        if record_log:
            self._last_push_and_log_time = time.time()

        self._has_critical_interaction_pending = False
        return True

    @maybe_async()
    def clear_ui(self):
        # this could be dangerous...
        log.info("Clearing UI")
        self._publish_to_channel(
            "ui_state",
            self._wrap_ui_state(None, clear=True),
            max_age=-1,
            record_log=False,
        )

    async def clear_ui_async(self):
        log.info("Clearing UI")
        # max-age=-1 to force an update right now. otherwise, first update will remove effect of "clearing" data.
        await self._publish_to_channel_async(
            "ui_state", self._wrap_ui_state(None, clear=True), max_age=-1
        )

    def _get_commands_update(
        self,
        publish_fields: list | None = None,
        only_local_changes: bool = True,
    ) -> dict[str, Any] | None:
        if publish_fields is None:
            publish_fields = []

        cloud_commands = copy.deepcopy(self.last_ui_cmds)
        local_commands = {
            k: v._json_safe_current_value() for k, v in self._interactions.items()
        }

        # don't include commands that are the same as the cloud, and values that aren't set
        # don't override other apps' commands if we haven't changed the value.
        result = {
            name: value
            for name, value in local_commands.items()
            if (
                cloud_commands.get(name) != value
                and value != NotSet
                and name in self._changed_interactions
                if only_local_changes
                else True
            )
            or name in publish_fields
        }

        self._changed_interactions.clear()

        # don't clean up commands that exist upstream but not locally for now.
        result.update(
            {c: None for c in cloud_commands.keys() if c not in local_commands}
        )

        log.debug("Last Commands: " + str(cloud_commands))
        log.debug("New Commands: " + str(local_commands))
        log.debug("Commands Update: " + str(result))

        if len(result) == 0:
            return None
        return result

    def _get_ui_state_update(
        self, should_remove: bool = True, retain_fields: list = list
    ) -> Optional[dict[str, Any]]:
        cloud_state = self.last_ui_state or {}
        # this recursively evaluates and finds the diff on all children, rather than trying to do the diff here
        result = self._base_container.get_diff(
            cloud_state, remove=should_remove, retain_fields=retain_fields
        )

        log.debug("Last UI State: " + str(cloud_state))
        log.debug("New UI State: " + str(self._base_container.to_dict()))
        log.debug("UI State Update: " + str(result))

        if not result or len(result) == 0:
            return None

        return result

    def _maybe_add_interaction_from_elems(
        self, *elements: Union[Element, Container]
    ) -> list[Element]:
        to_return = []
        for element in elements:
            # this is a bit hacky, but it's to stop passing in an unregistered interaction (ie. created with a decorator
            # outside of a submodule and hasn't been registered yet),
            # instead we'll silently register it and proceed as-is
            if not isinstance(element, Interaction) and hasattr(element, "_ui_type"):
                element = self._register_interaction(element, element.__self__)

            if isinstance(element, Container):
                self._maybe_add_interaction_from_elems(*element.children)
            elif isinstance(element, Interaction):
                self._add_interaction(element)
            to_return.append(element)

        return to_return

    def add_children(self, *children: Element) -> None:
        if len(children) == 1 and isinstance(children[0], list):
            # for backwards compatibility, this used to accept a single list of children
            children = children[0]

        updated = self._maybe_add_interaction_from_elems(*children)
        self._base_container.add_children(*updated)

    def remove_children(self, *children: Element) -> None:
        if len(children) == 1 and isinstance(children[0], list):
            # for backwards compatibility, this used to accept a single list of children
            children = children[0]

        for elem in children:
            if not isinstance(elem, Element):
                # sometimes an unregistered function can end up here and break things...
                continue

            if elem == self._base_container:
                raise RuntimeError("You can't remove the base container!")

            # this should never be None, but in case some numpty does something weird...
            if getattr(elem, "parent", None):
                elem.parent.remove_children(elem)

            ## Remove the element
            self._base_container.remove_children(elem)
            self._remove_interaction(elem.name)

    def set_children(self, children: list[Element]) -> None:
        updated = self._maybe_add_interaction_from_elems(*children)
        self._base_container.set_children(updated)
        # self._maybe_add_interaction_from_elems(*children)
        # self._base_container.set_children(children)

        # self._base_container.add_children( self.cameras )
        # if len(self.cameras) > 0:
        #     self._base_container.add_children( [ doover_ui_hidden_value(name="last_cam_snapshot") ] )

    def set_status_icon(self, icon_type: str, critical: bool = False):
        if icon_type == self._base_container.status_icon:
            return
        elif critical is True:
            # self._has_critical_ui_state_pending = True
            self._has_critical_interaction_pending = (
                True  # fixme: work out if we ever need this in element setting
            )

        self._base_container.status_icon = icon_type

    def set_display_name(self, name: str, critical: bool = False):
        if name == self._base_container.display_name:
            return
        elif critical is True:
            self._has_critical_interaction_pending = True

        self._base_container.display_name = name

    def set_variant(self, variant: ApplicationVariant) -> None:
        if variant not in (ApplicationVariant.submodule, ApplicationVariant.stacked):
            raise ValueError("Variant must be one of 'stacked', 'submodule'")

        self._base_container.variant = str(variant)

    def set_position(self, position: int):
        self._base_container.position = position
