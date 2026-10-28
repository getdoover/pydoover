from dataclasses import dataclass
from enum import IntEnum


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
        Whether the per-pulse edge *stream* (get_new_pulse_counter) works on this
        channel. Needs an edge source on the platform.
    supports_di_config : bool
        Whether get/set DI config (PNP/NPN, debounce, wake-on-event) works.
    supports_pulse_count : bool
        Whether this channel has a hardware pulse totaliser, read through
        :meth:`PlatformInterface.fetch_di_readings`. Distinct from
        ``supports_pulse_counter``: that promises per-pulse *timing*, while this
        is a number that can simply be read. A platform can have either, both or
        neither — an ELPRO Quantum counts on DIO1-4 and can time nothing.
    supports_pulse_rate : bool
        Whether the hardware measures pulse frequency on this channel.
    """

    channel: int
    device_channel: int
    io_type: str
    kind: str | None = None
    units: str | None = None
    supports_events: bool = False
    supports_pulse_counter: bool = False
    supports_di_config: bool = False
    supports_pulse_count: bool = False
    supports_pulse_rate: bool = False

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
            # getattr, not attribute access: a platform interface built against
            # stubs that predate these fields sends a message without them, and
            # discovery must degrade to "not advertised" rather than raise.
            supports_pulse_count=getattr(response, "supports_pulse_count", False),
            supports_pulse_rate=getattr(response, "supports_pulse_rate", False),
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


class ChannelQuality(IntEnum):
    """Why a channel in a :class:`ProcessImage` is not plain good.

    A value the platform interface sends that this pydoover does not know is
    read as :attr:`FAULT`, so an old client never mistakes a new kind of
    problem for a good reading.
    """

    GOOD = 0
    #: The device's data is older than its staleness limit.
    STALE = 1
    #: The device has not answered yet, or has dropped off.
    OFFLINE = 2
    #: The device answered but gave no value for this channel.
    NO_VALUE = 3
    #: The hardware reports a fault on this channel.
    FAULT = 4
    #: An analog input below its valid range (e.g. < 3.6 mA, a wire break).
    UNDER_RANGE = 5
    #: An analog input above its valid range (e.g. > 21 mA).
    OVER_RANGE = 6
    #: An input or output tripped on overcurrent.
    OVERCURRENT = 7

    @classmethod
    def _missing_(cls, value):
        return cls.FAULT


@dataclass
class ChannelStatus:
    """A channel that is not plain good, and why.

    Attributes
    ----------
    quality : ChannelQuality
    detail : str | None
        Human-readable context from the platform interface, if any.
    """

    quality: ChannelQuality
    detail: str | None = None


@dataclass
class DeviceImageStatus:
    """One device's part of a :class:`ProcessImage`.

    Attributes
    ----------
    index : int
        ``-1`` for the master, else the slave's configured index.
    name : str
        The device's name, as the platform interface reports it.
    online : bool
        Whether the device's data is fresh enough to serve.
    age_ms : int | None
        Age of the device's latest successful poll when the image was built,
        or ``None`` before the first poll.
    last_error : str | None
        The latest poll error, if the device is failing.
    timestamp_ms : int | None
        Wall-clock time of that poll, Unix milliseconds. Can be wrong on a
        device whose clock has not synced; ``age_ms`` is the reliable measure.
    """

    index: int
    name: str
    online: bool
    age_ms: int | None = None
    last_error: str | None = None
    timestamp_ms: int | None = None


@dataclass
class ProcessImage:
    """Every channel of every device, as of the platform interface's last poll.

    Returned by :meth:`PlatformInterface.fetch_image` and passed to
    :meth:`PlatformInterface.subscribe_image` callbacks. Lists are indexed by
    flat channel number, the same numbering as
    :meth:`PlatformInterface.fetch_io_table`, and indices never shift.

    A channel whose quality is not :attr:`ChannelQuality.GOOD` appears in the
    matching ``*_status`` dict. Check :meth:`valid` (or :meth:`quality`) before
    trusting a value: an offline channel reads ``False`` / ``0.0``, and an
    out-of-range analog input keeps the reading it has.

    Attributes
    ----------
    di, do : list[bool]
    ai, ao : list[float]
    di_status, do_status, ai_status, ao_status : dict[int, ChannelStatus]
        Only channels that are not good.
    di_count : dict[int, int]
        Pulse totals for the DI channels that have a counter.
    di_rate_hz : dict[int, float]
        Pulse rates for the DI channels whose hardware measures one.
    devices : list[DeviceImageStatus]
        Master first, then slaves in configured order.
    sequence : int
        Increases when any value or channel status changes, and only then.
    """

    di: list[bool]
    do: list[bool]
    ai: list[float]
    ao: list[float]
    di_status: dict[int, ChannelStatus]
    do_status: dict[int, ChannelStatus]
    ai_status: dict[int, ChannelStatus]
    ao_status: dict[int, ChannelStatus]
    di_count: dict[int, int]
    di_rate_hz: dict[int, float]
    devices: list[DeviceImageStatus]
    sequence: int

    def quality(self, io_type: str, channel: int) -> ChannelQuality:
        """The quality of ``channel`` of ``io_type`` ("DI", "DO", "AI" or "AO")."""
        statuses = {
            "DI": self.di_status,
            "DO": self.do_status,
            "AI": self.ai_status,
            "AO": self.ao_status,
        }[io_type.upper()]
        status = statuses.get(channel)
        return status.quality if status else ChannelQuality.GOOD

    def valid(self, io_type: str, channel: int) -> bool:
        """Whether ``channel`` of ``io_type`` has a good value."""
        return self.quality(io_type, channel) is ChannelQuality.GOOD

    @classmethod
    def from_response(cls, response) -> "ProcessImage":
        """Build a ProcessImage from a getImageResponse proto message."""

        def statuses(field):
            return {
                channel: ChannelStatus(
                    quality=ChannelQuality(status.quality),
                    detail=status.detail if status.HasField("detail") else None,
                )
                for channel, status in field.items()
            }

        def opt(message, field):
            return getattr(message, field) if message.HasField(field) else None

        return cls(
            di=list(response.di),
            do=list(response.do),
            ai=list(response.ai),
            ao=list(response.ao),
            di_status=statuses(response.di_status),
            do_status=statuses(response.do_status),
            ai_status=statuses(response.ai_status),
            ao_status=statuses(response.ao_status),
            di_count=dict(response.di_count),
            di_rate_hz=dict(response.di_rate_hz),
            devices=[
                DeviceImageStatus(
                    index=d.index,
                    name=d.name,
                    online=d.online,
                    age_ms=opt(d, "age_ms"),
                    last_error=opt(d, "last_error"),
                    timestamp_ms=opt(d, "timestamp_ms"),
                )
                for d in response.devices
            ],
            sequence=response.sequence,
        )
