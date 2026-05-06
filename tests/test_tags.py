import asyncio
import types

import pytest

from pydoover import config
from pydoover.docker.application import Application as DockerApplication
from pydoover.tags import (
    Boolean,
    BoundTag,
    Change,
    Cross,
    Enter,
    Exit,
    Fall,
    NotSet,
    Number,
    RemoteTag,
    Rise,
    String,
    Tag,
    Tags,
)
from pydoover.tags.manager import (
    FASTMODE_CHANNEL_NAME,
    TAG_CHANNEL_NAME,
    KeyPath,
    TagsManagerDocker,
)


class FakeTagsManager:
    def __init__(self, initial: dict | None = None):
        self.values = dict(initial or {})
        self.get_calls = []
        self.set_calls = []
        self.set_call_kwargs: list[dict] = []
        self.subscriptions: list = []

    def get_tag(self, key, default=None, app_key=None, raise_key_error=False):
        del raise_key_error
        self.get_calls.append((key, default, app_key))
        return self.values.get((app_key, key), default)

    async def set_tag(self, key, value, app_key=None, **kwargs):
        self.set_calls.append((key, value, app_key))
        self.set_call_kwargs.append(dict(kwargs))
        self.values[(app_key, key)] = value

    def subscribe_to_tag(self, key, callback, app_key=None):
        self.subscriptions.append((key, callback, app_key))


class FakeTagsManagerNoSub(FakeTagsManager):
    """Like FakeTagsManager but without subscription support — mirrors processor managers."""

    subscribe_to_tag = None  # type: ignore[assignment]


class FakeTagClient:
    def __init__(self, aggregates: dict | None = None):
        self.event_callbacks = []
        self.aggregate_updates = []
        self.messages = []
        self.aggregates = dict(aggregates or {})

    def add_event_callback(self, channel_name, callback, events):
        self.event_callbacks.append((channel_name, callback, events))

    async def wait_for_channels_sync(self, channel_names=None, timeout=None):
        del timeout
        # In the real client, _run_channel_stream fetches aggregates and fires
        # ChannelSyncEvent callbacks before marking channels as synced.
        # Reproduce that here so subscribers see the initial state.
        from pydoover.models import EventSubscription
        from pydoover.models.data.events import ChannelSyncEvent

        for channel_name in channel_names or []:
            agg = await self.fetch_channel_aggregate(channel_name)
            sync_event = ChannelSyncEvent(aggregate=agg)
            for cb_channel, callback, events in self.event_callbacks:
                if (
                    cb_channel == channel_name
                    and EventSubscription.channel_sync in events
                ):
                    await callback(sync_event)

    async def fetch_channel_aggregate(self, channel_name):
        return types.SimpleNamespace(data=self.aggregates.get(channel_name, {}))

    async def update_channel_aggregate(
        self, channel_name, data, max_age_secs=None, **kwargs
    ):
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


class RemoteTagSchema(config.Schema):
    upstream_pump = config.TagRef("Upstream Pump")


class RemoteTagSchemaWithSecond(config.Schema):
    upstream_pump = config.TagRef("Upstream Pump")
    upstream_valve = config.TagRef("Upstream Valve")


class RemoteTagTags(Tags):
    upstream_status = RemoteTag(
        "boolean",
        reference_name="upstream_pump_status",
        republish_locally=True,
        default=False,
    )


def _make_pump_config(
    *,
    reference_name: str = "upstream_pump_status",
    app_name: str = "pump_controller",
    tag_name: str = "running",
    agent_id: str | None = None,
) -> dict:
    # Always include every field so prior tests can't leak state through the
    # shared module-level TagRef instance.
    return {
        "upstream_pump": {
            "reference_name": reference_name,
            "agent_id": agent_id,
            "app_name": app_name,
            "tag_name": tag_name,
        }
    }


