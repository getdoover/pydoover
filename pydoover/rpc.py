"""RPC over Doover channels.

Provides request/response style communication between applications
using channel messages as the transport.
"""

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from .models.data import (
    ChannelID,
    EventSubscription,
    MessageCreateEvent,
    MessageUpdateEvent,
)

if TYPE_CHECKING:
    from .docker.application import Application

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


def handler(method: str, channel: str | None = None):
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
        return func

    return decorator


# ---------------------------------------------------------------------------
# RPCRequest — event object passed to handlers
# ---------------------------------------------------------------------------


class RPCRequest:
    """Represents an incoming RPC request passed to handler functions."""

    def __init__(
        self,
        method: str,
        params: dict[str, Any],
        message_id: int,
        channel_name: str,
        channel: ChannelID,
        author_id: int,
        _update_fn: Callable | None = None,
    ):
        self.method = method
        self.params = params
        self.message_id = message_id
        self.channel_name = channel_name
        self.channel = channel
        self.author_id = author_id
        self._update_fn = _update_fn

    async def acknowledge(self) -> None:
        """Send a non-terminal acknowledgement for this request."""
        if self._update_fn is None:
            raise RuntimeError("No update function available")
        rpc_data = {
            "method": self.method,
            "params": self.params,
            "status": "acknowledged",
        }
        await self._update_fn(self.channel_name, self.message_id, {RPC_KEY: rpc_data})

    @classmethod
    def from_event(
        cls,
        event: MessageCreateEvent,
        update_fn: Callable,
    ) -> "RPCRequest":
        """Create an RPCRequest from a MessageCreateEvent.

        Returns ``None`` if the event is not an RPC message.
        """
        rpc_payload = event.message.data.get(RPC_KEY)
        if rpc_payload is None:
            return None

        return cls(
            method=rpc_payload["method"],
            params=rpc_payload.get("params", {}),
            message_id=event.message.id,
            channel_name=event.channel.name,
            channel=event.channel,
            author_id=event.message.author_id,
            _update_fn=update_fn,
        )


# ---------------------------------------------------------------------------
# RPCManager
# ---------------------------------------------------------------------------


class RPCManager:
    """Orchestrates RPC over channel messages.

    Parameters
    ----------
    app : Application
        The application instance this manager is attached to.
    """

    def __init__(self, app: "Application"):
        self._app = app
        # (method_name, channel_or_None, callback)
        self._handlers: list[tuple[str, str | None, Callable]] = []
        # message_id → Future
        self._pending_calls: dict[int, asyncio.Future] = {}
        self._subscribed_channels: set[str] = set()

    # -- handler registration -----------------------------------------------

    def register_handlers(self, obj: object) -> None:
        """Scan *obj* for methods decorated with :func:`handler` and register them."""
        for _name, func in inspect.getmembers(
            obj,
            predicate=lambda f: inspect.ismethod(f) and hasattr(f, "_is_rpc_handler"),
        ):
            method_name = func._rpc_method
            channel = func._rpc_channel
            log.info(f"Registering RPC handler: {method_name} (channel={channel})")
            self._handlers.append((method_name, channel, func))

            # Auto-subscribe to the handler's channel if specified
            if channel is not None:
                self.subscribe(channel)

    # -- channel subscription -----------------------------------------------

    def subscribe(self, channel_name: str) -> None:
        """Subscribe to RPC events on *channel_name*."""
        if channel_name in self._subscribed_channels:
            return
        self._subscribed_channels.add(channel_name)
        self._app.device_agent.add_event_callback(
            channel_name,
            self._on_event,
            EventSubscription.message_create | EventSubscription.message_update,
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

        data = {RPC_KEY: {"method": method, "params": params or {}}}
        message_id = await self._app.create_message(channel, data)

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
        if isinstance(event, MessageCreateEvent):
            await self._handle_request(event)
        elif isinstance(event, MessageUpdateEvent):
            self._handle_response(event)

    async def _handle_request(self, event: MessageCreateEvent) -> None:
        """Dispatch an incoming RPC request to the appropriate handler."""
        rpc_payload = event.message.data.get(RPC_KEY)
        if rpc_payload is None:
            return

        method = rpc_payload.get("method")
        if method is None:
            return

        channel_name = event.channel.name

        # Find matching handler
        matched_handler = None
        for handler_method, handler_channel, callback in self._handlers:
            if handler_method != method:
                continue
            if handler_channel is not None and handler_channel != channel_name:
                continue
            matched_handler = callback
            break

        if matched_handler is None:
            return

        request = RPCRequest(
            method=method,
            params=rpc_payload.get("params", {}),
            message_id=event.message.id,
            channel_name=channel_name,
            channel=event.channel,
            author_id=event.message.author_id,
            _update_fn=self._app.update_message,
        )

        try:
            result = await matched_handler(request)
        except RPCError as e:
            await self._send_error(channel_name, event.message.id, e.code, e.message)
        except Exception as e:
            log.error(f"Unhandled exception in RPC handler '{method}': {e}", exc_info=e)
            await self._send_error(
                channel_name, event.message.id, "INTERNAL_ERROR", str(e)
            )
        else:
            if result is None:
                result = {}
            await self._send_result(channel_name, event.message.id, result)

    def _handle_response(self, event: MessageUpdateEvent) -> None:
        """Resolve a pending future if this update is an RPC response."""
        message = event.message
        rpc_payload = message.data.get(RPC_KEY)
        if rpc_payload is None:
            return

        message_id = message.id
        future = self._pending_calls.get(message_id)
        if future is None or future.done():
            return

        # Non-terminal status updates (e.g. "acknowledged") don't resolve
        if (
            "status" in rpc_payload
            and "result" not in rpc_payload
            and "error" not in rpc_payload
        ):
            return

        if "error" in rpc_payload:
            err = rpc_payload["error"]
            future.set_exception(
                RPCError(err.get("code", "UNKNOWN"), err.get("message", ""))
            )
        elif "result" in rpc_payload:
            future.set_result(rpc_payload["result"])

    # -- response helpers ---------------------------------------------------

    async def _send_result(
        self, channel_name: str, message_id: int, result: dict
    ) -> None:
        await self._app.update_message(
            channel_name, message_id, {RPC_KEY: {"result": result}}
        )

    async def _send_error(
        self, channel_name: str, message_id: int, code: str, message: str
    ) -> None:
        await self._app.update_message(
            channel_name,
            message_id,
            {RPC_KEY: {"error": {"code": code, "message": message}}},
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
        data = {RPC_KEY: {"method": method, "params": params or {}}}
        return await client.create_message(agent_id, channel, data)
