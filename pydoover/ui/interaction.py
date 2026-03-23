import logging
import warnings
from typing import TYPE_CHECKING, Any

from .declarative import normalize_ui_value
from .element import Element
from .misc import Option, NotSet

if TYPE_CHECKING:
    from .manager import UICommandsManager

log = logging.getLogger(__name__)


def _warn_legacy_ui_alias(old_name: str, new_name: str) -> None:
    warnings.warn(
        f"{old_name} is deprecated and will be removed in a future release. "
        f"Use {new_name} instead.",
        DeprecationWarning,
        stacklevel=3,
    )


class Interaction(Element):
    """Base class for all UI interactions.

    Interactions are elements that can be interacted with by the user, such as buttons, sliders, and text inputs.

    Parameters
    ----------
    name: str
        The name of the interaction, used to identify it in the UI.
    display_name: str, optional
        The display name of the interaction, shown in the UI.
    value: Any
        The current value of the interaction. Defaults to NotSet.
    default: Any
        The default value for the interaction, used if current_value is NotSet.
    callback: callable, optional
        A callback function that is called when the interaction value changes.
    transform_check: callable, optional
        A function to transform and check the new value before setting it. Defaults to None.
    show_activity: bool, optional
        Whether to show this interaction in the activity log. Defaults to None which uses the site default.
    """

    type = "uiInteraction"

    def __init__(
        self,
        display_name: str,
        default: Any = NotSet,
        show_activity: bool = NotSet,
        requires_confirm: bool = NotSet,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)
        self.default = default

        # these must both be set at runtime.
        self._manager: "UICommandsManager" = None

        self.show_activity = show_activity
        self.requires_confirm = requires_confirm

    @property
    def value(self):
        return self._manager.get_value(self.name)

    async def set(self, value: Any, max_age: float = 10.0, log_update: bool = True):
        # fixme: this is equivaltent to the old 'coerce' function which updates the UI to have this value
        # appear in the input box.
        # it will record a message in the ui_cmds channel if log_update is true, otherwise will just update the aggregate.
        await self._manager.set_value(self.name, value, log_update)
        # if log_update:
        #     await self._manager.create_log(self.name, value)
        # await self._api.create_message("ui_cmds", {"type": "log", "value": value})

    async def handler(self, ctx, payload):
        # raise NotImplementedError("you must implement this handler.")
        # fixme: default implementation ok??
        await self.set(payload)

    def to_dict(self):
        res = super().to_dict()
        if self.requires_confirm is not NotSet:
            res["requiresConfirm"] = self.requires_confirm
        if self.show_activity is not NotSet:
            res["showActivity"] = self.show_activity
        return normalize_ui_value(res)

    # @property
    # def current_value(self):
    #     """Returns the current value of the interaction."""
    #     if self._current_value is NotSet and self._default_value is not None:
    #         return self._default_value
    #     return self._current_value if self._current_value is not NotSet else None
    #
    # @current_value.setter
    # def current_value(self, new_val):
    #     """Sets the current value of the interaction.
    #
    #     This will also convert datetime objects to epoch seconds for internal storage.
    #     """
    #     self._ensure_current_value_writable()
    #     ## Store all datetime objects as epoch seconds internally
    #     if isinstance(new_val, datetime):
    #         new_val = int(new_val.timestamp())
    #     self._current_value = new_val
    #
    # def _json_safe_current_value(self):
    #     result = self.current_value
    #     if isinstance(result, datetime):
    #         return int(result.timestamp())
    #     if isinstance(result, (set, tuple, list)):
    #         # fixme: the site currently treats sets and tuples as lists, so lets just give in to that for now.
    #         return list(result)
    #     return result

    # def callback(self, new_value: Any):
    #     """Callback function to handle changes to the interaction value.
    #
    #     Parameters
    #     ----------
    #     new_value: Any
    #         The new value of the interaction.
    #     """
    #     return
    #
    # def transform_check(self, new_value: Any) -> Any:
    #     """Transform and check a new value before setting it.
    #
    #     This is called before any callback functions are invoked.
    #
    #     By default, this will replace any None values with a set default value.
    #
    #     Parameters
    #     ----------
    #     new_value: Any
    #         The new value to transform and check.
    #
    #     Returns
    #     -------
    #     Any: The transformed value, or the default value if new_value is None.
    #     """
    #     if new_value is None and self._default_value is not None:
    #         return self._default_value
    #     else:
    #         return new_value

    # def _is_new_value(self, new_value: Any) -> bool:
    #     if is_tag_reference(self._current_value):
    #         return new_value != self._last_command_value
    #     return new_value != self.current_value
    #
    # def _handle_new_value_common(self, new_value: Any):
    #     try:
    #         new_value = self._transform_check(new_value)
    #     except Exception as e:
    #         log.error(f"Error transforming value for {self.name}: {e}")
    #         return
    #
    #     log.debug(f"updating new value: {self.name} {new_value}")
    #     if is_tag_reference(self._current_value):
    #         self._last_command_value = new_value
    #     else:
    #         self.current_value = new_value
    #
    # def _handle_new_value(self, new_value: Any):
    #     self._handle_new_value_common(new_value)
    #     try:
    #         self._callback(new_value)
    #     except Exception as e:
    #         log.error(f"Error in callback for {self.name}: {e}")
    #
    # async def _handle_new_value_async(self, new_value: Any):
    #     self._handle_new_value_common(new_value)
    #     await call_maybe_async(self._callback, new_value)

    # def coerce(self, value: Any, critical: bool = False) -> None:
    #     """Coerce the interaction to a new value.
    #
    #     This will update the current value on the site.
    #
    #     The callback will be invoked once the site has set the value.
    #
    #     Parameters
    #     ----------
    #     value: Any
    #         The new value to set for the interaction.
    #     critical: bool
    #         If True, this interaction is considered critical and will mark the manager as having a pending critical interaction.
    #         This is used to ensure that critical interactions are processed immediately and logged on the site.
    #
    #     Returns
    #     -------
    #     None
    #     """
    #     self._ensure_current_value_writable()
    #
    #     if critical and self._manager and value != self.current_value:
    #         self._manager._has_critical_interaction_pending = True
    #
    #     if self._manager is not None and self._current_value != value:
    #         # we need a way to keep track of which interactions our application has "changed"
    #         # so we don't override ui_cmds that other apps set. ui_cmds ideally should be namespaced
    #         # so this isn't a problem.
    #         self._manager._changed_interactions.add(self.name)
    #
    #     self.current_value = value

    # def _ensure_current_value_writable(self) -> None:
    #     if is_tag_reference(self._current_value):
    #         raise RuntimeError(
    #             f"UI element '{self.name}' field 'currentValue' is tag-backed. "
    #             "Update the underlying tag instead."
    #         )


