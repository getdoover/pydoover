from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ResponseHeader(_message.Message):
    __slots__ = ("success", "response_code", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    response_code: int
    message: str
    def __init__(self, success: bool = ..., response_code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class TestCommsRequest(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class TestCommsResponse(_message.Message):
    __slots__ = ("response_header", "response")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    response: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., response: _Optional[str] = ...) -> None: ...

class getDIRequest(_message.Message):
    __slots__ = ("di",)
    DI_FIELD_NUMBER: _ClassVar[int]
    di: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, di: _Optional[_Iterable[int]] = ...) -> None: ...

class getDIResponse(_message.Message):
    __slots__ = ("response_header", "di")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    DI_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    di: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., di: _Optional[_Iterable[bool]] = ...) -> None: ...

class getAIRequest(_message.Message):
    __slots__ = ("ai",)
    AI_FIELD_NUMBER: _ClassVar[int]
    ai: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, ai: _Optional[_Iterable[int]] = ...) -> None: ...

class getAIResponse(_message.Message):
    __slots__ = ("response_header", "ai")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    AI_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    ai: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., ai: _Optional[_Iterable[float]] = ...) -> None: ...

class pulseCounterRequest(_message.Message):
    __slots__ = ("di", "edge")
    DI_FIELD_NUMBER: _ClassVar[int]
    EDGE_FIELD_NUMBER: _ClassVar[int]
    di: int
    edge: str
    def __init__(self, di: _Optional[int] = ..., edge: _Optional[str] = ...) -> None: ...

class pulseCounterResponse(_message.Message):
    __slots__ = ("response_header", "di", "value", "dt_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    DI_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    DT_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    di: int
    value: bool
    dt_secs: float
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., di: _Optional[int] = ..., value: bool = ..., dt_secs: _Optional[float] = ...) -> None: ...

class getDORequest(_message.Message):
    __slots__ = ("do",)
    DO_FIELD_NUMBER: _ClassVar[int]
    do: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, do: _Optional[_Iterable[int]] = ...) -> None: ...

class getDOResponse(_message.Message):
    __slots__ = ("response_header", "do")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    DO_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    do: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., do: _Optional[_Iterable[bool]] = ...) -> None: ...

class setDORequest(_message.Message):
    __slots__ = ("do", "value")
    DO_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    do: _containers.RepeatedScalarFieldContainer[int]
    value: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, do: _Optional[_Iterable[int]] = ..., value: _Optional[_Iterable[bool]] = ...) -> None: ...

class setDOResponse(_message.Message):
    __slots__ = ("response_header", "do")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    DO_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    do: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., do: _Optional[_Iterable[bool]] = ...) -> None: ...

class scheduleDORequest(_message.Message):
    __slots__ = ("do", "value", "time_secs")
    DO_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    do: _containers.RepeatedScalarFieldContainer[int]
    value: _containers.RepeatedScalarFieldContainer[bool]
    time_secs: float
    def __init__(self, do: _Optional[_Iterable[int]] = ..., value: _Optional[_Iterable[bool]] = ..., time_secs: _Optional[float] = ...) -> None: ...

class scheduleDOResponse(_message.Message):
    __slots__ = ("response_header", "do", "time_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    DO_FIELD_NUMBER: _ClassVar[int]
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    do: _containers.RepeatedScalarFieldContainer[bool]
    time_secs: float
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., do: _Optional[_Iterable[bool]] = ..., time_secs: _Optional[float] = ...) -> None: ...

class getAORequest(_message.Message):
    __slots__ = ("ao",)
    AO_FIELD_NUMBER: _ClassVar[int]
    ao: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, ao: _Optional[_Iterable[int]] = ...) -> None: ...

class getAOResponse(_message.Message):
    __slots__ = ("response_header", "ao")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    AO_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    ao: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., ao: _Optional[_Iterable[float]] = ...) -> None: ...

class getIoTableRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class getIoTableResponse(_message.Message):
    __slots__ = ("response_header", "io_table")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    IO_TABLE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    io_table: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., io_table: _Optional[str] = ...) -> None: ...

class setAORequest(_message.Message):
    __slots__ = ("ao", "value")
    AO_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    ao: _containers.RepeatedScalarFieldContainer[int]
    value: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, ao: _Optional[_Iterable[int]] = ..., value: _Optional[_Iterable[float]] = ...) -> None: ...

