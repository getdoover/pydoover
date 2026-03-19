"""Tests for pydoover.rpc module."""

import asyncio
import pytest

from pydoover.rpc import (
    RPCError,
    RPCTimeoutError,
    RPCManager,
    RPCRequest,
    RPC_KEY,
    handler,
)
from pydoover.models.data import (
    ChannelID,
    Message,
    MessageCreateEvent,
    MessageUpdateEvent,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_channel(name="test_channel"):
    return ChannelID(agent_id=1, name=name)


def _make_create_event(
    method, params=None, message_id=100, channel_name="test_channel"
):
    channel = _make_channel(channel_name)
    msg = Message(
        id=message_id,
        author_id=42,
        channel=channel,
        data={RPC_KEY: {"method": method, "params": params or {}}},
        attachments=[],
    )
    return MessageCreateEvent(channel=channel, message=msg)


def _make_update_event(rpc_data, message_id=100, channel_name="test_channel"):
    msg = Message(
        id=message_id,
        author_id=99,
        channel=_make_channel(channel_name),
        data={RPC_KEY: rpc_data},
        attachments=[],
    )
    return MessageUpdateEvent(
        channel=_make_channel(channel_name),
        author_id=99,
        organisation_id=1,
        message=msg,
        request_data={},
    )


class FakeApp:
    """Minimal Application stand-in for testing RPCManager."""

    def __init__(self):
        self._callbacks = {}
        self._messages = {}
        self._next_id = 1000

    class _FakeDA:
        def __init__(self, app):
            self._app = app

        def add_event_callback(self, channel_name, callback, events):
            self._app._callbacks.setdefault(channel_name, []).append(callback)

    @property
    def device_agent(self):
        return self._FakeDA(self)

    async def create_message(self, channel_name, data, **kwargs):
        mid = self._next_id
        self._next_id += 1
        self._messages[mid] = {"channel": channel_name, "data": data}
        return mid

    async def update_message(self, channel_name, message_id, data, **kwargs):
        self._messages.setdefault(message_id, {}).update({"data": data})
        return Message(
            id=message_id,
            author_id=0,
            channel=_make_channel(channel_name),
            data=data,
            attachments=[],
        )

    async def fire_event(self, channel_name, event):
        """Simulate the DDA dispatching an event to registered callbacks."""
        for cb in self._callbacks.get(channel_name, []):
            await cb(event)


# ---------------------------------------------------------------------------
# Tests: decorator
# ---------------------------------------------------------------------------


class TestHandlerDecorator:
    def test_sets_attributes(self):
        @handler("reboot")
        async def my_handler(self, event):
            pass

        assert my_handler._is_rpc_handler is True
        assert my_handler._rpc_method == "reboot"
        assert my_handler._rpc_channel is None

    def test_sets_channel(self):
        @handler("status", channel="control")
        async def my_handler(self, event):
            pass

        assert my_handler._rpc_channel == "control"


# ---------------------------------------------------------------------------
# Tests: RPCRequest
# ---------------------------------------------------------------------------


class TestRPCRequest:
    def test_from_event(self):
        event = _make_create_event("ping", {"timeout": 5})

        async def _update(ch, mid, data):
            pass

        req = RPCRequest.from_event(event, _update)
        assert req is not None
        assert req.method == "ping"
        assert req.params == {"timeout": 5}
        assert req.message_id == 100
        assert req.channel_name == "test_channel"
        assert req.author_id == 42

    def test_from_event_non_rpc(self):
        channel = _make_channel()
        msg = Message(
            id=1, author_id=2, channel=channel, data={"some": "data"}, attachments=[]
        )
        event = MessageCreateEvent(channel=channel, message=msg)
        req = RPCRequest.from_event(event, lambda *a: None)
        assert req is None

    @pytest.mark.asyncio
    async def test_acknowledge(self):
        updates = []

        async def _update(ch, mid, data):
            updates.append((ch, mid, data))

        req = RPCRequest(
            method="slow_op",
            params={"x": 1},
            message_id=55,
            channel_name="ch",
            channel=_make_channel("ch"),
            author_id=10,
            _update_fn=_update,
        )
        await req.acknowledge()

        assert len(updates) == 1
        ch, mid, data = updates[0]
        assert mid == 55
        assert data[RPC_KEY]["status"] == "acknowledged"
        assert data[RPC_KEY]["method"] == "slow_op"


# ---------------------------------------------------------------------------
# Tests: RPCManager.register_handlers
# ---------------------------------------------------------------------------


class TestRegisterHandlers:
    def test_discovers_handlers(self):
        class MyApp:
            @handler("do_thing")
            async def handle_thing(self, event):
                pass

            @handler("do_other", channel="ctrl")
            async def handle_other(self, event):
                pass

            async def not_a_handler(self):
                pass

        app = FakeApp()
        mgr = RPCManager(app)
        obj = MyApp()
        mgr.register_handlers(obj)

        assert len(mgr._handlers) == 2
        methods = {h[0] for h in mgr._handlers}
        assert methods == {"do_thing", "do_other"}


# ---------------------------------------------------------------------------
# Tests: RPCManager end-to-end
# ---------------------------------------------------------------------------


class TestRPCManagerIntegration:
    @pytest.mark.asyncio
    async def test_request_handler_response(self):
        """Simulate: request arrives → handler runs → response sent."""
        app = FakeApp()
        mgr = RPCManager(app)

        results = []

        async def my_handler(event: RPCRequest):
            results.append(event.params)
            return {"status": "done"}

        mgr._handlers.append(("ping", None, my_handler))
        mgr.subscribe("test_channel")

        event = _make_create_event("ping", {"val": 42})
        await app.fire_event("test_channel", event)

        assert len(results) == 1
        assert results[0] == {"val": 42}

        # Check response was sent via update_message (PATCH — only result key)
        assert 100 in app._messages
        response_data = app._messages[100]["data"]
        assert response_data[RPC_KEY] == {"result": {"status": "done"}}

    @pytest.mark.asyncio
    async def test_handler_rpc_error(self):
        """Handler raises RPCError → error response sent."""
        app = FakeApp()
        mgr = RPCManager(app)

        async def failing_handler(event: RPCRequest):
            raise RPCError("OFFLINE", "Device is offline")

        mgr._handlers.append(("check", None, failing_handler))
        mgr.subscribe("test_channel")

        event = _make_create_event("check")
        await app.fire_event("test_channel", event)

        response_data = app._messages[100]["data"]
        assert response_data[RPC_KEY] == {
            "error": {"code": "OFFLINE", "message": "Device is offline"}
        }

    @pytest.mark.asyncio
    async def test_handler_unhandled_exception(self):
        """Unhandled exception → INTERNAL_ERROR response."""
        app = FakeApp()
        mgr = RPCManager(app)

        async def bad_handler(event: RPCRequest):
            raise ValueError("something broke")

        mgr._handlers.append(("boom", None, bad_handler))
        mgr.subscribe("test_channel")

        event = _make_create_event("boom")
        await app.fire_event("test_channel", event)

        response_data = app._messages[100]["data"]
        assert response_data[RPC_KEY]["error"]["code"] == "INTERNAL_ERROR"
        assert "something broke" in response_data[RPC_KEY]["error"]["message"]
        # Should only contain error key (PATCH — no method/params echoed)
        assert "method" not in response_data[RPC_KEY]

    @pytest.mark.asyncio
    async def test_call_resolves_on_response(self):
        """call() creates message and resolves when update event arrives."""
        app = FakeApp()
        mgr = RPCManager(app)

        async def do_call():
            return await mgr.call(
                "ping", params={"x": 1}, channel="test_channel", timeout=2.0
            )

        task = asyncio.create_task(do_call())

        # Let the call() register its future
        await asyncio.sleep(0)

        # The message_id assigned by FakeApp starts at 1000
        message_id = 1000
        assert message_id in mgr._pending_calls

        # Simulate a response arriving
        update = _make_update_event(
            {"method": "ping", "params": {"x": 1}, "result": {"pong": True}},
            message_id=message_id,
            channel_name="test_channel",
        )
        await app.fire_event("test_channel", update)

        result = await task
        assert result == {"pong": True}
        assert message_id not in mgr._pending_calls

    @pytest.mark.asyncio
    async def test_call_timeout(self):
        """call() raises RPCTimeoutError when no response arrives."""
        app = FakeApp()
        mgr = RPCManager(app)

        with pytest.raises(RPCTimeoutError):
            await mgr.call("slow", channel="test_channel", timeout=0.05)

    @pytest.mark.asyncio
    async def test_call_rpc_error_response(self):
        """call() raises RPCError when remote returns an error."""
        app = FakeApp()
        mgr = RPCManager(app)

        async def do_call():
            return await mgr.call("fail", channel="test_channel", timeout=2.0)

        task = asyncio.create_task(do_call())
        await asyncio.sleep(0)

        message_id = 1000
        update = _make_update_event(
            {
                "method": "fail",
                "params": {},
                "error": {"code": "BAD", "message": "nope"},
            },
            message_id=message_id,
            channel_name="test_channel",
        )
        await app.fire_event("test_channel", update)

        with pytest.raises(RPCError) as exc_info:
            await task
        assert exc_info.value.code == "BAD"

    @pytest.mark.asyncio
    async def test_non_rpc_messages_ignored(self):
        """Messages without dv-rpc key are silently ignored."""
        app = FakeApp()
        mgr = RPCManager(app)
        mgr.subscribe("test_channel")

        channel = _make_channel()
        msg = Message(
            id=200,
            author_id=1,
            channel=channel,
            data={"normal": "message"},
            attachments=[],
        )
        event = MessageCreateEvent(channel=channel, message=msg)
        # Should not raise
        await app.fire_event("test_channel", event)

    @pytest.mark.asyncio
    async def test_acknowledge_does_not_resolve_future(self):
        """A status-only update should NOT resolve a pending call."""
        app = FakeApp()
        mgr = RPCManager(app)

        async def do_call():
            return await mgr.call("slow_op", channel="test_channel", timeout=0.5)

        task = asyncio.create_task(do_call())
        await asyncio.sleep(0)

        message_id = 1000

        # Send acknowledge (non-terminal)
        ack = _make_update_event(
            {"method": "slow_op", "params": {}, "status": "acknowledged"},
            message_id=message_id,
            channel_name="test_channel",
        )
        await app.fire_event("test_channel", ack)

        # Future should still be pending
        assert not mgr._pending_calls[message_id].done()

        # Now send actual result
        result = _make_update_event(
            {"method": "slow_op", "params": {}, "result": {"done": True}},
            message_id=message_id,
            channel_name="test_channel",
        )
        await app.fire_event("test_channel", result)

        assert await task == {"done": True}

    @pytest.mark.asyncio
    async def test_channel_scoped_handler(self):
        """Handler with channel constraint only fires on matching channel."""
        app = FakeApp()
        mgr = RPCManager(app)

        calls = []

        async def scoped_handler(event: RPCRequest):
            calls.append(event.channel_name)
            return {}

        mgr._handlers.append(("ping", "control", scoped_handler))
        mgr.subscribe("control")
        mgr.subscribe("other")

        # Event on matching channel
        await app.fire_event(
            "control", _make_create_event("ping", channel_name="control")
        )
        assert len(calls) == 1

        # Event on non-matching channel
        await app.fire_event("other", _make_create_event("ping", channel_name="other"))
        assert len(calls) == 1  # still 1 — handler didn't fire
