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
