from copy import copy

from pydoover import config

import pytest
from jsonschema import ValidationError, validate


class ConfigSchemaA(config.Schema):
    def __init__(self):
        self.a = config.Integer("A", default=1, minimum=0)
        self.b = config.Number("B", exclusive_minimum=0)
        self.c = config.String("C", pattern=r"^[a-zA-Z0-9_]+$")
        self.d = config.Enum("D", choices=["a", "b", "c"], default="a")
        self.e = config.Boolean("E", default=False)
        self.f = config.Array("F", element=config.Integer("F Element"))

        self.g = config.Object("G")
        self.g.a = config.Integer("G A", default=1, minimum=0)
        self.g.b = config.Number("G B", exclusive_minimum=0)


SAMPLE_CONFIG_A = {
    "a": 1,
    "b": 0.5,
    "c": "valid_string",
    "d": "a",
    "e": False,
    "f": [1, 2, 3],
    "g": {"g_a": 1, "g_b": 0.5},
}
schema = ConfigSchemaA()


class TestConfigSchemaA:
    def test_ok_schema(self):
        validate(copy(SAMPLE_CONFIG_A), schema.to_dict())

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
        sample_config = copy(SAMPLE_CONFIG_A)
        sample_config[key] = value
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())

    def test_enum(self):
        sample_config = copy(SAMPLE_CONFIG_A)
        sample_config["d"] = "not-a-choice"
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())

        sample_config["d"] = "c"
        validate(sample_config, schema.to_dict())

    def test_minimum(self):
        sample_config = copy(SAMPLE_CONFIG_A)
        sample_config["a"] = -1
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())

        sample_config["a"] = 0
        validate(sample_config, schema.to_dict())

    def test_exclusive_min(self):
        sample_config = copy(SAMPLE_CONFIG_A)
        sample_config["b"] = 0
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())

    def test_array(self):
        sample_config = copy(SAMPLE_CONFIG_A)
        sample_config["f"] = [1, 2, "not an int"]
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())

        sample_config["f"] = []
        validate(sample_config, schema.to_dict())

        sample_config["f"] = ["not an int"]
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())

    def test_object(self):
        sample_config = copy(SAMPLE_CONFIG_A)
        sample_config["g"]["g_a"] = "not an int"
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())

        sample_config["g"]["g_b"] = 0
        with pytest.raises(ValidationError):
            validate(sample_config, schema.to_dict())