class Button(Interaction):
    """Represents a UI button.

    Parameters
    ----------
    display_name: str
        The display name of the action, shown in the UI.
    disabled: bool
        Whether the button appears disabled in the UI. Defaults to False.
    """

    type = "uiButton"

    def __init__(
        self,
        display_name: str,
        disabled: bool = NotSet,
        label_string: str = NotSet,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)
        self.disabled = disabled
        self.label_string = label_string

    def to_dict(self):
        result = super().to_dict()
        if self.disabled is not NotSet:
            result["disabled"] = self.disabled
        if self.label_string is not NotSet:
            result["labelString"] = self.label_string
        return normalize_ui_value(result)


class WarningIndicator(Interaction):
    """Represents a warning indicator in the UI.

    Parameters
    ----------
    name: str
        The name of the warning indicator, used to identify it in the UI.
    display_name: str
        The display name of the warning indicator, shown in the UI.
    can_cancel: bool
        Whether the warning can be cancelled by the user. Defaults to True.
    """

    type = "uiWarningIndicator"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_cancel = kwargs.pop("can_cancel", True)

    def to_dict(self):
        result = super().to_dict()
        result["can_cancel"] = self.can_cancel
        return normalize_ui_value(result)


class Select(Interaction):
    """Represents a selectable input in the UI.

    Parameters
    ----------
    display_name: str, optional
        The display name of the state command, shown in the UI.
    options: list[Option]
        A list of options that the user can select from. Each option is an instance of the Option class.
        If not provided, an empty list will be created.
    """

    type = "uiSelect"

    def __init__(
        self,
        display_name: str | None = None,
        options: list[Option] | None = None,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)
        self.options = options

    def to_dict(self):
        result = super().to_dict()
        result["options"] = {o.name: o.to_dict() for o in self.options}
        return normalize_ui_value(result)