class TestRemoteTag:
    @pytest.mark.asyncio
    async def test_resolves_to_upstream_app_and_tag(self):
        schema = RemoteTagSchema()
        schema._inject_deployment_config(_make_pump_config())

        manager = FakeTagsManager()
        tags = RemoteTagTags("self_app", manager, schema)
        await tags._resolve_remote_tags()

        # The seed-on-resolve path looks up the upstream value once.
        assert ("running", NotSet, "pump_controller") in manager.get_calls
        # No upstream value yet → no mirror set.
        assert manager.set_calls == []

        manager.values[("pump_controller", "running")] = True
        assert tags.upstream_status.get() is True
        assert ("running", False, "pump_controller") in manager.get_calls

    @pytest.mark.asyncio
    async def test_set_writes_to_upstream_namespace(self):
        schema = RemoteTagSchema()
        schema._inject_deployment_config(_make_pump_config())

        manager = FakeTagsManager()
        tags = RemoteTagTags("self_app", manager, schema)
        await tags._resolve_remote_tags()

        await tags.upstream_status.set(True)

        assert ("running", True, "pump_controller") in manager.set_calls
        assert manager.values[("pump_controller", "running")] is True

    @pytest.mark.asyncio
    async def test_missing_tagref_raises(self):
        schema = config.Schema()  # empty schema, no TagRef
        manager = FakeTagsManager()
        tags = RemoteTagTags("self_app", manager, schema)

        with pytest.raises(ValueError, match="reference_name='upstream_pump_status'"):
            await tags._resolve_remote_tags()

    @pytest.mark.asyncio
    async def test_duplicate_reference_name_in_config_raises(self):
        schema = RemoteTagSchemaWithSecond()
        schema._inject_deployment_config(
            {
                "upstream_pump": {
                    "reference_name": "upstream_pump_status",
                    "app_name": "a",
                    "tag_name": "x",
                },
                "upstream_valve": {
                    "reference_name": "upstream_pump_status",  # collision
                    "app_name": "b",
                    "tag_name": "y",
                },
            }
        )

        manager = FakeTagsManager()
        tags = RemoteTagTags("self_app", manager, schema)

        with pytest.raises(ValueError, match="Duplicate TagRef reference_name"):
            await tags._resolve_remote_tags()

    @pytest.mark.asyncio
    async def test_cross_agent_raises_at_runtime_not_at_setup(self):
        schema = RemoteTagSchema()
        schema._inject_deployment_config(_make_pump_config(agent_id="42"))

        manager = FakeTagsManager()
        tags = RemoteTagTags("self_app", manager, schema)

        # Setup itself succeeds — the schema field is accepted.
        await tags._resolve_remote_tags()

        # The mirror subscription was skipped (cross-agent path is not wired).
        assert manager.subscriptions == []

        # But touching the value at runtime trips the not-implemented guard.
        with pytest.raises(NotImplementedError, match="Cross-agent RemoteTag"):
            tags.upstream_status.get()

        with pytest.raises(NotImplementedError, match="Cross-agent RemoteTag"):
            await tags.upstream_status.set(True)

    @pytest.mark.asyncio
    async def test_unresolved_remote_tag_raises_on_access(self):
        manager = FakeTagsManager()
        tags = RemoteTagTags("self_app", manager, FakeSchema())

        # _resolve_remote_tags() not called yet → access errors.
        with pytest.raises(RuntimeError, match="not been resolved"):
            tags.upstream_status.get()

    @pytest.mark.asyncio
    async def test_republish_locally_subscribes_and_seeds_mirror(self):
        schema = RemoteTagSchema()
        schema._inject_deployment_config(_make_pump_config())

        manager = FakeTagsManager(
            {("pump_controller", "running"): True}  # upstream already has a value
        )
        tags = RemoteTagTags("self_app", manager, schema)
        await tags._resolve_remote_tags()

        # Subscription registered against the upstream (app_key, tag_name).
        assert len(manager.subscriptions) == 1
        sub_key, sub_callback, sub_app_key = manager.subscriptions[0]
        assert sub_key == "running"
        assert sub_app_key == "pump_controller"

        # Initial mirror seed: local app namespace, key = reference_name.
        assert manager.values[("self_app", "upstream_pump_status")] is True

        # Subsequent upstream change fires the mirror callback.
        await sub_callback("running", False)
        assert manager.values[("self_app", "upstream_pump_status")] is False

    @pytest.mark.asyncio
    async def test_republish_locally_disabled_skips_subscription(self):
        class NoMirrorTags(Tags):
            upstream_status = RemoteTag(
                "boolean",
                reference_name="upstream_pump_status",
                republish_locally=False,
                default=False,
            )

        schema = RemoteTagSchema()
        schema._inject_deployment_config(_make_pump_config())
        manager = FakeTagsManager({("pump_controller", "running"): True})
        tags = NoMirrorTags("self_app", manager, schema)

        await tags._resolve_remote_tags()

        assert manager.subscriptions == []
        # No initial seed either when republish is off.
        assert ("self_app", "upstream_pump_status") not in manager.values

    @pytest.mark.asyncio
    async def test_processor_style_manager_skips_subscription_but_still_routes(self):
        schema = RemoteTagSchema()
        schema._inject_deployment_config(_make_pump_config())

        manager = FakeTagsManagerNoSub({("pump_controller", "running"): True})
        tags = RemoteTagTags("self_app", manager, schema)
        await tags._resolve_remote_tags()

        # subscribe_to_tag is None → no subscription / no seeding attempted.
        assert tags.upstream_status.get() is True

        await tags.upstream_status.set(False)
        assert manager.values[("pump_controller", "running")] is False


