import enum
import logging
import re

from datetime import datetime
from typing import Optional, Any

from .misc import NotSet
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
        if position is None:
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
    series: list[str] | dict[str, dict[str, Any]]
        Series configuration for the multiplot. New code should pass a mapping of
        series name to series configuration.
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
        display_name: str,
        series: list[str] | dict[str, dict[str, Any]],
        series_colours: Optional[list[str]] = None,
        series_active: Optional[list[bool]] = None,
        earliest_data_time: Optional[datetime] = None,
        title: Optional[str] = None,
        shared_axis: Optional[list[bool]] = None,
        step_labels: Optional[list[str]] = None,
        step_padding: Optional[list[int]] = None,
        default_zoom: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)

        self._legacy_series_input = isinstance(series, list)
        self.series_colours = series_colours
        self.series_active = series_active
        self.earliest_data_time = earliest_data_time
        self.title = title
        self.shared_axis = shared_axis
        self.step_labels = step_labels
        self.step_padding = step_padding
        self.default_zoom = default_zoom
        self.series = self._normalize_series(series)

        if self._legacy_series_input or any(
            value is not None
            for value in (
                series_colours,
                series_active,
                shared_axis,
                step_labels,
                step_padding,
            )
        ):
            raise RuntimeError(
                "Legacy uiMultiPlot list-based schema is deprecated. "
                "Pass series as a record keyed by series name instead."
            )
            # warnings.warn(
            #     "Legacy uiMultiPlot list-based schema is deprecated. "
            #     "Pass series as a record keyed by series name instead.",
            #     DeprecationWarning,
            #     stacklevel=2,
            # )

    def _normalize_series(self, series: list[str] | dict[str, dict[str, Any]]):
        return {
            name: self._normalize_series_entry(name, config, index)
            for index, (name, config) in enumerate(series.items())
        }

    def _normalize_series_entry(
        self, name: str, config: dict[str, Any] | str | None, index: int
    ) -> dict[str, Any]:
        if isinstance(config, str):
            result: dict[str, Any] = {"displayString": config}
        else:
            result = dict(config or {})

        result.setdefault("name", name)
        result.setdefault("displayString", result["name"])
        result.setdefault("dataType", "unknown")

        if "shared_axis" in result and "sharedAxis" not in result:
            result["sharedAxis"] = result.pop("shared_axis")
        if "step_labels" in result and "stepLabels" not in result:
            result["stepLabels"] = result.pop("step_labels")

        if self.series_colours is not None and "colour" not in result:
            colour = self._get_legacy_index_value(self.series_colours, index)
            if colour is not None:
                result["colour"] = colour
        if self.series_active is not None and "active" not in result:
            active = self._get_legacy_index_value(self.series_active, index)
            if active is not None:
                result["active"] = active
        if self.shared_axis is not None and "sharedAxis" not in result:
            shared_axis = self._get_legacy_index_value(self.shared_axis, index)
            if shared_axis is not None:
                result["sharedAxis"] = shared_axis
        if self.step_labels is not None and "stepLabels" not in result:
            result["stepLabels"] = self.step_labels

        return normalize_ui_value(result)

    @staticmethod
    def _get_legacy_index_value(values: list[Any], index: int):
        if index >= len(values):
            return None
        return values[index]

    def to_dict(self):
        result = super().to_dict()
        result["series"] = self.series

        if self.series_active is not None and not self._legacy_series_input:
            result["activeSeries"] = self.series_active
        if self.step_padding is not None:
            result["stepPadding"] = self.step_padding
        if self.default_zoom is not None:
            result["defaultZoom"] = self.default_zoom
        if self.title is not None:
            result["title"] = self.title

        if self.earliest_data_time is not None:
            # fixme: make this a delta - to make it more useful for static ui's
            if isinstance(self.earliest_data_time, datetime):
                result["earliestDataDate"] = int(self.earliest_data_time.timestamp())
            else:
                result["earliestDataDate"] = self.earliest_data_time

        return normalize_ui_value(result)
