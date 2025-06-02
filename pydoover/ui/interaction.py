import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from .element import Element
from .misc import Colour, Option, NotSet
from ..utils import call_maybe_async

if TYPE_CHECKING:
    from .manager import UIManager

log = logging.getLogger(__name__)


class Interaction(Element):
    """Base class for all UI interactions.

    Interactions are elements that can be interacted with by the user, such as buttons, sliders, and text inputs.

    Parameters
    ----------
    name: str
        The name of the interaction, used to identify it in the UI.
    display_name: str, optional
        The display name of the interaction, shown in the UI.
    current_value: Any
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
        name: str,
        display_name: str = None,
        current_value: Any = NotSet,
        default: Any = None,
        callback=None,
        transform_check=None,
        show_activity: bool | None = None,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)
        self._current_value = current_value
        self._default_value = default or kwargs.pop("default_val", None)

        self._manager: Optional["UIManager"] = None

        if callback:
            self.callback = callback
        if transform_check:
            self.transform_check = transform_check

        ## Handle default value 'statelessly' now in current_value property instead of here
        # if self._current_value in (None, NotSet) and self._default_value is not None:
        #     print(f"Coercing {self.name} to default value {self._default_value}")
        #     self.coerce(self._default_value)

        self.show_activity = show_activity

    @property
    def current_value(self):
        """Returns the current value of the interaction."""
        if self._current_value is NotSet and self._default_value is not None:
            return self._default_value
        return self._current_value if self._current_value is not NotSet else None

    @current_value.setter
    def current_value(self, new_val):
        """Sets the current value of the interaction.

        This will also convert datetime objects to epoch seconds for internal storage.
        """
        ## Store all datetime objects as epoch seconds internally
        if isinstance(new_val, datetime):
            new_val = int(new_val.timestamp())
        self._current_value = new_val

    def _json_safe_current_value(self):
        result = self.current_value
        if isinstance(result, datetime):
            return int(result.timestamp())
        if isinstance(result, (set, tuple, list)):
            # fixme: the site currently treats sets and tuples as lists, so lets just give in to that for now.
            return list(result)
        return result

    def callback(self, new_value: Any):
        """Callback function to handle changes to the interaction value.

        Parameters
        ----------
        new_value: Any
            The new value of the interaction.
        """
        return

    def transform_check(self, new_value: Any) -> Any:
        """Transform and check a new value before setting it.

        This is called before any callback functions are invoked.

        By default, this will replace any None values with a set default value.

        Parameters
        ----------
        new_value: Any
            The new value to transform and check.

        Returns
        -------
        Any: The transformed value, or the default value if new_value is None.
        """
        if new_value is None and self._default_value is not None:
            return self._default_value
        else:
            return new_value

    def _handle_new_value_common(self, new_value: Any):
        try:
            new_value = self.transform_check(new_value)
        except Exception as e:
            log.error(f"Error transforming value for {self.name}: {e}")
            return

        log.debug(f"updating new value: {self.name} {new_value}")
        self.current_value = new_value

    def _handle_new_value(self, new_value: Any):
        self._handle_new_value_common(new_value)
        try:
            self.callback(new_value)
        except Exception as e:
            log.error(f"Error in callback for {self.name}: {e}")

    async def _handle_new_value_async(self, new_value: Any):
        self._handle_new_value_common(new_value)
        await call_maybe_async(self.callback, new_value)
        # try:
        #     self.callback(new_value)
        # except Exception as e:
        #     log.error(f"Error in callback for {self.name}: {e}")

    def coerce(self, value: Any, critical: bool = False) -> None:
        """Coerce the interaction to a new value.

        This will update the current value on the site.

        The callback will be invoked once the site has set the value.

        Parameters
        ----------
        value: Any
            The new value to set for the interaction.
        critical: bool
            If True, this interaction is considered critical and will mark the manager as having a pending critical interaction.
            This is used to ensure that critical interactions are processed immediately and logged on the site.

        Returns
        -------
        None
        """
        if critical and self._manager and value != self.current_value:
            self._manager._has_critical_interaction_pending = True

        if self._manager is not None and self._current_value != value:
            # we need a way to keep track of which interactions our application has "changed"
            # so we don't override ui_cmds that other apps set. ui_cmds ideally should be namespaced
            # so this isn't a problem.
            self._manager._changed_interactions.add(self.name)

        self.current_value = value

    def to_dict(self):
        res = super().to_dict()
        if self._current_value is not NotSet:
            res["currentValue"] = self._json_safe_current_value()
        if self.show_activity is not None:
            res["showActivity"] = self.show_activity
        return res


class Action(Interaction):
    """Represents a UI action (button).

    Parameters
    ----------
    name: str
        The name of the action, used to identify it in the UI.
    display_name: str
        The display name of the action, shown in the UI.
    colour: Colour
        The colour of the action button. Defaults to Colour.blue.
    requires_confirm: bool
        Whether the action requires confirmation before execution on the site. Defaults to True.
    """

    type = "uiAction"

    def __init__(
        self,
        name: str,
        display_name: str,
        colour: Colour = Colour.blue,
        requires_confirm: bool = True,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)
        self.colour = colour
        self.requires_confirm = requires_confirm

    def to_dict(self):
        result = super().to_dict()
        result["colour"] = str(self.colour)
        result["requiresConfirm"] = self.requires_confirm
        return result


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
        return result


class HiddenValue(Interaction):
    type = "uiHiddenValue"

    def __init__(self, name, **kwargs):
        super().__init__(name, display_name=None, **kwargs)

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
        }


class SlimCommand(Interaction):
    """Base class for UI commands."""

    type = "uiStateCommand"


class StateCommand(SlimCommand):
    """Represents a state command in the UI (ie. a dropdown that the user can select a state)

    Parameters
    ----------
    name: str
        The name of the state command, used to identify it in the UI.
    display_name: str, optional
        The display name of the state command, shown in the UI.
    user_options: list[Option]
        A list of options that the user can select from. Each option is an instance of the Option class.
        If not provided, an empty list will be created.
    """

    type = "uiStateCommand"

    def __init__(
        self,
        name: str,
        display_name: str = None,
        user_options: list[Option] = None,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)

        # A list of doover_ui_element's
        self.user_options = []
        self.add_user_options(*user_options)

    def to_dict(self):
        result = super().to_dict()
        result["userOptions"] = {o.name: o.to_dict() for o in self.user_options}
        return result

    def add_user_options(self, *option: Option):
        """Add user options to the state command.

        Parameters
        ----------
        *option: Option
            One or more Option instances to add to the state command.
        """
        for o in option:
            # still support legacy dict passing of option values.
            if isinstance(o, Option):
                self.user_options.append(o)
            elif isinstance(o, dict):
                self.user_options.append(Option.from_dict(o))

    add_user_option = add_user_options


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

    def __init__(
        self,
        name: str,
        display_name: str = None,
        min_val: int = 0,
        max_val: int = 100,
        step_size: float = 0.1,
        dual_slider: bool = True,
        inverted: bool = True,
        icon: Optional[str] = None,
        colours: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.step_size = step_size
        self.dual_slider = dual_slider
        self.inverted = inverted
        self.icon = icon
        self.colours = colours

    def to_dict(self):
        result = super().to_dict()
        result["min"] = self.min_val
        result["max"] = self.max_val
        result["stepSize"] = self.step_size
        result["dualSlider"] = self.dual_slider
        result["isInverted"] = self.inverted

        # don't pass values if they have a default value of None since we treat this as "remove element" in a diff.
        if self.icon:
            result["icon"] = self.icon
        if self.colours:
            result["colours"] = self.colours

        return result


def action(
    name: str,
    display_name: str = None,
    colour: Colour = Colour.blue,
    requires_confirm: bool = True,
    **kwargs,
):
    """Decorator to mark a function as a UI action.

    This decorator will add the function to the UI as an action button.

    Parameters
    ----------
    name: str
        The name of the action, used to identify it in the UI.
    display_name: str, optional
        The display name of the action, shown in the UI.
    colour: Colour, optional
        The colour of the action button. Defaults to Colour.blue.
    requires_confirm: bool, optional
        Whether the action requires confirmation before execution on the site. Defaults to True.
    """

    def decorator(func):
        func._ui_type = Action
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "colour": colour,
            "requires_confirm": requires_confirm,
            **kwargs,
        }
        return func

    return decorator


def warning_indicator(
    name: str, display_name: str = None, can_cancel: bool = True, **kwargs
):
    """Decorator to mark a function as a UI warning indicator.

    Parameters
    ----------
    name: str
        The name of the warning indicator, used to identify it in the UI.
    display_name: str, optional
        The display name of the warning indicator, shown in the UI.
    can_cancel: bool
        Whether the warning can be cancelled by the user. Defaults to True.
    """

    def decorator(func):
        func._ui_type = WarningIndicator
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "can_cancel": can_cancel,
            **kwargs,
        }
        return func

    return decorator


def state_command(
    name: str, display_name: str = None, user_options: list[Option] = None, **kwargs
):
    """Decorator to mark a function as a UI state command.

    The decorated function will be added to the UI as a state command,
    which allows the user to select a state from a dropdown menu.
    The associated function to this decorator will be called whenever the state command is selected
    and should take one parameter, `new_value`, which is the new value that has been set for this state command.

    Examples
    --------

    A basic state command ::

        @ui.state_command(
            "my_state_command",
            display_name="My State Command",
            user_options=[
                ui.Option("option1", "Option 1"),
                ui.Option("option2", "Option 2")
            ]
        )
        def my_state_command(self, new_value):
            # This function will be called whenever the state command is selected.
            pass


    Parameters
    ----------
    name: str
        The name of the state command, used to identify it in the UI.
    display_name: str, optional
        The display name of the state command, shown in the UI.
    user_options: list[Option], optional
        A list of options that the user can select from. Each option is an instance of the Option class.
        If not provided, an empty list will be created.
    """

    def decorator(func):
        func._ui_type = StateCommand
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "user_options": user_options,
            **kwargs,
        }
        return func

    return decorator


def hidden_value(name: str, **kwargs):
    """Decorator to mark a function as a UI hidden value.

    This decorator will add the function to the UI as a hidden value, which can be used to store
    values that should not be displayed to the user but can be accessed programmatically.

    The associated function to this decorator will be called whenever this value changes
    and should take one parameter, `new_value`,
    which is the new value that has been set for this hidden value.

    Examples
    --------

    A basic hidden value ::

        @ui.hidden_value("my_hidden_value")
        def my_hidden_value(self, new_value):
            # This function will be called whenever the hidden value changes.
            pass


    Parameters
    ----------
    name: str
        The name of the hidden value.
    """

    def decorator(func):
        func._ui_type = HiddenValue
        func._ui_kwargs = {
            "name": name,
            **kwargs,
        }
        return func

    return decorator


def slider(
    name: str,
    display_name: str = None,
    min_val: int = 0,
    max_val: int = 100,
    step_size: float = 0.1,
    dual_slider: bool = True,
    inverted: bool = True,
    icon: Optional[str] = None,
    **kwargs,
):
    """Decorator to mark a function as a UI slider.

    This decorator will add the function to the UI as a slider element.

    The associated function to this decorator will be called whenever the slider value changes
    and should take one parameter, `new_value`, which is the new value that has been set for this slider.
    Examples
    --------

    A basic slider from 0-100 with a step size of 5 ::

        @ui.slider(
            "my_slider",
            display_name="My Slider",
            min_val=0,
            max_val=100,
            step_size=5
        )
        def my_slider(self, new_value):
            # This function will be called whenever the slider value changes.
            pass

    """

    def decorator(func):
        func._ui_type = Slider
        func._ui_kwargs = {
            "name": name,
            "display_name": display_name,
            "min_val": min_val,
            "max_val": max_val,
            "step_size": step_size,
            "dual_slider": dual_slider,
            "inverted": inverted,
            "icon": icon,
            **kwargs,
        }
        return func

    return decorator


def callback(pattern: str | re.Pattern[str]):
    """Decorator to mark a function as a UI callback.

    This accepts either a string or a compiled regex expression to match against the UI element name.

    Examples
    --------

    A callback for a single UI element ::

        @ui.callback("di_fetch")
        def fetch_di(self, element, new_value):
            pass


    A generic callback to match multiple elements ::

        @ui.callback(re.compile(r"do_\d+_toggle"))
        def do_toggle(self, element, new_value):
            pass

    Parameters
    ----------
    pattern: str | re.Pattern[str]
        A string or compiled regex pattern that matches the name of the UI element this callback is for.
    """

    def decorator(func):
        func._is_ui_callback = True
        if isinstance(pattern, str):
            func._ui_callback_pattern = re.compile(pattern)
        else:
            func._ui_callback_pattern = re.compile(pattern)
        return func

    return decorator
