"""RPC over Doover channels.

Provides request/response style communication between applications
using channel messages as the transport.
"""

import asyncio
import inspect
import logging
import re
from collections.abc import Callable
from datetime import timezone, timedelta, datetime
from typing import Any, TYPE_CHECKING, Union

from .models.data import (
    EventSubscription,
    MessageCreateEvent,
    MessageUpdateEvent,
    Message,
    OneShotMessage,
)

if TYPE_CHECKING:
    from .docker.application import DeviceAgentInterface
    from .api.data import AsyncDataClient

log = logging.getLogger(__name__)

RPC_KEY = "dv-rpc"
DEFAULT_CHANNEL = "dv-rpc"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RPCError(Exception):
    """An error returned by an RPC handler."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class RPCTimeoutError(RPCError):
    """Raised when an RPC call times out waiting for a response."""

    def __init__(self, method: str, timeout: float):
        super().__init__("TIMEOUT", f"RPC call '{method}' timed out after {timeout}s")


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


def handler(
    method: str | re.Pattern, channel: str | None = None, parser: Callable = None
):
    """Decorator to mark an async method as an RPC handler.

    Parameters
    ----------
    method : str
        The RPC method name this handler responds to.
    channel : str, optional
        If set, only handle requests arriving on this channel.
        If ``None``, matches requests on any subscribed channel.
    """

    def decorator(func: Callable) -> Callable:
        func._is_rpc_handler = True
        func._rpc_method = method
        func._rpc_channel = channel
        func._rpc_parser = parser
        return func

    return decorator


# ---------------------------------------------------------------------------
# RPCRequest — event object passed to handlers
# ---------------------------------------------------------------------------


class RPCContext:
    def __init__(self, method: str, message: Message, _update_fn: Callable):
        self.method = method
        self.message = message
        self._update_fn = _update_fn

    @property
    def channel(self):
        return self.message.channel

    async def acknowledge(self):
        # fixme: maybe these should be objects...
        payload = {
            "status": {
                "code": "acknowledged",
                "message": {
                    "timestamp": int(datetime.now(tz=timezone.utc).timestamp() * 1000)
                },
            }
        }
        await self._update_fn(self.channel.name, self.message.id, payload)

    async def defer(self, seconds: float):
        now = datetime.now(tz=timezone.utc)
        until = now + timedelta(seconds=seconds)
        payload = {
            "status": {
                "code": "deferred",
                "message": {
                    "until": int(until.timestamp() * 1000),
                    "at": int(now.timestamp() * 1000),
                },
            }
        }
        await self._update_fn(self.channel.name, self.message.id, payload)


# ---------------------------------------------------------------------------
# RPCManager
# ---------------------------------------------------------------------------


class RPCManager:
    """Orchestrates RPC over channel messages.

    Parameters
    ----------
    api : DeviceAgentInterface | AsyncDataClient
        The application instance this manager is attached to.
    app_key : str | None
        The application key for this app, used to reject messages not intended for this app.
    """

    def __init__(
        self,
        api: Union["DeviceAgentInterface", "AsyncDataClient"],
        app_key: str | None = None,
    ):
        self.api = api
        self.app_key = app_key
        # (channel_name, method_name) -> (parser, handler)
        self._handlers: dict[tuple[str, str], tuple[Callable, Callable]] = {}
        self._re_handlers: list[tuple[str, re.Pattern, Callable, Callable]] = []

        self._pending_calls: dict[int, asyncio.Future] = {}
        self._subscribed_channels: set[str] = set()

    @property
    def is_processor(self):
        return getattr(self.api, "is_processor_v2", False)

    # -- handler registration -----------------------------------------------

    def check_handler(self, func: Callable):
        return inspect.ismethod(func) and getattr(func, "_is_rpc_handler", False)

    def register_handlers(self, obj: object) -> None:
        """Scan *obj* for methods decorated with :func:`handler` and register them."""
        for _name, func in inspect.getmembers(
            obj,
            predicate=lambda f: self.check_handler(f),
        ):
            method_name = func._rpc_method
            channel = func._rpc_channel
            request_parser = func._rpc_parser
            log.info(f"Registering RPC handler: {method_name} (channel={channel})")
            if isinstance(method_name, re.Pattern):
                # this is less efficient lookup-wise, so only do it if needed
                # but is a pretty useful / flexible feature for the user (ie. subscribe to all get_*_di handlers)
                self._re_handlers.append((channel, method_name, request_parser, func))
            else:
                self._handlers[(channel, method_name)] = (request_parser, func)

            # Auto-subscribe to the handler's channel if specified
            if channel is not None:
                self.subscribe(channel)

    # -- channel subscription -----------------------------------------------

    def subscribe(self, channel_name: str) -> None:
        """Subscribe to RPC events on *channel_name*."""
        if channel_name in self._subscribed_channels:
            return
        if self.is_processor:
            return  # we can't subscribe on a processor...

        self._subscribed_channels.add(channel_name)
        self.api.add_event_callback(
            channel_name,
            self._on_event,
            EventSubscription.message_create
            | EventSubscription.message_update
            | EventSubscription.oneshot_message,
        )
        log.info(f"RPC subscribed to channel: {channel_name}")

    def _ensure_subscribed(self, channel_name: str) -> None:
        """Subscribe if not already subscribed."""
        self.subscribe(channel_name)

    # -- caller side --------------------------------------------------------

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        channel: str = DEFAULT_CHANNEL,
        app_key: str | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Make an RPC call and wait for the response.

        Parameters
        ----------
        method : str
            The RPC method to call.
        params : dict, optional
            Parameters to pass to the remote handler.
        channel : str
            Channel to send the request on. Defaults to ``"tag_values"``.
        timeout : float
            Seconds to wait for a response before raising :class:`RPCTimeoutError`.

        Returns
        -------
        dict
            The result payload from the remote handler.

        Raises
        ------
        RPCTimeoutError
            If no response arrives within *timeout* seconds.
        RPCError
            If the remote handler returned an error.
        """
        self._ensure_subscribed(channel)

        data = {
            "type": "rpc",
            "method": method,
            "request": params or {},
            "status": {"code": "sent"},
            "response": {},
        }
        if app_key:
            data["app_key"] = app_key
        message_id = await self.api.create_message(channel, data)

        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._pending_calls[message_id] = future

        try:
            result = await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise RPCTimeoutError(method, timeout)
        finally:
            self._pending_calls.pop(message_id, None)

        return result

    # -- event handling -----------------------------------------------------

    async def _on_event(self, event) -> None:
        """Route incoming events to handler dispatch or future resolution."""
        if isinstance(event, (MessageCreateEvent, OneShotMessage)):
            await self._handle_request(event)
        elif isinstance(event, MessageUpdateEvent):
            self._handle_response(event)

    def _get_handler(self, channel_name, method):
        try:
            return self._handlers[(channel_name, method)]
        except KeyError:
            for channel, pattern, parser, req_handler in self._re_handlers:
                if channel == channel_name and pattern.match(method):
                    return parser, req_handler

        # get global handlers
        try:
            return self._handlers[(None, method)]
        except KeyError:
            pass

        raise KeyError("could not find appropriate parser...")

    def _build_context(self, method, event: MessageCreateEvent | MessageUpdateEvent):
        return RPCContext(
            method=method,
            message=event.message,
            _update_fn=self.api.update_message,
        )

    async def _handle_request(self, event: MessageCreateEvent | OneShotMessage) -> None:
        """Dispatch an incoming RPC request to the appropriate handler."""
        try:
            event_type = event.message.data["type"]
        except KeyError:
            event_type = None

        if event_type != "rpc":
            log.info("Skipping non-rpc event")
            return

        try:
            method = event.message.data["method"]
        except KeyError:
            return

        try:
            app_key = event.message.data["app_key"]
        except KeyError:
            pass
        else:
            if app_key != self.app_key:
                log.debug(
                    f"Skipping RPC request for app_key={app_key!r} (ours={self.app_key!r})"
                )
                return

        try:
            payload = event.message.data["request"]
        except KeyError:
            log.info(f"Received malformed RPC request: {event.message.data}")
            return

        channel_name = event.channel.name

        try:
            parser, method_handler = self._get_handler(channel_name, method)
        except KeyError:
            return

        ctx = self._build_context(method, event)
        if parser:
            if asyncio.iscoroutinefunction(parser):
                payload = await parser(payload)
            else:
                payload = parser(payload)

        # we can't isinstance MessageCreateEvent because OneShotMessage is a subclass
        can_respond = not isinstance(event, OneShotMessage)

        try:
            result = await method_handler(ctx, payload)
        except RPCError as e:
            if can_respond:
                await self._send_error(event.message, e.code, e.message)
        except Exception as e:
            log.error(
                f"Unhandled exception in RPC handler '{method_handler}': {e}",
                exc_info=e,
            )
            if can_respond:
                await self._send_error(event.message, "INTERNAL_ERROR", str(e))
        else:
            if result is None:
                result = {}

            if can_respond:
                await self._send_result(event.message, result)

    def _handle_response(self, event: MessageUpdateEvent) -> None:
        """Resolve a pending future if this update is an RPC response."""
        try:
            status = event.message.data["status"]
        except KeyError:
            log.debug("Failed to get status from RPC message. Ignoring.")
            return

        future = self._pending_calls.get(event.message.id)
        if future is None or future.done():
            return

        status_code = status.get("code")
        if status_code in ("sent", "acknowledged", "deferred", "pending"):
            return

        if status_code == "error":
            err = status.get("message", "")
            if isinstance(err, dict):
                code = err.get("code", "UNKNOWN")
                message = err.get("message", "")
            else:
                code = "UNKNOWN"
                message = err
            future.set_exception(RPCError(code, message))
        elif status_code == "success":
            future.set_result(event.message.data.get("response", {}))

    # -- response helpers ---------------------------------------------------

    async def _send_result(self, message: Message, response: dict) -> None:
        data = {
            "status": {
                "code": "success",
                "message": None,
            },
            "response": response,
        }
        await self.api.update_message(message.channel.name, message.id, data)

    async def _send_error(
        self,
        request_message: Message,
        code: str,
        error_message: str | dict[str, Any],
    ) -> None:
        data = {
            "status": {
                "code": "error",
                "message": {"code": code, "message": error_message},
            },
            "response": {},
        }
        await self.api.update_message(
            request_message.channel.name,
            request_message.id,
            data,
        )

    # -- static helpers for processor usage ---------------------------------

    @staticmethod
    async def fire_and_forget(
        client,
        agent_id: int,
        channel: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> int:
        """Send an RPC request without waiting for a response.

        Intended for use from processors or other contexts without
        an event stream.

        Parameters
        ----------
        client
            A cloud API client with a ``create_message`` method.
        agent_id : int
            The target agent's ID.
        channel : str
            Channel name to send the request on.
        method : str
            The RPC method name.
        params : dict, optional
            Parameters for the call.

        Returns
        -------
        int
            The created message ID.
        """
        data = {
            "type": "rpc",
            "request": params or {},
            "method": method,
            "status": {"code": "sent"},
            "response": {},
        }
        return await client.create_message(channel_name=channel, data=data)
