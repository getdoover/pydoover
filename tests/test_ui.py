import asyncio

import pytest

from pydoover import ui
from pydoover.tags import Tag, Tags

from tests.test_tags import (
    DockerApplication,
    FakeDockerAppTagManager,
    FakeProcessorTagManager,
    FakeSchema,
    MyAppTags,
    ProcessorApplication,
)


class UITags(Tags):
    voltage = Tag("number")
    speed = Tag("number", default=0)
    enabled = Tag("boolean", default=False)
    mode = Tag("string", default="idle")
    meta = Tag("object", default={"source": "fallback"})


class BaseUI(ui.UI):
    voltage = ui.NumericVariable("voltage", "Voltage")


class ExtendedUI(BaseUI):
    enabled = ui.BooleanVariable("enabled", "Enabled")


class TagBoundUI(ui.UI):
    voltage = ui.NumericVariable(
        "voltage",
        "Voltage",
        curr_val=UITags.voltage,
        hidden=UITags.enabled,
        conditions={"armed": UITags.enabled},
        ranges=[
            ui.Range(
                label=UITags.mode,
                min_val=0,
                max_val=UITags.voltage,
                colour=UITags.mode,
            )
        ],
    )
    mode = ui.StateCommand(
        "mode",
        "Mode",
        currentValue=UITags.mode,
        user_options=[ui.Option("auto", UITags.mode)],
    )


def make_docker_app(config=None, tags=None, ui_source=None, app_key="test_app"):
    app = object.__new__(DockerApplication)
    app.config = config or FakeSchema()
    app.app_key = app_key
    app.tag_manager = FakeDockerAppTagManager()
    app.ui_manager = ui.UIManager(app_key=app_key)
    app._tags_source = tags
    app.tags = tags if isinstance(tags, Tags) else None
    app._ui_source = ui_source
    app.ui = ui_source if isinstance(ui_source, ui.UI) else None
    return app


def make_processor_app(config=None, tags=None, ui_source=None, app_key="test_app"):
    app = object.__new__(ProcessorApplication)
    app.config = config or FakeSchema()
    app.app_key = app_key
    app.tag_manager = FakeProcessorTagManager()
    app.ui_manager = ui.UIManager(app_key=app_key)
    app._tags_source = tags
    app.tags = tags if isinstance(tags, Tags) else None
    app._ui_source = ui_source
    app.ui = ui_source if isinstance(ui_source, ui.UI) else None
    return app


class TestDeclarativeUI:
    def test_declaration_order_and_inheritance_are_preserved(self):
        ui_obj = ExtendedUI()

        assert [element.name for element in ui_obj.children] == ["voltage", "enabled"]

    def test_instances_do_not_share_element_state(self):
        first = BaseUI()
        second = BaseUI()

        first.voltage.hidden = True

        assert second.voltage.hidden is False

    def test_add_and_remove_element_are_instance_local(self):
        ui_obj = BaseUI()
        extra = ui.TextVariable("extra", "Extra")

        ui_obj.add_element("extra", extra)

        assert ui_obj.extra is extra
        assert [element.name for element in ui_obj.children] == ["voltage", "extra"]

        ui_obj.remove_element("extra")

        assert "extra" not in ui_obj.__dict__
        assert [element.name for element in ui_obj.children] == ["voltage"]


