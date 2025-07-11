import copy
import json
import logging
import pathlib
import re

from enum import EnumType, Enum as _Enum
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
    """Represents the configuration schema for a Doover application.

    A config schema is a definition of the config for your application.

    It is used as `.config` in your application and can generate a JSON Schema
    which will provide user validation and a "form" in the Doover UI.

    Any attributes added in the `__init__` method will be added to the schema.
    Order is preserved from the order you define them in the `__init__` method.

    The schema can be exported to a JSON file using the `export` method, although in a template application this is done for you.

    To export the schema to the `doover_config.json` file, use the Doover cli: ``doover config-schema export``.
    This will validate and export the schema to the `doover_config.json` file in the root of your Doover project.

    Examples
    --------

    >>> from pydoover import config
    >>> class MyAppConfig(config.Schema):
    ...     def __init__(self):
    ...         self.pump_pin = config.Integer("Digital Output Number", description="The digital output pin to drive the pump.")
    ...         self.pump_on_time = config.Number("Pump On Time", default=5.2, description="The time in seconds to run the pump.")
    ...         self.engine_type = config.Enum(
    ...             "Engine Type",
    ...             choices=["Honda", "John Deere", "Cat"],
    ...             description="The type of diesel engine attached to the pump.",
    ...         )

    """

    __element_map: "dict[str, ConfigElement]" = {}

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

        for elem_name in set(self.__element_map.keys()) - set(config.keys()):
            # catch missing required elements, and set any other elements to their default value
            elem = self.__element_map[elem_name]
            if elem.required:
                raise ValueError(
                    f"Required config element {elem_name} not found in deployment config."
                )
            elem.load_data(elem.default)

    def export(self, fp: pathlib.Path, app_name: str):
        """Export the config schema to a JSON file.

        This will export the config schema to the ``config_schema`` field in the ``doover_config.json`` file in the root of your project .

        Examples
        --------

        Generally, this will be done in the application template.

        >>> from pydoover import config
        >>> class MyAppConfig(config.Schema):
        ...     def __init__(self):
        ...         self.pump_pin = config.Integer("Digital Output Number", description="The digital output pin to drive the pump.")
        ...
        ... if __name__ == "__main__":
        ...     from pathlib import Path
        ...     MyAppConfig().export(pathlib.Path("/path/to/my/app/doover_config.json"), "my_app_name")


        Parameters
        ----------
        fp: pathlib.Path
            The path to the JSON file to export the config schema to.
        app_name: str
            The name of the application to export the config schema for.
            This will be used as the key in the `doover_config.json` file.
        """
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
    """Represents a config element in the Doover configuration schema.

    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    default: int
        The default value for the integer. If NotSet, the value is required.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    """

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
        """Whether the config element is required."""
        return self.default is NotSet

    @property
    def value(self):
        """The value of the config element."""
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
    """Represents a JSON Integer type. Internally represented as an int.

    Attributes
    -----------
    display_name: str
        The display name of the config element. This is used in the UI.
    default: int
        The default value for the integer. If NotSet, the value is required.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    minimum: int | None
        The minimum value for the integer. If None, no minimum is enforced.
    exclusive_minimum: int | None
        The exclusive minimum value for the integer. If None, no exclusive minimum is enforced.
    maximum: int | None
        The maximum value for the integer. If None, no maximum is enforced.
    exclusive_maximum: int | None
        The exclusive maximum value for the integer. If None, no exclusive maximum is enforced.
    multiple_of: int | None
        The value that the integer must be a multiple of. If None, no multiple is enforced.
    """

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
    """Represents a JSON Number type, for any numeric type. Internally represented as a float.

    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    default: float
        The default value for the integer. If NotSet, the value is required.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    """

    _type = "number"
    value: float


class Boolean(ConfigElement):
    """Represents a JSON Boolean type. Internally represented as a bool.

    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    default: bool
        The default value for the integer. If NotSet, the value is required.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    """

    _type = "boolean"
    value: bool