class TestOptionalRemoteTag:
    """Optional TagRef + RemoteTag pair: the operator can leave the config
    blank and the matching RemoteTag falls back to its declared default
    instead of raising at resolution or read time.
    """

    @pytest.mark.asyncio
    async def test_optional_tagref_omitted_resolves_cleanly(self):
        class OptionalSchema(config.Schema):
            optional_ref = config.TagRef(
                "Optional Pump", default=None, required=False, name="optional_ref"
            )

        class OptionalTags(Tags):
            upstream = RemoteTag(
                "boolean",
                reference_name="optional_ref_target",
                optional=True,
            )

        schema = OptionalSchema()
        schema._inject_deployment_config({})  # optional_ref entirely omitted

        manager = FakeTagsManager()
        tags = OptionalTags("self_app", manager, schema)
        await tags._resolve_remote_tags()  # must not raise

        # Read returns the auto-defaulted None; no manager calls were made
        # against an upstream because nothing was resolved.
        assert tags.upstream.get() is None
        assert manager.subscriptions == []

    @pytest.mark.asyncio
    async def test_optional_tagref_null_resolves_cleanly(self):
        class OptionalSchema(config.Schema):
            optional_ref = config.TagRef(
                "Optional Pump", default=None, required=False, name="optional_ref"
            )

        class OptionalTags(Tags):
            upstream = RemoteTag(
                "boolean", reference_name="optional_ref_target", optional=True
            )

        schema = OptionalSchema()
        schema._inject_deployment_config({"optional_ref": None})

        tags = OptionalTags("self_app", FakeTagsManager(), schema)
        await tags._resolve_remote_tags()

        assert tags.upstream.get() is None

    @pytest.mark.asyncio
    async def test_optional_tagref_empty_object_resolves_cleanly(self):
        class OptionalSchema(config.Schema):
            optional_ref = config.TagRef(
                "Optional Pump", default=None, required=False, name="optional_ref"
            )

        class OptionalTags(Tags):
            upstream = RemoteTag(
                "boolean", reference_name="optional_ref_target", optional=True
            )

        schema = OptionalSchema()
        schema._inject_deployment_config({"optional_ref": {}})

        tags = OptionalTags("self_app", FakeTagsManager(), schema)
        await tags._resolve_remote_tags()

        assert tags.upstream.get() is None

    @pytest.mark.asyncio
    async def test_optional_set_on_unresolved_is_noop(self):
        class OptionalSchema(config.Schema):
            optional_ref = config.TagRef(
                "Optional Pump", default=None, required=False, name="optional_ref"
            )

        class OptionalTags(Tags):
            upstream = RemoteTag(
                "boolean", reference_name="optional_ref_target", optional=True
            )

        schema = OptionalSchema()
        schema._inject_deployment_config({})

        manager = FakeTagsManager()
        tags = OptionalTags("self_app", manager, schema)
        await tags._resolve_remote_tags()

        # No upstream resolved → set is silently dropped.
        await tags.upstream.set(True)
        assert manager.set_calls == []

    @pytest.mark.asyncio
    async def test_optional_remote_tag_still_works_when_filled(self):
        class OptionalSchema(config.Schema):
            optional_ref = config.TagRef(
                "Optional Pump", default=None, required=False, name="optional_ref"
            )

        class OptionalTags(Tags):
            upstream = RemoteTag(
                "boolean",
                reference_name="optional_ref_target",
                optional=True,
            )

        schema = OptionalSchema()
        schema._inject_deployment_config(
            {
                "optional_ref": {
                    "reference_name": "optional_ref_target",
                    "app_name": "pump_controller",
                    "tag_name": "running",
                }
            }
        )

        manager = FakeTagsManager({("pump_controller", "running"): True})
        tags = OptionalTags("self_app", manager, schema)
        await tags._resolve_remote_tags()

        assert tags.upstream.get() is True
        await tags.upstream.set(False)
        assert manager.values[("pump_controller", "running")] is False

    @pytest.mark.asyncio
    async def test_required_remote_tag_with_unset_optional_tagref_still_raises(self):
        # Mixing: an *optional* TagRef left blank, plus a *required*
        # RemoteTag that wanted to bind to it. The required RemoteTag must
        # still raise — its requirement contract is independent of the
        # TagRef's optionality.
        class MixedSchema(config.Schema):
            optional_ref = config.TagRef(
                "Optional", default=None, required=False, name="optional_ref"
            )

        class MixedTags(Tags):
            upstream = RemoteTag(
                "boolean", reference_name="optional_ref_target"
            )  # NOT optional

        schema = MixedSchema()
        schema._inject_deployment_config({})

        tags = MixedTags("self_app", FakeTagsManager(), schema)

        with pytest.raises(ValueError, match="reference_name='optional_ref_target'"):
            await tags._resolve_remote_tags()

    def test_optional_remote_tag_default_is_none_when_unspecified(self):
        tag = RemoteTag("boolean", reference_name="x", optional=True)
        assert tag.default is None
        assert tag.optional is True

    def test_optional_remote_tag_explicit_default_wins(self):
        tag = RemoteTag("boolean", reference_name="x", optional=True, default=False)
        assert tag.default is False

    def test_non_optional_remote_tag_default_unchanged(self):
        tag = RemoteTag("boolean", reference_name="x")
        assert tag.default is NotSet
        assert tag.optional is False


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


