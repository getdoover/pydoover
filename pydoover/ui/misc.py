from typing import Any, ClassVar

from .declarative import normalize_ui_value
from ..utils.utils import sanitize_display_name


class NotSet:
    """A sentinel value to indicate that a value has not been set."""


class Colour:
    """A class representing a colour, which can be used in various UI elements.

    This class provides a set of predefined colour constants that can be used directly,
    or allows conversion from hex strings and arbitrary strings to a colour representation.

    In reality, the Doover Site will accept any HTML colour name or hex string, but this class allows
    for future implementations of colour objects if needed.

    Attributes
    ----------
    blue
    yellow
    red
    green
    magenta
    limegreen
    tomato
    orange
    purple
    grey
    """

    blue: ClassVar[str] = "blue"
    yellow: ClassVar[str] = "yellow"
    red: ClassVar[str] = "red"
    green: ClassVar[str] = "green"
    magenta: ClassVar[str] = "magenta"
    limegreen: ClassVar[str] = "limegreen"
    tomato: ClassVar[str] = "tomato"
    orange: ClassVar[str] = "orange"
    purple: ClassVar[str] = "purple"
    grey: ClassVar[str] = "grey"

    @classmethod
    def from_hex(cls, hex_string: str) -> str:
        """Convert a hex string to a colour string.

        This method takes a hex string (e.g., "#FF5733") that can be used where a Colour object is accepted.
        """
        return hex_string

    @classmethod
    def from_string(cls, value: str) -> str:
        """Convert an arbitrary string to a Colour object.

        This method takes an HTML colour name (e.g. `brown`) and allows it to be used where a Colour object is accepted.
        """
        return value  # fixme: this hackiness


class Series:
    """Represents a series in a Multiplot UI element.

    Parameters
    ----------
    display_name: str
        The display string for the series.
    name: str, optional
        The key used in the serialized output. Defaults to a sanitized form of *display_name*.
    data_type: str
        The data type of the series (``"number"``, ``"string"``, ``"boolean"``, ``"unknown"``).
    active: bool, optional
        Whether the series is active by default.
    colour: str, optional
        The colour of the series (e.g. ``Colour.red`` or a hex string).
    icon: str, optional
        An icon identifier for the series.
    shared_axis: bool | str, optional
        Whether to share the axis, or the name of the axis to share.
    units: str, optional
        The units label for the series values.
    step_labels: list[str], optional
        Labels for step-type series.
    range: tuple[int | float | str, int | float | str], optional
        A ``(min, max)`` tuple for the series range. Values may be numeric or ``"auto"``.
    value: optional
        A bound tag reference (e.g. ``tag_ref("my_tag")``) that the series data is looked up from.
    """

    def __init__(
        self,
        display_name: str,
        value: Any,
        name: str | None = None,
        data_type: str = "unknown",
        active: bool | None = None,
        colour: str | None = None,
        icon: str | None = None,
        shared_axis: bool | str | None = None,
        units: str | None = None,
        step_labels: list[str] | None = None,
        range: tuple | None = None,
    ):
        self.display_name = display_name
        self.value = value
        self.name = name or sanitize_display_name(display_name)
        self.data_type = data_type
        self.active = active
        self.colour = colour
        self.icon = icon
        self.shared_axis = shared_axis
        self.units = units
        self.step_labels = step_labels
        self.range = range

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "displayString": self.display_name,
            "dataType": self.data_type,
        }
        if self.value is not None:
            result["lookup"] = self.value
        if self.active is not None:
            result["active"] = self.active
        if self.colour is not None:
            result["colour"] = self.colour
        if self.icon is not None:
            result["icon"] = self.icon
        if self.shared_axis is not None:
            result["sharedAxis"] = self.shared_axis
        if self.units is not None:
            result["units"] = self.units
        if self.step_labels is not None:
            result["stepLabels"] = self.step_labels
        if self.range is not None:
            result["range"] = {"min": self.range[0], "max": self.range[1]}
        return normalize_ui_value(result)


class Range:
    """Represents a range of values with associated properties for UI display.

    Attributes
    ----------
    label: str
        A label for the range, used for display purposes.
    min: Union[int, float]
        The minimum value of the range.
    max: Union[int, float]
        The maximum value of the range.
    colour: Colour
        The colour associated with the range, used for display.
    show_on_graph: bool
        Whether to show this range on the graph.
    """

    def __init__(
        self,
        label: Any = None,
        min_val: Any = None,
        max_val: Any = None,
        colour: Any = Colour.blue,
        show_on_graph: bool = True,
    ):
        self.label = label
        self.min = min_val
        self.max = max_val
        self.colour = colour
        self.show_on_graph = show_on_graph

    def __repr__(self) -> str:
        return f"Range(label={self.label}, min={self.min}, max={self.max}, colour={self.colour}, show_on_graph={self.show_on_graph})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Range):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def to_dict(self) -> dict[str, Any]:
        to_return = {
            "min": self.min,
            "max": self.max,
            "colour": self.colour,
            "show_on_graph": self.show_on_graph,
        }
        if self.label:
            to_return["label"] = self.label
        return normalize_ui_value(to_return)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            data.get("label"),
            data["min"],
            data["max"],
            Colour.from_string(data["colour"]),
            data["show_on_graph"],
        )


class Option:
    """Represents an option for a UI element, such as a dropdown or selection list.

    Attributes
    ----------
    display_name: str
        The display name of the option, used for user interface representation.
    """

    def __init__(self, display_name: Any):
        self.display_name = display_name
        self.name = sanitize_display_name(display_name)

    def to_dict(self) -> dict[str, Any]:
        return normalize_ui_value(
            {
                "name": self.name,
                "displayString": self.display_name,
                "type": "uiElement",
            }
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(data["display_str"])


class Widget:
    """Base class for UI widgets, which can be used to represent various UI elements.

    There are two main types of widgets: linear and radial gauges.

    Attributes
    ----------
    linear
        Represents a linear gauge widget.
    radial
        Represents a radial gauge widget.
    """

    linear: ClassVar[str] = "linearGauge"
    radial: ClassVar[str] = "radialGauge"

    @classmethod
    def from_string(cls, value: str) -> str:
        """Convert an arbitrary string to a Widget object.

        This method takes a string (e.g. `linearGauge`) and allows it to be used where a Widget object is accepted.

        This allows for future implementations of Widget objects if needed.
        """
        return value  # fixme: this hackiness


class ApplicationVariant:
    """Represents variants of how applications are displayed to users.

    The default variant is `submodule`.

    Attributes
    ----------
    submodule
        Embeds applications within a submodule to provide logical differences between multiple apps on a device.
    stacked
        Stacks applications on top of each other without submodule partitioning.
    """

    submodule: ClassVar[str] = "submodule"
    stacked: ClassVar[str] = "stacked"
