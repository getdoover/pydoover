import asyncio
import types

import pytest

from pydoover.docker.application import Application as DockerApplication
from pydoover.tags import BoundTag, NotSet, Tag, Tags
from pydoover.tags.manager import FASTMODE_CHANNEL_NAME, TAG_CHANNEL_NAME, KeyPath, TagsManagerDocker


class FakeTagsManager:
    def __init__(self, initial: dict | None = None):
        self.values = dict(initial or {})
        self.get_calls = []
        self.set_calls = []

    def get_tag(self, key, default=None, app_key=None, raise_key_error=False):
        del raise_key_error
        self.get_calls.append((key, default, app_key))
        return self.values.get((app_key, key), default)

    async def set_tag(self, key, value, app_key=None, **kwargs):
        del kwargs
        self.set_calls.append((key, value, app_key))
        self.values[(app_key, key)] = value


class FakeTagClient:
    def __init__(self, aggregates: dict | None = None):
        self.event_callbacks = []
        self.aggregate_updates = []
        self.messages = []
        self.aggregates = dict(aggregates or {})

    def add_event_callback(self, channel_name, callback, events):
        self.event_callbacks.append((channel_name, callback, events))

    async def wait_for_channels_sync(self, channel_names=None, timeout=None):
        del channel_names, timeout
        return True

    async def fetch_channel_aggregate(self, channel_name):
        return types.SimpleNamespace(data=self.aggregates.get(channel_name, {}))

    async def update_channel_aggregate(self, channel_name, data, max_age_secs=None, **kwargs):
        self.aggregate_updates.append((channel_name, data, max_age_secs, kwargs))
        self.aggregates[channel_name] = data

    async def create_message(self, channel_name, data, **kwargs):
        del kwargs
        self.messages.append((channel_name, data))
        return len(self.messages)


class FakeRuntimeDeviceAgent(FakeTagClient):
    def __init__(self, app_key: str = "test_app"):
        super().__init__(
            {
                "deployment_config": {"applications": {app_key: {}}},
                "ui_state": {},
                "ui_cmds": {},
                TAG_CHANNEL_NAME: {},
                FASTMODE_CHANNEL_NAME: {},
            }
        )
        self.app_key = app_key
        self.agent_id = None
        self.uri = ""
        self.subscriptions = {}

    def has_persistent_connection(self):
        return True

    async def wait_until_healthy(self, timeout):
        del timeout
        return True

    def add_event_callback(self, channel_name, callback, events):
        self.subscriptions[channel_name] = callback
        super().add_event_callback(channel_name, callback, events)

    async def close(self):
        return None

    def get_is_dda_available(self):
        return True

    def get_is_dda_online(self):
        return True

    def get_has_dda_been_online(self):
        return True


class FakeRuntimePlatformInterface:
    def __init__(self, app_key="test_app", uri="", is_async=False):
        self.app_key = app_key
        self.uri = uri
        self._is_async = is_async

    async def close(self):
        return None


class FakeRuntimeModbusInterface:
    def __init__(self, app_key="test_app", uri="", is_async=False, config=None):
        self.app_key = app_key
        self.uri = uri
        self._is_async = is_async
        self.config = config

    async def setup(self):
        return None

    async def close(self):
        return None


class FakeSchema:
    def __init__(self):
        self.injected = None
        self.some_flag = False

    def _inject_deployment_config(self, config):
        self.injected = config
        self.some_flag = bool(config.get("some_flag"))


class MyAppTags(Tags):
    voltage = Tag("number")
    speed = Tag("number", default=0)
    enabled = Tag("boolean", default=False)


class AsyncStartupTags(Tags):
    some_tag = Tag("string")


class AsyncStartupApp(DockerApplication):
    config_cls = FakeSchema
    tags_cls = AsyncStartupTags

    async def setup(self):
        await self.tags.some_tag.set("ready")

    async def main_loop(self):
        return None

    async def on_shutdown_at(self, dt):
        self.shutdown_events.append(dt)


def make_tags(
    manager: FakeTagsManager | None = None,
    config: FakeSchema | None = None,
    app_key: str = "test_app",
) -> MyAppTags:
    return MyAppTags(app_key, manager, config or FakeSchema())


