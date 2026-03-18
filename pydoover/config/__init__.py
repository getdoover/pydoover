from __future__ import annotations

import copy
import json
import logging
import pathlib
import re

from collections import OrderedDict
from enum import Enum as _Enum
from enum import EnumType
from typing import Any, Generic, Iterator, Self, TypeVar, overload

log = logging.getLogger(__name__)
KEY_VALIDATOR = re.compile(r"^[ a-zA-Z0-9_-]*$")


def transform_key(key: str) -> str:
    return key.lower().replace(" ", "_")


def check_key(key: str) -> None:
    if not KEY_VALIDATOR.match(key):
        raise ValueError(
            f"Invalid config key {key}. Keys must only contain alphanumeric characters, "
            f"hyphens (-), underscores (_) and spaces ( )."
        )


class NotSet:
    """Sentinel used when a config value has not been assigned."""


def _unwrap_runtime_value(element: "ConfigElement") -> Any:
    if isinstance(element, (Array, Object)):
        return element
    return element.value


def _build_runtime_elements(
    declarations: "OrderedDict[str, _DeclaredConfigElement[Any, ConfigElement[Any]]]",
) -> "OrderedDict[str, ConfigElement[Any]]":
    elements: "OrderedDict[str, ConfigElement[Any]]" = OrderedDict()
    schema_keys: set[str] = set()

    for attr_name, declaration in declarations.items():
        element = copy.deepcopy(declaration.template)
        element._declared_attr_name = attr_name

        if element._name in schema_keys:
            raise ValueError(f"Duplicate element name {element._name} not allowed.")
        schema_keys.add(element._name)

        if element._position is None:
            element._position = len(elements) + 1
        elements[attr_name] = element

    return elements


RuntimeValueT = TypeVar("RuntimeValueT")
ConfigElementT = TypeVar("ConfigElementT", bound="ConfigElement[Any]")


class _DeclaredConfigElement(Generic[RuntimeValueT, ConfigElementT]):
    def __init__(self, attr_name: str, template: ConfigElementT):
        self.attr_name = attr_name
        self.template = template
        self.template._declared_attr_name = attr_name

    @overload
    def __get__(self, instance: None, owner: type["Schema"]) -> ConfigElementT: ...

    @overload
    def __get__(self, instance: None, owner: type["Object"]) -> ConfigElementT: ...

    @overload
    def __get__(self, instance: "Schema", owner: type["Schema"]) -> RuntimeValueT: ...

    @overload
    def __get__(self, instance: "Object", owner: type["Object"]) -> RuntimeValueT: ...

    def __get__(
        self,
        instance: "Schema | Object | None",
        owner: type["Schema"] | type["Object"],
    ) -> ConfigElementT | RuntimeValueT:
        if instance is None:
            return self.template
        instance._ensure_runtime_state()
        return _unwrap_runtime_value(instance._elements[self.attr_name])

    def __set__(self, instance, value):
        raise AttributeError(
            "Config fields are read-only at runtime. "
            "Use element(name).value for explicit metadata/value access."
        )


def _collect_config_declarations(
    cls: type,
) -> "OrderedDict[str, _DeclaredConfigElement[Any, ConfigElement[Any]]]":
    declarations: "OrderedDict[str, _DeclaredConfigElement[Any, ConfigElement[Any]]]" = OrderedDict()
    for base in reversed(cls.__mro__[1:]):
        declarations.update(getattr(base, "__config_declarations__", {}))

    for attr_name, value in list(cls.__dict__.items()):
        if not isinstance(value, ConfigElement):
            continue

        declaration = _DeclaredConfigElement(attr_name, value)
        declarations[attr_name] = declaration
        setattr(cls, attr_name, declaration)

    return declarations


