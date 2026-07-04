import asyncio
import copy
from datetime import timedelta

import pytest

from pydoover import config, ui
from pydoover.config import ApplicationPosition
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
        )

        data = multiplot.to_dict()

        assert data["type"] == "uiMultiPlot"
        assert data["series"]["temperature"]["dataType"] == "number"
        assert data["series"]["temperature"]["displayString"] == "Temperature"
        assert data["series"]["temperature"]["colour"] == "red"
        assert data["series"]["temperature"]["units"] == "C"

    def test_timestamp_serializes_ms_epoch_precision_and_absolute_format(self):
        timestamp = ui.Timestamp(
            "Turns off at",
            name="turns_off_at",
            value=1_777_511_327_616,
            precision="second",
            absolute_format="HH:mm:ss",
        )

        data = timestamp.to_dict()

        assert data["type"] == "uiTimestamp"
        assert data["currentValue"] == 1_777_511_327_616
        assert data["precision"] == "second"
        assert data["absoluteFormat"] == "HH:mm:ss"

    def test_timestamp_still_serializes_datetime_values_as_ms_since_epoch(self):
        from datetime import datetime, timezone

        timestamp = ui.Timestamp(
            "Started",
            name="started",
            value=datetime(2026, 6, 24, 12, 0, tzinfo=timezone.utc),
        )

        assert timestamp.to_dict()["currentValue"] == 1_782_302_400_000


class TestLiveTagPropagation:
    """The customer-site gates Live Mode on a UI element's ``live`` field;
    that field must be derived from the underlying tag's ``live=True`` flag
    so dashboard authors don't have to declare it twice."""

    def _live_tags_cls(self):
        from pydoover.tags import Number

        class LiveTags(Tags):
            stream = Number(live=True)
            quiet = Number()

        return LiveTags

    def test_variable_inherits_live_from_class_tag_reference(self):
        LiveTags = self._live_tags_cls()

        class MyUI(ui.UI):
            stream = ui.NumericVariable("Stream", value=LiveTags.stream, name="stream")
            quiet = ui.NumericVariable("Quiet", value=LiveTags.quiet, name="quiet")

        tags = LiveTags("app", FakeTagsManager(), FakeSchema())
        ui_obj = MyUI(None, tags, "app").bind_tags(tags)

        assert ui_obj.stream.to_dict()["live"] is True
        assert "live" not in ui_obj.quiet.to_dict()

    def test_variable_inherits_live_from_bound_tag(self):
        LiveTags = self._live_tags_cls()
        tags = LiveTags("app", FakeTagsManager(), FakeSchema())

        var = ui.NumericVariable("Stream", value=tags.stream, name="stream")

        assert var.to_dict()["live"] is True

    def test_variable_inherits_live_via_tag_ref(self):
        LiveTags = self._live_tags_cls()

        var = ui.NumericVariable(
            "Stream", value=ui.tag_ref(LiveTags.stream), name="stream"
        )

        assert var.to_dict()["live"] is True

    def test_series_inherits_live_from_class_tag_reference(self):
        LiveTags = self._live_tags_cls()

        class MyUI(ui.UI):
            plot = ui.Multiplot(
                "Plot",
                name="plot",
                series=[
                    ui.Series("Stream", value=LiveTags.stream, data_type="number"),
                    ui.Series("Quiet", value=LiveTags.quiet, data_type="number"),
                ],
            )

        tags = LiveTags("app", FakeTagsManager(), FakeSchema())
        ui_obj = MyUI(None, tags, "app").bind_tags(tags)
        data = ui_obj.plot.to_dict()

        assert data["series"]["stream"]["live"] is True
        assert "live" not in data["series"]["quiet"]

    def test_no_live_when_value_is_literal(self):
        var = ui.NumericVariable("Stream", value=5, name="stream")
        series = ui.Series("Stream", value=5, data_type="number")

        assert "live" not in var.to_dict()
        assert "live" not in series.to_dict()


class TestConfigRefResolution:
    def _make_schema_cls(self):
        class S(config.Schema):
            position = ApplicationPosition(default=120)

        return S

    def test_resolves_position_from_explicit_deployment_value(self):
        schema = self._make_schema_cls()()
        schema._inject_deployment_config({"dv_app_position": 120})

        class MyUI(ui.UI):
            pass

        assert MyUI(schema, None, "app_key").to_schema()["position"] == 120

    def test_resolves_position_from_schema_default_when_omitted(self):
        schema = self._make_schema_cls()()
        schema._inject_deployment_config({})

        class MyUI(ui.UI):
            pass

        assert MyUI(schema, None, "app_key").to_schema()["position"] == 120

    def test_falls_back_to_lookup_default_when_element_absent(self):
        class S(config.Schema):
            pass

        schema = S()
        schema._inject_deployment_config({})

        class MyUI(ui.UI):
            pass

        assert MyUI(schema, None, "app_key").to_schema()["position"] == 100


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


class TestUiCommandOptions:
    def test_command_timeout_and_direct_serialize(self):
        button = ui.Button(
            "Restart",
            name="restart",
            command_timeout=timedelta(seconds=5),
            direct=True,
        )

        data = button.to_dict()

        assert data["commandTimeout"] == 5000
        assert data["direct"] is True

    def test_command_timeout_accepts_seconds(self):
        button = ui.Button("Restart", name="restart", command_timeout=2.5)

        assert button.to_dict()["commandTimeout"] == 2500

    def test_options_omitted_by_default(self):
        data = ui.Button("Restart", name="restart").to_dict()

        assert "commandTimeout" not in data
        assert "direct" not in data


class TestDatetimeInputOptions:
    def test_datetime_options_serialize(self):
        dt = ui.DatetimeInput(
            "Start",
            name="start",
            pickers=["date"],
            direction="future",
            max_future=timedelta(days=7),
            max_past=3600,
        )

        data = dt.to_dict()

        assert data["pickers"] == ["date"]
        assert data["direction"] == "future"
        assert data["maxFuture"] == 7 * 24 * 60 * 60 * 1000
        assert data["maxPast"] == 3600 * 1000
        assert "includeTime" not in data

    def test_include_time_is_deprecated_alias(self):
        with pytest.warns(DeprecationWarning):
            dt = ui.DatetimeInput("Start", name="start", include_time=True)

        assert dt.to_dict()["pickers"] == ["date", "time"]

    def test_time_input_no_deprecation(self):
        data = ui.TimeInput("Start Time", name="start_time").to_dict()

        assert data["type"] == "uiTimeInput"
        assert "pickers" not in data


class TestTabContainerOptions:
    def test_default_page_serializes(self):
        tabs = ui.TabContainer("Tabs", name="tabs", default_page=1)

        assert tabs.to_dict()["defaultPage"] == 1

    def test_default_page_omitted_by_default(self):
        assert "defaultPage" not in ui.TabContainer("Tabs", name="tabs").to_dict()
