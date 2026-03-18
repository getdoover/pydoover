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
        validate(deepcopy(SAMPLE_CONFIG_A), ConfigSchemaA().to_dict())

    @pytest.mark.parametrize(
        "key, value",
        [
            ("a", 1.5),
            ("b", "a string"),
            ("c", True),
            ("d", 0),
            ("e", "not_a_boolean"),
            ("f", ["a", "b", "c"]),
            ("g", {"a": 1, "b": 0.5}),
            ("g", "not-an-object"),
            ("g", ["an-array-of-string"]),
        ],
    )
    def test_invalid_type(self, key, value):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config[key] = value
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

    def test_enum(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["d"] = "not-a-choice"
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

        sample_config["d"] = "c"
        validate(sample_config, ConfigSchemaA().to_dict())

    def test_minimum(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["a"] = -1
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

        sample_config["a"] = 0
        validate(sample_config, ConfigSchemaA().to_dict())

    def test_exclusive_min(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["b"] = 0
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

    def test_array(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["f"] = [1, 2, "not an int"]
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

        sample_config["f"] = []
        validate(sample_config, ConfigSchemaA().to_dict())

        sample_config["f"] = ["not an int"]
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

    def test_object(self):
        sample_config = deepcopy(SAMPLE_CONFIG_A)
        sample_config["g"]["g_a"] = "not an int"
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

        sample_config["g"]["g_b"] = 0
        with pytest.raises(ValidationError):
            validate(sample_config, ConfigSchemaA().to_dict())

    def test_multiple_instances_do_not_share_elements(self):
        first = ConfigSchemaA()
        second = ConfigSchemaA()

        first._inject_deployment_config(SAMPLE_CONFIG_A)

        assert first.element("a") is not second.element("a")

    def test_runtime_access_is_direct(self):
        schema = ConfigSchemaA()
        schema._inject_deployment_config(SAMPLE_CONFIG_A)

        assert schema.a == 1
        assert schema.b == 0.5
        assert schema.c == "valid_string"
        assert schema.d == "a"
        assert schema.e is False
        assert list(schema.f) == [1, 2, 3]
        assert schema.f[1] == 2
        assert schema.g.a == 1
        assert schema.g.b == 0.5

    def test_metadata_bridge_exposes_bound_elements(self):
        schema = ConfigSchemaA()
        schema._inject_deployment_config(SAMPLE_CONFIG_A)

        assert schema.element("a").value == 1
        assert schema.element("a").minimum == 0
        assert schema.g.element("a").value == 1
        assert [element.value for element in schema.f.elements] == [1, 2, 3]

    def test_missing_required_scalar_still_raises(self):
        schema = ConfigSchemaA()

        with pytest.raises(ValueError, match="c"):
            _ = schema.c

    def test_schema_init_assignment_raises_helpful_error(self):
        with pytest.raises(TypeError, match="class attributes"):
            class BadSchema(config.Schema):
                def __init__(self):
                    self.foo = config.Integer("Foo", default=1)

            BadSchema()

    def test_object_init_assignment_raises_helpful_error(self):
        with pytest.raises(TypeError, match="class attributes"):
            class BadObject(config.Object):
                def __init__(self):
                    super().__init__("Bad Object")
                    self.foo = config.Integer("Foo", default=1)

            BadObject()