class String(ConfigElement):
    """Represents a JSON String type. Internally represented as a str.

    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    default: str
        The default value for the integer. If NotSet, the value is required.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    length: int | None
        The length of the string. If None, no length is enforced.
    pattern: str | None
        A regex pattern that the string must match. If None, no pattern is enforced.
    """

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
    """Represents a JSON Enum type. Internally represented as a list of choices.

    The UI renders this as a drop-down.

    Examples
    --------

    You can specify a list of choices as strings or floats, or use an EnumType::

        from pydoover import config

        class MyChoice(enum.Enum):
            A = "Choice 1"
            B = "Choice 2"
            C = "Choice 3"

        class AppConfig(config.Schema):
            def __init__(self):
                self.choice = config.Enum(
                    "Choose Something",
                    choices=MyChoice,
                    default=MyChoice.A,
                )

                self.other_choice = config.Enum(
                    "Other Choice",
                    choices=["a", "b", "c"],
                    default="a"
                )


    You can also set enum values to be objects to allow for custom attributes, provided your object implements ``__str__``::

        from pydoover import config

        class Choice:
            def __init__(self, name, level):
                self.name = name
                self.level = level

            def __str__(self):
                return self.name

        class ChoiceType(enum.Enum):
            A = Choice("A", 1)
            B = Choice("B", 2)
            C = Choice("C", 3)

        class AppConfig(config.Schema):
            def __init__(self):
                self.choice = config.Enum(
                    "Choose Something",
                    choices=ChoiceType,
                    default=ChoiceType.A,
                )

            @property
            def choice_value(self):
                return self.choice.value.level



    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    default: same type as choices.
        The default value for the integer. If NotSet, the value is required.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    choices: EnumType or list of str | float
        A list of choices for the enum. All choices must be of the same type (str or float).
        This optionally accepts an EnumType, with the value of the enum denoting the choice.
        The value can be an object which implements the ``__str__`` method. Each ``__str__`` value must be unique.
    """

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

    .. note::

        The ``default`` value is not allowed for Array elements, as it is confusing.

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
    """Represents a JSON Object type.

    This is a complex type that can contain multiple elements, each with its own type.
    It can also have additional elements that are not defined in the schema.

    The UI renders this as a form with fields for each element.

    Examples
    --------

    >>> from pydoover import config
    >>> class MyAppConfig(config.Schema):
    ...     def __init__(self):
    ...         self.pump = config.Object(
    ...             "Pump Settings",
    ...          )
    ...         self.pump.add_elements(
    ...             config.Integer("Digital Output Number", description="The digital output pin to drive the pump."),
    ...             config.Number("On Time", default=5.2, description="The time in seconds to run the pump."),
    ...         )


    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    additional_elements: bool | dict[str, Any]
        If True, allows additional elements that are not defined in the schema.
        If a dict, defines the schema for additional elements.
        If False, no additional elements are allowed.
    """

    _type = "object"

    def __init__(
        self,
        display_name,
        *,
        additional_elements: bool | dict[str, Any] = True,
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

    def __getattr__(self, key):
        # Safety check: if _elements doesn't exist yet, it means we're still initializing
        if "_elements" in self.__dict__ and key in self._elements:
            return self._elements[key]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{key}'"
        )

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
            try:
                self._elements[name].load_data(value)
            except KeyError:
                if self.additional_elements is True:
                    self._elements[name] = ConfigElement(name, default=value)
                else:
                    raise ValueError(f"Unknown element {name} in config.")


class Variable:
    """Represents a variable in the config schema.

    This is a special type of config element that is used to reference other config elements.
    It is used to create dynamic references to other config elements, such as device-specific settings.

    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    scope: str
        The scope of the variable, which is usually the application name.
    name: str
        The name of the variable, which is usually the key of the config element.

    """

    def __init__(self, scope: str, name: str):
        self._scope = transform_key(scope)
        self._name = transform_key(name)

    def __str__(self):
        return f"${self._scope}.{self._name}"


class Application(ConfigElement):
    """Represents a Doover application configuration element.

    This is used to reference other Doover applications in the configuration schema.

    This is rendered as a dropdown in the UI, allowing the user to select an installed application.

    Attributes
    ----------
    display_name: str
        The display name of the config element. This is used in the UI.
    description: str | None
        A help text for the config element.
    hidden: bool
        Whether the config element should be hidden in the UI.
    """

    _type = "string"
    value: str

    def to_dict(self):
        return {"format": "doover-application", **super().to_dict()}