class TestImmediateLog:
    @pytest.mark.asyncio
    async def test_set_with_log_buffers_immediate_not_periodic(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client)

        await manager.set_tag("voltage", 13.2, app_key="test_app", log=True)

        assert manager._pending_immediate_log == {"test_app": {"voltage": 13.2}}
        assert manager._pending_tag_log == {}
        assert manager._pending_tag_aggregate == {"test_app": {"voltage": 13.2}}

    @pytest.mark.asyncio
    async def test_commit_tags_creates_message_for_immediate_log(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client)

        await manager.set_tag("voltage", 13.2, app_key="test_app", log=True)
        await manager.commit_tags()

        assert client.messages == [(TAG_CHANNEL_NAME, {"test_app": {"voltage": 13.2}})]
        # Aggregate update also fires (end-of-loop flush_tags).
        assert any(entry[0] == TAG_CHANNEL_NAME for entry in client.aggregate_updates)
        # Immediate buffer is drained after the flush.
        assert manager._pending_immediate_log == {}

    @pytest.mark.asyncio
    async def test_log_true_strips_previous_periodic_entry(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client)

        await manager.set_tag("voltage", 12.0, app_key="test_app")
        assert manager._pending_tag_log == {"test_app": {"voltage": 12.0}}

        await manager.set_tag("voltage", 13.0, app_key="test_app", log=True)

        # Old periodic entry for the same path is removed; the new value
        # lives only in the immediate buffer.
        assert manager._pending_tag_log == {}
        assert manager._pending_immediate_log == {"test_app": {"voltage": 13.0}}

    @pytest.mark.asyncio
    async def test_multiple_log_true_calls_coalesce_into_one_message(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client)

        await manager.set_tag("voltage", 13.2, app_key="test_app", log=True)
        await manager.set_tag("speed", 50, app_key="test_app", log=True)
        await manager.commit_tags()

        assert client.messages == [
            (
                TAG_CHANNEL_NAME,
                {"test_app": {"voltage": 13.2, "speed": 50}},
            )
        ]

    @pytest.mark.asyncio
    async def test_log_false_routes_to_periodic_buffer(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client)

        await manager.set_tag("voltage", 13.2, app_key="test_app")

        assert manager._pending_tag_log == {"test_app": {"voltage": 13.2}}
        assert manager._pending_immediate_log == {}

    @pytest.mark.asyncio
    async def test_bound_tag_set_forwards_log_kwarg(self):
        manager = FakeTagsManager()
        tags = make_tags(manager)

        await tags.voltage.set(13.2, log=True)

        assert manager.set_calls == [("voltage", 13.2, "test_app")]
        assert manager.set_call_kwargs[-1].get("log") is True

    @pytest.mark.asyncio
    async def test_bound_tag_increment_forwards_log_kwarg(self):
        manager = FakeTagsManager({("test_app", "voltage"): 12.0})
        tags = make_tags(manager)

        await tags.voltage.increment(log=True)

        assert manager.set_call_kwargs[-1].get("log") is True


