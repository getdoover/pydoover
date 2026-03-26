import asyncio
import re

import pytest

from pydoover.models.data import (
    ChannelID,
    Message,
    MessageCreateEvent,
    MessageUpdateEvent,
)
from pydoover.rpc import RPCContext, RPCError, RPCManager, RPCTimeoutError, handler


def _make_channel(name: str = "test_channel") -> ChannelID:
    return ChannelID(agent_id=1, name=name)


def _make_request_event(
    method: str,
    payload: dict | None = None,
    message_id: int = 100,
    channel_name: str = "test_channel",
) -> MessageCreateEvent:
    channel = _make_channel(channel_name)
    message = Message(
        id=message_id,
        author_id=42,
        channel=channel,
        data={
            "type": "rpc",
            "method": method,
            "request": payload or {},
            "status": {"code": "sent"},
            "response": {},
        },
        attachments=[],
    )
    return MessageCreateEvent(channel=channel, message=message)


def _make_response_event(
    status: dict,
    response: dict | None = None,
    message_id: int = 100,
    channel_name: str = "test_channel",
) -> MessageUpdateEvent:
    channel = _make_channel(channel_name)
    message = Message(
        id=message_id,
        author_id=99,
        channel=channel,
        data={"status": status, "response": response or {}},
        attachments=[],
    )
    return MessageUpdateEvent(
        channel=channel,
        author_id=99,
        organisation_id=1,
        message=message,
        request_data={},
    )


class FakeApp:
    def __init__(self, app_key: str = "test_app"):
        self.app_key = app_key
        self.callbacks = {}
        self.messages = {}
        self.next_id = 1000

    def add_event_callback(self, channel_name, callback, events):
        del events
        self.callbacks.setdefault(channel_name, []).append(callback)

    async def create_message(self, channel_name, data, **kwargs):
        del kwargs
        message_id = self.next_id
        self.next_id += 1
        self.messages[message_id] = {"channel": channel_name, "data": data}
        return message_id

    async def update_message(self, channel_name, message_id, data, **kwargs):
        del kwargs
        self.messages.setdefault(message_id, {"channel": channel_name, "data": {}})
        self.messages[message_id]["data"] = data
        return Message(
            id=message_id,
            author_id=0,
            channel=_make_channel(channel_name),
            data=data,
            attachments=[],
        )

    async def fire_event(self, channel_name: str, event):
        for callback in self.callbacks.get(channel_name, []):
            await callback(event)


class TestHandlerDecorator:
    def test_sets_attributes(self):
        @handler("reboot")
        async def my_handler(self, ctx, payload):
            del ctx, payload

        assert my_handler._is_rpc_handler is True
        assert my_handler._rpc_method == "reboot"
        assert my_handler._rpc_channel is None

    def test_sets_channel_and_parser(self):
        parser = object()

        @handler("status", channel="control", parser=parser)
        async def my_handler(self, ctx, payload):
            del ctx, payload

        assert my_handler._rpc_channel == "control"
        assert my_handler._rpc_parser is parser


class TestRPCContext:
    @pytest.mark.asyncio
    async def test_acknowledge_updates_message_with_status(self):
        updates = []

        async def update_fn(channel_name, message_id, data):
            updates.append((channel_name, message_id, data))

        ctx = RPCContext(
            method="slow_op",
            message=Message(
                id=55,
                author_id=10,
                channel=_make_channel("control"),
                data={"type": "rpc", "method": "slow_op", "request": {}},
                attachments=[],
            ),
            _update_fn=update_fn,
        )

        await ctx.acknowledge()

        assert updates == [
            (
                "control",
                55,
                {
                    "type": "rpc",
                    "method": "slow_op",
                    "request": {},
                    "status": {
                        "code": "acknowledged",
                        "message": {"timestamp": pytest.approx(updates[0][2]["status"]["message"]["timestamp"])},
                    },
                    "response": {},
                },
            ),
        ]

    @pytest.mark.asyncio
    async def test_defer_sets_until_and_at_timestamps(self):
        updates = []

        async def update_fn(channel_name, message_id, data):
            updates.append((channel_name, message_id, data))

        ctx = RPCContext(
            method="slow_op",
            message=Message(
                id=55,
                author_id=10,
                channel=_make_channel("control"),
                data={"type": "rpc", "method": "slow_op", "request": {}},
                attachments=[],
            ),
            _update_fn=update_fn,
        )

        await ctx.defer(5)

        status = updates[0][2]["status"]
        assert status["code"] == "deferred"
        assert isinstance(status["message"]["until"], int)
        assert isinstance(status["message"]["at"], int)
        assert status["message"]["until"] >= status["message"]["at"]


class TestRegisterHandlers:
    def test_discovers_string_and_regex_handlers(self):
        class HandlerSet:
            @handler("do_thing")
            async def do_thing(self, ctx, payload):
                del ctx, payload

            @handler(re.compile(r"^get_.*$"), channel="control")
            async def get_anything(self, ctx, payload):
                del ctx, payload

        manager = RPCManager(FakeApp())
        manager.register_handlers(HandlerSet())

        assert (None, "do_thing") in manager._handlers
        assert manager._re_handlers[0][0] == "control"


