import base64
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from typing import Any

from ..rpc import RPCManager
from ..tags import Tags
from ..tags.manager import TagsManagerProcessor

from ..models import (
    ManualInvokeEvent,
    MessageCreateEvent,
    Channel,
    DeploymentEvent,
    ScheduleEvent,
    IngestionEndpointEvent,
    ConnectionConfig,
    AggregateUpdateEvent,
    ConnectionDetermination,
    ConnectionStatus,
    Message,
    Notification,
    NotificationSeverity,
    SubscriptionInfo,
    DooverConnectionStatus,
)
from .config import ProcessorConfig
from .data_client import ProcessorDataClient
from ._logging import apply_log_levels, update_context
from ..ui import UI, UICommandsManager
from ..config import Schema


log = logging.getLogger(__name__)


DEFAULT_DATA_ENDPOINT = "https://data.doover.com/api"
DEFAULT_OFFLINE_AFTER = 60 * 60  # 1 hour


class SkipReason(StrEnum):
    no_handler = "no_handler"
    pre_hook_filter = "pre_hook_filter"
    tag_values_self_loop = "tag_values_self_loop"
    post_setup_filter = "post_setup_filter"


class ProcessorSkipped(Exception):
    """Raised inside ``_dispatch_invocation`` to signal a deliberate no-op.

    The :class:`SkipReason` is recorded in the invocation summary's
    ``skip_reason`` field. ``StrEnum`` means it serialises as its string
    value when the body is JSON-encoded.
    """

    def __init__(self, reason: SkipReason):
        super().__init__(reason.value)
        self.reason = reason


