import asyncio
import importlib
import sys
import types

import pytest

from pydoover.tags import BoundTag, NotSet, Tag, Tags
from pydoover.tags.manager import TAG_CHANNEL_NAME, KeyPath, TagsManagerDocker


def _load_docker_application_class():
    for module_name, class_names in (
        (
            "pydoover.docker.device_agent",
            ["DeviceAgentInterface", "MockDeviceAgentInterface"],
        ),
        (
            "pydoover.docker.modbus",
            ["ModbusInterface", "ModbusConfig", "ManyModbusConfig"],
        ),
        (
            "pydoover.docker.platform",
            ["PlatformInterface", "PulseCounter"],
        ),
    ):
        if module_name not in sys.modules:
            module = types.ModuleType(module_name)
            for class_name in class_names:
                setattr(module, class_name, type(class_name, (), {}))
            sys.modules[module_name] = module

    return importlib.import_module("pydoover.docker.application").Application


DockerApplication = _load_docker_application_class()


def _load_processor_application_class():
    if "pydoover.cloud.processor.data_client" not in sys.modules:
        module = types.ModuleType("pydoover.cloud.processor.data_client")
        module.DooverData = type("DooverData", (), {})
        module.ConnectionDetermination = type("ConnectionDetermination", (), {})
        module.ConnectionStatus = type(
            "ConnectionStatus",
            (),
            {"periodic_unknown": object()},
        )
        sys.modules["pydoover.cloud.processor.data_client"] = module

    if "pydoover.cloud.processor.types" not in sys.modules:
        module = types.ModuleType("pydoover.cloud.processor.types")
        for class_name in (
            "ManualInvokeEvent",
            "MessageCreateEvent",
            "Channel",
            "Message",
            "DeploymentEvent",
            "ScheduleEvent",
            "IngestionEndpointEvent",
            "ConnectionConfig",
            "AggregateUpdateEvent",
            "DooverConnectionStatus",
        ):
            setattr(module, class_name, type(class_name, (), {}))
        sys.modules["pydoover.cloud.processor.types"] = module

    return importlib.import_module("pydoover.cloud.processor.application").Application


ProcessorApplication = _load_processor_application_class()


class FakeTagsManager:
    _is_async = False

    def __init__(self, initial=None):
        self.values = initial or {}
        self.get_calls = []
        self.set_calls = []

    def get_tag(self, key, default=None, app_key=None):
        self.get_calls.append((key, default, app_key))
        return self.values.get(key, default)

    def set_tag(self, key, value, app_key=None):
        self.set_calls.append((key, value, app_key))
        self.values[key] = value


class AsyncFakeTagsManager(FakeTagsManager):
    _is_async = True

    async def set_tag_async(self, key, value, app_key=None):
        self.set_calls.append((key, value, app_key))
        self.values[key] = value


class FakeTagClient:
    def __init__(self):
        self.subscriptions = []
        self.sync_publishes = []
        self.async_publishes = []

    def add_subscription(self, channel_name, callback):
        self.subscriptions.append((channel_name, callback))

    def publish_to_channel(self, channel_name, payload, max_age=None, record_log=None):
        self.sync_publishes.append(
            {
                "channel_name": channel_name,
                "payload": payload,
                "max_age": max_age,
                "record_log": record_log,
            }
        )

    async def publish_to_channel_async(
        self, channel_name, payload, max_age=None, record_log=None
    ):
        self.async_publishes.append(
            {
                "channel_name": channel_name,
                "payload": payload,
                "max_age": max_age,
                "record_log": record_log,
            }
        )


