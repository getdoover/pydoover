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


@dataclass
class IoChannel:
    """One IO channel in the flat namespace shared with fetch_di/set_do/etc.

    Attributes
    ----------
    channel : int
        Global flat channel number — the number you pass to fetch_di, set_do, etc.
    device_channel : int
        Channel number on the owning device (e.g. DI 0 of slave 2).
    io_type : str
        One of "DI", "DO", "AI", "AO".
    kind : str | None
        Analog channels only: e.g. "voltage", "current", "temperature".
    units : str | None
        Display units, e.g. "V", "mA", "degC".
    supports_events : bool
        Whether DI edge events (fetch_di_events) work on this channel.
    supports_pulse_counter : bool
        Whether pulse counters work on this channel.
    supports_di_config : bool
        Whether get/set DI config (PNP/NPN, debounce, wake-on-event) works.
    """

    channel: int
    device_channel: int
    io_type: str
    kind: str | None = None
    units: str | None = None
    supports_events: bool = False
    supports_pulse_counter: bool = False
    supports_di_config: bool = False

    @classmethod
    def from_response(cls, response) -> "IoChannel":
        """Build an IoChannel from an IoChannelDetail proto message."""
        return cls(
            channel=response.channel,
            device_channel=response.device_channel,
            io_type=response.io_type,
            kind=response.kind if response.HasField("kind") else None,
            units=response.units if response.HasField("units") else None,
            supports_events=response.supports_events,
            supports_pulse_counter=response.supports_pulse_counter,
            supports_di_config=response.supports_di_config,
        )


@dataclass
class IoDevice:
    """The master or one slave, with the channels it contributes to the flat namespace.

    Attributes
    ----------
    name : str
        "master", or the slave's configured name.
    type : str
        Driver type, e.g. "doovit", "moxa1242", "point_io". Empty string when
        synthesized from an old server that only supports fetch_io_table.
    index : int
        Slave index; 0 for the master (check is_master, not index).
    is_master : bool
        Whether this device is the master platform.
    online : bool
        Best-effort connectivity to the device.
    channels : list[IoChannel]
        The channels this device contributes, in flat-channel order.
    """

    name: str
    type: str
    index: int
    is_master: bool
    online: bool
    channels: "list[IoChannel]"

    def channels_of(self, io_type: str) -> "list[IoChannel]":
        """Return this device's channels of one IO type ("DI", "DO", "AI", "AO")."""
        return [c for c in self.channels if c.io_type == io_type]

    @classmethod
    def from_response(cls, response) -> "IoDevice":
        """Build an IoDevice from an IoDeviceDetail proto message."""
        return cls(
            name=response.name,
            type=response.type,
            index=response.index,
            is_master=response.is_master,
            online=response.online,
            channels=[IoChannel.from_response(c) for c in response.channels],
        )


@dataclass
class IoDetails:
    """The full IO layout of a device: master plus any configured slaves.

    Attributes
    ----------
    devices : list[IoDevice]
        Master first, then slaves in index order — matching the flat channel
        numbering the platform interface assigns.
    """

    devices: "list[IoDevice]"

    @property
    def master(self) -> "IoDevice | None":
        """The master device, or None if the layout has no marked master."""
        for device in self.devices:
            if device.is_master:
                return device
        return None

    def channels(self, io_type: str) -> "list[IoChannel]":
        """All channels of one IO type across every device, in flat-channel order."""
        found = [c for d in self.devices for c in d.channels if c.io_type == io_type]
        return sorted(found, key=lambda c: c.channel)

    @classmethod
    def from_response(cls, response) -> "IoDetails | None":
        """Build an IoDetails from a getIoDetailsResponse proto message."""
        if response is None:
            return None
        return cls(devices=[IoDevice.from_response(d) for d in response.devices])

    @classmethod
    def from_io_table(cls, io_table: dict) -> "IoDetails":
        """Synthesize an IoDetails from a fetch_io_table dict.

        Fallback for servers that predate getIoDetails: the table only lists
        flat channel numbers per IO type, so everything lands on one anonymous
        master device with no per-channel metadata or capability flags.
        """
        channels = [
            IoChannel(channel=int(ch), device_channel=int(ch), io_type=io_type)
            for io_type, table_channels in io_table.items()
            for ch in table_channels
        ]
        device = IoDevice(
            name="master",
            type="",
            index=0,
            is_master=True,
            online=True,
            channels=channels,
        )
        return cls(devices=[device])


@dataclass
class DIReading:
    """One digital input's level, plus its hardware pulse counters if it has any.

    Returned by :meth:`PlatformInterface.fetch_di_readings`.

    Attributes
    ----------
    pin : int
        The digital input pin this reading is for.
    value : bool
        Pin level: True is high (1), False is low (0).
    pulse_count : int | None
        Total pulses counted in hardware since the *device* started counting -
        not since this app connected, so it is unaffected by the app
        restarting, and on some platforms it wraps rather than resetting. How
        to handle that is the app's call.

        ``None`` means this pin has no hardware counter. ``0`` means it has one
        and nothing has been counted yet. The two are not the same, so test for
        ``None`` rather than falsiness.
    pulse_rate_hz : float | None
        Pulse frequency in Hz, where the hardware measures it. ``None`` means
        this platform does not measure rate on this pin - a driver with only a
        totaliser leaves it unset rather than differencing counts, because the
        caller knows its own sampling interval and the driver does not. Derive
        the rate from successive ``pulse_count`` readings instead.
    """

    pin: int
    value: bool
    pulse_count: int | None = None
    pulse_rate_hz: float | None = None
