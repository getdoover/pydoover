import asyncio
import base64 as base64_module
import copy
import logging
import re
import sys
import json

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...utils.snowflake import generate_snowflake_id_at

import grpc

from ...models.data._proto_json import decode_data_fields, encode_data_fields
from ...models.generated.device_agent import device_agent_pb2, device_agent_pb2_grpc
from ...models.data import (
    Aggregate,
    AggregateUpdateEvent,
    ChannelList,
    ChannelListing,
    ChannelSyncEvent,
    EventSubscription,
    File,
    Message,
    MessageCreateEvent,
    MessageUpdateEvent,
    OneShotMessage,
    TurnCredential,
    Attachment,
    WireFormat,
)
from ..grpc_interface import GRPCInterface
from ...models.data.exceptions import DooverAPIError, NotFoundError
from ...cli.decorators import command as cli_command

log = logging.getLogger(__name__)

_VALID_KEY_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_SCALAR_TYPES = (bool, int, float, str, type(None))


def validate_payload(data, _path=""):
    """Validate that a payload is compatible with doover channel data.

    The top level must be a dict. Keys must be strings containing only
    alphanumeric characters, hyphens, and underscores. Values may be
    dicts, lists, strings, numbers, booleans, or None.

    Raises ValueError with a clear path to the offending key/value.
    """
    if not _path and not isinstance(data, dict):
        raise ValueError(f"Payload must be a dict, got {type(data).__name__}")

    if isinstance(data, dict):
        for key, value in data.items():
            key_path = f"{_path}.{key}" if _path else key
            if not isinstance(key, str):
                raise ValueError(
                    f"Keys must be strings, "
                    f"got {type(key).__name__} ({key!r}) at '{_path or 'root'}'"
                )
            if not _VALID_KEY_RE.match(key):
                raise ValueError(
                    f"Key '{key}' at '{_path or 'root'}' contains invalid characters — "
                    f"only a-z, A-Z, 0-9, hyphens and underscores are allowed"
                )
            validate_payload(value, key_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            validate_payload(item, f"{_path}[{i}]")
    elif not isinstance(data, _SCALAR_TYPES):
        raise ValueError(
            f"Unsupported type {type(data).__name__} at '{_path}' — "
            f"allowed types: dict, list, str, int, float, bool, None"
        )


class DeviceAgentInterface(GRPCInterface):
    """Interface for interacting with the Device Agent gRPC service.

    Attributes
    ----------
    dda_timeout : int
        Timeout for requests to the Device Agent service.
    max_connection_attempts : int
        Maximum number of attempts to connect to the Device Agent service.
    time_between_connection_attempts : int
        Time to wait between connection attempts to the Device Agent service.

    is_dda_available : bool
        Whether the Device Agent service is available. This is set to True once a successful request has been made to the service.
    is_dda_online: bool
        Whether the Device Agent service is currently online.
    has_dda_been_online: bool
        Whether the Device Agent service has been online at least once since the interface was created.

    last_channel_message_ts : dict
        A dictionary that stores the last time a message was received from each channel.
    """

    stub = device_agent_pb2_grpc.deviceAgentStub

    def __init__(
        self,
        app_key: str,
        dda_uri: str = "127.0.0.1:50051",
        dda_timeout: int = 7,
        max_conn_attempts: int = 5,
        time_between_connection_attempts: int = 10,
        service_name: str = "doover.DeviceAgent",
    ):
        super().__init__(app_key, dda_uri, service_name, dda_timeout)

        self.dda_timeout = dda_timeout
        self.max_connection_attempts = max_conn_attempts
        self.time_between_connection_attempts = time_between_connection_attempts

        self.is_dda_available = False
        self.is_dda_online = False
        self.has_dda_been_online = False
        self.agent_id = None

        # Single event stream per channel, distributing to all registered callbacks
        self._event_callbacks: dict[str, list[tuple[Callable, EventSubscription]]] = {}
        self._stream_tasks: dict[str, asyncio.Task] = {}

        # Aggregate state tracking
        self._synced_channels: dict[str, bool] = {}
        self._aggregates: dict[str, Aggregate] = {}
        self.last_channel_message_ts: dict[str, datetime] = {}

    @staticmethod
    def has_persistent_connection():
        """For the Device Agent, this always returns `True`. This method exists to provide interoperability with the API client."""
        return True

    @cli_command()
    def get_is_dda_available(self):
        return self.is_dda_available

    @cli_command()
    def get_is_dda_online(self):
        return self.is_dda_online

    @cli_command()
    def get_has_dda_been_online(self):
        return self.has_dda_been_online

    async def wait_until_healthy(self, timeout: float = 10):
        start_time = datetime.now(tz=timezone.utc)
        backoff = 1
        while True:
            try:
                healthy = await self.health_check()
            except Exception as e:
                log.error(f"Failed to get DDA comms: {e}")
                healthy = False

            if healthy:
                log.info("DDA is available.")
                return True

            if (datetime.now(tz=timezone.utc) - start_time).seconds > timeout:
                log.warning(
                    f"Timed out waiting {timeout} seconds for DDA to become available"
                )
                return False

            log.info(f"DDA is not available. Retrying in {backoff} seconds...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 1)

    def _ensure_stream(
        self,
        channel_name: str,
        wire_format: WireFormat = WireFormat.json_only,
        replay_missed_messages: bool = True,
    ) -> None:
        """Ensure a single event stream is running for this channel."""
        if channel_name not in self._stream_tasks:
            self._stream_tasks[channel_name] = asyncio.create_task(
                self._run_channel_stream(
                    channel_name, wire_format, replay_missed_messages
                )
            )

    def add_event_callback(
        self,
        channel_name: str,
        callback: Callable,
        events: EventSubscription = EventSubscription.all,
        wire_format: WireFormat = WireFormat.json_only,
        replay_missed_messages: bool = True,
    ) -> None:
        """Register a callback for events on a channel.

        The callback receives a single event argument, one of
        ``MessageCreateEvent``, ``MessageUpdateEvent``, ``AggregateUpdateEvent``,
        or ``OneShotMessage``, filtered by the ``events`` parameter.

        The channel name is accessible via the event payload itself.

        Starts the event stream for the channel if not already running.

        Parameters
        ----------
        channel_name : str
            Name of channel to subscribe to.
        callback : Callable
            An async callback ``(event) -> None``.
        events : EventSubscription, optional
            Which event types to deliver. Defaults to ``EventSubscription.all``.
        wire_format : WireFormat, optional
            Delivery format requested from the device agent. Defaults to
            ``WireFormat.json_only`` (events are decoded from ``data_json``, so
            the agent can skip the protobuf ``Struct`` build). Only the first
            subscriber to a channel establishes the stream's format.
        replay_missed_messages : bool, optional
            Whether to receive messages the agent replays after a reconnect —
            ones created while it was offline. Defaults to ``True``. Pass
            ``False`` for live-only delivery, e.g. a control loop that should
            act on current state rather than re-run a backlog of stale
            commands. Like ``wire_format``, only the first subscriber to a
            channel establishes this.
        """
        entry = (callback, events)
        try:
            self._event_callbacks[channel_name].append(entry)
        except KeyError:
            self._event_callbacks[channel_name] = [entry]

        self._ensure_stream(channel_name, wire_format, replay_missed_messages)

    @staticmethod
    def _event_type_to_flag(event) -> EventSubscription | None:
        if isinstance(event, OneShotMessage):
            return EventSubscription.oneshot_message
        elif isinstance(event, MessageCreateEvent):
            return EventSubscription.message_create
        elif isinstance(event, MessageUpdateEvent):
            return EventSubscription.message_update
        elif isinstance(event, AggregateUpdateEvent):
            return EventSubscription.aggregate_update
        elif isinstance(event, ChannelSyncEvent):
            return EventSubscription.channel_sync
        return None

    async def _run_channel_stream(
        self,
        channel_name: str,
        wire_format: WireFormat = WireFormat.json_only,
        replay_missed_messages: bool = True,
    ):
        """Single event stream per channel. Seeds aggregate cache, then distributes events."""
        await self.wait_until_healthy()

        # Seed the aggregate cache, then fire ChannelSyncEvent so subscribers get the initial state.
        agg = None
        try:
            agg = await self.fetch_channel_aggregate(channel_name)
            self._aggregates[channel_name] = agg
        except NotFoundError:
            log.info(
                f"Channel '{channel_name}' not found, creating with empty aggregate"
            )
            try:
                agg = await self.update_channel_aggregate(channel_name, {})
            except Exception as e:
                log.error(f"Failed to create channel '{channel_name}': {e}")
            else:
                self._aggregates[channel_name] = agg
        except Exception as e:
            log.error(f"Failed to seed aggregate cache for '{channel_name}': {e}")

        self._synced_channels[channel_name] = True

        if agg is not None:
            sync_event = ChannelSyncEvent(aggregate=agg)
            for callback, events in self._event_callbacks.get(channel_name, []):
                if EventSubscription.channel_sync not in events:
                    continue
                try:
                    asyncio.create_task(callback(sync_event))
                except Exception as e:
                    log.error(
                        f"Error dispatching channel sync callback for {channel_name}: {e}",
                        exc_info=e,
                    )

        # Wrap the event loop in a retry loop so any uncaught exception from
        # stream_channel_events or the dispatch body does not silently kill the
        # subscription task. Without this, an unexpected error leaves the task
        # dead and _ensure_stream has no mechanism to restart it, causing
        # subscriptions to stop firing until the process restarts.
        while True:
            try:
                async for event in self.stream_channel_events(
                    channel_name, wire_format, replay_missed_messages
                ):
                    # Update internal aggregate state on AggregateUpdate
                    if isinstance(event, AggregateUpdateEvent):
                        self._aggregates[channel_name] = event.aggregate
                        self._synced_channels[channel_name] = True
                        self.last_channel_message_ts[channel_name] = datetime.now(
                            tz=timezone.utc
                        )

                    # Determine which flag this event corresponds to
                    event_flag = self._event_type_to_flag(event)

                    # Distribute to matching registered callbacks
                    for callback, events in self._event_callbacks.get(channel_name, []):
                        if event_flag is None or event_flag not in events:
                            continue
                        try:
                            asyncio.create_task(callback(event))
                        except Exception as e:
                            log.error(
                                f"Error dispatching event callback for {channel_name}: {e}",
                                exc_info=e,
                            )
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                log.exception(
                    f"Stream task for {channel_name} crashed, restarting: {e}"
                )
                await asyncio.sleep(1)
                continue

    async def stream_channel_events(
        self,
        channel_name: str,
        wire_format: WireFormat = WireFormat.json_only,
        replay_missed_messages: bool = True,
    ):
        backoff = 1
        while True:
            try:
                async with grpc.aio.insecure_channel(self.uri) as channel:
                    pl = device_agent_pb2.ChannelEventSubscriptionRequest(
                        channel_name=channel_name,
                        wire_format=int(wire_format),
                        replay_missed_messages=replay_missed_messages,
                    )
                    channel_stream = device_agent_pb2_grpc.deviceAgentStub(
                        channel
                    ).ChannelEventSubscription(pl)

                    backoff = 1  # reset on successful connection
                    while True:
                        try:
                            response: device_agent_pb2.ChannelEventSubscriptionResponse = await channel_stream.read()
                            log.debug(
                                f"Received event response from subscription request on {channel_name}: {str(response)[:120]}"
                            )
                            if not response.response_header.success:
                                raise RuntimeError(
                                    f"Failed to subscribe to channel {channel_name}: {response.response_header.response_message}"
                                )

                            match response.event_name:
                                case "MessageCreate":
                                    yield MessageCreateEvent.from_dict(
                                        decode_data_fields(response)
                                    )
                                case "MessageUpdate":
                                    yield MessageUpdateEvent.from_dict(
                                        decode_data_fields(response)
                                    )
                                case "AggregateUpdate":
                                    yield AggregateUpdateEvent.from_dict(
                                        decode_data_fields(response)
                                    )
                                case "OneShotMessage":
                                    yield OneShotMessage.from_dict(
                                        decode_data_fields(response)
                                    )

                        except StopAsyncIteration:
                            log.debug("Channel event stream ended.")
                            break
            except Exception as e:
                log.error(
                    f"Error in channel event stream for {channel_name}: {e}",
                    exc_info=e,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self.time_between_connection_attempts)

    def process_response(self, stub_call: str, response, *args, **kwargs):
        if response is not None:
            self.update_dda_status(response.response_header)
        return super().process_response(stub_call, response, *args, **kwargs)

    def update_dda_status(self, header):
        if header.success:
            self.is_dda_available = True
        else:
            self.is_dda_available = False

        if header.cloud_synced:
            self.is_dda_online = True
            if not self.has_dda_been_online:
                log.info("Device Agent is online")
            self.has_dda_been_online = True
        else:
            self.is_dda_online = False

    def is_channel_synced(self, channel_name):
        """Check if a channel is synced with DDA.

        During normal operation, this should always return `True` while DDA is active.

        It is only really useful for timing during the startup process.

        Parameters
        ----------
        channel_name : str
            Name of the channel to check.

        Returns
        -------
        bool
            True if the channel is synced, False otherwise.
        """
        if channel_name not in self._event_callbacks:
            return False
        if channel_name not in self._synced_channels:
            return False
        return self._synced_channels[channel_name]

    async def wait_for_channels_sync(
        self, channel_names: list[str], timeout: int = 5, inter_wait: float = 0.2
    ) -> bool:
        """Wait for all specified channels to be synced with DDA.

        This is invoked internally at startup to ensure that all channels are ready before proceeding with operations that depend on them.

        You shouldn't need to use this during normal operation.

        Parameters
        ----------
        channel_names : list[str]
            List of channel names to check for sync status.
        timeout : int
            Maximum time to wait for all channels to sync, in seconds.
        inter_wait : float
            Time to wait between checks, in seconds.

        Returns
        -------
        bool
            True if all channels are synced within the timeout, False otherwise.
        """
        start_time = datetime.now(tz=timezone.utc)
        while not all(
            [self.is_channel_synced(channel_name) for channel_name in channel_names]
        ):
            if (datetime.now(tz=timezone.utc) - start_time).seconds > timeout:
                return False
            await asyncio.sleep(inter_wait)
        return True

    @cli_command()
    async def list_channels(self, include_aggregate: bool = False) -> ChannelList:
        """List the agent's channels.

        The device agent answers from the cloud when it can reach it, and from
        the channels it tracks locally when it can't — see
        :attr:`ChannelList.from_cloud`, since a local answer covers only the
        channels this agent has touched and may be a subset.

        Examples
        --------
        >>> listing = await self.device_agent.list_channels()
        >>> [c.name for c in listing]
        ['ui_state', 'tag_values']

        Parameters
        ----------
        include_aggregate : bool, optional
            Populate each channel's ``aggregate``. Defaults to False, so a
            name-only listing doesn't pull every aggregate body over.

        Returns
        -------
        ChannelList
            The channels, and whether the cloud answered.

        Raises
        ------
        DooverAPIError
            If the request fails.
        """
        resp = await self.make_request(
            "ListChannels",
            device_agent_pb2.ListChannelsRequest(
                header=device_agent_pb2.RequestHeader(app_id=self.app_key),
                include_aggregate=include_aggregate,
            ),
        )
        return ChannelList.from_proto(resp)

    @cli_command()
    async def fetch_channel_aggregate(self, channel_name: str) -> Aggregate:
        """Fetch a channel's current aggregate payload.

        If the channel has been subscribed to via :meth:`add_event_callback`, the cached
        aggregate is returned. Otherwise, a gRPC call is made to fetch it.

        Examples
        --------
        >>> aggregate = await self.device_agent.fetch_channel_aggregate("my_channel")
        >>> print(aggregate.data)

        Parameters
        ----------
        channel_name : str
            Name of channel to get aggregate from.

        Returns
        -------
        Aggregate
            Aggregate from channel.

        Raises
        ------
        NotFoundError
            If the channel does not exist.
        DooverAPIError
            If the request fails.
        """
        if channel_name in self._aggregates:
            return copy.deepcopy(self._aggregates[channel_name])

        log.debug(f"Getting channel aggregate for {channel_name}")
        resp = await self.make_request(
            "GetAggregate",
            device_agent_pb2.GetAggregateRequest(channel_name=channel_name),
        )
        return Aggregate.from_proto(resp.aggregate)

    @cli_command()
    async def fetch_turn_token(
        self,
    ) -> TurnCredential:
        resp = await self.make_request(
            "GetTurnCredential",
            device_agent_pb2.TurnCredentialRequest(
                header=device_agent_pb2.RequestHeader(app_id=self.app_key)
            ),
        )
        return TurnCredential.from_proto(resp.turn_credential)

    @cli_command()
    async def fetch_message(
        self,
        channel_name: str,
        message_id: int,
    ) -> Message:
        resp = await self.make_request(
            "GetMessage",
            device_agent_pb2.GetMessageRequest(
                channel_name=channel_name,
                message_id=message_id,
            ),
        )
        return Message.from_proto(resp.message)

    @cli_command()
    async def list_messages(
        self,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        limit: int | None = None,
        field_names: list[str] | None = None,
    ) -> list[Message]:
        kwargs = {}
        if before is not None:
            kwargs["before"] = (
                before if isinstance(before, int) else generate_snowflake_id_at(before)
            )
        if after is not None:
            kwargs["after"] = (
                after if isinstance(after, int) else generate_snowflake_id_at(after)
            )
        if limit is not None:
            kwargs["limit"] = limit
        if field_names is not None:
            if isinstance(field_names, str):
                field_names = [f.strip() for f in field_names.split(",")]
            kwargs["field_names"] = field_names

        resp = await self.make_request(
            "GetMessages",
            device_agent_pb2.GetMessagesRequest(
                channel_name=channel_name,
                **kwargs,
            ),
        )
        return [Message.from_proto(m) for m in resp.messages]

    @cli_command()
    async def create_message(
        self,
        channel_name: str,
        data: dict[str, Any],
        files: list[File] = None,
        timestamp: datetime = None,
    ) -> int:
        validate_payload(data)

        files = files or []
        timestamp = (timestamp or datetime.now(tz=timezone.utc)).timestamp() * 1000
        req = device_agent_pb2.CreateMessageRequest(
            header=device_agent_pb2.RequestHeader(app_id=self.app_key),
            channel_name=channel_name,
            files=[file.to_proto() for file in files],
            timestamp=int(timestamp),
            **encode_data_fields(data),
        )
        resp = await self.make_request("CreateMessage", req)
        return resp.message_id

    @cli_command()
    async def send_oneshot_message(
        self, channel_name: str, data: dict[str, Any], timestamp: datetime | None = None
    ) -> bool:
        # Oneshot messages are fire-and-forget (e.g. live tags) — best-effort by
        # nature, with no retry or delivery guarantee. A DDA that's too old to accept
        # the request rejects it, so swallow transport/rejection errors and return
        # False rather than crashing the caller's loop. Local payload errors (e.g. a
        # bad ``data`` dict failing to encode) are caller bugs and still raise.
        req = device_agent_pb2.SendOneShotMessageRequest(
            header=device_agent_pb2.RequestHeader(app_id=self.app_key),
            channel_name=channel_name,
            **encode_data_fields(data),
        )
        if timestamp is not None:
            req.timestamp = int(timestamp.timestamp() * 1000)
        try:
            await self.make_request("SendOneShotMessage", req)
        except DooverAPIError as e:
            log.warning(
                "Oneshot message to '%s' dropped (device agent rejected or "
                "unreachable): %s",
                channel_name,
                e,
            )
            return False
        return True

    @cli_command()
    async def update_message(
        self,
        channel_name: str,
        message_id: int,
        data: dict[str, Any],
        files: list[File] = None,
        replace_data: bool = False,
        clear_attachments: bool = False,
    ) -> Message:
        validate_payload(data)

        files = files or []
        req = device_agent_pb2.UpdateMessageRequest(
            header=device_agent_pb2.RequestHeader(app_id=self.app_key),
            channel_name=channel_name,
            message_id=str(message_id),
            files=[file.to_proto() for file in files],
            clear_attachments=clear_attachments,
            replace_data=replace_data,
            **encode_data_fields(data),
        )
        resp = await self.make_request("UpdateMessage", req)
        return Message.from_proto(resp.message)

    @cli_command()
    async def update_channel_aggregate(
        self,
        channel_name: str,
        data: dict[str, Any],
        files: list[File] = None,
        clear_attachments: bool = False,
        replace_data: bool = False,
        max_age_secs: float = None,
        return_aggregate: bool = True,
        replace_keys: list[str] = None,
    ):
        validate_payload(data)

        files = files or []
        req = device_agent_pb2.UpdateAggregateRequest(
            channel_name=channel_name,
            files=[file.to_proto() for file in files],
            clear_attachments=clear_attachments,
            replace_data=replace_data,
            max_age_secs=max_age_secs,
            return_aggregate=return_aggregate,
            replace_keys=replace_keys or [],
            **encode_data_fields(data),
        )
        resp = await self.make_request("UpdateAggregate", req)
        if not return_aggregate:
            return None
        return Aggregate.from_proto(resp.aggregate)

    async def fetch_message_attachment(self, attachment: Attachment) -> File:
        req = device_agent_pb2.FetchAttachmentRequest(
            attachment=attachment.to_proto(),
        )
        resp = await self.make_request("FetchAttachment", req)
        return File.from_proto(resp.file)

    @cli_command(name="fetch_message_attachment")
    async def _cli_fetch_message_attachment(
        self,
        url: str,
        output: str | None = None,
        force: bool = False,
        base64: bool = False,
    ) -> dict[str, Any] | None:
        """Download an attachment from its URL.

        When no output path is supplied, ASCII attachments are written as text.
        Attachments containing non-ASCII bytes are written as raw bytes when
        stdout is redirected or piped. Binary output to an interactive terminal
        is refused unless base64 output is requested. Status and error messages
        are not written to stdout in these modes.

        Parameters
        ----------
        url : str
            Attachment URL returned by a message or aggregate.
        output : str, optional
            File path at which to save the downloaded attachment.
        force : bool, optional
            Overwrite the output file if it already exists.
        base64 : bool, optional
            Write the attachment to stdout as Base64-encoded ASCII text.
        """
        if output is not None and base64:
            raise ValueError("--output and --base64 cannot be used together")

        output_path = Path(output) if output is not None else None
        if output_path is not None and output_path.exists() and not force:
            raise FileExistsError(
                f"{output_path} already exists; use --force to overwrite it"
            )

        # FetchAttachment currently only uses the URL. Populate the remaining
        # protobuf fields with harmless placeholders so callers do not need to
        # reproduce metadata they already received alongside the URL.
        attachment = Attachment(
            filename="attachment",
            content_type="application/octet-stream",
            size=0,
            url=url,
        )

        try:
            downloaded = await self.fetch_message_attachment(attachment)
        finally:
            await self.close()

        if base64:
            encoded = base64_module.b64encode(downloaded.data).decode("ascii")
            sys.stdout.write(encoded + "\n")
            sys.stdout.flush()
            return None

        if output is None:
            try:
                text = downloaded.data.decode("ascii")
            except UnicodeDecodeError:
                pass
            else:
                sys.stdout.write(text)
                sys.stdout.flush()
                return None

            if sys.stdout.isatty():
                raise RuntimeError(
                    "Binary attachment cannot be written to an interactive terminal; "
                    "use --output PATH, --base64, or redirect stdout"
                )

            binary_stdout = getattr(sys.stdout, "buffer", None)
            if binary_stdout is None:
                raise RuntimeError(
                    "Binary stdout is unavailable; specify an output path with --output"
                )
            binary_stdout.write(downloaded.data)
            binary_stdout.flush()
            return None

        assert output_path is not None
        output_path.write_bytes(downloaded.data)
        return {
            "path": str(output_path),
            "content_type": downloaded.content_type,
            "size": len(downloaded.data),
        }

    async def close(self):
        for task in self._stream_tasks.values():
            task.cancel()
        self._stream_tasks.clear()
        logging.info("Closing device agent interface...")
        await super().close()

    @cli_command()
    async def listen_channel(self, channel_name: str) -> None:
        """Listen to channel events, printing the output to the console.

        Parameters
        ----------
        channel_name : str
            Name of channel to listen to.
        """
        try:
            async for event in self.stream_channel_events(channel_name):
                print(json.dumps(obj=event.to_dict()))
                sys.stdout.flush()
        except asyncio.CancelledError:
            await self.close()


class MockDeviceAgentInterface(DeviceAgentInterface):
    """
    This interface is used to test the Device Agent Interface without relying on a real Device Agent service.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_dda_online = True
        self.is_dda_available = True
        self.has_dda_been_online = True

    async def wait_for_channels_sync(
        self, channel_names: list[str], timeout: int = 5, inter_wait: float = 0.2
    ):
        for channel in channel_names:
            if channel not in self._aggregates:
                self._aggregates[channel] = Aggregate(
                    data={}, attachments=[], last_updated=None
                )
            self._synced_channels[channel] = True
        return True

    async def _run_channel_stream(
        self,
        channel_name: str,
        wire_format: WireFormat = WireFormat.json_only,
        replay_missed_messages: bool = True,
    ):
        # No-op in mock — no real event stream to listen to
        return

    async def fetch_channel_aggregate(self, channel_name):
        return copy.deepcopy(
            self._aggregates.get(
                channel_name,
                Aggregate(data={}, attachments=[], last_updated=None),
            )
        )

    async def list_channels(self, include_aggregate: bool = False) -> ChannelList:
        # There is no cloud in the mock, so the channels it knows of are the
        # ones it has been given — reported as a local answer.
        return ChannelList(
            [
                ChannelListing(
                    name, copy.deepcopy(agg.data) if include_aggregate else None
                )
                for name, agg in self._aggregates.items()
            ],
            from_cloud=False,
        )

    async def wait_until_healthy(self, timeout: float = 10):
        return True

    async def make_request(self, *args, **kwargs):
        raise NotImplementedError("make_request is not implemented")

    async def update_channel_aggregate(self, channel_name, data, **kwargs):
        existing = self._aggregates.get(
            channel_name, Aggregate(data={}, attachments=[], last_updated=None)
        )
        existing.data.update(data)
        self._aggregates[channel_name] = existing
        return copy.deepcopy(existing)

    async def create_message(self, channel_name, data, **kwargs):
        return 0