class FakeRuntimeDeviceAgent:
    def __init__(self, app_key="test_app"):
        self.app_key = app_key
        self.agent_id = None
        self.uri = ""
        self.subscriptions = {}
        self.sync_publishes = []
        self.async_publishes = []

    def has_persistent_connection(self):
        return True

    async def await_dda_available_async(self, timeout):
        return True

    def add_subscription(self, channel_name, callback):
        self.subscriptions[channel_name] = callback

    async def wait_for_channels_sync_async(self, channel_names=None, timeout=None):
        if channel_names and "deployment_config" in channel_names:
            callback = self.subscriptions.get("deployment_config")
            if callback is not None:
                await callback(
                    "deployment_config",
                    {"applications": {self.app_key: {}}},
                )
        return True

    def publish_to_channel(self, channel_name, payload, max_age=None, record_log=None):
        self.sync_publishes.append(
            (channel_name, payload, max_age, record_log)
        )

    async def publish_to_channel_async(
        self, channel_name, payload, max_age=None, record_log=None
    ):
        self.async_publishes.append(
            (channel_name, payload, max_age, record_log)
        )

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


class FakeDockerAppTagManager:
    def __init__(self):
        self.get_calls = []
        self.set_calls = []
        self.set_tags_calls = []
        self.subscribe_calls = []
        self.values = {}

    def get_tag(self, key, default=None, app_key=None, **kwargs):
        self.get_calls.append((key, default, app_key, kwargs))
        if app_key is None:
            return self.values.get(key, default)
        return self.values.get((app_key, key), default)

    def set_tag(self, key, value, app_key=None, only_if_changed=True, **kwargs):
        self.set_calls.append((key, value, app_key, only_if_changed, kwargs))
        if app_key is None:
            self.values[key] = value
        else:
            self.values[(app_key, key)] = value

    async def set_tag_async(
        self, key, value, app_key=None, only_if_changed=True, **kwargs
    ):
        self.set_tag(
            key,
            value,
            app_key=app_key,
            only_if_changed=only_if_changed,
            **kwargs,
        )

    def set_tags(self, tags, app_key=None, only_if_changed=True, **kwargs):
        self.set_tags_calls.append((tags, app_key, only_if_changed, kwargs))

    async def set_tags_async(self, tags, app_key=None, only_if_changed=True, **kwargs):
        self.set_tags(tags, app_key=app_key, only_if_changed=only_if_changed, **kwargs)

    def subscribe_to_tag(self, key, callback, app_key=None, **kwargs):
        self.subscribe_calls.append((key, callback, app_key, kwargs))


class FakeSchema:
    def __init__(self):
        self.injected = None
        self.some_flag = False

    def _inject_deployment_config(self, config):
        self.injected = config
        self.some_flag = bool(config.get("some_flag"))


class FakeProcessorTagManager:
    _is_async = True

    def __init__(self):
        self.registered_tags = None



def make_docker_app(tag_manager=None, app_key="test_app", is_async=False):
    app_cls = type("ConfiguredDockerApplication", (DockerApplication,), {})
    app = object.__new__(app_cls)
    app.app_key = app_key
    app.tag_manager = tag_manager or FakeDockerAppTagManager()
    app._is_async = is_async
    app.config = FakeSchema()
    app.tags = None
    return app


def make_processor_app(config=None, tags_class=None, tag_manager=None):
    app_cls = type(
        "ConfiguredProcessorApplication",
        (ProcessorApplication,),
        {"tags_class": tags_class},
    )
    app = object.__new__(app_cls)
    app.config = config
    app.tags = None
    app.tag_manager = tag_manager or FakeProcessorTagManager()
    return app


def resolve_tags(app):
    return asyncio.run(app._resolve_tags())


class MyAppTags(Tags):
    voltage = Tag("number")
    speed = Tag("number", default=0)
    enabled = Tag("boolean", default=False)


class AsyncStartupTags(Tags):
    some_tag = Tag("string")


class AsyncStartupApp(DockerApplication):
    config_class = FakeSchema
    tags_class = AsyncStartupTags

    async def setup(self):
        self.setup_tag_manager_is_async = self.tag_manager._is_async
        await self.tags.some_tag.set("ready")

    async def main_loop(self):
        return None

    async def on_shutdown_at(self, dt):
        self.shutdown_events.append(dt)


