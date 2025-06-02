class Location:
    """Dataclass for a Location object as returned by platform interface.

    Attributes
    ----------
    latitude : float
        Latitude in degrees.
    longitude : float
        Longitude in degrees.
    altitude_m: float
        Altitude in meters above sea level.
    accuracy_m: float
        Accuracy of the location in meters.
    speed_mps: float
        Speed in meters per second.
    heading_deg: float
        Heading in degrees (0-360).
    sat_count: int
        Number of satellites used to determine the location.
    timestamp: str
        Timestamp of the location in ISO 8601 format (e.g., "2023-10-01T12:00:00Z").
    """

    latitude: float
    longitude: float
    altitude_m: float
    accuracy_m: float
    speed_mps: float
    heading_deg: float
    sat_count: int
    timestamp: str


class Event:
    """Dataclass for an Event object as returned by platform interface.

    Attributes
    ----------
    event_id : int
        Unique identifier for the event.
    event : str
        The type of event, e.g., "DI_R" for rising edge, "DI_F" for falling edge.
    pin : int
        The digital input pin number the event occurred on.
    value : str
        The value of the digital input pin at the time of the event (e.g., "1" for high, "0" for low).
    time : int
        The timestamp of the event in milliseconds since epoch.
    cm4_online : bool | None
        Whether the CM4 is online at the time of the event. This can be None if not applicable.
    """

    event_id: int
    event: str
    pin: int
    value: str
    time: int
    cm4_online: bool | None
