import warnings

from .declarative import normalize_ui_value
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
        display_name,
        min_val: int | float = NotSet,
        max_val: int | float = NotSet,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)

        self.min = min_val
        self.max = max_val

    def to_dict(self):
        result = super().to_dict()

        if self.min is not NotSet:
            result["min"] = self.min
        if self.max is not NotSet:
            result["max"] = self.max

        return normalize_ui_value(result)


class TextInput(Parameter):
    """A text input that can be used to represent string values for a user to modify.

    This can either be inline or a large form text area, depending on the `is_text_area` parameter.

    Attributes
    ----------
    display_name: str
        The display name of the parameter.
    is_text_area: bool
        Whether the text parameter should be displayed as a text area. Defaults to False.
    """

    type = "uiTextInput"

    def __init__(self, display_name, is_text_area: bool = False, **kwargs):
        super().__init__(display_name, **kwargs)
        self.is_text_area = is_text_area

    def to_dict(self):
        result = super().to_dict()
        result["isTextArea"] = self.is_text_area
        return normalize_ui_value(result)


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

    def __init__(self, display_name: str, include_time: bool = False, **kwargs):
        super().__init__(display_name, **kwargs)
        self.include_time = include_time

    # @property
    # def current_value(self) -> datetime | None:
    #     """datetime, optional: Returns the current value of the parameter as a datetime object, or `None` if it isn't set."""
    #     if self._current_value is NotSet or self._current_value is None:
    #         return None
    #     if is_tag_reference(self._current_value):
    #         return self._current_value
    #     if isinstance(self._current_value, datetime):
    #         return self._current_value
    #     elif isinstance(self._current_value, (int, float)):
    #         return datetime.utcfromtimestamp(self._current_value)
    #     return None

    def to_dict(self):
        result = super().to_dict()
        result["includeTime"] = self.include_time
        return normalize_ui_value(result)


class TimeInput(DatetimeInput):
    """A time-only input."""

    type = "uiTimeInput"

    def __init__(self, display_name: str, **kwargs):
        super().__init__(display_name, include_time=True, **kwargs)