class TestTags:
    def test_class_attributes_are_templates(self):
        assert isinstance(MyAppTags.voltage, Tag)
        assert isinstance(MyAppTags.speed, Tag)

    def test_instance_access_returns_bound_proxy(self):
        tags = MyAppTags()

        assert isinstance(tags.voltage, BoundTag)
        assert tags.voltage.name == "voltage"
        assert tags.voltage.tag_type == "number"

    def test_get_uses_manager(self):
        manager = FakeTagsManager({"voltage": 12.7})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.voltage.get() == 12.7
        assert manager.get_calls == [("voltage", NotSet, None)]

    def test_get_returns_default_when_manager_has_no_value(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.speed.get() == 0
        assert tags.voltage.get() is NotSet

    def test_set_uses_manager(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        tags.voltage.set(13.1)

        assert manager.set_calls == [("voltage", 13.1, None)]
        assert manager.values["voltage"] == 13.1

    def test_assignment_still_sets_via_manager(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        tags.voltage = 10.5

        assert manager.values["voltage"] == 10.5

    def test_increment_and_decrement_use_manager(self):
        manager = FakeTagsManager({"voltage": 12.0})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.voltage.increment() == 13.0
        assert tags.voltage.decrement(0.5) == 12.5
        assert manager.values["voltage"] == 12.5

    def test_increment_non_numeric_tag_raises(self):
        manager = FakeTagsManager({"enabled": True})
        tags = MyAppTags()
        tags.register_manager(manager)

        with pytest.raises(TypeError):
            tags.enabled.increment()

    def test_to_dict_reads_all_declared_tags_from_manager(self):
        manager = FakeTagsManager({"voltage": 12.7})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.to_dict() == {"voltage": 12.7, "speed": 0, "enabled": False}

    def test_get_tag_returns_bound_tag(self):
        manager = FakeTagsManager({"voltage": 12.4})
        tags = MyAppTags()
        tags.register_manager(manager)

        voltage = tags.get_tag("voltage")
        assert isinstance(voltage, BoundTag)
        assert voltage.get() == 12.4

    def test_get_definition_returns_declared_tag_definition(self):
        tags = MyAppTags()

        voltage = tags.get_definition("voltage")
        assert isinstance(voltage, Tag)
        assert voltage.name is None
        assert voltage.tag_type == "number"

    def test_add_tag_adds_runtime_tag(self):
        tags = MyAppTags()

        tags.add_tag("extra_sensor", Tag("number"))

        assert tags.get_tag("extra_sensor") is not None
        assert tags.get_definition("extra_sensor").tag_type == "number"
        assert {tag.name for tag in tags} == {
            "voltage",
            "speed",
            "enabled",
            "extra_sensor",
        }

    def test_remove_tag_removes_runtime_tag(self):
        tags = MyAppTags()

        tags.remove_tag("speed")

        assert tags.get_tag("speed") is None
        assert tags.get_definition("speed") is None
        assert {tag.name for tag in tags} == {"voltage", "enabled"}

    def test_setting_without_manager_raises(self):
        tags = MyAppTags()

        with pytest.raises(RuntimeError):
            tags.voltage.set(1.0)

    def test_value_like_dunders(self):
        manager = FakeTagsManager({"voltage": 12.7, "enabled": True})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert str(tags.voltage) == "12.7"
        assert float(tags.voltage) == 12.7
        assert int(tags.speed) == 0
        assert bool(tags.enabled) is True
        assert tags.voltage > 10
        assert tags.voltage >= 12.7
        assert tags.voltage == 12.7

    def test_async_set_uses_async_manager_path(self):
        import asyncio

        manager = AsyncFakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        asyncio.run(tags.voltage.set(14.2))

        assert manager.values["voltage"] == 14.2
        assert manager.set_calls == [("voltage", 14.2, None)]

    def test_async_increment_uses_async_manager_path(self):
        import asyncio

        manager = AsyncFakeTagsManager({"voltage": 11.0})
        tags = MyAppTags()
        tags.register_manager(manager)

        new_value = asyncio.run(tags.voltage.increment(2.5))

        assert new_value == 13.5
        assert manager.values["voltage"] == 13.5


class TestKeyPath:
    def test_single_key_path(self):
        path = KeyPath("voltage")

        assert path.get() == ["voltage"]
        assert path.construct_dict(12.7) == {"voltage": 12.7}
        assert path.lookup_dict({"voltage": 12.7}) == 12.7

    def test_list_key_path(self):
        path = KeyPath(["metrics", "voltage"])

        assert path.get() == ["metrics", "voltage"]
        assert path.construct_dict(12.7) == {"metrics": {"voltage": 12.7}}
        assert path.lookup_dict({"metrics": {"voltage": 12.7}}) == 12.7

    def test_app_key_is_prepended(self):
        path = KeyPath("voltage", app_key="my_app")

        assert path.get() == ["my_app", "voltage"]
        assert path.construct_dict(12.7) == {"my_app": {"voltage": 12.7}}
        assert path.lookup_dict({"my_app": {"voltage": 12.7}}) == 12.7

    def test_lookup_missing_returns_none(self):
        path = KeyPath(["metrics", "voltage"])

        assert path.lookup_dict({"metrics": {}}) is None
        assert path.lookup_dict({"metrics": 1}) is None

    def test_in_dict(self):
        path = KeyPath(["metrics", "voltage"])

        assert path.in_dict({"metrics": {"voltage": 12.7}}) is True
        assert path.in_dict({"metrics": {}}) is False
        assert path.in_dict({"metrics": 1}) is False

    def test_invalid_path_raises(self):
        with pytest.raises(ValueError):
            KeyPath([])

        with pytest.raises(ValueError):
            KeyPath(["valid", ""])
            
    def test_equality(self):
        assert KeyPath("voltage") == ["voltage"]
        assert KeyPath(["metrics", "voltage"]) == ["metrics", "voltage"]
        assert KeyPath("voltage") == "voltage"
        assert not KeyPath(["metrics", "voltage"]) == "metrics.voltage"
        assert KeyPath("voltage") == KeyPath(["voltage"])
        assert KeyPath(["metrics", "voltage"]) == KeyPath(["metrics", "voltage"])
        
    def test_dict(self):
        tags_dict = {
            KeyPath("voltage"): 1,
            KeyPath(["metrics", "voltage"]): 2,
        }
        assert KeyPath("voltage") in tags_dict
        assert KeyPath(["metrics", "voltage"]) in tags_dict
        assert tags_dict[KeyPath("voltage")] == 1
        assert tags_dict[KeyPath(["metrics", "voltage"])] == 2


class TestTagsManagerDocker:
    def test_setup_registers_tag_subscription(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        manager.setup()

        assert len(client.subscriptions) == 1
        assert client.subscriptions[0][0] == TAG_CHANNEL_NAME

    def test_sync_set_tag_publishes_and_updates_local_state(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        manager.set_tag("voltage", 12.7)

        assert manager.get_tag("voltage") == 12.7
        assert client.sync_publishes == [
            {
                "channel_name": TAG_CHANNEL_NAME,
                "payload": {"voltage": 12.7},
                "max_age": 60 * 60,
                "record_log": True,
            }
        ]

    def test_sync_set_tag_skips_publish_when_unchanged(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        manager.set_tag("voltage", 12.7)
        manager.set_tag("voltage", 12.7)

        assert len(client.sync_publishes) == 1

    def test_sync_set_tag_with_app_key_builds_nested_payload(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        manager.set_tag("voltage", 12.7, app_key="my_app")

        assert manager.get_tag("voltage", app_key="my_app") == 12.7
        assert client.sync_publishes[-1]["payload"] == {"my_app": {"voltage": 12.7}}

    def test_get_tag_raise_key_error(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        with pytest.raises(KeyError):
            manager.get_tag("missing", raise_key_error=True)

    def test_async_set_tag_uses_async_publish_path(self):
        import asyncio

        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=True)

        asyncio.run(manager.set_tag("voltage", 12.7))

        assert manager.get_tag("voltage") == 12.7
        assert client.async_publishes == [
            {
                "channel_name": TAG_CHANNEL_NAME,
                "payload": {"voltage": 12.7},
                "max_age": 60 * 60,
                "record_log": True,
            }
        ]
        assert client.sync_publishes == []

    def test_on_tag_update_updates_state_and_invokes_subscription(self):
        import asyncio

        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)
        received = []

        def callback(key, value):
            received.append((key, value))

        manager.subscribe_to_tag(["metrics", "voltage"], callback)

        asyncio.run(
            manager._on_tag_update(
                TAG_CHANNEL_NAME,
                {"metrics": {"voltage": 12.7, "current": 4.1}},
            )
        )

        assert manager.get_tag(["metrics", "voltage"]) == 12.7
        assert manager._tag_ready.is_set() is True
        assert received == [(["metrics", "voltage"], 12.7)]

    def test_await_tags_ready_waits_for_first_update(self):
        import asyncio

        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        async def run_test():
            waiter = asyncio.create_task(manager.await_tags_ready())
            await asyncio.sleep(0)
            assert waiter.done() is False

            await manager._on_tag_update(TAG_CHANNEL_NAME, {"voltage": 12.7})
            await waiter

            assert manager._tag_ready.is_set() is True
            assert manager.get_tag("voltage") == 12.7

        asyncio.run(run_test())

    def test_await_tags_ready_works_with_asyncio_wait_for(self):
        import asyncio

        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        async def run_test():
            async def publish_later():
                await asyncio.sleep(0.01)
                await manager._on_tag_update(TAG_CHANNEL_NAME, {"voltage": 12.7})

            publisher = asyncio.create_task(publish_later())
            await asyncio.wait_for(manager.await_tags_ready(), timeout=10.0)
            await publisher

            assert manager._tag_ready.is_set() is True
            assert manager.get_tag("voltage") == 12.7

        asyncio.run(run_test())

    def test_await_tags_ready_wait_for_times_out_when_no_update_arrives(self):
        import asyncio

        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)

        async def run_test():
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(manager.await_tags_ready(), timeout=0.01)

            assert manager._tag_ready.is_set() is False

        asyncio.run(run_test())

    def test_tags_object_works_with_sync_docker_tag_manager(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=False)
        tags = MyAppTags()
        tags.register_manager(manager)

        tags.voltage.set(12.7)

        assert tags.voltage.get() == 12.7
        assert tags.voltage > 10
        assert client.sync_publishes[-1]["payload"] == {"voltage": 12.7}

    def test_tags_object_works_with_async_docker_tag_manager(self):
        import asyncio

        client = FakeTagClient()
        manager = TagsManagerDocker(client=client, is_async=True)
        tags = MyAppTags()
        tags.register_manager(manager)

        async def run_test():
            await tags.voltage.set(12.7)
            new_value = await tags.voltage.increment(0.3)

            assert new_value == 13.0
            assert tags.voltage.get() == 13.0
            assert tags.to_dict() == {"voltage": 13.0, "speed": 0, "enabled": False}

        asyncio.run(run_test())

        assert client.async_publishes[0]["payload"] == {"voltage": 12.7}
        assert client.async_publishes[1]["payload"] == {"voltage": 13.0}


class TestDockerApplicationTagMethods:
    def test_get_tag_defaults_to_current_app_key(self):
        manager = FakeDockerAppTagManager()
        manager.values[("test_app", "voltage")] = 12.7
        app = make_docker_app(tag_manager=manager)

        assert app.get_tag("voltage") == 12.7
        assert manager.get_calls == [("voltage", None, "test_app", {})]

    def test_get_tag_allows_explicit_app_key(self):
        manager = FakeDockerAppTagManager()
        manager.values[("other_app", "voltage")] = 8.4
        app = make_docker_app(tag_manager=manager)

        assert app.get_tag("voltage", app_key="other_app") == 8.4
        assert manager.get_calls == [("voltage", None, "other_app", {})]

    def test_get_global_tag_uses_none_app_key(self):
        manager = FakeDockerAppTagManager()
        manager.values["shutdown_requested"] = True
        app = make_docker_app(tag_manager=manager)

        assert app.get_global_tag("shutdown_requested") is True
        assert manager.get_calls == [("shutdown_requested", None, None, {})]

    def test_subscribe_to_tag_defaults_to_current_app_key(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager)

        def callback(key, value):
            return None

        app.subscribe_to_tag("voltage", callback)

        assert manager.subscribe_calls == [("voltage", callback, "test_app", {})]

    def test_subscribe_to_global_tag_uses_none_app_key(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager)

        def callback(key, value):
            return None

        app.subscribe_to_tag("shutdown_requested", callback, global_tag=True)

        assert manager.subscribe_calls == [("shutdown_requested", callback, None, {})]

    def test_sync_set_tag_routes_to_manager(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager, is_async=False)

        app.set_tag("voltage", 12.7)

        assert manager.set_calls == [("voltage", 12.7, None, True, {})]

    def test_async_set_tag_routes_to_manager_async(self):
        import asyncio

        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager, is_async=True)

        asyncio.run(app.set_tag("voltage", 12.7))

        assert manager.set_calls == [("voltage", 12.7, None, True, {})]

    def test_sync_set_tags_routes_to_manager(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager, is_async=False)

        app.set_tags({"voltage": 12.7})

        assert manager.set_tags_calls == [({"voltage": 12.7}, None, True, {})]

    def test_set_global_tag_routes_to_manager_with_none_app_key(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager, is_async=False)

        app.set_global_tag("system_status", "ok")

        assert manager.set_calls == [("system_status", "ok", None, True, {})]

    def test_request_shutdown_sets_shutdown_requested_tag(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager, is_async=False)

        app.request_shutdown()

        assert manager.set_calls == [("shutdown_requested", True, None, True, {})]

    def test_shutdown_requested_property_reads_from_manager(self):
        manager = FakeDockerAppTagManager()
        manager.values["shutdown_requested"] = True
        app = make_docker_app(tag_manager=manager)

        assert app._shutdown_requested is True
        assert manager.get_calls == [("shutdown_requested", None, None, {})]

    def test_async_app_initializes_tag_manager_as_async(self):
        device_agent = FakeRuntimeDeviceAgent()
        app = AsyncStartupApp(
            app_key="test_app",
            device_agent=device_agent,
            platform_iface=FakeRuntimePlatformInterface(),
            modbus_iface=FakeRuntimeModbusInterface(),
            test_mode=True,
            healthcheck_port=0,
        )

        assert app._is_async is True
        assert app.tag_manager._is_async is True
        assert app.ui_manager._is_async is True

    def test_async_run_startup_handles_declarative_tags_and_shutdown_subscription(
        self, monkeypatch
    ):
        import asyncio
        import time

        docker_application_module = importlib.import_module("pydoover.docker.application")
        monkeypatch.setattr(docker_application_module, "RUN_HEALTHCHECK", False)

        async def run_test():
            initial_shutdown_at = time.time() + 60
            updated_shutdown_at = initial_shutdown_at + 60

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
            app.tag_manager._tag_values = {"shutdown_at": initial_shutdown_at}

            task = asyncio.create_task(app._run())
            try:
                await app.wait_until_ready()
                await asyncio.sleep(0.05)

                assert app.setup_tag_manager_is_async is True
                assert app.tag_manager.get_tag("some_tag") == "ready"
                assert len(app.shutdown_events) == 1
                assert app.shutdown_events[0].timestamp() == pytest.approx(
                    initial_shutdown_at
                )
                assert KeyPath("shutdown_at") in app.tag_manager._tag_subscriptions

                await app.tag_manager._on_tag_update(
                    TAG_CHANNEL_NAME,
                    {
                        "shutdown_at": updated_shutdown_at,
                        "some_tag": "ready",
                    },
                )

                assert len(app.shutdown_events) == 2
                assert app.shutdown_events[1].timestamp() == pytest.approx(
                    updated_shutdown_at
                )
            finally:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task

        asyncio.run(run_test())


class TestTagClassResolution:
    def test_docker_resolve_tags_instantiates_declared_class(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager)
        app.__class__.tags_class = MyAppTags

        resolved = resolve_tags(app)

        assert isinstance(resolved, MyAppTags)
        assert app.tags is resolved
        assert resolved._manager is manager

    def test_docker_resolve_tags_setup_receives_injected_config(self):
        manager = FakeDockerAppTagManager()
        config = FakeSchema()
        config._inject_deployment_config({"some_flag": True})
        calls = []

        class ConfiguredTags(MyAppTags):
            async def setup(self, resolved_config):
                calls.append(resolved_config)

        app = make_docker_app(tag_manager=manager)
        app.config = config
        app.__class__.tags_class = ConfiguredTags

        resolved = resolve_tags(app)

        assert isinstance(resolved, ConfiguredTags)
        assert calls == [config]
        assert resolved._manager is manager

    def test_docker_tag_setup_can_change_available_tags_based_on_config(self):
        manager = FakeDockerAppTagManager()
        config = FakeSchema()
        config._inject_deployment_config({"some_flag": True})

        class ConfiguredTags(MyAppTags):
            async def setup(self, resolved_config):
                self.remove_tag("enabled")
                if resolved_config.some_flag:
                    self.add_tag("extra_sensor", Tag("number"))
                else:
                    self.add_tag("legacy_sensor", Tag("number"))

        app = make_docker_app(tag_manager=manager)
        app.config = config
        app.__class__.tags_class = ConfiguredTags

        resolved = resolve_tags(app)

        assert resolved.get_tag("voltage") is not None
        assert resolved.get_tag("extra_sensor") is not None
        assert resolved.get_tag("legacy_sensor") is None
        assert resolved.get_tag("enabled") is None
        assert {tag.name for tag in resolved} == {"voltage", "speed", "extra_sensor"}

    def test_docker_tags_class_none_is_allowed(self):
        manager = FakeDockerAppTagManager()
        app = make_docker_app(tag_manager=manager)

        resolved = resolve_tags(app)

        assert resolved is None
        assert app.tags is None

    def test_docker_resolve_tags_propagates_setup_error(self):
        app = make_docker_app()
        app.config = FakeSchema()

        class BrokenTags(MyAppTags):
            async def setup(self, _config):
                raise RuntimeError("boom")

        app.__class__.tags_class = BrokenTags

        with pytest.raises(RuntimeError, match="boom"):
            resolve_tags(app)

    def test_processor_resolve_tags_setup_runs_after_config_injection(self):
        config = FakeSchema()
        manager = FakeProcessorTagManager()
        calls = []

        class ConfiguredTags(MyAppTags):
            async def setup(self, resolved_config):
                calls.append(resolved_config.some_flag)

        config._inject_deployment_config({"some_flag": True})
        app = make_processor_app(
            config=config,
            tags_class=ConfiguredTags,
            tag_manager=manager,
        )

        resolved = resolve_tags(app)

        assert isinstance(resolved, ConfiguredTags)
        assert calls == [True]
        assert resolved._manager is manager

    def test_processor_tag_setup_can_change_available_tags_based_on_config(self):
        config = FakeSchema()
        config._inject_deployment_config({"some_flag": False})
        manager = FakeProcessorTagManager()

        class ConfiguredTags(MyAppTags):
            async def setup(self, resolved_config):
                self.remove_tag("enabled")
                if resolved_config.some_flag:
                    self.add_tag("extra_sensor", Tag("number"))
                else:
                    self.add_tag("legacy_sensor", Tag("number"))

        app = make_processor_app(
            config=config,
            tags_class=ConfiguredTags,
            tag_manager=manager,
        )

        resolved = resolve_tags(app)

        assert resolved.get_tag("voltage") is not None
        assert resolved.get_tag("legacy_sensor") is not None
        assert resolved.get_tag("extra_sensor") is None
        assert resolved.get_tag("enabled") is None
        assert {tag.name for tag in resolved} == {"voltage", "speed", "legacy_sensor"}

    def test_processor_resolve_tags_instantiates_declared_class(self):
        config = FakeSchema()
        manager = FakeProcessorTagManager()
        app = make_processor_app(config=config, tags_class=MyAppTags, tag_manager=manager)

        resolved = resolve_tags(app)

        assert isinstance(resolved, MyAppTags)
        assert resolved._manager is manager