class Slider(Interaction):
    """Represents a slider in the UI.

    Parameters
    ----------
    name: str
        The name of the slider, used to identify it in the UI.
    display_name: str, optional
        The display name of the slider, shown in the UI.
    min_val: int
        The minimum value of the slider. Defaults to 0.
    max_val: int
        The maximum value of the slider. Defaults to 100.
    step_size: float
        The step size of the slider. Defaults to 0.1.
    dual_slider: bool
        Whether the slider has a dual handle. Defaults to True.
    inverted: bool
        Whether the slider is inverted (i.e., moves left for higher values). Defaults to True.
    icon: str, optional
        An optional icon to display with the slider.
    colours: str, optional
        An optional string representing colours for the slider, such as "red,green,blue".
    """

    type = "uiSlider"

    # fixme: should these parameters all be not set's?
    def __init__(
        self,
        display_name: str,
        min_val: int = 0,
        max_val: int = 100,
        step_size: float = 0.1,
        dual_slider: bool = True,
        inverted: bool = True,
        colours: str = NotSet,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.step_size = step_size
        self.dual_slider = dual_slider
        self.inverted = inverted
        self.colours = colours

    def to_dict(self):
        result = super().to_dict()
        result["min"] = self.min_val
        result["max"] = self.max_val
        result["stepSize"] = self.step_size
        result["dualSlider"] = self.dual_slider
        result["isInverted"] = self.inverted

        # don't pass values if they have a default value of None since we treat this as "remove element" in a diff.
        if self.colours is not NotSet:
            result["colours"] = self.colours

        return normalize_ui_value(result)


class Switch(Interaction):
    type = "uiSwitch"


# def callback(pattern: str | re.Pattern[str], global_interaction: bool = False):
#     r"""Decorator to mark a function as a UI callback.
#
#     This accepts either a string or a compiled regex expression to match against the UI element name.
#
#     Examples
#     --------
#
#     A callback for a single UI element ::
#
#         @ui.callback("di_fetch")
#         def fetch_di(self, element, new_value):
#             pass
#
#
#     A generic callback to match multiple elements ::
#
#         @ui.callback(re.compile(r"do_\d+_toggle"))
#         def do_toggle(self, element, new_value):
#             pass
#
#     .. note::
#
#         Due to how apps namespace interaction names, if you pass in a string, `{app_name}_` will be prepended to the pattern.
#         This means that if you want to trigger a callback for a "global" interaction
#         (the most notable example being the camera "Get Now" button), global_interaction=True.
#
#     An example global command::
#
#         @ui.callback("camera_get_now", global_interaction=True)
#         def camera_get_now(self, element, new_value):
#             pass
#
#
#     .. note::
#
#         Similar to the above, regex patterns will also be re-compiled and prepended with `{app_name}_` by default.
#         You can disable this behaviour by passing `global_interaction=True` to the decorator.
#
#     An example regex compiled global command::
#
#         @ui.callback("^test_global_param_\d+$", global_interaction=True)
#         def test_global_param(self, element, new_value):
#             pass
#
#
#     Parameters
#     ----------
#     pattern: str | re.Pattern[str]
#         A string or compiled regex pattern that matches the name of the UI element this callback is for.
#     global_interaction: bool
#         See above examples for when to use this. This is a special case.
#     """
#
#     def decorator(func):
#         func._is_ui_callback = True
#         func._is_ui_global_interaction = global_interaction
#         func._ui_callback_pattern = pattern
#         return func
#
#     return decorator
