from typing import Union
from datetime import datetime

from .interaction import Interaction
from .misc import NotSet


class Parameter(Interaction):
    """Base class for UI parameters. All parameters should inherit from this class."""

    type = NotImplemented


class NumericParameter(Parameter):
    """A numeric parameter that can be used to represent both integer and float values.

    Attributes
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    min: Union[int, float], optional
        The minimum value for the parameter. Defaults to None.
    max: Union[int, float], optional
        The maximum value for the parameter. Defaults to None.
    """

    type = "uiFloatParam"

    def __init__(
        self,
        name,
        display_name,
        min_val: Union[int, float] = None,
        max_val: Union[int, float] = None,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)

        self.min = min_val or kwargs.pop("float_min", None)
        self.max = max_val or kwargs.pop("float_max", None)

    def to_dict(self):
        result = super().to_dict()

        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max

        return result


class TextParameter(Parameter):
    """A text parameter that can be used to represent string values for a user to modify.

    This can either be inline or a large form text area, depending on the `is_text_area` parameter.

    Attributes
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    is_text_area: bool
        Whether the text parameter should be displayed as a text area. Defaults to False.
    """

    type = "uiTextParam"

    def __init__(self, name, display_name, is_text_area: bool = False, **kwargs):
        super().__init__(name, display_name, **kwargs)
        self.is_text_area = is_text_area

    def to_dict(self):
        result = super().to_dict()
        result["isTextArea"] = self.is_text_area
        return result


class BooleanParameter(Parameter):
    """
    A boolean parameter that can be used to represent true/false values.

    Warnings
    --------
    This is not implemented in the doover site yet, and will raise a NotImplementedError if used!

    Attributes
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    """

    type = "uiBoolParam"

    def __init__(self, name, display_name, **kwargs):
        super().__init__(name, display_name, **kwargs)
        raise NotImplementedError("boolean parameter not implemented in doover site.")


class DateTimeParameter(Parameter):
    """Date and time parameter that can be used to request date/time values from a user.

    Internally, all datetime values are stored as epoch seconds in UTC

    Attributes
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    include_time: bool
        Whether to include time in the datetime picker. Defaults to False.
    """

    type = "uiDatetimeParam"

    def __init__(
        self, name: str, display_name: str, include_time: bool = False, **kwargs
    ):
        super().__init__(name, display_name, **kwargs)
        self.include_time = include_time

    @property
    def current_value(self) -> datetime | None:
        """datetime, optional: Returns the current value of the parameter as a datetime object, or `None` if it isn't set."""
        if self._current_value is NotSet or self._current_value is None:
            return None
        if isinstance(self._current_value, datetime):
            return self._current_value
        elif isinstance(self._current_value, (int, float)):
            return datetime.utcfromtimestamp(self._current_value)
        return None

    @current_value.setter
    def current_value(self, new_val):
        if isinstance(new_val, datetime):
            new_val = int(new_val.timestamp())
        self._current_value = new_val

    def to_dict(self):
        result = super().to_dict()
        result["includeTime"] = self.include_time
        return result


def numeric_parameter(
    name: str,
    display_name: str,
    min_val: Union[int, float] = None,
    max_val: Union[int, float] = None,
    **kwargs,
):
    """Decorator to create a numeric parameter for a function.

    The function decorated by this decorator will be called whenever the value of the numeric parameter changes.

    Examples
    --------

    A basic numeric parameter with a range of 0 to 100 ::

        @ui.numeric_parameter(
            name="example_numeric",
            display_name="Example Numeric Parameter",
            min_val=0,
            max_val=100
        )
        def example_function(value: float):
            print(f"Numeric parameter changed to: {value}")


    Parameters
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    min_val: Union[int, float], optional
        The minimum value for the parameter. Defaults to None.
    max_val: Union[int, float], optional
        The maximum value for the parameter. Defaults to None.
    """

    def decorator(func):
        func._ui_type = NumericParameter
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "min_val": min_val,
            "max_val": max_val,
            **kwargs,
        }
        return func

    return decorator


def text_parameter(name: str, display_name: str, is_text_area: bool = False, **kwargs):
    """Decorator to create a text parameter for a function.

    The function decorated by this decorator will be called whenever the value of the text parameter changes.

    Examples
    --------

    A basic text parameter ::

        @ui.text_parameter(
            name="example_text",
            display_name="Example Text Parameter"
        )
        def example_function(value: str):
            print(f"Text parameter changed to: {value}")


    Parameters
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    is_text_area: bool
        Whether the text parameter should be displayed as a text area. Defaults to False.
    """

    def decorator(func):
        func._ui_type = TextParameter
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "is_text_area": is_text_area,
            **kwargs,
        }
        return func

    return decorator


def boolean_parameter(name: str, display_name: str, **kwargs):
    """Decorator to create a boolean parameter for a function.

    The function decorated by this decorator will be called whenever the value of the boolean parameter changes.

    Warnings
    --------
    This is not implemented in the doover site yet, and will raise a NotImplementedError if used!

    Parameters
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    """

    def decorator(func):
        func._ui_type = BooleanParameter
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            **kwargs,
        }
        return func

    return decorator


def datetime_parameter(
    name: str, display_name: str, include_time: bool = False, **kwargs
):
    """Decorator to create a datetime parameter for a function.

    The function decorated by this decorator will be called whenever the value of the datetime parameter (picker) changes.

    Examples
    --------
    A basic datetime parameter with time included ::

        @ui.datetime_parameter(
            name="example_datetime",
            display_name="Example Datetime Parameter",
            include_time=True
        )
        def example_function(value: datetime):
            print(f"Datetime parameter changed to: {value}")


    Parameters
    ----------
    name: str
        The name of the parameter.
    display_name: str
        The display name of the parameter.
    include_time: bool
        Whether to include time in the datetime picker. Defaults to False.
    """

    def decorator(func):
        func._ui_type = DateTimeParameter
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "include_time": include_time,
            **kwargs,
        }
        return func

    return decorator
