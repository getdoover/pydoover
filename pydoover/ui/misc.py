from typing import Union, Any


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

    blue = "blue"
    yellow = "yellow"
    red = "red"
    green = "green"
    magenta = "magenta"
    limegreen = "limegreen"
    tomato = "tomato"
    orange = "orange"
    purple = "purple"
    grey = "grey"

    @classmethod
    def from_hex(cls, hex_string):
        """Convert a hex string to a colour string.

        This method takes a hex string (e.g., "#FF5733") that can be used where a Colour object is accepted.
        """
        return hex_string

    @classmethod
    def from_string(cls, value):
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
        label: str = None,
        min_val: Union[int, float] = None,
        max_val: Union[int, float] = None,
        colour: "Colour" = Colour.blue,
        show_on_graph: bool = True,
    ):
        self.label = label
        self.min = min_val
        self.max = max_val
        self.colour = colour
        self.show_on_graph = show_on_graph

    def to_dict(self):
        to_return = {
            "min": self.min,
            "max": self.max,
            "colour": self.colour,
            "show_on_graph": self.show_on_graph,
        }
        if self.label:
            to_return["label"] = self.label
        return to_return

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

    def __init__(self, name: str, display_name: str):
        self.name = name
        self.display_name = display_name

    def to_dict(self):
        return {
            "name": self.name,
            "displayString": self.display_name,
            "type": "uiElement",
        }

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

    linear = "linearGauge"
    radial = "radialGauge"

    @classmethod
    def from_string(cls, value):
        """Convert an arbitrary string to a Widget object.

        This method takes a string (e.g. `linearGauge`) and allows it to be used where a Widget object is accepted.

        This allows for future implementations of Widget objects if needed.
        """
        return value  # fixme: this hackiness