class setAOResponse(_message.Message):
    __slots__ = ("response_header", "ao")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    AO_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    ao: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., ao: _Optional[_Iterable[float]] = ...) -> None: ...

class scheduleAORequest(_message.Message):
    __slots__ = ("ao", "value", "time_secs")
    AO_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    ao: _containers.RepeatedScalarFieldContainer[int]
    value: _containers.RepeatedScalarFieldContainer[float]
    time_secs: float
    def __init__(self, ao: _Optional[_Iterable[int]] = ..., value: _Optional[_Iterable[float]] = ..., time_secs: _Optional[float] = ...) -> None: ...

class scheduleAOResponse(_message.Message):
    __slots__ = ("response_header", "ao", "time_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    AO_FIELD_NUMBER: _ClassVar[int]
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    ao: _containers.RepeatedScalarFieldContainer[float]
    time_secs: float
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., ao: _Optional[_Iterable[float]] = ..., time_secs: _Optional[float] = ...) -> None: ...

class getValueRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[_Iterable[str]] = ...) -> None: ...

class getValueResponse(_message.Message):
    __slots__ = ("response_header", "value")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    value: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., value: _Optional[_Iterable[str]] = ...) -> None: ...

class setValueRequest(_message.Message):
    __slots__ = ("name", "value")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    name: _containers.RepeatedScalarFieldContainer[str]
    value: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[_Iterable[str]] = ..., value: _Optional[_Iterable[str]] = ...) -> None: ...

class setValueResponse(_message.Message):
    __slots__ = ("response_header", "value")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    value: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., value: _Optional[_Iterable[str]] = ...) -> None: ...

class getSystemStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class getSystemStatusResponse(_message.Message):
    __slots__ = ("response_header", "input_voltage", "temperature", "rtc_time", "uptime", "system_info", "scheduled_startup_secs", "scheduled_shutdown_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    INPUT_VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    RTC_TIME_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_INFO_FIELD_NUMBER: _ClassVar[int]
    SCHEDULED_STARTUP_SECS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULED_SHUTDOWN_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    input_voltage: float
    temperature: float
    rtc_time: str
    uptime: float
    system_info: str
    scheduled_startup_secs: int
    scheduled_shutdown_secs: int
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., input_voltage: _Optional[float] = ..., temperature: _Optional[float] = ..., rtc_time: _Optional[str] = ..., uptime: _Optional[float] = ..., system_info: _Optional[str] = ..., scheduled_startup_secs: _Optional[int] = ..., scheduled_shutdown_secs: _Optional[int] = ...) -> None: ...

class getShutdownImmunityRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class getShutdownImmunityResponse(_message.Message):
    __slots__ = ("response_header", "immunity_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    IMMUNITY_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    immunity_secs: int
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., immunity_secs: _Optional[int] = ...) -> None: ...

class scheduleStartupRequest(_message.Message):
    __slots__ = ("time_secs",)
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    time_secs: float
    def __init__(self, time_secs: _Optional[float] = ...) -> None: ...

class scheduleStartupResponse(_message.Message):
    __slots__ = ("response_header", "time_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    time_secs: float
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., time_secs: _Optional[float] = ...) -> None: ...

class scheduleShutdownRequest(_message.Message):
    __slots__ = ("time_secs",)
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    time_secs: float
    def __init__(self, time_secs: _Optional[float] = ...) -> None: ...

class scheduleShutdownResponse(_message.Message):
    __slots__ = ("response_header", "time_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    time_secs: float
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., time_secs: _Optional[float] = ...) -> None: ...

class rebootRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class rebootResponse(_message.Message):
    __slots__ = ("response_header",)
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ...) -> None: ...

class shutdownRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class shutdownResponse(_message.Message):
    __slots__ = ("response_header",)
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ...) -> None: ...

class getTemperatureRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class getTemperatureResponse(_message.Message):
    __slots__ = ("response_header", "temperature")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    temperature: float
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., temperature: _Optional[float] = ...) -> None: ...

class getInputVoltageRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class getInputVoltageResponse(_message.Message):
    __slots__ = ("response_header", "voltage")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    voltage: float
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., voltage: _Optional[float] = ...) -> None: ...

