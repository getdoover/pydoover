from dataclasses import dataclass


@dataclass
class Location:
    """Dataclass for a Location object as returned by platform interface.

    Attributes
    ----------
    latitude : float
        Latitude in degrees.
    longitude : float
        Longitude in degrees.
    altitude_m: float | None
        Altitude in meters above sea level.
    accuracy_m: float | None
        Accuracy of the location in meters.
    speed_mps: float | None
        Speed in meters per second.
    heading_deg: float | None
        Heading in degrees (0-360).
    sat_count: int | None
        Number of satellites used to determine the location.
    timestamp: str | None
        Timestamp of the location in ISO 8601 format (e.g., "2023-10-01T12:00:00Z").
    """

    latitude: float
    longitude: float
    altitude_m: float | None = None
    accuracy_m: float | None = None
    speed_mps: float | None = None
    heading_deg: float | None = None
    sat_count: int | None = None
    timestamp: str | None = None

    @classmethod
    def from_response(cls, response) -> "Location | None":
        """Build a Location from a getLocationResponse proto message.

        The response carries the fix as flat optional fields; a missing
        latitude or longitude means the device has no fix, which maps to None
        rather than a Location at proto-default (0, 0).
        """
        if response is None:
            return None

        def get(field):
            return getattr(response, field) if response.HasField(field) else None

        latitude, longitude = get("latitude"), get("longitude")
        if latitude is None or longitude is None:
            return None

        return cls(
            latitude=latitude,
            longitude=longitude,
            altitude_m=get("altitude_m"),
            accuracy_m=get("accuracy_m"),
            speed_mps=get("speed_mps"),
            heading_deg=get("heading_deg"),
            sat_count=get("sat_count"),
            timestamp=get("timestamp"),
        )


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
