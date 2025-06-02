import copy
import json
import logging
import pathlib
import re

from typing import Any

log = logging.getLogger(__name__)
KEY_VALIDATOR = re.compile(r"^[ a-zA-Z0-9_-]*$")


def transform_key(key: str):
    return key.lower().replace(" ", "_")


def check_key(key: str):
    if not KEY_VALIDATOR.match(key):
        raise ValueError(
            f"Invalid config key {key}. Keys must only contain alphanumeric characters, "
            f"hyphens (-), underscores (_) and spaces ( )."
        )


class NotSet:
    pass


class Schema:
    __element_map: "dict[str, ConfigElement]"

    def add_element(self, element):
        try:
            # do this here so we don't have to override __init__
            elem_map = self.__element_map
        except AttributeError:
            # this is the first element, so create the map
            elem_map = self.__element_map = dict()

        element._name = transform_key(element.display_name)
        if element._name in elem_map:
            raise ValueError(f"Duplicate element name {element._name} not allowed.")

        elem_map[element._name] = element

    def __setattr__(self, key, value):
        if isinstance(value, ConfigElement):
            # value._name = key
            self.add_element(value)
        super().__setattr__(key, value)

    def to_dict(self):
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "",
            "title": "Application Config",
            "type": "object",
            "properties": {
                name: element.to_dict()
                for name, element in self.__element_map.items()
                if isinstance(element, ConfigElement)
            },
            "additionalElements": True,
            "required": [
                name
                for name, element in self.__element_map.items()
                if isinstance(element, ConfigElement) and element.required
            ],
        }

    def _inject_deployment_config(self, config: dict[str, Any]):
        for name, value in config.items():
            try:
                elem = self.__element_map[name]
            except KeyError:
                log.info(f"Skipping unknown config key {name} ({value})")
            else:
                elem.load_data(value)

    def export(self, fp: pathlib.Path, app_name: str):
        if fp.exists():
            data = json.loads(fp.read_text())
        else:
            data = {}

        try:
            data[app_name]["config_schema"] = self.to_dict()
        except KeyError:
            data[app_name] = {"config_schema": self.to_dict()}

        fp.write_text(json.dumps(data, indent=4))


class ConfigElement:
    _type = "unknown"

    def __init__(
        self,
        display_name,
        *,
        default: Any = NotSet,
        description: str = None,
        deprecated: bool = None,
        hidden: bool = False,
    ):
        self._name = transform_key(display_name)
        self.display_name = display_name
        self.default = default
        self.description = description
        self.hidden = hidden
        self.deprecated = deprecated

        self._value = NotSet

        if (
            default is not NotSet
            and not isinstance(default, Variable)
            and default is not None
        ):
            match self._type:
                case "integer":
                    assert isinstance(default, int)
                case "number":
                    assert isinstance(default, float)
                case "string":
                    assert isinstance(default, str)
                case "boolean":
                    assert isinstance(default, bool)
                case ("array", "object"):
                    if default is not None:
                        raise ValueError(
                            "You cannot set default values for arrays and objects. It's confusing."
                        )

    @property
    def required(self):
        return self.default is NotSet

    @property
    def value(self):
        if self._value is NotSet:
            raise ValueError(f"Value for {self._name} not set. Check your config file?")
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def to_dict(self):
        payload = {
            "title": self.display_name,
            "x-name": self._name,
            "x-hidden": self.hidden,
        }

        if self._type is not None:
            payload["type"] = self._type

        if self.description is not None:
            payload["description"] = self.description

        if isinstance(self.default, Variable):
            payload["default"] = str(self.default)
        elif self.default is not NotSet:
            payload["default"] = self.default

        if self.deprecated is not None:
            payload["deprecated"] = self.deprecated

        return payload

    def load_data(self, data):
        self.value = data