class Schema:
    """Represents the configuration schema for a Doover application."""

    __config_declarations__: "OrderedDict[str, _DeclaredConfigElement[Any, ConfigElement[Any]]]" = OrderedDict()

    def __init__(self):
        self._ensure_runtime_state()

    def __init_subclass__(cls, name: str = "$default", **kwargs):
        super().__init_subclass__(**kwargs)
        cls.name = name
        cls.__config_declarations__ = _collect_config_declarations(cls)

    def __setattr__(self, key, value):
        if isinstance(value, ConfigElement):
            raise TypeError(
                "Config declarations must be defined as class attributes. "
                f"Move '{key}' out of __init__ and onto the Schema class body."
            )
        super().__setattr__(key, value)

    def _ensure_runtime_state(self) -> None:
        if "_elements" in self.__dict__:
            return
        super().__setattr__(
            "_elements", _build_runtime_elements(self.__class__.__config_declarations__)
        )

    @classmethod
    def clear_elements(cls):
        cls.__config_declarations__.clear()

    @property
    def elements(self) -> "OrderedDict[str, ConfigElement]":
        self._ensure_runtime_state()
        return self._elements

    def element(self, name: str) -> "ConfigElement":
        self._ensure_runtime_state()
        try:
            return self._elements[name]
        except KeyError:
            for element in self._elements.values():
                if element._name == name:
                    return element
        raise KeyError(name)

    def to_dict(self):
        self._ensure_runtime_state()
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "",
            "title": self.__class__.name,
            "type": "object",
            "properties": {
                element._name: element.to_dict()
                for element in self._elements.values()
                if isinstance(element, ConfigElement)
            },
            "additionalElements": True,
            "required": [
                element._name
                for element in self._elements.values()
                if isinstance(element, ConfigElement) and element.required
            ],
        }

    def _inject_deployment_config(self, config: dict[str, Any]):
        self._ensure_runtime_state()
        remaining = set(self._elements.keys())

        for name, value in config.items():
            try:
                element = self.element(name)
            except KeyError:
                log.debug(f"Skipping unknown config key {name} ({value})")
                continue

            element.load_data(value)
            remaining.discard(element._declared_attr_name)

        for attr_name in remaining:
            element = self._elements[attr_name]
            if element.required:
                raise ValueError(
                    f"Required config element {element._name} not found in deployment config."
                )
            element.load_data(copy.deepcopy(element.default))

    def export(self, fp: pathlib.Path, app_name: str):
        """Export the schema to the ``config_schema`` field in ``doover_config.json``."""
        if fp.exists():
            data = json.loads(fp.read_text())
        else:
            data = {}

        try:
            data[app_name]["config_schema"] = self.to_dict()
        except KeyError:
            data[app_name] = {"config_schema": self.to_dict()}

        fp.write_text(json.dumps(data, indent=4))


class ConfigElement(Generic[RuntimeValueT]):
    """Represents a config element declaration and bound runtime value container."""

    _type = "unknown"

    def __init__(
        self,
        display_name,
        *,
        default: Any = NotSet,
        description: str | None = None,
        deprecated: bool | None = None,
        hidden: bool = False,
        format: str | None = None,
        position: int | None = None,
        name: str | None = None,
    ):
        if name is not None:
            check_key(name)
            resolved_name = name
        else:
            resolved_name = display_name

        self._name = transform_key(resolved_name)
        self._declared_attr_name: str | None = None
        self._position = position
        self.display_name = display_name
        self.default = default
        self.description = description
        self.hidden = hidden
        self.deprecated = deprecated
        self.format = format
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
                case "array":
                    assert isinstance(default, list)
                    # fixme: we don't really need to do this, but assert all values in default list are the correct type
                    # for item in default:
                    #     assert isinstance(item, self.element.primitive)
                case "object":
                    assert isinstance(default, dict)

    @overload
    def __get__(self, instance: None, owner: type["Schema"]) -> Self: ...

    @overload
    def __get__(self, instance: None, owner: type["Object"]) -> Self: ...

    @overload
    def __get__(self, instance: "Schema", owner: type["Schema"]) -> RuntimeValueT: ...

    @overload
    def __get__(self, instance: "Object", owner: type["Object"]) -> RuntimeValueT: ...

    def __get__(
        self,
        instance: "Schema | Object | None",
        owner: type["Schema"] | type["Object"],
    ) -> Self | RuntimeValueT:
        if instance is None:
            return self
        instance._ensure_runtime_state()
        if self._declared_attr_name is None:
            raise AttributeError(
                "Config elements must be declared on a Schema or Object subclass."
            )
        return _unwrap_runtime_value(instance._elements[self._declared_attr_name])

    def __set__(self, instance: "Schema | Object", value: Any) -> None:
        raise AttributeError(
            "Config fields are read-only at runtime. "
            "Use element(name).value for explicit metadata/value access."
        )

    @property
    def required(self):
        return self.default is NotSet

    @property
    def value(self):
        if self._value is NotSet:
            if self.default is None:
                return None
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
            if self.required:
                payload["type"] = self._type
            else:
                payload["type"] = [self._type, "null"]

        payload["x-required"] = self.required

        if self.description is not None:
            payload["description"] = self.description

        if isinstance(self.default, Variable):
            payload["default"] = str(self.default)
        elif self.default is not NotSet:
            payload["default"] = self.default

        if self._position is not None:
            payload["x-position"] = self._position

        if self.deprecated is not None:
            payload["deprecated"] = self.deprecated

        if self.format is not None:
            payload["format"] = self.format

        return payload

    def load_data(self, data):
        self.value = data