class TestDelete:
    @pytest.mark.asyncio
    async def test_bound_tag_delete_writes_none(self):
        manager = FakeTagsManager({("test_app", "voltage"): 12.0})
        tags = make_tags(manager)

        await tags.voltage.delete()

        assert manager.set_calls[-1] == ("voltage", None, "test_app")

    @pytest.mark.asyncio
    async def test_bound_tag_delete_forwards_log_kwarg(self):
        manager = FakeTagsManager({("test_app", "voltage"): 12.0})
        tags = make_tags(manager)

        await tags.voltage.delete(log=True)

        assert manager.set_calls[-1] == ("voltage", None, "test_app")
        assert manager.set_call_kwargs[-1].get("log") is True

    @pytest.mark.asyncio
    async def test_docker_manager_delete_via_tag_logs_immediately(self):
        client = FakeTagClient()
        manager = TagsManagerDocker(client=client)
        # Seed an existing value so the diff registers as a change.
        manager._tag_values = {"test_app": {"voltage": 12.0}}

        await manager.set_tag("voltage", None, app_key="test_app", log=True)
        await manager.commit_tags()

        assert client.messages == [(TAG_CHANNEL_NAME, {"test_app": {"voltage": None}})]


class TestProcessorImmediateLog:
    @pytest.mark.asyncio
    async def test_log_true_forces_message_when_record_disabled(self):
        from pydoover.tags.manager import TagsManagerProcessor

        client = FakeTagClient()
        manager = TagsManagerProcessor(
            app_key="test_app",
            client=client,
            agent_id=1,
            tag_values={},
            record_tag_update=False,
        )

        await manager.set_tag("voltage", 13.2, log=True)
        await manager.commit_tags()

        assert client.messages == [(TAG_CHANNEL_NAME, {"test_app": {"voltage": 13.2}})]

    @pytest.mark.asyncio
    async def test_log_false_respects_record_disabled(self):
        from pydoover.tags.manager import TagsManagerProcessor

        client = FakeTagClient()
        manager = TagsManagerProcessor(
            app_key="test_app",
            client=client,
            agent_id=1,
            tag_values={},
            record_tag_update=False,
        )

        await manager.set_tag("voltage", 13.2)
        await manager.commit_tags()

        # Aggregate updates but no message is created.
        assert client.messages == []
        assert client.aggregate_updates  # at least one aggregate update


