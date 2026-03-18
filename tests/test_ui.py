import asyncio
import copy
import warnings
from typing import Any

import pytest

from pydoover import ui
from pydoover.tags import Tag, Tags

from tests.test_tags import (
    DockerApplication,
    FakeRuntimeDeviceAgent,
    FakeRuntimeModbusInterface,
    FakeRuntimePlatformInterface,
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
    mode = ui.Select(
        "mode",
        "Mode",
        current_value=UITags.mode,
        options=[ui.Option("auto", UITags.mode)],
    )


def make_docker_app(config=None, tags_class=None, ui_class=None, app_key="test_app"):
    app_cls = type(
        "ConfiguredDockerApplication",
        (DockerApplication,),
        {"tags_class": tags_class, "ui_class": ui_class},
    )
    app = object.__new__(app_cls)
    app.config = config or FakeSchema()
    app.app_key = app_key
    app.tag_manager = FakeDockerAppTagManager()
    app.ui_manager = ui.UIManager(app_key=app_key)
    app.tags = None
    app.ui = None
    return app


def make_processor_app(config=None, tags_class=None, ui_class=None, app_key="test_app"):
    app_cls = type(
        "ConfiguredProcessorApplication",
        (ProcessorApplication,),
        {"tags_class": tags_class, "ui_class": ui_class},
    )
    app = object.__new__(app_cls)
    app.config = config or FakeSchema()
    app.app_key = app_key
    app.tag_manager = FakeProcessorTagManager()
    app.ui_manager = ui.UIManager(app_key=app_key)
    app.tags = None
    app.ui = None
    return app


async def _resolve_app_async(app):
    await app._resolve_tags()
    return await app._resolve_ui()


def resolve_app(app):
    return asyncio.run(_resolve_app_async(app))


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

    def test_tag_binding_survives_deepcopy_without_serializing_missing_default(self):
        binding = ui.tag_ref("voltage", tag_type="number")
        copied = copy.deepcopy(binding)

        assert copied.to_lookup() == "$tag.voltage:number"


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

    def test_runtime_bound_tag_from_get_tag_is_supported(self):
        tags = MyAppTags()

        class FactoryUI(ui.UI):
            voltage = ui.NumericVariable(
                "voltage",
                "Voltage",
                curr_val=tags.get_tag("speed"),
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
        assert mode["options"]["auto"]["displayString"] == '$tag.mode:string:"idle"'

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


class TestCanonicalUiTypes:
    def test_select_serializes_with_canonical_type_and_options(self):
        select = ui.Select(
            "mode",
            "Mode",
            options=[ui.Option("auto", "Auto"), ui.Option("manual", "Manual")],
            current_value="auto",
        )

        data = select.to_dict()

        assert data["type"] == "uiSelect"
        assert data["options"]["auto"]["displayString"] == "Auto"
        assert data["currentValue"] == "auto"

    def test_button_serializes_with_canonical_type(self):
        button = ui.Button("restart", "Restart", label_string="Restart now")

        data = button.to_dict()

        assert data["type"] == "uiButton"
        assert data["labelString"] == "Restart now"

    def test_float_and_time_inputs_serialize_with_canonical_types(self):
        float_input = ui.FloatInput("setpoint", "Setpoint", min_val=0, max_val=5)
        time_input = ui.TimeInput("start_time", "Start Time", current_value=60)

        assert float_input.to_dict()["type"] == "uiFloatInput"
        assert float_input.to_dict()["min"] == 0
        assert time_input.to_dict()["type"] == "uiTimeInput"

    def test_multiplot_serializes_record_based_series_schema(self):
        multiplot = ui.Multiplot(
            "history",
            "History",
            series={
                "temperature": {
                    "dataType": "number",
                    "displayString": "Temperature",
                    "colour": "red",
                    "units": "C",
                }
            },
            title="History",
        )

        data = multiplot.to_dict()

        assert data["type"] == "uiMultiPlot"
        assert data["series"]["temperature"]["dataType"] == "number"
        assert data["series"]["temperature"]["displayString"] == "Temperature"
        assert "colours" not in data
        assert "sharedAxis" not in data


class TestLegacyUiAliases:
    def test_legacy_aliases_warn_and_preserve_legacy_types(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            state_command = ui.StateCommand(
                "mode",
                "Mode",
                user_options=[ui.Option("auto", "Auto")],
            )
            text_param = ui.TextParameter("notes", "Notes")

        messages = [str(w.message) for w in caught]

        assert any("StateCommand is deprecated" in message for message in messages)
        assert any("TextParameter is deprecated" in message for message in messages)
        assert state_command.to_dict()["type"] == "uiStateCommand"
        assert "userOptions" in state_command.to_dict()
        assert text_param.to_dict()["type"] == "uiTextParam"

    def test_multiplot_legacy_series_input_warns_and_normalizes_to_record_schema(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            multiplot = ui.Multiplot(
                "history",
                "History",
                series=["temperature", "pressure"],
                series_colours=["red", "blue"],
                series_active=[True, False],
                shared_axis=[True, False],
                step_labels=["Low", "High"],
            )

        messages = [str(w.message) for w in caught]
        data = multiplot.to_dict()

        assert any("Legacy uiMultiPlot list-based schema is deprecated" in message for message in messages)
        assert data["series"]["temperature"]["colour"] == "red"
        assert data["series"]["temperature"]["active"] is True
        assert data["series"]["pressure"]["sharedAxis"] is False
        assert data["series"]["temperature"]["stepLabels"] == ["Low", "High"]
        assert "colours" not in data


class TestApplicationUIResolution:
    def test_docker_resolves_ui_subclass_and_installs_it(self):
        app = make_docker_app(tags_class=UITags, ui_class=TagBoundUI)
        resolved = resolve_app(app)

        assert isinstance(resolved, TagBoundUI)
        assert app.ui is resolved
        assert app.ui_manager.get_element("voltage") is resolved.voltage

    def test_docker_ui_setup_receives_config_and_tags(self):
        config = FakeSchema()
        config._inject_deployment_config({"some_flag": True})
        calls = []

        class ConfiguredUI(ui.UI):
            async def setup(self, config: Any = None, tags: Any = None) -> None:
                calls.append((config.some_flag, tags))
                self.add_element(
                    "voltage",
                    ui.NumericVariable(
                        "voltage",
                        "Voltage",
                        curr_val=tags.speed,
                    ),
                )

        app = make_docker_app(config=config, tags_class=MyAppTags, ui_class=ConfiguredUI)
        resolved = resolve_app(app)

        assert isinstance(resolved, ui.UI)
        assert calls == [(True, app.tags)]
        assert resolved.voltage.to_dict()["currentValue"] == "$tag.speed:number:0"

    def test_docker_ui_setup_supports_dynamic_children_with_manager_bound_tags(self):
        class DynamicUI(ui.UI):
            async def setup(self, config: Any = None, tags: Any = None) -> None:
                del config
                self.add_element(
                    "voltage",
                    ui.NumericVariable(
                        "voltage",
                        "Voltage",
                        curr_val=tags.speed,
                    ),
                )
                self.add_element(
                    "telemetry",
                    ui.Submodule(
                        "telemetry",
                        "Telemetry",
                        children=[
                            ui.NumericVariable(
                                "inner_voltage",
                                "Inner Voltage",
                                curr_val=tags.get_tag("speed"),
                            )
                        ],
                    ),
                )

        app = make_docker_app(config=FakeSchema(), tags_class=MyAppTags, ui_class=DynamicUI)
        resolved = resolve_app(app)

        assert resolved.voltage.to_dict()["currentValue"] == "$tag.speed:number:0"
        telemetry = resolved.telemetry.to_dict()
        assert telemetry["children"]["inner_voltage"]["currentValue"] == "$tag.speed:number:0"

    def test_docker_ui_class_none_is_allowed(self):
        app = make_docker_app(tags_class=MyAppTags, ui_class=None)
        resolved = resolve_app(app)

        assert resolved is None
        assert app.ui is None

    def test_processor_resolves_ui_after_tags(self):
        config = FakeSchema()
        config._inject_deployment_config({"some_flag": True})
        app = make_processor_app(config=config, tags_class=UITags, ui_class=TagBoundUI)
        resolved = resolve_app(app)

        assert isinstance(resolved, TagBoundUI)
        assert app.ui_manager.get_command("mode") is resolved.mode

    def test_processor_ui_setup_receives_config_and_tags(self):
        config = FakeSchema()
        calls = []

        class ConfiguredUI(TagBoundUI):
            async def setup(self, config: Any = None, tags: Any = None) -> None:
                calls.append((config, tags))

        app = make_processor_app(config=config, tags_class=UITags, ui_class=ConfiguredUI)
        resolved = resolve_app(app)

        assert isinstance(resolved, TagBoundUI)
        assert calls == [(config, app.tags)]

    def test_processor_missing_tag_reference_raises_deterministically(self):
        config = FakeSchema()
        
        class MissingEnabledTags(UITags):
            async def setup(self, config: Any = None) -> None:
                del config
                self.remove_tag("enabled")

        app = make_processor_app(
            config=config,
            tags_class=MissingEnabledTags,
            ui_class=TagBoundUI,
        )

        with pytest.raises(ValueError, match="enabled"):
            resolve_app(app)

    def test_async_docker_startup_handles_ui_setup_with_runtime_bound_tags(self, monkeypatch):
        docker_application_module = pytest.importorskip("pydoover.docker.application")
        monkeypatch.setattr(docker_application_module, "RUN_HEALTHCHECK", False)

        class DynamicStartupUI(ui.UI):
            async def setup(self, config: Any = None, tags: Any = None) -> None:
                del config
                self.add_element(
                    "voltage",
                    ui.NumericVariable(
                        "voltage",
                        "Voltage",
                        curr_val=tags.speed,
                    ),
                )
                self.add_element(
                    "telemetry",
                    ui.Submodule(
                        "telemetry",
                        "Telemetry",
                        children=[
                            ui.NumericVariable(
                                "inner_voltage",
                                "Inner Voltage",
                                curr_val=tags.get_tag("speed"),
                            )
                        ],
                    ),
                )

        class AsyncUIApp(DockerApplication):
            config_class = FakeSchema
            tags_class = MyAppTags
            ui_class = DynamicStartupUI

            async def setup(self):
                return None

            async def main_loop(self):
                return None

        async def run_test():
            device_agent = FakeRuntimeDeviceAgent()
            app = AsyncUIApp(
                app_key="test_app",
                device_agent=device_agent,
                platform_iface=FakeRuntimePlatformInterface(is_async=True),
                modbus_iface=FakeRuntimeModbusInterface(is_async=True),
                test_mode=True,
                healthcheck_port=0,
            )

            task = asyncio.create_task(app._run())
            try:
                await app.wait_until_ready()
                assert app.ui.voltage.to_dict()["currentValue"] == "$tag.speed:number:0"
                assert (
                    app.ui.telemetry.to_dict()["children"]["inner_voltage"]["currentValue"]
                    == "$tag.speed:number:0"
                )
            finally:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task

        asyncio.run(run_test())