class Integer(ConfigElement[int]):
    _type = "integer"
    value: int

    def __init__(
        self,
        display_name,
        *,
        minimum: int | None = None,
        exclusive_minimum: int | None = None,
        maximum: int | None = None,
        exclusive_maximum: int | None = None,
        multiple_of: int | None = None,
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
    _type = "number"
    value: float


class Boolean(ConfigElement[bool]):
    _type = "boolean"
    value: bool


class String(ConfigElement[str]):
    _type = "string"
    value: str

    def __init__(
        self, display_name, *, length: int | None = None, pattern: str | None = None, **kwargs
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


class DateTime(ConfigElement[str]):
    _type = "string"
    value: str

    def to_dict(self):
        res = super().to_dict()
        res["format"] = "date-time"
        return res


class Enum(ConfigElement[Any]):
    _type = None

    def __init__(
        self, display_name, *, choices: list | EnumType = None, default: Any, **kwargs
    ):
        if isinstance(default, _Enum):
            default = str(default.value)

        super().__init__(display_name, default=default, **kwargs)

        if isinstance(choices, EnumType):
            choices = [choice.value for choice in choices]
            self._enum_lookup = {str(choice): choice for choice in choices}
            choices = list(self._enum_lookup.keys())
        else:
            self._enum_lookup = None

        if all(isinstance(choice, str) for choice in choices):
            self._type = "string"
        elif all(isinstance(choice, float) for choice in choices):
            self._type = "number"

        self.choices = choices

    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, value):
        if self._enum_lookup is None:
            self._value = value
        else:
            self._value = self._enum_lookup[value]

    def to_dict(self):
        return {"enum": self.choices, **super().to_dict()}


class Array(ConfigElement["Array"]):
    """Represents a JSON Array type. Internally represented as a list.

    Only a subset of JSON Schema is supported:
    - Item type
    - Minimum and maximum number of items
    - Unique items

    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    element: ConfigElement
        The type of elements in the array. This can be any ConfigElement, such as String, Integer, etc.
    min_items: int | None
        The minimum number of items in the array. If None, no minimum is enforced.
    max_items: int | None
        The maximum number of items in the array. If None, no maximum is enforced.
    unique_items: bool | None
        Whether the items in the array must be unique. If None, no uniqueness is enforced.

    """

    _type = "array"

    def __init__(
        self,
        display_name,
        *,
        element: ConfigElement | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        unique_items: bool | None = None,
        **kwargs,
    ):
        if element and not isinstance(element, ConfigElement):
            raise ValueError("Many element must be a ConfigElement instance")

        super().__init__(display_name, **kwargs)
        self.element = element or ConfigElement("unknown")
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items
        self._elements: list[ConfigElement] = []

    def __iter__(self) -> Iterator[Any]:
        for element in self._elements:
            yield _unwrap_runtime_value(element)

    def __len__(self) -> int:
        return len(self._elements)

    def __getitem__(self, index):
        return _unwrap_runtime_value(self._elements[index])

    @property
    def elements(self) -> list[ConfigElement]:
        return self._elements

    @property
    def value(self):
        return list(self)

    def to_dict(self):
        res = super().to_dict()
        res["items"] = self.element.to_dict()
        if self.min_items is not None:
            res["minItems"] = self.min_items
        if self.max_items is not None:
            res["maxItems"] = self.max_items
        if self.unique_items is not None:
            res["uniqueItems"] = self.unique_items
        return res

    def load_data(self, data):
        self._elements.clear()
        for row in data:
            element = copy.deepcopy(self.element)
            element.load_data(row)
            self._elements.append(element)


class Object(ConfigElement["Object"]):
    _type = "object"
    __config_declarations__: "OrderedDict[str, _DeclaredConfigElement[Any, ConfigElement[Any]]]" = OrderedDict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__config_declarations__ = _collect_config_declarations(cls)

    def __init__(
        self,
        display_name,
        *,
        additional_elements: bool | dict[str, Any] = True,
        collapsible: bool = True,
        default_collapsed: bool = False,
        **kwargs,
    ):
        if default_collapsed and not collapsible:
            raise ValueError("default_collapsed is not allowed if collapsible is False")

        super().__init__(display_name, **kwargs)
        self.additional_elements = additional_elements
        self.collapsible = collapsible
        self.default_collapsed = default_collapsed
        self._ensure_runtime_state()

    def __setattr__(self, key, value):
        if isinstance(value, ConfigElement):
            raise TypeError(
                "Object declarations must be defined as class attributes. "
                f"Move '{key}' out of __init__ and onto the Object class body."
            )
        super().__setattr__(key, value)

    def __getattr__(self, key):
        self._ensure_runtime_state()

        if key in self._elements:
            return _unwrap_runtime_value(self._elements[key])
        if key in self._dynamic_elements:
            return _unwrap_runtime_value(self._dynamic_elements[key])

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{key}'"
        )

    def _ensure_runtime_state(self) -> None:
        if "_elements" in self.__dict__ and "_dynamic_elements" in self.__dict__:
            return
        super().__setattr__(
            "_elements", _build_runtime_elements(self.__class__.__config_declarations__)
        )
        super().__setattr__("_dynamic_elements", OrderedDict())

    @property
    def elements(self) -> "OrderedDict[str, ConfigElement]":
        self._ensure_runtime_state()
        return OrderedDict([*self._elements.items(), *self._dynamic_elements.items()])

    @property
    def value(self):
        self._ensure_runtime_state()
        return {
            element._name: _unwrap_runtime_value(element)
            for element in self.elements.values()
        }

    def element(self, name: str) -> ConfigElement:
        self._ensure_runtime_state()
        for element_map in (self._elements, self._dynamic_elements):
            try:
                return element_map[name]
            except KeyError:
                pass

            for element in element_map.values():
                if element._name == name:
                    return element
        raise KeyError(name)

    def to_dict(self):
        self._ensure_runtime_state()
        res = super().to_dict()
        res["properties"] = {
            element._name: element.to_dict() for element in self._elements.values()
        }
        res["additionalElements"] = self.additional_elements
        res["required"] = [
            element._name for element in self._elements.values() if element.required
        ]
        res["x-collapsible"] = self.collapsible
        res["x-defaultCollapsed"] = self.default_collapsed
        return res

    def load_data(self, data):
        self._ensure_runtime_state()
        self._dynamic_elements.clear()
        remaining = set(self._elements.keys())

        for name, value in data.items():
            try:
                element = self.element(name)
            except KeyError:
                if self.additional_elements is True:
                    attr_name = transform_key(name)
                    element = ConfigElement(name, default=value, name=name)
                    element._declared_attr_name = attr_name
                    self._dynamic_elements[attr_name] = element
                else:
                    raise ValueError(f"Unknown element {name} in config.")

            element.load_data(value)
            if element._declared_attr_name in remaining:
                remaining.discard(element._declared_attr_name)

        for attr_name in remaining:
            element = self._elements[attr_name]
            if element.required:
                raise ValueError(
                    f"Required config element {element._name} not found in deployment config."
                )
            element.load_data(copy.deepcopy(element.default))