class TestTags:
    def test_class_attributes_are_templates(self):
        assert isinstance(MyAppTags.voltage, Tag)
        assert isinstance(MyAppTags.speed, Tag)

    def test_instance_access_returns_bound_proxy(self):
        tags = make_tags(FakeTagsManager())

        assert isinstance(tags.voltage, BoundTag)
        assert tags.voltage.name == "voltage"
        assert tags.voltage.tag_type == "number"

    def test_get_uses_manager_with_app_key_scope(self):
        manager = FakeTagsManager({("test_app", "voltage"): 12.7})
        tags = make_tags(manager)

        assert tags.voltage.get() == 12.7
        assert manager.get_calls == [("voltage", NotSet, "test_app")]

    def test_get_returns_default_when_manager_has_no_value(self):
        tags = make_tags(FakeTagsManager())

        assert tags.speed.get() == 0
        assert tags.voltage.get() is NotSet

    @pytest.mark.asyncio
    async def test_set_uses_manager(self):
        manager = FakeTagsManager()
        tags = make_tags(manager)

        await tags.voltage.set(13.1)

        assert manager.set_calls == [("voltage", 13.1, "test_app")]
        assert manager.values[("test_app", "voltage")] == 13.1

    @pytest.mark.asyncio
    async def test_increment_and_decrement_use_manager(self):
        manager = FakeTagsManager({("test_app", "voltage"): 12.0})
        tags = make_tags(manager)

        assert await tags.voltage.increment() == 13.0
        assert await tags.voltage.decrement(0.5) == 12.5
        assert manager.values[("test_app", "voltage")] == 12.5

    @pytest.mark.asyncio
    async def test_setting_without_manager_raises(self):
        tags = make_tags(manager=None)

        with pytest.raises(RuntimeError, match="manager"):
            await tags.voltage.set(1.0)

    def test_add_and_remove_runtime_tags(self):
        tags = make_tags(FakeTagsManager())

        tags.add_tag("extra_sensor", Tag("number"))
        assert tags.get_tag("extra_sensor").tag_type == "number"

        tags.remove_tag("speed")

        assert tags.find_tag("speed") is None
        assert {tag.name for tag in tags} == {"voltage", "enabled", "extra_sensor"}

    @pytest.mark.asyncio
    async def test_setup_can_mutate_available_tags(self):
        class ConfiguredTags(MyAppTags):
            async def setup(self):
                self.remove_tag("enabled")
                if self.config.some_flag:
                    self.add_tag("extra_sensor", Tag("number"))

        config = FakeSchema()
        config._inject_deployment_config({"some_flag": True})
        tags = ConfiguredTags("test_app", FakeTagsManager(), config)

        await tags.setup()

        assert {tag.name for tag in tags} == {"voltage", "speed", "extra_sensor"}

    def test_to_schema_uses_declared_defaults(self):
        tags = make_tags(FakeTagsManager())

        assert tags.to_schema() == {
            "voltage": {"type": "number"},
            "speed": {"type": "number", "default": 0},
            "enabled": {"type": "boolean", "default": False},
        }


class TestKeyPath:
    def test_single_key_path(self):
        path = KeyPath("voltage")

        assert path.get() == ["voltage"]
        assert path.construct_dict(12.7) == {"voltage": 12.7}
        assert path.lookup_dict({"voltage": 12.7}) == 12.7

    def test_app_key_prefix_is_included(self):
        path = KeyPath("voltage", app_key="test_app")

        assert path.get() == ["test_app", "voltage"]
        assert path.construct_dict(12.7) == {"test_app": {"voltage": 12.7}}


class TestTagsManagerDocker:
    @pytest.mark.asyncio
    async def test_setup_registers_callbacks_and_loads_cached_aggregates(self):
        client = FakeTagClient(
            {
                TAG_CHANNEL_NAME: {"test_app": {"voltage": 12.3}},
                FASTMODE_CHANNEL_NAME: {"viewer": 1},
            }
        )
        manager = TagsManagerDocker(client=client)

        await manager.setup()

        channel_names = {entry[0] for entry in client.event_callbacks}
        assert channel_names == {TAG_CHANNEL_NAME, FASTMODE_CHANNEL_NAME}
        assert manager.get_tag("voltage", app_key="test_app") == 12.3

    @pytest.mark.asyncio
    async def test_subscriptions_fire_on_matching_tag_updates(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client)
        updates = []

        async def callback(key, value):
            updates.append((key, value))

        manager.subscribe_to_tag("voltage", callback, app_key="test_app")
        await manager._on_tag_update(
            types.SimpleNamespace(
                aggregate=types.SimpleNamespace(data={"test_app": {"voltage": 13.2}})
            )
        )

        assert updates == [("voltage", 13.2)]


class TestDockerApplicationStartup:
    def test_async_startup_sets_tags_through_tag_manager(self, monkeypatch):
        docker_application_module = pytest.importorskip("pydoover.docker.application")
        monkeypatch.setattr(docker_application_module, "RUN_HEALTHCHECK", False)

        async def run_test():
            device_agent = FakeRuntimeDeviceAgent()
            app = AsyncStartupApp(
                app_key="test_app",
                device_agent=device_agent,
                platform_iface=FakeRuntimePlatformInterface(is_async=True),
                modbus_iface=FakeRuntimeModbusInterface(is_async=True),
                test_mode=True,
                healthcheck_port=0,
            )
            app.shutdown_events = []

            task = asyncio.create_task(app._run())
            try:
                await app.wait_until_ready()
                await asyncio.sleep(0.05)

                assert app.tags.some_tag.get() == "ready"
                assert app.tag_manager._pending_tag_aggregate == {
                    "test_app": {"some_tag": "ready"}
                }
            finally:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task

        asyncio.run(run_test())
