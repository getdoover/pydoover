import asyncio
import re
from datetime import datetime, timedelta, timezone

import pytest

from pydoover.models.data import (
    ChannelID,
    Message,
    MessageCreateEvent,
    MessageUpdateEvent,
)
from pydoover.rpc import RPCContext, RPCError, RPCManager, RPCTimeoutError, handler
from pydoover.utils.snowflake import SnowflakeType, generate_snowflake_id_at


def _snowflake_at(dt: datetime) -> int:
    return generate_snowflake_id_at(dt, type_id=SnowflakeType.Message)


def _make_channel(name: str = "test_channel") -> ChannelID:
    return ChannelID(agent_id=1, name=name)


def _make_request_event(
    method: str,
    payload: dict | None = None,
    message_id: int = 100,
    channel_name: str = "test_channel",
    extra_data: dict | None = None,
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
            **(extra_data or {}),
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
            _handler=lambda ctx: None,
        )

        await ctx.acknowledge()

        assert len(updates) == 1
        assert updates[0][0] == "control"
        assert updates[0][1] == 55
        assert updates[0][2]["status"]["code"] == "acknowledged"
        assert isinstance(updates[0][2]["status"]["message"]["timestamp"], int)

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
            _handler=lambda ctx: None,
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
        assert app.messages[100]["data"]["status"] == {
            "code": "success",
            "message": None,
        }
        assert app.messages[100]["data"]["response"] == {"pong": True}

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

        status = app.messages[100]["data"]["status"]
        assert status["code"] == "error"
        assert status["message"]["code"] == "OFFLINE"
        assert status["message"]["message"] == "Device is offline"

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
        assert app.messages[1000]["data"]["method"] == "ping"
        assert app.messages[1000]["data"]["request"] == {"x": 1}
        assert app.messages[1000]["data"]["status"] == {"code": "sent"}

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
    async def test_call_fire_and_forget(self):
        app = FakeApp()
        manager = RPCManager(app)

        result = await manager.call(
            "notify",
            params={"x": 1},
            channel="test_channel",
            app_key="target_app",
            wait_for_response=False,
        )

        # Returns the sent message id immediately, registers no pending future,
        # and doesn't subscribe for a response it will never read.
        assert result == 1000
        assert manager._pending_calls == {}
        assert "test_channel" not in app.callbacks
        assert app.messages[1000]["data"]["method"] == "notify"
        assert app.messages[1000]["data"]["app_key"] == "target_app"

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
        event = MessageCreateEvent(
            channel=_make_channel("test_channel"), message=message
        )

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

        await app.fire_event(
            "control", _make_request_event("ping", channel_name="control")
        )
        await app.fire_event("other", _make_request_event("ping", channel_name="other"))

        assert calls == ["control"]


class TestCommandExpiry:
    @pytest.mark.asyncio
    async def test_expired_command_is_not_processed(self):
        app = FakeApp()
        manager = RPCManager(app)
        calls = []

        class HandlerSet:
            @handler("do_thing", channel="test_channel")
            async def do_thing(self, ctx, payload):
                calls.append(payload)
                return {}

        manager.register_handlers(HandlerSet())

        # message created 60s ago with a 30s lifetime -> already expired
        created_at = datetime.now(tz=timezone.utc) - timedelta(seconds=60)
        event = _make_request_event(
            "do_thing",
            {"x": 1},
            message_id=_snowflake_at(created_at),
            extra_data={"expires_after": 30_000},
        )
        await app.fire_event("test_channel", event)

        assert calls == []
        # the handler never ran, so no response status was written
        assert event.message.id not in app.messages

    @pytest.mark.asyncio
    async def test_unexpired_command_is_processed(self):
        app = FakeApp()
        manager = RPCManager(app)
        calls = []

        class HandlerSet:
            @handler("do_thing", channel="test_channel")
            async def do_thing(self, ctx, payload):
                calls.append(payload)
                return {"ok": True}

        manager.register_handlers(HandlerSet())

        # message created just now with a generous lifetime -> still valid
        created_at = datetime.now(tz=timezone.utc)
        event = _make_request_event(
            "do_thing",
            {"x": 1},
            message_id=_snowflake_at(created_at),
            extra_data={"expires_after": 60_000},
        )
        await app.fire_event("test_channel", event)

        assert calls == [{"x": 1}]
        assert app.messages[event.message.id]["data"]["status"]["code"] == "success"

    @pytest.mark.asyncio
    async def test_command_without_expiry_is_processed(self):
        app = FakeApp()
        manager = RPCManager(app)
        calls = []

        class HandlerSet:
            @handler("do_thing", channel="test_channel")
            async def do_thing(self, ctx, payload):
                calls.append(payload)
                return {}

        manager.register_handlers(HandlerSet())

        created_at = datetime.now(tz=timezone.utc) - timedelta(days=1)
        event = _make_request_event(
            "do_thing", {"x": 1}, message_id=_snowflake_at(created_at)
        )
        await app.fire_event("test_channel", event)

        assert calls == [{"x": 1}]


class TestCommandAuditFields:
    @pytest.mark.asyncio
    async def test_context_exposes_actor_reason_and_old_value(self):
        app = FakeApp()
        manager = RPCManager(app)
        seen = {}

        actor = {"id": "u1", "name": "Ada", "email": "ada@example.com"}

        class HandlerSet:
            @handler("do_thing", channel="test_channel")
            async def do_thing(self, ctx, payload):
                seen["actor"] = ctx.actor
                seen["reason"] = ctx.reason
                seen["old_value"] = ctx.old_value
                seen["retry_of"] = ctx.retry_of
                seen["expires_after"] = ctx.expires_after
                seen["is_expired"] = ctx.is_expired
                return {}

        manager.register_handlers(HandlerSet())

        event = _make_request_event(
            "do_thing",
            {"x": 1},
            message_id=_snowflake_at(datetime.now(tz=timezone.utc)),
            extra_data={
                "actor": actor,
                "reason": "maintenance",
                "old_value": "off",
                "retry_of": "42",
                "expires_after": 60_000,
            },
        )
        await app.fire_event("test_channel", event)

        assert seen["actor"] == actor
        assert seen["reason"] == "maintenance"
        assert seen["old_value"] == "off"
        assert seen["retry_of"] == "42"
        assert seen["expires_after"] == 60_000
        assert seen["is_expired"] is False

    @pytest.mark.asyncio
    async def test_call_sends_audit_and_expiry_fields(self):
        app = FakeApp()
        manager = RPCManager(app)
        actor = {"id": "u1", "name": "Ada", "email": "ada@example.com"}

        task = asyncio.create_task(
            manager.call(
                "do_thing",
                params={"x": 1},
                channel="test_channel",
                actor=actor,
                reason="maintenance",
                old_value=None,
                expires_after=timedelta(seconds=30),
                retry_of="7",
                timeout=1.0,
            )
        )
        await asyncio.sleep(0)

        data = app.messages[1000]["data"]
        assert data["actor"] == actor
        assert data["reason"] == "maintenance"
        assert data["old_value"] is None
        assert data["expires_after"] == 30_000
        assert data["retry_of"] == "7"

        await app.fire_event(
            "test_channel",
            _make_response_event({"code": "success"}, {}, message_id=1000),
        )
        await task