class Integer(ConfigElement):
    """Represents a JSON Integer type. Internally represented as an int."""

    _type = "integer"
    value: int

    def __init__(
        self,
        display_name,
        *,
        minimum: int = None,
        exclusive_minimum: int = None,
        maximum: int = None,
        exclusive_maximum: int = None,
        multiple_of: int = None,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        self.multiple_of = multiple_of

    def to_dict(self):
        res = super().to_dict()
        if self.minimum is not None:
            res["minimum"] = self.minimum
        if self.exclusive_minimum is not None:
            res["exclusiveMinimum"] = self.exclusive_minimum
        if self.maximum is not None:
            res["maximum"] = self.maximum
        if self.exclusive_maximum is not None:
            res["exclusiveMaximum"] = self.exclusive_maximum
        if self.multiple_of is not None:
            res["multipleOf"] = self.multiple_of

        return res


class Number(Integer):
    """Represents a JSON Number type, for any numeric type. Internally represented as a float."""

    _type = "number"
    value: float


class Boolean(ConfigElement):
    _type = "boolean"
    value: bool


class String(ConfigElement):
    _type = "string"
    value: str

    def __init__(
        self, display_name, *, length: int = None, pattern: str = None, **kwargs
    ):
        super().__init__(display_name, **kwargs)
        self.length = length
        self.pattern = pattern

    def to_dict(self):
        res = super().to_dict()
        if self.length is not None:
            res["length"] = self.length
        if self.pattern is not None:
            res["pattern"] = self.pattern

        return res


class Enum(ConfigElement):
    _type = None

    def __init__(self, display_name, *, choices: list = None, **kwargs):
        super().__init__(display_name, **kwargs)
        self.choices = choices

        if all(isinstance(choice, str) for choice in choices):
            self._type = "string"
        elif all(isinstance(choice, float) for choice in choices):
            self._type = "number"

    def to_dict(self):
        return {
            "enum": self.choices,
            **super().to_dict(),
        }


class Array(ConfigElement):
    """Represents a JSON Array type. Internally represented as a list.

    Only a subset of JSON Schema is supported:
    - Item type
    - Minimum and maximum number of items
    - Unique items
    """

    _type = "array"

    def __init__(
        self,
        display_name,
        *,
        element: ConfigElement = None,
        min_items: int = None,
        max_items: int = None,
        unique_items: bool = None,
        **kwargs,
    ):
        if element and not isinstance(element, ConfigElement):
            raise ValueError("Many element must be a ConfigElement instance")
        if "default" in kwargs:
            raise ValueError(
                "Default value not allowed for Many elements. It's confusing."
            )

        super().__init__(display_name, **kwargs)

        self.element = element or ConfigElement("unknown")
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items

        self._elements = []

    def to_dict(self):
        res = super().to_dict()
        if self.element is not None:
            res["items"] = self.element.to_dict()
        if self.min_items is not None:
            res["minItems"] = self.min_items
        if self.max_items is not None:
            res["maxItems"] = self.max_items
        if self.unique_items is not None:
            res["uniqueItems"] = self.unique_items
        return res

    @property
    def elements(self) -> list[ConfigElement]:
        return self._elements

    def load_data(self, data):
        self._elements.clear()
        for row in data:
            elem = copy.deepcopy(self.element)
            elem.load_data(row)
            self._elements.append(elem)


class Object(ConfigElement):
    """Represents a JSON Object type."""

    _type = "object"

    def __init__(
        self,
        display_name,
        *,
        additional_elements: bool | dict[str, Any] = False,
        **kwargs,
    ):
        if "default" in kwargs:
            raise ValueError(
                "Default value not allowed for Object elements. It's confusing."
            )

        super().__init__(display_name, **kwargs)
        self._elements = {}
        self.additional_elements = additional_elements

    def __setattr__(self, key, value):
        if isinstance(value, ConfigElement):
            self.add_elements(value)
        super().__setattr__(key, value)

    def add_elements(self, *element):
        for element in element:
            if element._name in self._elements:
                raise ValueError(f"Duplicate element name {element._name} not allowed.")
            self._elements[element._name] = element

    def to_dict(self):
        res = super().to_dict()
        res["properties"] = {
            element._name: element.to_dict() for element in self._elements.values()
        }
        res["additionalElements"] = self.additional_elements
        res["required"] = [
            elem._name for elem in self._elements.values() if elem.required is True
        ]
        return res

    def load_data(self, data):
        for name, value in data.items():
            self._elements[name].load_data(value)


class Variable:
    def __init__(self, scope: str, name: str):
        self._scope = transform_key(scope)
        self._name = transform_key(name)

    def __str__(self):
        return f"${self._scope}.{self._name}"


class Application(ConfigElement):
    _type = "string"
    value: str

    def to_dict(self):
        return {"format": "doover-application", **super().to_dict()}
