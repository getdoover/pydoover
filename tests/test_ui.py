import asyncio
import copy

import pytest

from pydoover import ui
from pydoover.tags import Tag, Tags

from tests.test_tags import (
    DockerApplication,
    FakeRuntimeDeviceAgent,
    FakeRuntimeModbusInterface,
    FakeRuntimePlatformInterface,
    FakeSchema,
    FakeTagsManager,
    MyAppTags,
)


class UITags(Tags):
    voltage = Tag("number")
    speed = Tag("number", default=0)
    enabled = Tag("boolean", default=False)
    mode = Tag("string", default="idle")


class BaseUI(ui.UI):
    voltage = ui.NumericVariable("Voltage", name="voltage")


class ExtendedUI(BaseUI):
    enabled = ui.BooleanVariable("Enabled", value=False, name="enabled")


class TagBoundUI(ui.UI):
    voltage = ui.NumericVariable(
        "Voltage",
        name="voltage",
        value=UITags.voltage,
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
        "Mode",
        name="mode",
        options=[ui.Option("Auto"), ui.Option("Manual")],
    )


def make_tags(app_key: str = "test_app") -> UITags:
    return UITags(app_key, FakeTagsManager(), FakeSchema())


class TestDeclarativeUI:
    def test_declaration_order_and_inheritance_are_preserved(self):
        ui_obj = ExtendedUI(None, None, "test_app")

        assert [element.name for element in ui_obj.children] == ["voltage", "enabled"]

    def test_instances_do_not_share_element_state(self):
        first = BaseUI(None, None, "test_app")
        second = BaseUI(None, None, "test_app")

        first.voltage.hidden = True

        assert second.voltage.hidden is False

    def test_add_and_remove_element_are_instance_local(self):
        ui_obj = BaseUI(None, None, "test_app")
        extra = ui.TextVariable("Extra", value="hello", name="extra")

        ui_obj.add_element(extra)

        assert ui_obj.extra is extra
        assert [element.name for element in ui_obj.children] == ["voltage", "extra"]

        ui_obj.remove_element("extra")

        assert "extra" not in ui_obj.__dict__
        assert [element.name for element in ui_obj.children] == ["voltage"]

    def test_tag_binding_survives_deepcopy_without_serializing_missing_default(self):
        binding = ui.tag_ref("voltage", tag_type="number")
        copied = copy.deepcopy(binding)

        assert copied.to_lookup() == "$tag.app().voltage:number"


class TestTagReferenceSerialization:
    def test_class_tag_reference_serializes_to_compact_lookup_string(self):
        ui_obj = TagBoundUI(None, None, "test_app").bind_tags(make_tags())

        data = ui_obj.voltage.to_dict()

        assert data["currentValue"] == "$tag.app().voltage:number"

    def test_bound_tag_reference_serializes_with_default(self):
        tags = MyAppTags("test_app", FakeTagsManager(), FakeSchema())

        class FactoryUI(ui.UI):
            voltage = ui.NumericVariable("Voltage", name="voltage", value=tags.speed)

        ui_obj = FactoryUI(None, tags, "test_app").bind_tags(tags)

        assert ui_obj.voltage.to_dict()["currentValue"] == "$tag.app().speed:number:0"

    def test_recursive_serialization_handles_nested_objects_lists_and_ranges(self):
        ui_obj = TagBoundUI(None, None, "test_app").bind_tags(make_tags())
        voltage = ui_obj.voltage.to_dict()

        assert voltage["hidden"] == "$tag.app().enabled:boolean:false"
        assert voltage["conditions"]["armed"] == "$tag.app().enabled:boolean:false"
        assert voltage["ranges"][0]["label"] == '$tag.app().mode:string:"idle"'
        assert voltage["ranges"][0]["max"] == "$tag.app().voltage:number"

    def test_name_field_cannot_reference_a_tag(self):
        bad = ui.TextVariable("Bad", value="x", name="bad")
        bad.name = MyAppTags.voltage

        with pytest.raises(ValueError, match="name"):
            bad.to_dict()

    def test_missing_class_level_tag_reference_raises(self):
        tags = make_tags()
        tags.remove_tag("enabled")

        class MissingUI(ui.UI):
            status = ui.BooleanVariable("Status", value=UITags.enabled, name="status")

        with pytest.raises(ValueError, match="enabled"):
            MissingUI(None, tags, "test_app").bind_tags(tags)


class TestCanonicalUiTypes:
    def test_select_serializes_with_canonical_type_and_options(self):
        select = ui.Select(
            "Mode",
            name="mode",
            options=[ui.Option("Auto"), ui.Option("Manual")],
        )

        data = select.to_dict()

        assert data["type"] == "uiSelect"
        assert data["options"]["auto"]["displayString"] == "Auto"

    def test_button_serializes_with_canonical_type(self):
        button = ui.Button("Restart", name="restart", label_string="Restart now")

        data = button.to_dict()

        assert data["type"] == "uiButton"
        assert data["labelString"] == "Restart now"

    def test_float_and_time_inputs_serialize_with_canonical_types(self):
        float_input = ui.FloatInput("Setpoint", name="setpoint", min_val=0, max_val=5)
        time_input = ui.TimeInput("Start Time", name="start_time")

        assert float_input.to_dict()["type"] == "uiFloatInput"
        assert float_input.to_dict()["min"] == 0
        assert time_input.to_dict()["type"] == "uiTimeInput"

    def test_multiplot_serializes_series(self):
        multiplot = ui.Multiplot(
            "History",
            name="history",
            series=[
                ui.Series(
                    "Temperature",
                    value=5,
                    data_type="number",
                    colour="red",
                    units="C",
                )
            ],
            title="History",
        )

        data = multiplot.to_dict()

        assert data["type"] == "uiMultiPlot"
        assert data["series"]["temperature"]["dataType"] == "number"
        assert data["series"]["temperature"]["displayString"] == "Temperature"
        assert data["series"]["temperature"]["colour"] == "red"
        assert data["series"]["temperature"]["units"] == "C"


class TestApplicationUIResolution:
    def test_async_docker_startup_binds_dynamic_ui_to_runtime_tags(self, monkeypatch):
        docker_application_module = pytest.importorskip("pydoover.docker.application")
        monkeypatch.setattr(docker_application_module, "RUN_HEALTHCHECK", False)

        class DynamicStartupUI(ui.UI):
            async def setup(self):
                self.add_element(
                    ui.NumericVariable(
                        "Voltage",
                        name="voltage",
                        value=self.tags.speed,
                    )
                )
                self.add_element(
                    ui.Submodule(
                        "Telemetry",
                        name="telemetry",
                        children=[
                            ui.NumericVariable(
                                "Inner Voltage",
                                name="inner_voltage",
                                value=self.tags.get_tag("speed"),
                            )
                        ],
                    )
                )

        class AsyncUIApp(DockerApplication):
            config_cls = FakeSchema
            tags_cls = MyAppTags
            ui_cls = DynamicStartupUI

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
            await app._setup()

            assert (
                app.ui.voltage.to_dict()["currentValue"] == "$tag.app().speed:number:0"
            )
            assert (
                app.ui.telemetry.to_dict()["children"]["inner_voltage"]["currentValue"]
                == "$tag.app().speed:number:0"
            )

        asyncio.run(run_test())