class TestTagReferenceSerialization:
    def test_class_tag_reference_serializes_to_compact_lookup_string(self):
        ui_obj = TagBoundUI().bind_tags(UITags())

        data = ui_obj.voltage.to_dict()

        assert data["currentValue"] == "$tag.voltage:number"

    def test_bound_tag_reference_serializes_to_same_compact_lookup_string(self):
        tags = MyAppTags()

        class FactoryUI(ui.UI):
            voltage = ui.NumericVariable(
                "voltage",
                "Voltage",
                curr_val=tags.speed,
            )

        ui_obj = FactoryUI().bind_tags(tags)

        assert ui_obj.voltage.to_dict()["currentValue"] == "$tag.speed:number:0"

    def test_recursive_serialization_handles_nested_objects_lists_ranges_and_options(self):
        ui_obj = TagBoundUI().bind_tags(UITags())

        voltage = ui_obj.voltage.to_dict()
        mode = ui_obj.mode.to_dict()

        assert voltage["hidden"] == "$tag.enabled:boolean:false"
        assert voltage["conditions"]["armed"] == "$tag.enabled:boolean:false"
        assert voltage["ranges"][0]["label"] == '$tag.mode:string:"idle"'
        assert voltage["ranges"][0]["max"] == "$tag.voltage:number"
        assert mode["userOptions"]["auto"]["displayString"] == '$tag.mode:string:"idle"'

    def test_name_field_cannot_reference_a_tag(self):
        bad = ui.TextVariable("bad", "Bad")
        bad.name = MyAppTags.voltage
        ui_obj = ui.UI()
        ui_obj.add_element("bad", bad)
        ui_obj.bind_tags(MyAppTags())

        with pytest.raises(ValueError, match="name"):
            bad.to_dict()

    def test_missing_class_level_tag_reference_raises(self):
        tags = MyAppTags()
        tags.remove_tag("enabled")

        class MissingUI(ui.UI):
            status = ui.BooleanVariable("status", "Status", curr_val=MyAppTags.enabled)

        with pytest.raises(ValueError, match="enabled"):
            MissingUI().bind_tags(tags)


class TestRuntimeGuards:
    def test_tag_bound_variable_cannot_be_updated_directly(self):
        ui_obj = TagBoundUI().bind_tags(UITags())
        manager = ui.UIManager(app_key="test_app")
        manager.set_children(ui_obj.to_elements())

        with pytest.raises(RuntimeError, match="tag-backed"):
            ui_obj.voltage.current_value = 12.7

        with pytest.raises(RuntimeError, match="tag-backed"):
            manager.update_variable("voltage", 12.7)

    def test_tag_bound_interaction_cannot_be_coerced(self):
        ui_obj = TagBoundUI().bind_tags(UITags())
        manager = ui.UIManager(app_key="test_app")
        manager.set_children(ui_obj.to_elements())

        with pytest.raises(RuntimeError, match="tag-backed"):
            ui_obj.mode.coerce("manual")

        with pytest.raises(RuntimeError, match="tag-backed"):
            ui_obj.mode.current_value = "manual"

    def test_unbound_fields_still_work(self):
        manager = ui.UIManager(app_key="test_app")
        variable = ui.NumericVariable("voltage", "Voltage")
        manager.set_children([variable])

        assert manager.update_variable("voltage", 12.7) is True
        assert variable.current_value == 12.7


class TestCallbacksAndInteractions:
    def test_tag_bound_interactions_do_not_autowrite_but_callbacks_can_update_tags(self):
        class Handler:
            def __init__(self, tags):
                self.tags = tags
                self.values = []

            @ui.callback("mode")
            def on_mode(self, _command, new_value):
                self.values.append(new_value)
                self.tags.mode.set(new_value)

        tags = UITags()
        tags.register_manager(FakeDockerAppTagManager())
        handler = Handler(tags)
        manager = ui.UIManager(app_key="test_app")
        ui_obj = TagBoundUI().bind_tags(tags)

        manager.register_callbacks(handler)
        manager.set_children(ui_obj.to_elements())

        asyncio.run(manager.on_command_update_async(None, {"test_app_mode": "manual"}))

        assert handler.values == ["manual"]
        assert tags.mode.get() == "manual"
        assert ui_obj.mode.to_dict()["currentValue"] == '$tag.mode:string:"idle"'

    def test_tag_bound_interactions_without_callback_do_not_write_tags(self):
        tags = UITags()
        manager_backend = FakeDockerAppTagManager()
        tags.register_manager(manager_backend)
        manager = ui.UIManager(app_key="test_app")
        ui_obj = TagBoundUI().bind_tags(tags)

        manager.set_children(ui_obj.to_elements())

        asyncio.run(manager.on_command_update_async(None, {"test_app_mode": "manual"}))

        assert tags.mode.get() == "idle"
        assert manager_backend.values == {}