class Variable:
    """Represents a deployment-time variable reference."""

    def __init__(self, scope: str, name: str):
        self._scope = transform_key(scope)
        self._name = transform_key(name)

    def __str__(self):
        return f"${self._scope}.{self._name}"


class Application(String):
    def __init__(
        self,
        display_name: str = "Application",
        *,
        description: str = "Application",
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            format="doover-resource-application",
            **kwargs,
        )


class ApplicationInstall(String):
    def __init__(
        self,
        display_name: str = "ApplicationInstall",
        *,
        description: str = "Application Installation",
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            format="doover-application",
            **kwargs,
        )


class Device(String):
    def __init__(
        self, display_name: str = "Device", *, description: str = "Device ID", **kwargs
    ):
        super().__init__(
            display_name,
            description=description,
            pattern=r"\d+",
            format="doover-resource-device",
            **kwargs,
        )


class DevicesConfig(Array):
    def __init__(
        self,
        display_name: str = "Devices",
        *,
        description: str = "List of devices to grant permissions to.",
        **kwargs,
    ):
        super().__init__(
            display_name,
            element=Device(),
            description=description,
            **kwargs,
        )


class Group(String):
    def __init__(
        self, display_name: str = "Group", *, description: str = "Group ID", **kwargs
    ):
        super().__init__(
            display_name,
            description=description,
            pattern=r"\d+",
            format="doover-resource-group",
            **kwargs,
        )


class GroupsConfig(Array):
    def __init__(
        self,
        display_name: str = "Groups",
        *,
        description: str = "List of groups to grant permissions to.",
        **kwargs,
    ):
        super().__init__(
            display_name,
            element=Group(),
            description=description,
            **kwargs,
        )


class ApplicationPosition(Integer):
    def __init__(
        self,
        display_name: str = "Position",
        *,
        description: str = "Position of Application in UI Structure. Smaller numbers are closer to the top.",
        default: int = 50,
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            minimum=0,
            default=default,
            name="dv-app-position",
            hidden=True,
            **kwargs,
        )


ApplicationConfig = Schema


class LLMAPIKey(String):
    def __init__(
        self,
        display_name: str = "LLM API Key",
        *,
        description: str = "API key for the LLM service.",
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            hidden=True,
            default="placeholder",
            **kwargs,
        )
        self._name = "dv-llm-api-key"
