from copy import deepcopy

import pytest

from jsonschema import ValidationError, validate
from pydoover import config


class NestedConfig(config.Object):
    a = config.Integer("G A", default=1, minimum=0)
    b = config.Number("G B", exclusive_minimum=0)

    def __init__(self, display_name: str = "G"):
        super().__init__(display_name)


class ConfigSchemaA(config.Schema):
    a = config.Integer("A", default=1, minimum=0)
    b = config.Number("B", exclusive_minimum=0)
    c = config.String("C", pattern=r"^[a-zA-Z0-9_]+$")
    d = config.Enum("D", choices=["a", "b", "c"], default="a")
    e = config.Boolean("E", default=False)
    f = config.Array("F", element=config.Integer("F Element"))
    g = NestedConfig("G")


SAMPLE_CONFIG_A = {
    "a": 1,
    "b": 0.5,
    "c": "valid_string",
    "d": "a",
    "e": False,
    "f": [1, 2, 3],
    "g": {"g_a": 1, "g_b": 0.5},
}


class TestConfigSchemaA:
    def test_ok_schema(self):
        validate(deepcopy(SAMPLE_CONFIG_A), ConfigSchemaA().to_schema())

    @pytest.mark.parametrize(
        "key, value",
        [
            ("a", 1.5),
            ("b", "a string"),
            ("c", True),
            ("d", 0),
            ("e", "not_a_boolean"),
            ("f", ["a", "b", "c"]),
            ("g", {"g_a": "not_an_int", "g_b": 0.5}),
            ("g", "not-an-object"),
            ("g", ["an-array-of-string"]),
        ],
    )
    def test_invalid_type(self, key, value):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config[key] = value
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

    def test_enum(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["d"] = "not-a-choice"
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

        sample_config["d"] = "c"
        validate(sample_config, ConfigSchemaA().to_schema())

    def test_minimum(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["a"] = -1
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

        sample_config["a"] = 0
        validate(sample_config, ConfigSchemaA().to_schema())

    def test_exclusive_min(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["b"] = 0
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

    def test_array(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["f"] = [1, 2, "not an int"]
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

        sample_config["f"] = []
        validate(sample_config, ConfigSchemaA().to_schema())

        sample_config["f"] = ["not an int"]
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

    def test_object(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["g"]["g_a"] = "not an int"
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

        sample_config["g"]["g_b"] = 0
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_schema())

    def test_runtime_access_via_value(self):
        schema = ConfigSchemaA()
        schema._inject_deployment_config(SAMPLE_CONFIG_A)

        assert schema.a.value == 1
        assert schema.b.value == 0.5
        assert schema.c.value == "valid_string"
        assert schema.d.value == "a"
        assert schema.e.value is False
        assert [elem.value for elem in schema.f.elements] == [1, 2, 3]

    def test_element_metadata_accessible(self):
        schema = ConfigSchemaA()
        schema._inject_deployment_config(SAMPLE_CONFIG_A)

        assert schema.a.value == 1
        assert schema.a.minimum == 0

    def test_missing_required_scalar_still_raises(self):
        class FreshSchema(config.Schema):
            c = config.String("C")

        with pytest.raises(ValueError, match="c"):
            _ = FreshSchema().c.value

    def test_object_subclasses_do_not_share_elements(self):
        class ObjA(config.Object):
            x = config.String("X")

        class ObjB(config.Object):
            y = config.Integer("Y", default=1)

        a = ObjA("a")
        b = ObjB("b")

        a_keys = set(a._elements.keys())
        b_keys = set(b._elements.keys())

        assert "x" in a_keys
        assert "y" not in a_keys
        assert "y" in b_keys

    def test_nested_object_values_accessible(self):
        class Inner(config.Object):
            x = config.String("X")
            y = config.Integer("Y", default=0)

        class Outer(config.Schema):
            inner = Inner("Inner")

        schema = Outer()
        schema._inject_deployment_config({"inner": {"x": "hello", "y": 42}})

        assert schema.inner.x.value == "hello"
        assert schema.inner.y.value == 42

    def test_tagref_schema_emits_format_and_required_fields(self):
        class S(config.Schema):
            ref = config.TagRef("Ref")

        schema = S().to_schema()
        ref_schema = schema["properties"]["ref"]

        assert ref_schema["type"] == "object"
        assert ref_schema["format"] == "doover-tag-reference"

        # Sub-fields are present and addressable by their JSON keys.
        sub_props = ref_schema["properties"]
        assert set(sub_props) == {"reference_name", "agent_id", "app_name", "tag_name"}

        # reference_name / app_name / tag_name are required; agent_id has default=None.
        assert set(ref_schema["required"]) == {"reference_name", "app_name", "tag_name"}

    def test_tagref_loads_runtime_values(self):
        class S(config.Schema):
            ref = config.TagRef("Ref")

        schema = S()
        schema._inject_deployment_config(
            {
                "ref": {
                    "reference_name": "upstream_pump_status",
                    "app_name": "pump_controller",
                    "tag_name": "running",
                }
            }
        )

        assert schema.ref.reference_name.value == "upstream_pump_status"
        assert schema.ref.agent_id.value is None
        assert schema.ref.app_name.value == "pump_controller"
        assert schema.ref.tag_name.value == "running"

    def test_tagref_accepts_agent_id_when_supplied(self):
        class S(config.Schema):
            ref = config.TagRef("Ref")

        schema = S()
        schema._inject_deployment_config(
            {
                "ref": {
                    "reference_name": "x",
                    "agent_id": "42",
                    "app_name": "a",
                    "tag_name": "t",
                }
            }
        )

        assert schema.ref.agent_id.value == "42"

    def test_optional_tagref_is_not_required(self):
        class S(config.Schema):
            ref = config.TagRef("Ref", default=None, required=False, name="ref")

        schema = S.to_schema()
        # Optional TagRef must not appear in the schema's `required` list.
        assert "ref" not in schema["required"]

    def test_optional_tagref_can_be_omitted_from_deployment_config(self):
        from pydoover.config import NotSet

        class S(config.Schema):
            ref = config.TagRef("Ref", default=None, required=False, name="ref")

        schema = S()
        schema._inject_deployment_config({})  # must not raise

        # Sub-fields stay unset; downstream code uses the same NotSet check
        # in `_resolve_remote_tags` to decide whether to skip the binding.
        assert schema.ref.reference_name._value is NotSet

    def test_optional_tagref_accepts_null_in_deployment_config(self):
        class S(config.Schema):
            ref = config.TagRef("Ref", default=None, required=False, name="ref")

        schema = S()
        schema._inject_deployment_config({"ref": None})  # must not raise

    def test_optional_tagref_accepts_empty_object_in_deployment_config(self):
        class S(config.Schema):
            ref = config.TagRef("Ref", default=None, required=False, name="ref")

        schema = S()
        schema._inject_deployment_config({"ref": {}})  # must not raise

    def test_required_tagref_still_required_when_omitted(self):
        class S(config.Schema):
            ref = config.TagRef("Ref")  # default: not optional

        schema = S()
        with pytest.raises(ValueError, match="ref"):
            schema._inject_deployment_config({})

    def test_nested_object_applies_defaults_for_missing_keys(self):
        # Schema applies defaults for keys absent from incoming data;
        # nested Object must do the same so .value doesn't raise on the
        # half of the schema the user didn't supply.
        class Inner(config.Object):
            present = config.Integer("Present")
            missing_with_default = config.Integer("Missing", default=42)

        class Outer(config.Schema):
            inner = Inner("Inner")

        schema = Outer()
        schema._inject_deployment_config({"inner": {"present": 1}})

        assert schema.inner.present.value == 1
        assert schema.inner.missing_with_default.value == 42

    def test_nested_object_raises_for_missing_required_key(self):
        # Match Schema's eager-raise behaviour for required-but-missing.
        class Inner(config.Object):
            required_no_default = config.Integer("Req")

        class Outer(config.Schema):
            inner = Inner("Inner")

        with pytest.raises(ValueError, match="req"):
            Outer()._inject_deployment_config({"inner": {}})

    def test_object_load_data_handles_none(self):
        # ``load_data(None)`` is what nested loaders pass when the parent
        # key is absent / null. It must not crash.
        class Inner(config.Object):
            n = config.Integer("N", default=7)

        inner = Inner("inner")
        inner.load_data(None)
        assert inner.n.value == 7

    def test_additional_elements_freeform_keys_are_readable(self):
        # ``additional_elements=True`` synthesises a ConfigElement for each
        # free-form key. Without load_data on it, .value raises for any
        # non-None value — which makes the feature unusable.
        obj = config.Object("o", additional_elements=True)
        obj.load_data({"freeform_int": 42, "freeform_str": "hi"})

        assert obj._elements["freeform_int"].value == 42
        assert obj._elements["freeform_str"].value == "hi"

    def test_subclass_can_redeclare_to_override_default(self):
        class Base(config.Schema):
            n = config.Integer("N", default=1)
            arr = config.Array("Arr", element=config.String("Item"), default=[])

        class Sub(Base):
            n = config.Integer("N", default=99)
            arr = config.Array("Arr", element=config.String("Item"), default=["a", "b"])

        # Base defaults are unaffected
        assert Base._element_map["n"].default == 1
        assert Base._element_map["arr"].default == []

        # Subclass picks up overridden defaults
        assert Sub._element_map["n"].default == 99
        assert Sub._element_map["arr"].default == ["a", "b"]

        # Field order in subclass matches the base (override preserves position)
        assert list(Sub._element_map.keys()) == list(Base._element_map.keys())


class TestNestedKwargOverrides:
    """Django-style ``child__attr`` kwargs on Object subclasses route to the
    matching nested element, sparing callers from manual ``_elements[...]``
    poking when they only want to tweak a sub-field's metadata."""

    def test_overrides_default_on_child(self):
        ref = config.TagRef(
            "Gearbox 1 Temp",
            reference_name__default="gearbox1_temp",
        )
        assert ref._elements["reference_name"].default == "gearbox1_temp"
        assert ref._elements["reference_name"].required is False

    def test_overrides_advanced_flag(self):
        ref = config.TagRef(
            "Gearbox 1 Temp",
            reference_name__advanced=True,
        )
        assert ref._elements["reference_name"].advanced is True
        assert "x-advanced" in ref._elements["reference_name"].to_dict()

    def test_multiple_overrides_on_same_child(self):
        ref = config.TagRef(
            "Gearbox 1 Temp",
            reference_name__default="gearbox1_temp",
            reference_name__advanced=True,
            reference_name__hidden=False,
        )
        sub = ref._elements["reference_name"]
        assert sub.default == "gearbox1_temp"
        assert sub.advanced is True
        assert sub.hidden is False

    def test_per_instance_isolation(self):
        # Two TagRefs with different overrides must not bleed into each other,
        # since ``_elements`` is deep-copied from the class template.
        a = config.TagRef("A", reference_name__default="a_ref")
        b = config.TagRef("B", reference_name__default="b_ref")
        assert a._elements["reference_name"].default == "a_ref"
        assert b._elements["reference_name"].default == "b_ref"

    def test_unknown_child_raises(self):
        with pytest.raises(TypeError, match="no child element named 'nonexistent'"):
            config.TagRef("X", nonexistent__default="oops")

    def test_unknown_attr_on_known_child_raises(self):
        with pytest.raises(TypeError, match="no attribute 'nonsense_attr'"):
            config.TagRef("X", reference_name__nonsense_attr="oops")

    def test_invalid_path_no_child_segment_raises(self):
        # Single-underscore key isn't intercepted at all (no ``__``); a key
        # like ``__attr`` (leading double-underscore, empty child path) is.
        class Holder(config.Object):
            inner = config.String("Inner")

        with pytest.raises(TypeError, match="expected '<child>__<attr>'"):
            Holder("h", **{"__default": "x"})

    def test_deep_nested_override(self):
        class Inner(config.Object):
            count = config.Integer("Count", default=1)

        class Outer(config.Object):
            inner = Inner("Inner")

        outer = Outer("Outer", inner__count__default=99)
        assert outer._elements["inner"]._elements["count"].default == 99

    def test_schema_emits_overridden_default_in_to_dict(self):
        # End-to-end: the override flows into the exported schema so the UI
        # picks up the seeded value without a separate ``export()`` step.
        class S(config.Schema):
            ref = config.TagRef(
                "Gearbox 1 Temp",
                name="ref",
                reference_name__default="gearbox1_temp",
                reference_name__advanced=True,
            )

        schema = S.to_schema()
        ref_props = schema["properties"]["ref"]["properties"]
        assert ref_props["reference_name"]["default"] == "gearbox1_temp"
        assert ref_props["reference_name"]["x-advanced"] is True
        # And reference_name is no longer in the required list (since it now
        # has a default).
        assert "reference_name" not in schema["properties"]["ref"]["required"]


class TestExplicitRequiredFlag:
    """``required`` is a tri-state on every ConfigElement: ``None`` (default)
    keeps the historical "required iff default is NotSet" rule; ``True`` /
    ``False`` override it. ``required=False`` without a default is rejected
    at construction because the loader would have nothing to substitute."""

    def test_required_none_falls_back_to_default_set(self):
        with_default = config.Integer("With Default", default=5)
        without_default = config.Integer("Without Default")
        assert with_default.required is False
        assert without_default.required is True

    def test_required_true_with_default_still_marks_required(self):
        # Useful when the schema author wants to force operators to confirm a
        # value explicitly, even though the loader knows what to fall back to.
        elem = config.Integer("Forced", default=5, required=True)
        assert elem.required is True
        # Schema reflects the override.
        assert elem.to_dict()["x-required"] is True
        # Type stays non-nullable (mirrors the historical required-True path).
        assert elem.to_dict()["type"] == "integer"

    def test_required_false_with_default_marks_optional(self):
        elem = config.Integer("Optional", default=5, required=False)
        assert elem.required is False
        # Schema reflects the override.
        d = elem.to_dict()
        assert d["x-required"] is False
        # Type becomes nullable, mirroring the existing not-required path.
        assert d["type"] == ["integer", "null"]
        assert d["default"] == 5

    def test_required_false_without_default_raises(self):
        with pytest.raises(ValueError, match="needs a default"):
            config.Integer("Bad", required=False)

    def test_required_false_with_none_default_is_ok(self):
        # ``default=None`` is a real, non-NotSet value (means "explicitly
        # null"), so this satisfies the validation.
        elem = config.String("Optional", default=None, required=False)
        assert elem.required is False
        assert elem.default is None

    def test_schema_required_list_honours_explicit_override(self):
        class S(config.Schema):
            forced = config.Integer("Forced", default=5, required=True, name="forced")
            opt = config.Integer("Opt", default=5, required=False, name="opt")
            implicit_required = config.Integer("Imp", name="implicit_required")

        schema = S.to_schema()
        assert "forced" in schema["required"]
        assert "opt" not in schema["required"]
        assert "implicit_required" in schema["required"]

    def test_object_load_data_skips_overridden_optional_when_absent(self):
        # An Object child whose required is False (via override) and which is
        # missing from incoming data should fall back to its default rather
        # than raise.
        class Holder(config.Object):
            x = config.Integer("X", default=42, required=False, name="x")

        h = Holder("h")
        h.load_data({})  # must not raise
        assert h._elements["x"].value == 42

    def test_required_true_works_on_object_subclass_too(self):
        # The flag flows through Object.__init__ via **kwargs to ConfigElement.
        ref = config.TagRef("Ref", default=None, required=True)
        assert ref.required is True
