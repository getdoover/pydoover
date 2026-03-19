import warnings
from typing import Union
from datetime import datetime

from .declarative import is_tag_reference, normalize_ui_value
from .interaction import Interaction
from .misc import NotSet


def _warn_legacy_ui_alias(old_name: str, new_name: str) -> None:
    warnings.warn(
        f"{old_name} is deprecated and will be removed in a future release. "
        f"Use {new_name} instead.",
        DeprecationWarning,
        stacklevel=3,
    )


class Parameter(Interaction):
    """Base class for UI parameters. All parameters should inherit from this class."""

    type = NotImplemented


class FloatInput(Parameter):
    """A numeric input that can be used to represent both integer and float values.

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

    type = "uiFloatInput"

    def __init__(
        self,
        name,
        display_name,
        min_val: Union[int, float] = None,
        max_val: Union[int, float] = None,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)

        self.min = min_val if min_val is not None else kwargs.pop("float_min", None)
        self.max = max_val if max_val is not None else kwargs.pop("float_max", None)

    def to_dict(self):
        result = super().to_dict()

        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max

        return normalize_ui_value(result)


class NumericParameter(FloatInput):
    """Deprecated Doover 1.0 alias for :class:`FloatInput`."""

    type = "uiFloatParam"

    def __init__(self, *args, **kwargs):
        if self.__class__ is NumericParameter:
            _warn_legacy_ui_alias("NumericParameter", "FloatInput")
        super().__init__(*args, **kwargs)


class TextInput(Parameter):
    """A text input that can be used to represent string values for a user to modify.

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

    type = "uiTextInput"

    def __init__(self, name, display_name, is_text_area: bool = False, **kwargs):
        super().__init__(name, display_name, **kwargs)
        self.is_text_area = is_text_area

    def to_dict(self):
        result = super().to_dict()
        result["isTextArea"] = self.is_text_area
        return normalize_ui_value(result)


class TextParameter(TextInput):
    """Deprecated Doover 1.0 alias for :class:`TextInput`."""

    type = "uiTextParam"

    def __init__(self, *args, **kwargs):
        if self.__class__ is TextParameter:
            _warn_legacy_ui_alias("TextParameter", "TextInput")
        super().__init__(*args, **kwargs)


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


class DatetimeInput(Parameter):
    """A datetime input that can be used to request date and time values from a user.

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

    type = "uiDatetimeInput"

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
        if is_tag_reference(self._current_value):
            return self._current_value
        if isinstance(self._current_value, datetime):
            return self._current_value
        elif isinstance(self._current_value, (int, float)):
            return datetime.utcfromtimestamp(self._current_value)
        return None

    @current_value.setter
    def current_value(self, new_val):
        self._ensure_current_value_writable()
        if isinstance(new_val, datetime):
            new_val = int(new_val.timestamp())
        self._current_value = new_val

    def to_dict(self):
        result = super().to_dict()
        result["includeTime"] = self.include_time
        return normalize_ui_value(result)


class TimeInput(DatetimeInput):
    """A time-only input."""

    type = "uiTimeInput"

    def __init__(self, name: str, display_name: str, **kwargs):
        super().__init__(name, display_name, include_time=True, **kwargs)


class DateTimeParameter(DatetimeInput):
    """Deprecated Doover 1.0 alias for :class:`DatetimeInput`."""

    type = "uiDatetimeParam"

    def __init__(self, *args, **kwargs):
        if self.__class__ is DateTimeParameter:
            _warn_legacy_ui_alias("DateTimeParameter", "DatetimeInput")
        super().__init__(*args, **kwargs)


def float_input(
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
        func._ui_type = FloatInput
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "min_val": min_val,
            "max_val": max_val,
            **kwargs,
        }
        return func

    return decorator


def numeric_parameter(
    name: str,
    display_name: str,
    min_val: Union[int, float] = None,
    max_val: Union[int, float] = None,
    **kwargs,
):
    """Deprecated Doover 1.0 alias for :func:`float_input`."""

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


def text_input(name: str, display_name: str, is_text_area: bool = False, **kwargs):
    """Decorator to create a text input for a function.

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
        func._ui_type = TextInput
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "is_text_area": is_text_area,
            **kwargs,
        }
        return func

    return decorator


def text_parameter(name: str, display_name: str, is_text_area: bool = False, **kwargs):
    """Deprecated Doover 1.0 alias for :func:`text_input`."""

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


def datetime_input(name: str, display_name: str, include_time: bool = False, **kwargs):
    """Decorator to create a datetime input for a function.

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
        func._ui_type = DatetimeInput
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "include_time": include_time,
            **kwargs,
        }
        return func

    return decorator


def time_input(name: str, display_name: str, **kwargs):
    """Decorator to create a time-only input for a function."""

    def decorator(func):
        func._ui_type = TimeInput
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
    """Deprecated Doover 1.0 alias for :func:`datetime_input`."""

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
