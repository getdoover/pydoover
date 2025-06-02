import asyncio
import copy
import datetime
import json
import logging
import sys

from collections.abc import Coroutine, Callable
from typing import Any, Union

import grpc

from .grpc_stubs import device_agent_pb2, device_agent_pb2_grpc
from ..grpc_interface import GRPCInterface
from ...utils import apply_diff, call_maybe_async, maybe_async, maybe_load_json
from ...cli.decorators import command as cli_command

log = logging.getLogger(__name__)

MaybeAsyncCallback = Union[
    Callable[[str, dict[str, Any] | str], None],
    Coroutine[[str, dict[str, Any] | str], None],
]


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
        is_async: bool = None,
        dda_timeout: int = 7,
        max_conn_attempts: int = 5,
        time_between_connection_attempts: int = 10,
    ):
        super().__init__(app_key, dda_uri, is_async, dda_timeout)

        self.dda_timeout = dda_timeout
        self.max_connection_attempts = max_conn_attempts
        self.time_between_connection_attempts = time_between_connection_attempts

        self.is_dda_available = False
        self.is_dda_online = False
        self.has_dda_been_online = False

        # this is a list of channels that the agent interface will subscribe to,
        # and a list of callbacks that will be called when a message is received,
        # as well as the aggregate data that is received from the channel
        ## for channel in default_subscriptions:
        self._subscriptions: dict[str, list[Callable]] = {}
        self._synced_channels: dict[str, bool] = {}
        self._listeners: dict[str, asyncio.Task] = {}
        self._aggregates: dict[str, dict[str, Any] | str] = {}

        self.last_channel_message_ts = {}  # this is a dictionary of the last time a message was received from a channel

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

    def add_subscription(self, channel_name: str, callback: MaybeAsyncCallback) -> None:
        """Add a subscription to a channel.

        This does not block, but will start a background task to asynchronously
        invoke the callback when a new message is received on the given channel.

        The callback may be a regular function or an async function.

        Examples
        --------

        >>> async def my_callback(name, data):
        ...     print(f"Received data on {name}: {data}")
        >>> self.device_agent.add_subscription("my_channel", my_callback)

        Parameters
        ----------
        channel_name : str
            Name of channel to subscribe to.
        callback : Callable
            A callback function that will be called when a message is received on the channel.
            This callback should accept two parameters: channel_name, aggregate_data.
            It may be a regular function or an async function.
        """
        try:
            self._subscriptions[channel_name].append(callback)
        except KeyError:
            self._subscriptions[channel_name] = [callback]
            self._listeners[channel_name] = asyncio.create_task(
                self.start_subscription_listener(channel_name)
            )

    async def start_subscription_listener(self, channel_name):
        # """Start a subscription listener for the given channel.
        #
        # You should instead use the `add_subscription` method to add a subscription with a passed callback.
        #
        # This method will continually wait for updates from a channel,
        # and re-try connections that fail after `self.time_between_connection_attempts` seconds.
        # """
        while True:
            try:
                log.debug(f"Starting subscription to channel: {channel_name}")
                await self._subscribe_receive_channel_updates(channel_name)
            except Exception as e:
                log.error(
                    f"Error starting subscription listener for {channel_name}: {e}",
                    exc_info=e,
                )
                await asyncio.sleep(self.time_between_connection_attempts)

    async def _subscribe_receive_channel_updates(self, channel_name):
        async with grpc.aio.insecure_channel(self.uri) as channel:
            channel_stream = device_agent_pb2_grpc.deviceAgentStub(
                channel
            ).GetChannelSubscription(
                device_agent_pb2.ChannelSubscriptionRequest(channel_name=channel_name)
            )
            while True:
                try:
                    response: device_agent_pb2.ChannelSubscriptionResponse = (
                        await channel_stream.read()
                    )
                    log.debug(
                        f"Received response from subscription request on {channel_name}: {str(response)[:120]}"
                    )
                    self.update_dda_status(response.response_header)
                    if not response.response_header.success:
                        raise RuntimeError(
                            f"Failed to subscribe to channel {channel_name}: {response.response_header.response_message}"
                        )

                    log.debug(
                        f"Calling callback with subscription response for {channel_name}..."
                    )
                    await self.recv_update_callback(channel_name, response)
                except StopAsyncIteration:
                    log.debug("Channel stream ended.")
                    break

    async def recv_update_callback(self, channel_name, response):
        log.debug(f"Received response from subscription request: {str(response)[:100]}")
        try:
            existing = self._aggregates[channel_name]
        except KeyError:
            data = await self.get_channel_aggregate_async(channel_name)
        else:
            diff = maybe_load_json(response.message.payload)
            log.debug(
                f"Applying diff to existing data for channel {channel_name}: {diff}"
            )
            data = copy.deepcopy(existing)
            if diff:
                data = apply_diff(data, diff)
                log.debug(f"Applied diff result ({channel_name}): {data}")
            # else:
            #     log.debug(f"No diff found for channel {channel_name}. Skipping...")
            #     return

        if data in (None, "None"):
            log.warning(f"Received empty data from channel {channel_name}")
            data = {}
            # return

        self._aggregates[channel_name] = data
        self._synced_channels[channel_name] = True
        self.last_channel_message_ts[channel_name] = datetime.datetime.now()

        log.debug(
            f"Calling {len(self._subscriptions.get(channel_name, []))} "
            f"callbacks for channel {channel_name} with data: {str(data)[:100]}"
        )
        _tasks = [
            await call_maybe_async(
                callback, channel_name, copy.deepcopy(data), as_task=True
            )
            for callback in self._subscriptions.get(channel_name, [])
        ]
        # await asyncio.gather(*tasks)

    def process_response(self, stub_call: str, response, *args, **kwargs):
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
        if channel_name not in self._subscriptions:
            return False
        if channel_name not in self._synced_channels:
            return False
        return self._synced_channels[channel_name]

    async def wait_for_channels_sync_async(
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
        start_time = datetime.datetime.now()
        while not all(
            [self.is_channel_synced(channel_name) for channel_name in channel_names]
        ):
            if (datetime.datetime.now() - start_time).seconds > timeout:
                return False
            await asyncio.sleep(inter_wait)
        return True

    @cli_command()
    @maybe_async()
    def get_channel_aggregate(self, channel_name: str) -> str | dict[str, Any] | None:
        """Fetch a channel's current aggregate payload.

        .. note:: This method can be called in both sync and asynchronous contexts.

        Examples
        --------
        >>> aggregate = await self.device_agent.get_channel_aggregate("my_channel")
        >>> print(aggregate)  # This will print the aggregate data as a dictionary or string.

        Parameters
        ----------
        channel_name : str
            Name of channel to get aggregate from.

        Returns
        -------
        dict | str, optional
            Aggregate data from channel. If the request fails for any reason, this will return `None`.
        """
        log.debug(f"Getting channel aggregate for {channel_name}")
        resp = self.make_request(
            "GetChannelDetails",
            device_agent_pb2.ChannelDetailsRequest(channel_name=channel_name),
        )
        if not resp:
            return None

        return maybe_load_json(resp.channel.aggregate)

    async def get_channel_aggregate_async(self, channel_name):
        log.debug(f"Getting channel aggregate (async) for {channel_name}")
        resp = await self.make_request_async(
            "GetChannelDetails",
            device_agent_pb2.ChannelDetailsRequest(channel_name=channel_name),
        )
        if not resp:
            return

        return maybe_load_json(resp.channel.aggregate)

    @cli_command()
    @maybe_async()
    def publish_to_channel(
        self,
        channel_name: str,
        message: dict | str,
        record_log: bool = True,
        max_age: int = None,
    ) -> bool:
        """Publish a message to a channel.

        .. note:: This method can be called in both sync and asynchronous contexts.

        There is a special case with the `max_age` parameter where you can set it to `-1` to publish the message immediately.
        This is useful for ensuring that the message is sent to the cloud immediately and won't be bundled in with other messages.
        A good example is when you want to clear the UI. However, use this sparingly!

        Examples
        --------

        Simple example::

        >>> result = await self.device_agent.publish_to_channel("my_channel", {"foo": "bar"})
        >>> print(f"Publishing the message was {'successful' if result else 'unsuccessful'}.")


        Publish to the cloud in 5 seconds::

        >>> result = await self.device_agent.publish_to_channel("my_channel", {"foo": "bar"}, max_age=5)
        >>> print(f"Publishing the message was {'successful' if result else 'unsuccessful'}.")

        Publish to the cloud immediately and save to the log::

        >>> result = await self.device_agent.publish_to_channel("my_channel", {"foo": "bar"}, record_log=True, max_age=-1)
        >>> print(f"Publishing the message was {'successful' if result else 'unsuccessful'}.")



        Parameters
        ----------
        channel_name : str
            Name of channel to publish data too.
        message : dict or str
            The data to send either in a dictionary or string format
        record_log :
            Whether to save to the log
        max_age : int
            The maximum age of the message before publishing to the cloud

        Returns
        -------
        bool
            Whether publishing was successful
        """
        if isinstance(message, dict):
            message = json.dumps(message)

        req = device_agent_pb2.ChannelWriteRequest(
            header=device_agent_pb2.RequestHeader(app_id=self.app_key),
            channel_name=channel_name,
            message_payload=message,
            save_log=record_log,
            max_age=max_age,
        )
        resp = self.make_request("WriteToChannel", req)
        return resp and resp.response_header.success or False

    async def publish_to_channel_async(
        self,
        channel_name: str,
        message: dict | str,
        record_log: bool = True,
        max_age: int = None,
    ):
        if isinstance(message, dict):
            message = json.dumps(message)

        req = device_agent_pb2.ChannelWriteRequest(
            header=device_agent_pb2.RequestHeader(app_id=self.app_key),
            channel_name=channel_name,
            message_payload=message,
            save_log=record_log,
            max_age=max_age,
        )
        resp = await self.make_request_async("WriteToChannel", req)
        return resp and resp.response_header.success or False

    @staticmethod
    def _parse_get_token_response(
        response,
    ) -> tuple[str, datetime.datetime, str] | None:
        if response is None:
            return None

        try:
            return (
                response.token,
                datetime.datetime.fromtimestamp(float(response.valid_until)),
                response.endpoint,
            )
        except (ValueError, Exception) as e:
            logging.error("Failed to parse output from get_temp_token", exc_info=e)
            return None

    @cli_command()
    @maybe_async()
    def get_temp_token(self) -> tuple[str, datetime.datetime, str] | None:
        """Get a temporary API token.

        .. deprecated:: 0.4.0
            WSS Tokens are now valid for API calls. Use that instead.

        .. note:: This method can be called in both sync and asynchronous contexts.

        Returns
        -------
        tuple, optional
            (token, expire_time, url_endpoint) if the request succeeds, otherwise None.
        """
        resp = self.make_request(
            "GetTempAPIToken", device_agent_pb2.TempAPITokenRequest()
        )
        return self._parse_get_token_response(resp)

    async def get_temp_token_async(
        self,
    ) -> tuple[str, datetime.datetime, str] | None:
        resp = await self.make_request_async(
            "GetTempAPIToken", device_agent_pb2.TempAPITokenRequest()
        )
        return self._parse_get_token_response(resp)

    async def close(self):
        for listener in self._listeners.values():
            listener.cancel()
        logging.info("Closing device agent interface...")

    @cli_command()
    def test_comms(self, message: str = "Comms Check Message") -> str | None:
        """Test connection by sending a basic echo response to device agent container.

        Parameters
        ----------
        message : str
            Message to send to device agent to have echo'd as a response

        Returns
        -------
        str
            The response from device agent.
        """
        return self.make_request(
            "TestComms",
            device_agent_pb2.TestCommsRequest(message=message),
            response_field="response",
        )

    @cli_command()
    def listen_channel(self, channel_name: str) -> None:
        """Listen to channel printing the output to the console.

        Parameters
        ----------
        channel_name : str
            Name of channel to get aggregate from.

        Returns
        -------
        None
            Response is printed to stdout directly
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.run_channel_listening(channel_name))
        else:
            asyncio.create_task(self.run_channel_listening(channel_name))

    async def run_channel_listening(self, channel_name: str):
        def callback(name, aggregate):
            print(name, json.dumps(aggregate))
            sys.stdout.flush()

        self.add_subscription(channel_name, callback)

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await self.close()


device_agent_iface = DeviceAgentInterface
