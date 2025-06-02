import enum
import logging

from datetime import datetime
from typing import Optional, Any

from .misc import Colour


class NotSet:
    pass


log = logging.getLogger(__name__)


class Element:
    """Base class for UI elements.

    Attributes
    ----------
    name: str
        The name of the UI element.
    display_name: str, optional
        The display name of the UI element.
    is_available: bool, optional
        Indicates if the UI element is available.
    help_str: str, optional
        A help string for the UI element.
    verbose_str: str, optional
        A verbose string for the UI element.
    show_activity: bool
        Whether to show activity for the UI element.
    form: str, optional
        The form associated with the UI element.
    graphic: str, optional
        The graphic associated with the UI element.
    layout: str, optional
        The layout associated with the UI element.
    component_url: str, optional
        The URL for a remote component associated with the UI element.
    position: int, optional
        The position of the UI element in the UI.
    conditions: dict[str, Any], optional
        Conditions under which the UI element is displayed.
    hidden: bool
        Whether the UI element is hidden.
    """

    type = "uiElement"

    def __init__(
        self,
        name: str,
        optional,
        display_name: str | None = None,
        is_available: bool = None,  # not sure of type
        help_str: str = None,
        verbose_str: str = None,
        show_activity: bool = True,
        form: str = None,
        graphic: str = None,  # not sure of type
        layout: str = None,  # not sure of type
        component_url: str = None,  # not sure of type
        position: Optional[int] = None,  # 100,
        conditions: Optional[dict] = None,
        hidden: bool = False,
        **kwargs,
    ):
        self.name = name
        self.display_name = display_name or kwargs.get(
            "display_str", None
        )  # backwards compatibility
        self.is_available = is_available
        self.help_str = help_str
        self.verbose_str = verbose_str
        self.show_activity = show_activity
        self.form = form
        self.graphic = graphic
        self.layout = layout
        self.component_url = component_url
        self.position = position
        self.conditions = conditions
        self.hidden = hidden

        for k, v in kwargs.items():
            log.debug(f"Setting kwarg {k} to {v}")
            setattr(self, k, v)

        self._retain_fields = []

    def to_dict(self):
        """Convert the element to a dictionary representation.

        Returns
        -------
        dict[str, Any]
            A dictionary representation of the UI element. This is used to serialize the element for the site API.
        """
        to_return = {
            "name": self.name,
            "type": self.type,
            "displayString": self.display_name,
            "isAvailable": self.is_available,
            "helpString": self.help_str,
            "verboseString": self.verbose_str,
            "showActivity": self.show_activity,
            "form": self.form,
            "graphic": self.graphic,
            "layout": self.layout,
            "componentUrl": self.component_url,
            "position": self.position,
            "conditions": self.conditions,
            "hidden": self.hidden,
        }
        # filter out any null values
        return {k: v for k, v in to_return.items() if v is not None}

    def get_diff(
        self,
        other: dict[str, Any],
        remove: bool = True,
        retain_fields: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Get the difference between this element and another dictionary representation of an element.

        Parameters
        ----------
        other: dict[str, Any]
            The other element to compare against.
        remove: bool
            If True, fields that are not present in this element but are in the other will be set to None.
        retain_fields: list[str], optional
            A list of fields to retain in the difference, even if they are not different.

        Returns
        -------
        dict[str, Any], optional
            A dictionary containing the differences between this element and the other. If there are no differences, returns None.
        """

        this = self.to_dict()

        retain_fields = retain_fields or []
        to_retain = list(set(retain_fields) | set(self._retain_fields))
        # if this == other:
        #     return None

        result = {k: v for k, v in this.items() if other.get(k) != v or k in to_retain}
        if remove:
            result.update(
                **{k: None for k in other if k not in this and k not in to_retain}
            )  # to_remove
        if len(result) == 0:
            return None

        return result

    ## A stub for the method that will be called when the UI state is updated.
    # The element can choose to update its internal state based on the previous state and the new state.
    def recv_ui_state_update(self, state: dict[str, Any]) -> None:
        pass


class ConnectionType(enum.Enum):
    constant = "constant"
    periodic = "periodic"
    other = "other"


class ConnectionInfo(Element):
    """Connection Info

    Parameters
    ----------
    name: str
    connection_type: ConnectionType

    connection_period: int
        The expected time between connection events (seconds) - only applicable for "periodic"
    next_connection: int
        Expected time of next connection (seconds after shutdown)
    offline_after: int
        Show as offline if disconnected for more than x secs

    """

    type = "uiConnectionInfo"

    def __init__(
        self,
        name: str = "connectionInfo",
        connection_type: ConnectionType = ConnectionType.constant,
        connection_period: int = None,
        next_connection: int = None,
        offline_after: int = None,
        allowed_misses: int = None,
        **kwargs,
    ):
        super().__init__(name, None, **kwargs)
        self.name = name
        self.connection_type = connection_type
        self.connection_period = connection_period
        self.next_connection = next_connection
        self.offline_after = offline_after
        self.allowed_misses = allowed_misses

        if self.connection_type is not ConnectionType.periodic and (
            self.connection_period is not None
            or self.next_connection is not None
            or self.allowed_misses is not None
        ):
            raise RuntimeError(
                "connection_type must be periodic to set connection_period, next_connection or offline_after"
            )

    def to_dict(self):
        result = {
            "name": self.name,
            "type": self.type,
            "connectionType": self.connection_type.value,
        }

        if self.connection_period is not None:
            result["connectionPeriod"] = self.connection_period
        if self.next_connection is not None:
            result["nextConnection"] = self.next_connection
        if self.offline_after is not None:
            result["offlineAfter"] = self.offline_after
        if self.allowed_misses is not None:
            result["allowedMisses"] = self.allowed_misses

        return result


class AlertStream(Element):
    """Represents an Alert Stream UI Element

    Parameters
    ----------
    name: str
        The name of the alert stream.
    display_name: str, optional
        The display name of the alert stream.
    """

    type = "uiAlertStream"

    def __init__(self, name, display_name: str = None, **kwargs):
        super().__init__(name, display_name, is_available=None, help_str=None, **kwargs)


class Multiplot(Element):
    """Represents a MultiPlot UI Element.

    Parameters
    ----------
    name: str
        The name of the multiplot.
    display_name: str
        The display name of the multiplot.
    series: list[str]
        A list of series names to be displayed in the multiplot.
    series_colours: list[Colour], optional
        A list of colours for each series in the multiplot.
    series_active: list[bool], optional
        A list indicating whether each series is active or not.
    earliest_data_time: datetime, optional
        The earliest time for which data is available in the multiplot.
    title: str, optional
        The title of the multiplot.
    """

    type = "uiMultiPlot"

    def __init__(
        self,
        name: str,
        display_name: str,
        series: list[str],
        series_colours: Optional[list[Colour]] = None,
        series_active: Optional[list[bool]] = None,
        earliest_data_time: Optional[datetime] = None,
        title: Optional[str] = None,
        shared_axis: Optional[list[bool]] = None,
        step_labels: Optional[list[str]] = None,
        step_padding: Optional[list[int]] = None,
        default_zoom: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)

        self.series = series
        self.series_colours = series_colours
        self.series_active = series_active
        self.earliest_data_time = earliest_data_time
        self.title = title
        self.shared_axis = shared_axis
        self.step_labels = step_labels
        self.step_padding = step_padding
        self.default_zoom = default_zoom

    def to_dict(self):
        result = super().to_dict()
        result["series"] = self.series
        result["colours"] = self.series_colours

        if self.series_active is not None:
            result["activeSeries"] = self.series_active
        if self.shared_axis is not None:
            result["sharedAxis"] = self.shared_axis
        if self.step_labels is not None:
            result["stepLabels"] = self.step_labels
        if self.step_padding is not None:
            result["stepPadding"] = self.step_padding
        if self.default_zoom is not None:
            result["defaultZoom"] = self.default_zoom
        if self.title is not None:
            result["title"] = self.title

        if self.earliest_data_time is not None:
            if isinstance(self.earliest_data_time, datetime):
                result["earliestDataDate"] = int(self.earliest_data_time.timestamp())
            else:
                result["earliestDataDate"] = self.earliest_data_time

        return result


class RemoteComponent(Element):
    """Represents a remote component in the UI.

    Parameters
    ----------
    name: str
        The name of the remote component.
    display_name: str
        The display name of the remote component.
    component_url: str
        The URL of the remote component.
    """

    type = "uiRemoteComponent"

    def __init__(self, name: str, display_name: str, component_url: str, **kwargs):
        super().__init__(name, display_name, component_url=component_url)
        self.kwargs = kwargs

    def to_dict(self):
        res = super().to_dict()
        res.update(self.kwargs)
        return res