class loadFirmwareRequest(_message.Message):
    __slots__ = ("url", "target")
    URL_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    url: str
    target: str
    def __init__(self, url: _Optional[str] = ..., target: _Optional[str] = ...) -> None: ...

class loadFirmwareResponse(_message.Message):
    __slots__ = ("response_header",)
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ...) -> None: ...

class loadBootloaderRequest(_message.Message):
    __slots__ = ("url",)
    URL_FIELD_NUMBER: _ClassVar[int]
    url: str
    def __init__(self, url: _Optional[str] = ...) -> None: ...

class loadBootloaderResponse(_message.Message):
    __slots__ = ("response_header",)
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ...) -> None: ...

class getFirmwareVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class getFirmwareVersionResponse(_message.Message):
    __slots__ = ("response_header", "version")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    version: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., version: _Optional[str] = ...) -> None: ...

class getLocationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class getLocationResponse(_message.Message):
    __slots__ = ("response_header", "latitude", "longitude", "altitude_m", "accuracy_m", "speed_mps", "heading_deg", "sat_count", "timestamp")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    ALTITUDE_M_FIELD_NUMBER: _ClassVar[int]
    ACCURACY_M_FIELD_NUMBER: _ClassVar[int]
    SPEED_MPS_FIELD_NUMBER: _ClassVar[int]
    HEADING_DEG_FIELD_NUMBER: _ClassVar[int]
    SAT_COUNT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    latitude: float
    longitude: float
    altitude_m: float
    accuracy_m: float
    speed_mps: float
    heading_deg: float
    sat_count: int
    timestamp: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., altitude_m: _Optional[float] = ..., accuracy_m: _Optional[float] = ..., speed_mps: _Optional[float] = ..., heading_deg: _Optional[float] = ..., sat_count: _Optional[int] = ..., timestamp: _Optional[str] = ...) -> None: ...

class syncRtcTimeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class syncRtcTimeResponse(_message.Message):
    __slots__ = ("response_header",)
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ...) -> None: ...

class EventDetail(_message.Message):
    __slots__ = ("event_id", "event", "pin", "value", "time", "cm4_online")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    PIN_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    CM4_ONLINE_FIELD_NUMBER: _ClassVar[int]
    event_id: int
    event: str
    pin: int
    value: str
    time: int
    cm4_online: bool
    def __init__(self, event_id: _Optional[int] = ..., event: _Optional[str] = ..., pin: _Optional[int] = ..., value: _Optional[str] = ..., time: _Optional[int] = ..., cm4_online: bool = ...) -> None: ...

class getEventsRequest(_message.Message):
    __slots__ = ("events_from",)
    EVENTS_FROM_FIELD_NUMBER: _ClassVar[int]
    events_from: int
    def __init__(self, events_from: _Optional[int] = ...) -> None: ...

class getEventsResponse(_message.Message):
    __slots__ = ("response_header", "events", "events_synced")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    EVENTS_SYNCED_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    events: _containers.RepeatedCompositeFieldContainer[EventDetail]
    events_synced: bool
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., events: _Optional[_Iterable[_Union[EventDetail, _Mapping]]] = ..., events_synced: bool = ...) -> None: ...

class getDIEventsRequest(_message.Message):
    __slots__ = ("pin", "rising", "falling", "include_system_events", "events_from")
    PIN_FIELD_NUMBER: _ClassVar[int]
    RISING_FIELD_NUMBER: _ClassVar[int]
    FALLING_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_SYSTEM_EVENTS_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FROM_FIELD_NUMBER: _ClassVar[int]
    pin: int
    rising: bool
    falling: bool
    include_system_events: bool
    events_from: int
    def __init__(self, pin: _Optional[int] = ..., rising: bool = ..., falling: bool = ..., include_system_events: bool = ..., events_from: _Optional[int] = ...) -> None: ...

class getDIEventsResponse(_message.Message):
    __slots__ = ("response_header", "events", "events_synced")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    EVENTS_SYNCED_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    events: _containers.RepeatedCompositeFieldContainer[EventDetail]
    events_synced: bool
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., events: _Optional[_Iterable[_Union[EventDetail, _Mapping]]] = ..., events_synced: bool = ...) -> None: ...