class Application:
    config_cls: type[Schema] = Schema
    ui_cls: type[UI] = UI
    tags_cls: type[Tags] = Tags

    def __init__(self):
        self.config = self.config_cls()

        self.received_deployment_config = None
        self.proc_config = ProcessorConfig()
        self.proc_config.load_data({})

        self._api_endpoint = (
            os.environ.get("DOOVER_DATA_ENDPOINT") or DEFAULT_DATA_ENDPOINT
        )

        self.api = ProcessorDataClient(self._api_endpoint)

        # set per-task
        self.agent_id: int | None = None
        self.app_key: str | None = None
        self.app_id: str | None = None
        self.organisation_id: int | str | None = None
        self.subscription_id: str | None = None
        self.schedule_id: str | None = None
        self.ingestion_id: str | None = None
        self.event_type: str | None = None
        self.lambda_request_id: str | None = None
        self.lambda_function_name: str | None = None
        self.lambda_function_version: str | None = None
        self._initial_token: str | None = None

        self.tag_manager: TagsManagerProcessor | None = None
        self._connection_config: dict[str, Any] | None = None

        self._record_tag_update: bool = True
        self._update_external_tags: bool = False
        self._clear_ui_schema = True

    async def _setup(self, initial_payload: dict[str, Any]):
        # this is ok to setup because it doesn't store any state
        await self.api.setup()

        # this is essentially an oauth2 "upgrade" request with some more niceties.
        # we give it a minimal token provisioned from doover data, along with our subscription (uuid) ID
        # and we get back a full token, agent id, app key and a few common channels - ui state, ui cmds,
        # tag values and deployment config.
        if self._initial_token is None:
            raise RuntimeError("Initial token has not been set.")
        self.api.set_token(self._initial_token)

        # Always prioritise the upgrade payload, otherwise get it from the normal method
        if initial_payload["d"].get("upgrade", None) is not None:
            info = SubscriptionInfo.from_dict(initial_payload["d"]["upgrade"])
        else:
            if self.subscription_id:
                info = await self.api.fetch_subscription_info(self.subscription_id)
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

        self.app_key = self.api.app_key = info.app_key
        self.tag_manager = TagsManagerProcessor(
            self.app_key,
            self.api,
            self.agent_id,
            info.tag_values,
            record_tag_update=self._record_tag_update,
        )
        self.tags = self.tags_cls(self.app_key, self.tag_manager, self.config)
        self.ui = self.ui_cls(self.config, self.tags, self.app_key)

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

        self.ui_manager = UICommandsManager(self.api)
        self.rpc = RPCManager(self.api, self.app_key)

        self.ui_manager.register_handlers(self)
        self.rpc.register_handlers(self)

        if info.ui_cmds is not None:
            try:
                self.ui_manager.values = info.ui_cmds[self.app_key]
            except KeyError:
                log.debug("ui_cmds not set. Skipping.")

        if self.config is not None:
            # if there's no config defined this can legitimately be None in which case don't bother.
            self.config._inject_deployment_config(info.deployment_config)

        await self.tags.setup()
        await self.ui.setup()
        self.ui_manager._set_interactions(self.ui.get_interactions())

        # Store the deployment config for later use
        self.received_deployment_config = info.deployment_config
        self.display_name = self.received_deployment_config.get("APP_DISPLAY_NAME")
        self.app_id = self.received_deployment_config.get("APP_ID")
        self.proc_config = ProcessorConfig()
        self.proc_config.load_data(
            self.received_deployment_config.get("dv_proc_config")
        )

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
        """Invoked when the app is (re)deployed to an agent.

        The framework internally publishes the UI schema to ``ui_state`` on deployment
        (for non-static UIs), so normal ``on_message_create`` / ``on_aggregate_update``
        events do not re-post it. Override this to run any additional one-off setup
        you need to do on deployment (e.g. seeding channels, priming tags).

        You do **not** need to call ``super().on_deployment()``.
        """
        return NotImplemented

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
        started_at_ms = int(start_time * 1000)
        # Set early so the summary still has them if dispatch raises before
        # _dispatch_invocation gets a chance to populate the rest.
        self.subscription_id = subscription_id
        self.event_type = event.get("op")

        log.info("Initialising processor task")
        log.info(f"Started at {start_time}.")

        result = None
        status = "success"
        skip_reason: SkipReason | None = None
        error: dict[str, str] | None = None

        try:
            result = await self._dispatch_invocation(event, subscription_id)
        except ProcessorSkipped as e:
            status = "skipped"
            skip_reason = e.reason
        except Exception as e:
            log.error("Unhandled error in invocation", exc_info=e)
            status = "error"
            error = {"type": type(e).__name__, "message": str(e)}
        finally:
            end_time = time.time()
            log.info(
                f"Finished at {end_time}. Process took {end_time - start_time} seconds. result: {result}"
            )
            try:
                await self._publish_invocation_summary(
                    started_at_ms=started_at_ms,
                    duration_ms=int((end_time - start_time) * 1000),
                    status=status,
                    skip_reason=skip_reason,
                    error=error,
                )
            except Exception as e:
                log.error("Failed to publish invocation summary", exc_info=e)
            try:
                await self._close()
            except Exception as e:
                log.error("Error closing processor api client", exc_info=e)

        return result

    async def _dispatch_invocation(
        self, event: dict[str, Any], subscription_id: str | None
    ) -> Any:
        """Run the event-handling pipeline and return the handler's result.

        Raises :class:`ProcessorSkipped` when the invocation should be
        recorded as a deliberate no-op (filter rejection, no overridden
        handler, self-loop guard).
        """
        self.schedule_id = event["d"].get("schedule_id")
        self.ingestion_id = event["d"].get("ingestion_id")
        # org ID should be set in both schedules and subscriptions, but just in case it isn't...
        self.organisation_id = event["d"].get("organisation_id")

        # this is the initial token provided. For a subscription, it will be a temporary token.
        # For a schedule, it will be a long-lived token.
        # Both have permission to access the info endpoint, only.
        self._initial_token = event["token"]
        # this can be set during testing. during normal operation it's signed in the JWT.
        self.agent_id = event.get("agent_id", self.agent_id)

        func = None
        original_func = None
        payload = None
        match event["op"]:
            case "on_message_create":
                func = self.on_message_create
                payload = MessageCreateEvent.from_dict(event["d"])
                # prevent infinite loops
                self.api._invoking_channel_name = payload.channel.name
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

        is_deployment = event["op"] == "on_deployment"
        if func == original_func and not is_deployment:
            log.info(f"Skipping {func.__name__} event as no overridden handler found.")
            raise ProcessorSkipped(SkipReason.no_handler)

        self._payload = payload

        if not await self.pre_hook_filter(payload):
            log.info("Pre-hook filter rejected event.")
            raise ProcessorSkipped(SkipReason.pre_hook_filter)

        s = time.perf_counter()
        await self._setup(event)
        log.info(f"Setup took {time.perf_counter() - s} seconds.")

        # Mirror app_id into the log-record filter so logs from here on
        # carry it. Everything else summary-bound stays on ``self``.
        update_context(app_id=self.app_id)

        apply_log_levels(
            self.proc_config.log_level.value,
            {
                name: elem.value
                for name, elem in self.proc_config.log_overrides._elements.items()
            },
        )

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
            raise ProcessorSkipped(SkipReason.tag_values_self_loop)

        s = time.perf_counter()
        try:
            await self.setup()
        except Exception as e:
            log.error(f"Error attempting to setup processor: {e} ", exc_info=e)
        log.info(f"user Setup took {time.perf_counter() - s} seconds.")

        if not await self.post_setup_filter(payload):
            log.info("Post-setup filter rejected event.")
            raise ProcessorSkipped(SkipReason.post_setup_filter)

        if is_deployment and not self.ui.is_static:
            log.info("Publishing ui_state schema on deployment.")
            await self.publish_ui_schema(clear=True)

        try:
            await self.ui_manager._on_event(payload)
        except Exception as e:
            log.error(f"Error handling UI event: {e} ", exc_info=e)

        try:
            await self.rpc._on_event(payload)
        except Exception as e:
            log.error(f"Error handling RPC event: {e} ", exc_info=e)

        result = None
        if func is None or payload is None:
            log.error(f"Unknown event type: {event['op']}")
        elif func == original_func:
            log.info(f"No overridden {func.__name__} handler; skipping user handler.")
        else:
            try:
                s = time.perf_counter()
                result = await func(payload)
                log.info(f"Processing event took {time.perf_counter() - s} seconds.")
            except Exception as e:
                log.error(f"Error attempting to process event: {e} ", exc_info=e)

        if self.tag_manager is None:
            raise RuntimeError("Tag manager has not been initialized.")
        await self.tag_manager.commit_tags()

        try:
            await self.close()
        except Exception as e:
            log.error(f"Error attempting to close processor: {e} ", exc_info=e)

        return result, None

    async def _publish_invocation_summary(
        self,
        *,
        started_at_ms: int,
        duration_ms: int,
        status: str,
        skip_reason: SkipReason | None,
        error: dict[str, str] | None,
    ) -> None:
        targets = self.proc_config.inv_targets.value
        if not targets:
            return

        body = {
            "app_key": self.app_key,
            "app_id": self.app_id,
            # Doover IDs are 64-bit; JS truncates above 2^53.
            "agent_id": str(self.agent_id) if self.agent_id is not None else None,
            "event_type": self.event_type,
            "subscription_id": self.subscription_id,
            "schedule_id": self.schedule_id,
            "ingestion_id": self.ingestion_id,
            "started_at": started_at_ms,
            "duration_ms": duration_ms,
            "status": status,
            "skip_reason": skip_reason,
            "error": error,
            "requestId": self.lambda_request_id,
            "function_name": self.lambda_function_name,
            "function_version": self.lambda_function_version,
        }

        for target in targets:
            agent_id = target.agent_id.value
            channel = target.channel.value.replace("$app_id", self.app_id)
            try:
                await self.api.create_message(channel, body, agent_id=agent_id)
            except Exception as e:
                log.error(
                    "Failed to post invocation summary to %s/%s",
                    agent_id,
                    channel,
                    exc_info=e,
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
        if self.agent_id is None:
            raise RuntimeError("Agent ID has not been initialized.")
        return await self.api.fetch_channel(channel_name)

    def get_tag(self, key: str, default: Any = None):
        if self.tag_manager is None:
            raise RuntimeError("Tag manager has not been initialized.")
        return self.tag_manager.get_tag(key, default)

    async def set_tag(self, key: str, value: Any, log: bool = False):
        if self.tag_manager is None:
            raise RuntimeError("Tag manager has not been initialized.")
        await self.tag_manager.set_tag(key, value, log=log)

    async def send_notification(
        self,
        message: str | Notification,
        *,
        title: str | None = None,
        severity: NotificationSeverity | int | None = None,
        topic: str | None = None,
        agent_id: int | None = None,
    ) -> Message:
        """Send a notification via the ``notifications`` channel.

        The Doover cloud fans this out to any notification subscriptions
        (email / SMS / web push / http) that match the given severity and
        topic.

        Parameters
        ----------
        message : str | Notification
            Either the notification body, or a fully-constructed
            :class:`~pydoover.models.Notification` (in which case ``title``,
            ``severity`` and ``topic`` are ignored).
        title : str, optional
            Optional title / headline for the notification.
        severity : NotificationSeverity | int, optional
            Severity level. Subscribers only receive notifications at or
            above their subscription severity.
        topic : str, optional
            Optional topic used to match subscription ``topic_filter``
            entries.
        agent_id : int, optional
            Override the agent to send the notification on behalf of.
            Defaults to the processor's current agent.

        Returns
        -------
        Message
            The created channel message.
        """
        if isinstance(message, Notification):
            notification = message
        else:
            notification = Notification(
                message=message, title=title, severity=severity, topic=topic
            )
        return await self.api.create_message(
            Notification.NOTIFICATIONS_CHANNEL,
            notification.to_dict(),
            agent_id=agent_id,
        )

    async def publish_ui_schema(self, clear: bool = True):
        schema = self.ui.to_schema()
        if clear:
            await self.api.update_channel_aggregate(
                "ui_state",
                {"state": {"children": {self.app_key: schema}}},
                replace_keys=[f"state.children.{self.app_key}"],
            )
        else:
            await self.api.update_channel_aggregate(
                "ui_state",
                {"state": {"children": {self.app_key: schema}}},
            )

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
            offline_after = (self._connection_config or {}).get(
                "offline_after", DEFAULT_OFFLINE_AFTER
            )

        if datetime.now(tz=timezone.utc) - online_at > timedelta(seconds=offline_after):
            determination = ConnectionDetermination.offline
        else:
            determination = ConnectionDetermination.online

        if self.agent_id is None:
            raise RuntimeError("Agent ID has not been initialized.")
        await self.api.ping_connection_at(
            online_at,
            connection_status=connection_status,
            determination=determination,
            user_agent=f"pydoover-processor,app_key={self.app_key}",
            agent_id=self.agent_id,
        )