class TestConcreteTagClasses:
    def test_number_subclass_sets_type_and_no_triggers_by_default(self):
        n = Number(default=0)
        assert n.tag_type == "number"
        assert n.default == 0
        assert n.log_on == []

    def test_boolean_subclass_sets_type(self):
        b = Boolean(default=False, log_on=Change())
        assert b.tag_type == "boolean"
        assert len(b.log_on) == 1

    def test_string_subclass_sets_type(self):
        s = String(default="idle")
        assert s.tag_type == "string"

    def test_legacy_tag_constructor_still_works(self):
        # Backwards compat: ``Tag(type, ...)`` keeps working even after
        # the typed subclasses are introduced.
        t = Tag("number", default=5)
        assert t.tag_type == "number"
        assert t.default == 5
        assert t._evaluate_log_trigger(None, 100, {}) is False

    def test_log_on_accepts_single_descriptor_or_list(self):
        n_one = Number(log_on=Cross(100))
        n_many = Number(log_on=[Cross(100), Rise(110)])
        assert len(n_one.log_on) == 1
        assert len(n_many.log_on) == 2

    def test_number_rejects_non_numeric_descriptors(self):
        with pytest.raises(TypeError, match="Number log_on accepts"):
            Number(log_on=Change())
        with pytest.raises(TypeError, match="Number log_on accepts"):
            Number(log_on=Enter(1))

    def test_boolean_rejects_numeric_descriptors(self):
        with pytest.raises(TypeError, match="Boolean log_on accepts"):
            Boolean(log_on=Cross(1))
        with pytest.raises(TypeError, match="Boolean log_on accepts"):
            Boolean(log_on=Rise(1))

    def test_string_rejects_numeric_descriptors(self):
        with pytest.raises(TypeError, match="String log_on accepts"):
            String(log_on=Fall(1))

    def test_crossing_descriptors_require_a_threshold(self):
        with pytest.raises(ValueError, match="requires at least one threshold"):
            Cross()

    def test_crossing_accepts_multiple_thresholds(self):
        c = Cross(90, 100, 110, deadband=2)
        assert c.thresholds == [90.0, 100.0, 110.0]
        assert c.deadband == 2.0

    def test_membership_holds_single_value(self):
        e = Enter("error")
        assert e.value == "error"
        x = Exit(True)
        assert x.value is True


class _NumericTags(Tags):
    voltage = Number(log_on=Cross(100))
    temp = Number(log_on=Cross(50, 100, deadband=4))


