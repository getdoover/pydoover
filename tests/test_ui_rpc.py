"""End-to-end test (and worked example) of UI command RPC between two local apps.

Two docker apps run side by side, sharing the ``ui_cmds`` channel:

- ``PumpApp`` (app_key="my_other_app") declares a ``set_pump_mode`` interaction
  and a ``@ui.handler`` for it.
- ``ControllerApp`` calls ``self.ui_manager.call("set_pump_mode", "on",
  app_key="my_other_app")`` and waits for the response.

The flow over the channel:

1. Caller creates a message on ``ui_cmds``:
   ``{"type": "rpc", "method": "set_pump_mode", "request": "on",
     "app_key": "my_other_app", "status": {"code": "sent"}}``
2. Every app subscribed to ``ui_cmds`` sees the message; only the app whose
   ``app_key`` matches dispatches it to its handler.
3. The handler's return value is written back as a *message update*:
   ``{"status": {"code": "success"}, "response": {...}}``.
4. The caller sees the update, matches it to its pending call by message id,
   and ``call()`` returns the response.
5. Because the handler was registered with ``auto_update=True`` (the default),
   the target app also writes the new value into its ``ui_cmds`` aggregate.

``SharedChannelBus`` below plays the role of the cloud: it assigns message ids
and fans events out to every connected device agent.
"""

import asyncio

import pytest

from pydoover import ui
from pydoover.models import EventSubscription
from pydoover.models.data import (
    ChannelID,
    Message,
    MessageCreateEvent,
    MessageUpdateEvent,
)
from pydoover.rpc import RPCTimeoutError

from tests.test_tags import (
    FakeRuntimeDeviceAgent,
    FakeRuntimeModbusInterface,
    FakeRuntimePlatformInterface,
    FakeSchema,
)

docker_application = pytest.importorskip("pydoover.docker.application")


class SharedChannelBus:
    """A stand-in for the cloud: routes channel messages between agents.

    Delivery is scheduled on the event loop rather than done inline, matching
    the real system where a response can only arrive after ``call()`` has
    registered its pending future.
    """

    def __init__(self):
        self.agents: list["BusDeviceAgent"] = []
        self.messages: dict[int, Message] = {}
        self.next_id = 1000

    async def create_message(self, channel_name, data):
        message_id = self.next_id
        self.next_id += 1
        channel = ChannelID(agent_id=1, name=channel_name)
        message = Message(
            id=message_id,
            author_id=1,
            channel=channel,
            data=dict(data),
            attachments=[],
        )
        self.messages[message_id] = message
        self._deliver(
            channel_name,
            MessageCreateEvent(channel=channel, message=message),
            EventSubscription.message_create,
        )
        return message_id

    async def update_message(self, channel_name, message_id, data):
        channel = ChannelID(agent_id=1, name=channel_name)
        existing = self.messages.get(message_id)
        merged = {**(existing.data if existing else {}), **data}
        message = Message(
            id=message_id,
            author_id=1,
            channel=channel,
            data=merged,
            attachments=[],
        )
        self.messages[message_id] = message
        self._deliver(
            channel_name,
            MessageUpdateEvent(
                channel=channel,
                author_id=1,
                organisation_id=1,
                message=message,
                request_data=data,
            ),
            EventSubscription.message_update,
        )
        return message

    def _deliver(self, channel_name, event, kind):
        loop = asyncio.get_running_loop()
        for agent in self.agents:
            for cb_channel, callback, events in agent.event_callbacks:
                if cb_channel == channel_name and kind in events:
                    loop.create_task(callback(event))


class BusDeviceAgent(FakeRuntimeDeviceAgent):
    """A fake device agent whose messages go through the shared bus."""

    def __init__(self, bus: SharedChannelBus, app_key: str):
        super().__init__(app_key=app_key)
        self.bus = bus
        bus.agents.append(self)

    async def create_message(self, channel_name, data, **kwargs):
        return await self.bus.create_message(channel_name, data)

    async def update_message(self, channel_name, message_id, data, **kwargs):
        return await self.bus.update_message(channel_name, message_id, data)


class PumpUI(ui.UI):
    pump_mode = ui.Select(
        "Pump Mode",
        name="set_pump_mode",
        options=[ui.Option("on"), ui.Option("off")],
    )


class PumpApp(docker_application.Application):
    """The app that owns the ``set_pump_mode`` command."""

    config_cls = FakeSchema
    ui_cls = PumpUI

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modes_received = []

    async def setup(self):
        return None

    async def main_loop(self):
        return None

    @ui.handler("set_pump_mode")
    async def set_pump_mode(self, ctx, payload):
        self.modes_received.append(payload)
        return {"mode": payload}


class ControllerApp(docker_application.Application):
    """The app that sends the command to PumpApp."""

    config_cls = FakeSchema

    async def setup(self):
        return None

    async def main_loop(self):
        return None

    async def turn_pump_on(self):
        return await self.ui_manager.call(
            "set_pump_mode", "on", app_key="my_other_app", timeout=1.0
        )


async def make_apps(monkeypatch):
    monkeypatch.setattr(docker_application, "RUN_HEALTHCHECK", False)
    bus = SharedChannelBus()

    pump_app = PumpApp(
        app_key="my_other_app",
        device_agent=BusDeviceAgent(bus, "my_other_app"),
        platform_iface=FakeRuntimePlatformInterface(is_async=True),
        modbus_iface=FakeRuntimeModbusInterface(is_async=True),
        test_mode=True,
        healthcheck_port=0,
    )
    controller_app = ControllerApp(
        app_key="controller",
        device_agent=BusDeviceAgent(bus, "controller"),
        platform_iface=FakeRuntimePlatformInterface(is_async=True),
        modbus_iface=FakeRuntimeModbusInterface(is_async=True),
        test_mode=True,
        healthcheck_port=0,
    )
    await pump_app._setup()
    await controller_app._setup()
    return pump_app, controller_app


class TestUICommandRPCBetweenApps:
    @pytest.mark.asyncio
    async def test_call_reaches_handler_and_returns_response(self, monkeypatch):
        pump_app, controller_app = await make_apps(monkeypatch)

        result = await controller_app.turn_pump_on()

        assert result == {"mode": "on"}
        assert pump_app.modes_received == ["on"]

    @pytest.mark.asyncio
    async def test_handler_auto_updates_target_apps_ui_cmds_aggregate(
        self, monkeypatch
    ):
        pump_app, controller_app = await make_apps(monkeypatch)

        await controller_app.turn_pump_on()
        # auto-update runs after the response is sent; let its tasks finish
        await asyncio.sleep(0)

        assert ("ui_cmds", {"my_other_app": {"set_pump_mode": "on"}}) in [
            (channel, data)
            for channel, data, *_ in pump_app.device_agent.aggregate_updates
        ]

    @pytest.mark.asyncio
    async def test_call_targeting_other_app_key_is_ignored(self, monkeypatch):
        pump_app, controller_app = await make_apps(monkeypatch)

        with pytest.raises(RPCTimeoutError):
            await controller_app.ui_manager.call(
                "set_pump_mode", "on", app_key="not_this_app", timeout=0.05
            )

        assert pump_app.modes_received == []
