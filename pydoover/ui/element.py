import enum
import logging
import re

from datetime import datetime
from typing import Optional, Any

from .misc import NotSet, Series
from .declarative import normalize_ui_value
from ..utils.utils import sanitize_display_name


VALID_NAME_RE = re.compile(r"^[0-9a-zA-Z_]+$")

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
    __global_position_counter = 50

    def __init__(
        self,
        display_name: str,
        is_available=NotSet,
        help_str: str = NotSet,
        verbose_str: str = NotSet,
        show_activity: bool = True,
        form=NotSet,
        graphic: str = NotSet,
        layout: str = NotSet,
        component_url: str = NotSet,
        position: int = NotSet,
        conditions: dict[str] = NotSet,
        hidden: Any = False,
        units: str = NotSet,
        icon: str = NotSet,
        colour: str = NotSet,
        name: str = None,
        **kwargs,
    ):
        self.display_name = display_name
        self.is_available = is_available
        self.help_str = help_str
        self.verbose_str = verbose_str
        self.show_activity = show_activity
        self.form = form
        self.graphic = graphic
        self.layout = layout
        self.component_url = component_url

        Element.__global_position_counter += 1
        if position is NotSet:
            self.position = Element.__global_position_counter
        else:
            self.position = position

        self.conditions = conditions
        self.hidden = hidden
        self.units = units
        self.icon = icon
        self.colour = colour

        self.name = name or sanitize_display_name(display_name)
        if not VALID_NAME_RE.match(self.name):
            raise ValueError(f"Invalid name: {name}. Must be [a-zA-Z0-9_]")

        for k, v in kwargs.items():
            log.debug(f"Setting kwarg {k} to {v}")
            setattr(self, k, v)

        self._retain_fields = []

    def to_dict(self) -> dict[str, Any]:
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
            "units": self.units,
            "icon": self.icon,
            "colour": self.colour,
        }
        # filter out any null values
        return normalize_ui_value(
            {k: v for k, v in to_return.items() if v is not None and v is not NotSet}
        )


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

    # fixme: work out what to do with periodic docker devices / ui...

    type = "uiConnectionInfo"

    def __init__(
        self,
        name: str = "connectionInfo",
        connection_type: ConnectionType = ConnectionType.constant,
        connection_period: int | None = None,
        next_connection: int | None = None,
        offline_after: int | None = None,
        allowed_misses: int | None = None,
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

        return normalize_ui_value(result)


class Multiplot(Element):
    """Represents a MultiPlot UI Element.

    Parameters
    ----------
    display_name: str
        The display name of the multiplot.
    series: list[Series]
        A list of :class:`~pydoover.ui.Series` objects defining the plot series.
    earliest_data_time: datetime, optional
        The earliest time for which data is available in the multiplot.
    title: str, optional
        The title of the multiplot.
    default_zoom: str, optional
        The default zoom level for the multiplot.
    default_range_view: str, optional
        Initial range view for the plot (``"line"``, ``"zone"`` or ``"off"``).
        Only applies when exactly one series defines ranges or thresholds.
    """

    type = "uiMultiPlot"

    def __init__(
        self,
        title: str,
        series: list[Series],
        earliest_data_time: Optional[datetime] = None,
        default_zoom: Optional[str] = None,
        default_range_view: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(title, **kwargs)

        self.series = series
        self.earliest_data_time = earliest_data_time
        self.title = title
        self.default_zoom = default_zoom
        self.default_range_view = default_range_view

    def to_dict(self):
        result = super().to_dict()
        result["series"] = {s.name: s.to_dict() for s in self.series}

        if self.default_zoom is not None:
            result["defaultZoom"] = self.default_zoom
        if self.default_range_view is not None:
            result["defaultRangeView"] = self.default_range_view
        if self.title is not None:
            result["title"] = self.title

        if self.earliest_data_time is not None:
            # fixme: make this a delta - to make it more useful for static ui's
            if isinstance(self.earliest_data_time, datetime):
                result["earliestDataDate"] = int(self.earliest_data_time.timestamp())
            else:
                result["earliestDataDate"] = self.earliest_data_time

        return normalize_ui_value(result)
