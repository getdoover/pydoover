from datetime import datetime, timedelta

from typing import Any

from .declarative import is_tag_reference, normalize_ui_value
from .element import Element
from .misc import Range, Widget, NotSet


class Variable(Element):
    """Base class for UI variables. All variables should inherit from this class.

    A variable is a read-only value in the UI which is updated by a device periodically.

    Parameters
    ----------
    display_name: str
        The display name of the variable.
    var_type: str
        The type of the variable (e.g., "float", "string", "bool", "time").
    value: Any
        The current value of the variable. If not set, defaults to NotSet.
    precision: int, optional
        The number of decimal places to round the current value to. Defaults to None.
    ranges: list[Range]
        A list of ranges associated with the variable, used for display purposes.
    earliest_data_time: datetime, optional
        The earliest time for which data is available for this variable. Defaults to None.
    default_range_since: timedelta, optional
        The timedelta which defines how many seconds the plot should show on load. Defaults to a week if not set.
    default_zoom: str, optional
        The default zoom setting for the inbuilt plot viewer. Defaults to None.
    log_threshold: float, optional
        The change threshold for logging the variable. Defaults to None (no threshold). 0 means log every change.
    """

    type = "uiVariable"

    def __init__(
        self,
        display_name: str,
        var_type: str,
        value: Any = NotSet,
        precision: int = NotSet,
        ranges: list[Range] = NotSet,
        earliest_data_time: datetime = NotSet,
        default_range_since: timedelta = NotSet,
        default_zoom: str = NotSet,
        log_threshold: float = NotSet,
        **kwargs,
    ):
        # kwargs: verbose_str=verbose_str, show_activity=show_activity, form=form, graphic=graphic, layout=layout
        super().__init__(display_name, **kwargs)

        self.var_type = var_type
        self.value = value
        self.precision = precision
        self.earliest_data_time = earliest_data_time
        self.default_range_since = default_range_since
        self.default_zoom = default_zoom
        self.log_threshold = log_threshold

        self.ranges = ranges

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["type"] = self.type
        result["varType"] = self.var_type

        if self.value is not NotSet:
            result["currentValue"] = self.value

        if self.precision is not NotSet:
            result["decPrecision"] = self.precision

        # fixme: this should be in milliseconds
        if self.earliest_data_time is not NotSet:
            if isinstance(self.earliest_data_time, datetime):
                result["earliestDataDate"] = int(self.earliest_data_time.timestamp())
            else:
                result["earliestDataDate"] = self.earliest_data_time

        if self.default_range_since is not NotSet:
            result["defaultRangeSince"] = (
                int(self.default_range_since.total_seconds()) * 1000
            )

        if self.default_zoom is not NotSet:
            result["defaultZoom"] = self.default_zoom

        if self.ranges is not NotSet:
            result["ranges"] = [r.to_dict() for r in self.ranges]
        return normalize_ui_value(result)


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
        display_name: str,
        value: Any = None,
        precision: int = NotSet,
        ranges: list[Range] = NotSet,
        form: Widget = NotSet,
        **kwargs,
    ):
        super().__init__(
            display_name,
            var_type="float",
            value=value,
            precision=precision,
            ranges=ranges,
            **kwargs,
        )
        self.form = form

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        if self.form is not NotSet:
            result["form"] = self.form
        return normalize_ui_value(result)


class TextVariable(Variable):
    """Represents a text variable in the UI, which can be used to display or input string values.

    Parameters
    ----------
    display_name: str
        The display name of the variable.
    value: str, optional
        The current value of the variable. Defaults to None.
    """

    def __init__(self, display_name: str, value: str, **kwargs):
        # fixme: double check this type
        super().__init__(display_name, var_type="string", value=value, **kwargs)


class BooleanVariable(Variable):
    """Represents a boolean variable in the UI, which can be used to represent true/false values.

    Parameters
    ----------
    display_name: str
        The display name of the variable.
    curr_val: bool, optional
        The current value of the variable. Defaults to None.
    log_threshold: float, optional
        The change threshold for logging the variable. Defaults to 0 (log every change). None means don't log on change.
    """

    def __init__(
        self,
        display_name: str,
        value: bool,
        log_threshold: float | None = 0,
        **kwargs,
    ):
        super().__init__(
            display_name,
            var_type="bool",
            value=value,
            log_threshold=log_threshold,
            **kwargs,
        )


class DateTimeVariable(Variable):
    """Represents a date/time variable in the UI, which can be used to display or input datetime values.

    Parameters
    ----------
    name: str
        The name of the variable.
    display_name: str
        The display name of the variable.
    value: datetime, optional
        The current value of the variable, which can be a datetime object or a timestamp (int). Defaults to None.
    """

    def __init__(
        self,
        display_name: str,
        value: datetime,
        **kwargs,
    ):
        # fixme: double check this type, and how to handle different date / time / datetime
        super().__init__(display_name, var_type="time", value=value, **kwargs)


class Timestamp(Variable):
    type = "uiTimestamp"

    def __init__(self, display_name: str, value: datetime, **kwargs):
        # this might do some weird stuff where people think they can have ranges and what not, but yeah...
        # this will do for now...
        super().__init__(display_name, value=value, var_type="timestamp", **kwargs)

    def to_dict(self):
        result = super().to_dict()
        if is_tag_reference(self.value):
            result["currentValue"] = self.value
        else:
            result["currentValue"] = self.value and int(self.value.timestamp() * 1000)
        return normalize_ui_value(result)