class TestNumericTriggers:
    @pytest.mark.asyncio
    async def test_initial_value_above_threshold_logs(self):
        manager = FakeTagsManager()
        tags = _NumericTags("test_app", manager, FakeSchema())

        await tags.voltage.set(120)

        assert manager.set_call_kwargs[-1].get("log") is True

    @pytest.mark.asyncio
    async def test_initial_value_below_threshold_does_not_log(self):
        manager = FakeTagsManager()
        tags = _NumericTags("test_app", manager, FakeSchema())

        await tags.voltage.set(80)

        assert manager.set_call_kwargs[-1].get("log") is False

    @pytest.mark.asyncio
    async def test_crossing_up_then_down_both_log(self):
        manager = FakeTagsManager()
        tags = _NumericTags("test_app", manager, FakeSchema())

        await tags.voltage.set(80)  # below — no log
        await tags.voltage.set(120)  # crosses up — log
        await tags.voltage.set(70)  # crosses down — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [False, True, True]

    @pytest.mark.asyncio
    async def test_no_relog_while_staying_above(self):
        manager = FakeTagsManager()
        tags = _NumericTags("test_app", manager, FakeSchema())

        await tags.voltage.set(120)  # crosses up — log
        await tags.voltage.set(130)  # still above — no log
        await tags.voltage.set(110)  # still above — no log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [True, False, False]

    @pytest.mark.asyncio
    async def test_deadband_suppresses_oscillation(self):
        manager = FakeTagsManager()
        tags = _NumericTags("test_app", manager, FakeSchema())

        # threshold=50, deadband=4 → fires up at >=52, down at <=48.
        await tags.temp.set(40)  # below band — no log
        await tags.temp.set(51)  # inside band — no log
        await tags.temp.set(49)  # inside band — no log
        await tags.temp.set(53)  # clears upper edge — log
        await tags.temp.set(49)  # back inside band — no log
        await tags.temp.set(47)  # clears lower edge — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [False, False, False, True, False, True]

    @pytest.mark.asyncio
    async def test_multiple_thresholds_each_fire_independently(self):
        manager = FakeTagsManager()
        tags = _NumericTags("test_app", manager, FakeSchema())

        await tags.temp.set(60)  # crosses 50 — log
        await tags.temp.set(110)  # crosses 100 — log
        await tags.temp.set(95)  # below 100 (clear of band) — log
        await tags.temp.set(40)  # below 50 — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [True, True, True, True]

    @pytest.mark.asyncio
    async def test_explicit_log_true_combines_with_threshold(self):
        manager = FakeTagsManager()
        tags = _NumericTags("test_app", manager, FakeSchema())

        await tags.voltage.set(50, log=True)

        assert manager.set_call_kwargs[-1].get("log") is True


class _DirectionalNumericTags(Tags):
    high_alarm = Number(log_on=Rise(100))
    low_alarm = Number(log_on=Fall(10))
    combined = Number(log_on=[Rise(100), Fall(10)])


class TestDirectionalNumericTriggers:
    @pytest.mark.asyncio
    async def test_rise_only_fires_going_up(self):
        manager = FakeTagsManager()
        tags = _DirectionalNumericTags("test_app", manager, FakeSchema())

        await tags.high_alarm.set(80)  # below — no log
        await tags.high_alarm.set(120)  # rise → log
        await tags.high_alarm.set(80)  # fall — no log (one-sided)
        await tags.high_alarm.set(120)  # rise again — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [False, True, False, True]

    @pytest.mark.asyncio
    async def test_fall_only_fires_going_down(self):
        manager = FakeTagsManager()
        tags = _DirectionalNumericTags("test_app", manager, FakeSchema())

        await tags.low_alarm.set(50)  # above 10 — silent rise
        await tags.low_alarm.set(5)  # fall through 10 — log
        await tags.low_alarm.set(50)  # rise — no log (one-sided)
        await tags.low_alarm.set(5)  # fall — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [False, True, False, True]

    @pytest.mark.asyncio
    async def test_rise_initial_above_fires(self):
        manager = FakeTagsManager()
        tags = _DirectionalNumericTags("test_app", manager, FakeSchema())

        await tags.high_alarm.set(120)

        assert manager.set_call_kwargs[-1].get("log") is True

    @pytest.mark.asyncio
    async def test_fall_initial_below_does_not_fire(self):
        manager = FakeTagsManager()
        tags = _DirectionalNumericTags("test_app", manager, FakeSchema())

        await tags.low_alarm.set(5)

        assert manager.set_call_kwargs[-1].get("log") is False

    @pytest.mark.asyncio
    async def test_combining_rise_and_fall_descriptors(self):
        manager = FakeTagsManager()
        tags = _DirectionalNumericTags("test_app", manager, FakeSchema())

        # combined = Number(log_on=[Rise(100), Fall(10)])
        await tags.combined.set(50)  # 10 silent (Fall only); not at 100 — no log
        await tags.combined.set(150)  # rise through 100 — log
        await tags.combined.set(5)  # silent fall through 100; fall through 10 — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [False, True, True]