class TestApplicationUIResolution:
    def test_docker_resolves_ui_subclass_and_installs_it(self):
        app = make_docker_app(tags=UITags(), ui_source=TagBoundUI)

        app._resolve_tags()
        resolved = app._resolve_ui()

        assert isinstance(resolved, TagBoundUI)
        assert app.ui is resolved
        assert app.ui_manager.get_element("voltage") is resolved.voltage

    def test_docker_preserves_prebuilt_ui_instance(self):
        ui_obj = BaseUI()
        app = make_docker_app(tags=MyAppTags(), ui_source=ui_obj)

        app._resolve_tags()
        resolved = app._resolve_ui()

        assert resolved is ui_obj

    def test_docker_ui_factory_receives_config_and_tags(self):
        config = FakeSchema()
        config._inject_deployment_config({"some_flag": True})
        calls = []

        def build_ui(resolved_config, resolved_tags):
            calls.append((resolved_config.some_flag, resolved_tags))

            class FactoryUI(ui.UI):
                voltage = ui.NumericVariable(
                    "voltage",
                    "Voltage",
                    curr_val=resolved_tags.speed,
                )

            return FactoryUI()

        app = make_docker_app(config=config, tags=MyAppTags(), ui_source=build_ui)
        app._resolve_tags()

        resolved = app._resolve_ui()

        assert isinstance(resolved, ui.UI)
        assert calls == [(True, app.tags)]
        assert resolved.voltage.to_dict()["currentValue"] == "$tag.speed:number:0"

    def test_docker_ui_factory_with_one_argument_remains_supported(self):
        calls = []

        def build_ui(resolved_config):
            calls.append(resolved_config)
            return BaseUI()

        app = make_docker_app(config=FakeSchema(), tags=MyAppTags(), ui_source=build_ui)
        app._resolve_tags()

        resolved = app._resolve_ui()

        assert isinstance(resolved, BaseUI)
        assert calls == [app.config]

    def test_docker_ui_factory_returning_none_is_allowed(self):
        app = make_docker_app(tags=MyAppTags(), ui_source=lambda config: None)
        app._resolve_tags()

        resolved = app._resolve_ui()

        assert resolved is None
        assert app.ui is None

    def test_processor_resolves_ui_after_tags(self):
        config = FakeSchema()
        config._inject_deployment_config({"some_flag": True})
        app = make_processor_app(config=config, tags=UITags(), ui_source=TagBoundUI)

        app._resolve_tags()
        resolved = app._resolve_ui()

        assert isinstance(resolved, TagBoundUI)
        assert app.ui_manager.get_command("mode") is resolved.mode

    def test_processor_ui_factory_receives_config_and_tags(self):
        config = FakeSchema()
        calls = []

        def build_ui(resolved_config, resolved_tags):
            calls.append((resolved_config, resolved_tags))
            return TagBoundUI()

        app = make_processor_app(config=config, tags=UITags(), ui_source=build_ui)
        app._resolve_tags()

        resolved = app._resolve_ui()

        assert isinstance(resolved, TagBoundUI)
        assert calls == [(config, app.tags)]

    def test_processor_missing_tag_reference_raises_deterministically(self):
        config = FakeSchema()
        tags = UITags()
        tags.remove_tag("enabled")
        app = make_processor_app(config=config, tags=tags, ui_source=TagBoundUI)

        app._resolve_tags()

        with pytest.raises(ValueError, match="enabled"):
            app._resolve_ui()
