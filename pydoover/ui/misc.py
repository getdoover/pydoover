from typing import Any, ClassVar

from .declarative import normalize_ui_value


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
    name: str
        The name of the option, used for identification.
    display_name: str
        The display name of the option, used for user interface representation.
    """

    def __init__(self, name: str, display_name: Any):
        self.name = name
        self.display_name = display_name

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
        return cls(data["name"], data["display_str"])


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