class _BoolTags(Tags):
    fault_change = Boolean(log_on=Change())
    # Bidirectional on a single value via composition.
    fault_bidirectional = Boolean(log_on=[Enter(True), Exit(True)])


class TestBooleanTriggers:
    @pytest.mark.asyncio
    async def test_change_fires_each_transition(self):
        manager = FakeTagsManager()
        tags = _BoolTags("test_app", manager, FakeSchema())

        await tags.fault_change.set(True)
        await tags.fault_change.set(False)
        await tags.fault_change.set(True)

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [True, True, True]

    @pytest.mark.asyncio
    async def test_enter_plus_exit_fires_both_directions(self):
        manager = FakeTagsManager()
        tags = _BoolTags("test_app", manager, FakeSchema())

        await tags.fault_bidirectional.set(True)  # entering True — log
        await tags.fault_bidirectional.set(False)  # exiting True — log
        await tags.fault_bidirectional.set(False)  # prev == new — no log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [True, True, False]


class _StringTags(Tags):
    enter_only = String(log_on=Enter("error"))
    exit_only = String(log_on=Exit("ok"))
    # Multi-value bidirectional via list composition.
    multi = String(log_on=[Enter("error"), Exit("error"), Enter("ok"), Exit("ok")])


class TestStringTriggers:
    @pytest.mark.asyncio
    async def test_enter_only_fires_on_entry(self):
        manager = FakeTagsManager()
        tags = _StringTags("test_app", manager, FakeSchema())

        await tags.enter_only.set("error")  # enter — log
        await tags.enter_only.set("warn")  # exit not configured

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [True, False]

    @pytest.mark.asyncio
    async def test_exit_only_fires_on_exit(self):
        manager = FakeTagsManager()
        tags = _StringTags("test_app", manager, FakeSchema())

        await tags.exit_only.set("ok")  # enter not configured
        await tags.exit_only.set("warn")  # exit — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [False, True]

    @pytest.mark.asyncio
    async def test_multi_value_via_list_composition(self):
        manager = FakeTagsManager()
        tags = _StringTags("test_app", manager, FakeSchema())

        await tags.multi.set("error")  # Enter("error") — log
        await tags.multi.set("warn")  # Exit("error") — log
        await tags.multi.set("ok")  # Enter("ok") — log
        await tags.multi.set("warn")  # Exit("ok") — log

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [True, True, True, True]


class _CompositeStringTags(Tags):
    # Asymmetric: log entry to "error" but exit from "ok".
    state = String(log_on=[Enter("error"), Exit("ok")])


class TestCompositeTriggers:
    @pytest.mark.asyncio
    async def test_each_descriptor_fires_independently(self):
        manager = FakeTagsManager()
        tags = _CompositeStringTags("test_app", manager, FakeSchema())

        await tags.state.set("ok")  # not entering "error", no prev to exit from
        await tags.state.set("warn")  # exits "ok" — log via Exit
        await tags.state.set("error")  # enters "error" — log via Enter
        await tags.state.set("warn")  # exit not configured for "error"

        log_flags = [kw.get("log") for kw in manager.set_call_kwargs]
        assert log_flags == [False, True, True, False]


class TestTriggerEndToEnd:
    @pytest.mark.asyncio
    async def test_threshold_crossing_creates_message_via_docker_manager(self):
        client = FakeTagClient(
            {
                TAG_CHANNEL_NAME: {},
                FASTMODE_CHANNEL_NAME: {},
            }
        )
        manager = TagsManagerDocker(client=client)
        await manager.setup()

        tags = _NumericTags("test_app", manager, FakeSchema())

        await tags.voltage.set(120)  # crosses 100 — should immediate-log
        await manager.commit_tags()

        assert client.messages == [(TAG_CHANNEL_NAME, {"test_app": {"voltage": 120}})]


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