class TestRPCManagerIntegration:
    @pytest.mark.asyncio
    async def test_request_handler_response(self):
        app = FakeApp()
        manager = RPCManager(app)
        calls = []

        class HandlerSet:
            @handler("ping", channel="test_channel")
            async def ping(self, ctx, payload):
                calls.append((ctx.channel.name, payload))
                return {"pong": True}

        manager.register_handlers(HandlerSet())
        await app.fire_event("test_channel", _make_request_event("ping", {"x": 1}))

        assert calls == [("test_channel", {"x": 1})]
        assert app.messages[100]["data"] == {
            "type": "rpc",
            "method": "ping",
            "request": {"x": 1},
            "status": {"code": "success"},
            "response": {"pong": True},
        }

    @pytest.mark.asyncio
    async def test_handler_rpc_error(self):
        app = FakeApp()
        manager = RPCManager(app)

        class HandlerSet:
            @handler("check", channel="test_channel")
            async def check(self, ctx, payload):
                del ctx, payload
                raise RPCError("OFFLINE", "Device is offline")

        manager.register_handlers(HandlerSet())
        await app.fire_event("test_channel", _make_request_event("check"))

        assert app.messages[100]["data"] == {
            "type": "rpc",
            "method": "check",
            "request": {},
            "status": {
                "code": "error",
                "message": {
                    "code": "OFFLINE",
                    "message": "Device is offline",
                },
            },
            "response": {},
        }

    @pytest.mark.asyncio
    async def test_handler_unhandled_exception(self):
        app = FakeApp()
        manager = RPCManager(app)

        class HandlerSet:
            @handler("boom", channel="test_channel")
            async def boom(self, ctx, payload):
                del ctx, payload
                raise ValueError("something broke")

        manager.register_handlers(HandlerSet())
        await app.fire_event("test_channel", _make_request_event("boom"))

        status = app.messages[100]["data"]["status"]
        assert status["code"] == "error"
        assert status["message"]["code"] == "INTERNAL_ERROR"
        assert "something broke" in status["message"]["message"]

    @pytest.mark.asyncio
    async def test_call_resolves_on_response(self):
        app = FakeApp()
        manager = RPCManager(app)

        async def do_call():
            return await manager.call(
                "ping", params={"x": 1}, channel="test_channel", timeout=1.0
            )

        task = asyncio.create_task(do_call())
        await asyncio.sleep(0)

        assert 1000 in manager._pending_calls
        assert app.messages[1000]["data"] == {
            "type": "rpc",
            "method": "ping",
            "request": {"x": 1},
            "status": {"code": "sent"},
            "response": {},
            "app_key": "test_app",
        }

        await app.fire_event(
            "test_channel",
            _make_response_event(
                {"code": "success"},
                {"pong": True},
                message_id=1000,
            ),
        )

        assert await task == {"pong": True}
        assert 1000 not in manager._pending_calls

    @pytest.mark.asyncio
    async def test_call_timeout(self):
        manager = RPCManager(FakeApp())

        with pytest.raises(RPCTimeoutError):
            await manager.call("slow", channel="test_channel", timeout=0.01)

    @pytest.mark.asyncio
    async def test_call_rpc_error_response(self):
        app = FakeApp()
        manager = RPCManager(app)

        task = asyncio.create_task(
            manager.call("fail", channel="test_channel", timeout=1.0)
        )
        await asyncio.sleep(0)

        await app.fire_event(
            "test_channel",
            _make_response_event(
                {"code": "error", "message": {"code": "BAD", "message": "nope"}},
                message_id=1000,
            ),
        )

        with pytest.raises(RPCError, match="BAD"):
            await task

    @pytest.mark.asyncio
    async def test_non_rpc_messages_are_ignored(self):
        app = FakeApp()
        manager = RPCManager(app)
        manager.subscribe("test_channel")

        message = Message(
            id=200,
            author_id=1,
            channel=_make_channel("test_channel"),
            data={"normal": "message"},
            attachments=[],
        )
        event = MessageCreateEvent(channel=_make_channel("test_channel"), message=message)

        await app.fire_event("test_channel", event)

        assert 200 not in app.messages

    @pytest.mark.asyncio
    async def test_acknowledge_does_not_resolve_future(self):
        app = FakeApp()
        manager = RPCManager(app)

        task = asyncio.create_task(
            manager.call("slow_op", channel="test_channel", timeout=0.5)
        )
        await asyncio.sleep(0)

        await app.fire_event(
            "test_channel",
            _make_response_event(
                {"code": "acknowledged", "message": {"timestamp": 123}},
                message_id=1000,
            ),
        )

        assert not manager._pending_calls[1000].done()

        await app.fire_event(
            "test_channel",
            _make_response_event(
                {"code": "success"},
                {"done": True},
                message_id=1000,
            ),
        )

        assert await task == {"done": True}

    @pytest.mark.asyncio
    async def test_channel_scoped_handler(self):
        app = FakeApp()
        manager = RPCManager(app)
        calls = []

        class HandlerSet:
            @handler("ping", channel="control")
            async def ping(self, ctx, payload):
                del payload
                calls.append(ctx.channel.name)
                return {}

        manager.register_handlers(HandlerSet())
        manager.subscribe("other")

        await app.fire_event("control", _make_request_event("ping", channel_name="control"))
        await app.fire_event("other", _make_request_event("ping", channel_name="other"))

        assert calls == ["control"]
