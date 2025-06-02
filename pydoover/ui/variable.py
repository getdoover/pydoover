from datetime import datetime

from typing import Union, Any

from .element import Element
from .misc import Range, Widget, NotSet


class Variable(Element):
    """Base class for UI variables. All variables should inherit from this class.

    A variable is a read-only value in the UI which is updated by a device periodically.

    Parameters
    ----------
    name: str
        The name of the variable.
    display_name: str
        The display name of the variable.
    var_type: str
        The type of the variable (e.g., "float", "string", "bool", "time").
    curr_val: Any
        The current value of the variable. If not set, defaults to NotSet.
    precision: int, optional
        The number of decimal places to round the current value to. Defaults to None.
    ranges: list[Range]
        A list of ranges associated with the variable, used for display purposes.
    earliest_data_time: datetime, optional
        The earliest time for which data is available for this variable. Defaults to None.
    """

    type = "uiVariable"

    def __init__(
        self,
        name: str,
        display_name: str,
        var_type: str,
        curr_val: Any = NotSet,
        precision: int = None,
        ranges: list[Union[Range, dict]] = None,
        earliest_data_time: datetime | None = None,
        default_zoom: str | None = None,
        **kwargs,
    ):
        # kwargs: verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout
        super().__init__(name, display_name, **kwargs)

        self.var_type = var_type
        self._curr_val = curr_val
        self.precision = precision or kwargs.pop("dec_precision", None)
        self.earliest_data_time = earliest_data_time
        self.default_zoom = default_zoom or kwargs.pop("default_zoom", None)

        self.ranges = []
        if ranges is not None:
            self.add_ranges(*ranges)

    def to_dict(self):
        result = super().to_dict()
        result["type"] = self.type
        result["varType"] = self.var_type

        curr_val = self.current_value
        if curr_val is not None:
            result["currentValue"] = curr_val

        if self.precision is not None:
            result["decPrecision"] = self.precision

        if self.earliest_data_time is not None:
            if isinstance(self.earliest_data_time, datetime):
                result["earliestDataDate"] = int(self.earliest_data_time.timestamp())
            else:
                result["earliestDataDate"] = self.earliest_data_time

        if self.default_zoom is not None:
            result["defaultZoom"] = self.default_zoom

        result["ranges"] = [r.to_dict() for r in self.ranges]
        return result

    @property
    def current_value(self):
        """Returns the current value of the variable."""
        if self._curr_val is NotSet:
            return None
        return self._curr_val

    @current_value.setter
    def current_value(self, val):
        """Updates the current value of the variable."""
        self.update(val)

    def update(self, new_value: Any) -> None:
        """Updates the current value of the variable.

        If precision is set, rounds the value to the specified number of decimal places.

        Parameters
        ----------
        new_value: Any
            The new value to set for the variable. If None, it sets the current value to None.
        """
        if self.precision is not None and new_value is not None:
            self._curr_val = round(new_value, self.precision)
        else:
            self._curr_val = new_value

    def recv_ui_state_update(self, state: dict[str, Any]) -> None:
        if self._curr_val is NotSet and "currentValue" in state:
            self.current_value = state["currentValue"]

    def add_ranges(self, *range_val: Range):
        """Adds one or more ranges to the variable.

        Parameters
        ----------
        range_val: list[Range]
            A list of Range objects to be added.
        """
        for r in range_val:
            # still support legacy dict passing of range values.
            if isinstance(r, Range):
                self.ranges.append(r)
            elif isinstance(r, dict):
                self.ranges.append(Range.from_dict(r))


class NumericVariable(Variable):
    """Represents a numeric variable in the UI, which can be an integer or a float.

    Parameters
    ----------
    name: str
        The name of the variable.
    display_name: str
        The display name of the variable.
    curr_val: Union[int, float], optional
        The current value of the variable. Defaults to None.
    precision: int, optional
        The number of decimal places to round the current value to. Defaults to None.
    ranges: list[Range], optional
        A list of ranges associated with the variable, used for display purposes. Defaults to None.
    form: Widget, optional
        A widget or string representing the form for this variable. Defaults to None.
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        curr_val: Union[int, float] = None,
        precision: int = None,
        ranges: list[Range] = None,
        form: Widget | None = None,
        **kwargs,
    ):
        super().__init__(
            name,
            display_name,
            var_type="float",
            curr_val=curr_val,
            precision=precision,
            ranges=ranges,
            **kwargs,
        )
        self.form = form

    def to_dict(self):
        result = super().to_dict()
        if self.form is not None:
            result["form"] = self.form
        return result


class TextVariable(Variable):
    """Represents a text variable in the UI, which can be used to display or input string values.

    Parameters
    ----------
    name: str
        The name of the variable.
    display_name: str
        The display name of the variable.
    curr_val: str, optional
        The current value of the variable. Defaults to None.
    """

    def __init__(self, name: str, display_name: str, curr_val: str = None, **kwargs):
        # fixme: double check this type
        super().__init__(
            name, display_name, var_type="string", curr_val=curr_val, **kwargs
        )


class BooleanVariable(Variable):
    """Represents a boolean variable in the UI, which can be used to represent true/false values.

    Parameters
    ----------
    name: str
        The name of the variable.
    display_name: str
        The display name of the variable.
    curr_val: bool, optional
        The current value of the variable. Defaults to None.
    """

    def __init__(self, name: str, display_name: str, curr_val: bool = None, **kwargs):
        super().__init__(
            name, display_name, var_type="bool", curr_val=curr_val, **kwargs
        )


class DateTimeVariable(Variable):
    """Represents a date/time variable in the UI, which can be used to display or input datetime values.

    Parameters
    ----------
    name: str
        The name of the variable.
    display_name: str
        The display name of the variable.
    curr_val: Union[datetime, int], optional
        The current value of the variable, which can be a datetime object or a timestamp (int). Defaults to None.
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        curr_val: Union[datetime, int] = None,
        **kwargs,
    ):
        # fixme: double check this type, and how to handle different date / time / datetime
        super().__init__(
            name, display_name, var_type="time", curr_val=curr_val, **kwargs
        )
