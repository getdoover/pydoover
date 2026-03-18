from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class busStatus(_message.Message):
    __slots__ = ("bus_id", "open", "serial_settings", "ethernet_settings")
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    OPEN_FIELD_NUMBER: _ClassVar[int]
    SERIAL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ETHERNET_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    open: bool
    serial_settings: serialBusSettings
    ethernet_settings: ethernetBusSettings
    def __init__(self, bus_id: _Optional[str] = ..., open: bool = ..., serial_settings: _Optional[_Union[serialBusSettings, _Mapping]] = ..., ethernet_settings: _Optional[_Union[ethernetBusSettings, _Mapping]] = ...) -> None: ...

class responseHeader(_message.Message):
    __slots__ = ("success", "response_code", "response_message", "bus_status")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BUS_STATUS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    response_code: int
    response_message: str
    bus_status: _containers.RepeatedCompositeFieldContainer[busStatus]
    def __init__(self, success: bool = ..., response_code: _Optional[int] = ..., response_message: _Optional[str] = ..., bus_status: _Optional[_Iterable[_Union[busStatus, _Mapping]]] = ...) -> None: ...

class serverResponseHeader(_message.Message):
    __slots__ = ("success", "response_code", "response_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    response_code: int
    response_message: str
    def __init__(self, success: bool = ..., response_code: _Optional[int] = ..., response_message: _Optional[str] = ...) -> None: ...

class testCommsRequest(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class testCommsResponse(_message.Message):
    __slots__ = ("response_header", "response")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    response: str
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., response: _Optional[str] = ...) -> None: ...

class serialBusSettings(_message.Message):
    __slots__ = ("port", "baud", "modbus_method", "data_bits", "parity", "stop_bits", "timeout")
    PORT_FIELD_NUMBER: _ClassVar[int]
    BAUD_FIELD_NUMBER: _ClassVar[int]
    MODBUS_METHOD_FIELD_NUMBER: _ClassVar[int]
    DATA_BITS_FIELD_NUMBER: _ClassVar[int]
    PARITY_FIELD_NUMBER: _ClassVar[int]
    STOP_BITS_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    port: str
    baud: int
    modbus_method: str
    data_bits: int
    parity: str
    stop_bits: int
    timeout: float
    def __init__(self, port: _Optional[str] = ..., baud: _Optional[int] = ..., modbus_method: _Optional[str] = ..., data_bits: _Optional[int] = ..., parity: _Optional[str] = ..., stop_bits: _Optional[int] = ..., timeout: _Optional[float] = ...) -> None: ...

class ethernetBusSettings(_message.Message):
    __slots__ = ("ip", "port", "modbus_method", "timeout")
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    MODBUS_METHOD_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    modbus_method: str
    timeout: float
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ..., modbus_method: _Optional[str] = ..., timeout: _Optional[float] = ...) -> None: ...

class openBusRequest(_message.Message):
    __slots__ = ("bus_id", "serial_settings", "ethernet_settings")
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    SERIAL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ETHERNET_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    serial_settings: serialBusSettings
    ethernet_settings: ethernetBusSettings
    def __init__(self, bus_id: _Optional[str] = ..., serial_settings: _Optional[_Union[serialBusSettings, _Mapping]] = ..., ethernet_settings: _Optional[_Union[ethernetBusSettings, _Mapping]] = ...) -> None: ...

class openBusResponse(_message.Message):
    __slots__ = ("response_header", "bus_id")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    bus_id: str
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., bus_id: _Optional[str] = ...) -> None: ...

class listBusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class listBusResponse(_message.Message):
    __slots__ = ("response_header", "bus_status")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    BUS_STATUS_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    bus_status: _containers.RepeatedCompositeFieldContainer[busStatus]
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., bus_status: _Optional[_Iterable[_Union[busStatus, _Mapping]]] = ...) -> None: ...

class busStatusRequest(_message.Message):
    __slots__ = ("bus_id",)
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    def __init__(self, bus_id: _Optional[str] = ...) -> None: ...

class busStatusResponse(_message.Message):
    __slots__ = ("response_header", "bus_status")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    BUS_STATUS_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    bus_status: busStatus
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., bus_status: _Optional[_Union[busStatus, _Mapping]] = ...) -> None: ...

class closeBusRequest(_message.Message):
    __slots__ = ("bus_id",)
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    def __init__(self, bus_id: _Optional[str] = ...) -> None: ...

class closeBusResponse(_message.Message):
    __slots__ = ("response_header", "bus_id")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    bus_id: str
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., bus_id: _Optional[str] = ...) -> None: ...

class readRegisterRequest(_message.Message):
    __slots__ = ("bus_id", "modbus_id", "register_type", "address", "count")
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    MODBUS_ID_FIELD_NUMBER: _ClassVar[int]
    REGISTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    modbus_id: int
    register_type: int
    address: int
    count: int
    def __init__(self, bus_id: _Optional[str] = ..., modbus_id: _Optional[int] = ..., register_type: _Optional[int] = ..., address: _Optional[int] = ..., count: _Optional[int] = ...) -> None: ...

class readRegisterResponse(_message.Message):
    __slots__ = ("response_header", "response_code", "values")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    response_code: int
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., response_code: _Optional[int] = ..., values: _Optional[_Iterable[int]] = ...) -> None: ...

class writeRegisterRequest(_message.Message):
    __slots__ = ("bus_id", "modbus_id", "register_type", "address", "values")
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    MODBUS_ID_FIELD_NUMBER: _ClassVar[int]
    REGISTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    modbus_id: int
    register_type: int
    address: int
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, bus_id: _Optional[str] = ..., modbus_id: _Optional[int] = ..., register_type: _Optional[int] = ..., address: _Optional[int] = ..., values: _Optional[_Iterable[int]] = ...) -> None: ...

class writeRegisterResponse(_message.Message):
    __slots__ = ("response_header", "response_code")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    response_code: int
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., response_code: _Optional[int] = ...) -> None: ...

class scheduleWriteRegisterRequest(_message.Message):
    __slots__ = ("bus_id", "register_type", "address", "values", "delay_secs")
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    REGISTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    DELAY_SECS_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    register_type: int
    address: int
    values: _containers.RepeatedScalarFieldContainer[int]
    delay_secs: int
    def __init__(self, bus_id: _Optional[str] = ..., register_type: _Optional[int] = ..., address: _Optional[int] = ..., values: _Optional[_Iterable[int]] = ..., delay_secs: _Optional[int] = ...) -> None: ...

class scheduleWriteRegisterResponse(_message.Message):
    __slots__ = ("response_header", "bus_id", "delay_secs")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    DELAY_SECS_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    bus_id: str
    delay_secs: int
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., bus_id: _Optional[str] = ..., delay_secs: _Optional[int] = ...) -> None: ...

class readRegisterSubscriptionRequest(_message.Message):
    __slots__ = ("bus_id", "modbus_id", "register_type", "address", "count", "poll_secs")
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    MODBUS_ID_FIELD_NUMBER: _ClassVar[int]
    REGISTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    POLL_SECS_FIELD_NUMBER: _ClassVar[int]
    bus_id: str
    modbus_id: int
    register_type: int
    address: int
    count: int
    poll_secs: int
    def __init__(self, bus_id: _Optional[str] = ..., modbus_id: _Optional[int] = ..., register_type: _Optional[int] = ..., address: _Optional[int] = ..., count: _Optional[int] = ..., poll_secs: _Optional[int] = ...) -> None: ...

class readRegisterSubscriptionResponse(_message.Message):
    __slots__ = ("response_header", "bus_id", "response_code", "values")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    BUS_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    response_header: responseHeader
    bus_id: str
    response_code: int
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, response_header: _Optional[_Union[responseHeader, _Mapping]] = ..., bus_id: _Optional[str] = ..., response_code: _Optional[int] = ..., values: _Optional[_Iterable[int]] = ...) -> None: ...

class createServerRequest(_message.Message):
    __slots__ = ("type", "port", "host", "holding_registers", "input_registers", "coils", "discrete_inputs", "modbus_id")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    HOLDING_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    INPUT_REGISTERS_FIELD_NUMBER: _ClassVar[int]
    COILS_FIELD_NUMBER: _ClassVar[int]
    DISCRETE_INPUTS_FIELD_NUMBER: _ClassVar[int]
    MODBUS_ID_FIELD_NUMBER: _ClassVar[int]
    type: str
    port: int
    host: str
    holding_registers: _containers.RepeatedScalarFieldContainer[int]
    input_registers: _containers.RepeatedScalarFieldContainer[int]
    coils: _containers.RepeatedScalarFieldContainer[bool]
    discrete_inputs: _containers.RepeatedScalarFieldContainer[bool]
    modbus_id: int
    def __init__(self, type: _Optional[str] = ..., port: _Optional[int] = ..., host: _Optional[str] = ..., holding_registers: _Optional[_Iterable[int]] = ..., input_registers: _Optional[_Iterable[int]] = ..., coils: _Optional[_Iterable[bool]] = ..., discrete_inputs: _Optional[_Iterable[bool]] = ..., modbus_id: _Optional[int] = ...) -> None: ...

class createServerResponse(_message.Message):
    __slots__ = ("response_header", "response")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response_header: serverResponseHeader
    response: str
    def __init__(self, response_header: _Optional[_Union[serverResponseHeader, _Mapping]] = ..., response: _Optional[str] = ...) -> None: ...

class listServerRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class listServerResponse(_message.Message):
    __slots__ = ("response_header", "servers")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    SERVERS_FIELD_NUMBER: _ClassVar[int]
    response_header: serverResponseHeader
    servers: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, response_header: _Optional[_Union[serverResponseHeader, _Mapping]] = ..., servers: _Optional[_Iterable[str]] = ...) -> None: ...

class closeServerRequest(_message.Message):
    __slots__ = ("port",)
    PORT_FIELD_NUMBER: _ClassVar[int]
    port: int
    def __init__(self, port: _Optional[int] = ...) -> None: ...

class closeServerResponse(_message.Message):
    __slots__ = ("response_header", "port")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    response_header: serverResponseHeader
    port: int
    def __init__(self, response_header: _Optional[_Union[serverResponseHeader, _Mapping]] = ..., port: _Optional[int] = ...) -> None: ...

class setServerRegistersRequest(_message.Message):
    __slots__ = ("port", "function_code", "address", "values")
    PORT_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_CODE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    port: int
    function_code: int
    address: _containers.RepeatedScalarFieldContainer[int]
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, port: _Optional[int] = ..., function_code: _Optional[int] = ..., address: _Optional[_Iterable[int]] = ..., values: _Optional[_Iterable[int]] = ...) -> None: ...

class setServerRegistersResponse(_message.Message):
    __slots__ = ("response_header",)
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    response_header: serverResponseHeader
    def __init__(self, response_header: _Optional[_Union[serverResponseHeader, _Mapping]] = ...) -> None: ...

class getServerRegistersRequest(_message.Message):
    __slots__ = ("port", "function_code", "address", "count")
    PORT_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_CODE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    port: int
    function_code: int
    address: int
    count: int
    def __init__(self, port: _Optional[int] = ..., function_code: _Optional[int] = ..., address: _Optional[int] = ..., count: _Optional[int] = ...) -> None: ...

class getServerRegistersResponse(_message.Message):
    __slots__ = ("response_header", "values")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    response_header: serverResponseHeader
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, response_header: _Optional[_Union[serverResponseHeader, _Mapping]] = ..., values: _Optional[_Iterable[int]] = ...) -> None: ...

class scheduleServerRegistersRequest(_message.Message):
    __slots__ = ("port", "function_code", "address", "values", "delay_secs")
    PORT_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_CODE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    DELAY_SECS_FIELD_NUMBER: _ClassVar[int]
    port: int
    function_code: int
    address: int
    values: _containers.RepeatedScalarFieldContainer[int]
    delay_secs: float
    def __init__(self, port: _Optional[int] = ..., function_code: _Optional[int] = ..., address: _Optional[int] = ..., values: _Optional[_Iterable[int]] = ..., delay_secs: _Optional[float] = ...) -> None: ...

class scheduleServerRegistersResponse(_message.Message):
    __slots__ = ("response_header",)
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    response_header: serverResponseHeader
    def __init__(self, response_header: _Optional[_Union[serverResponseHeader, _Mapping]] = ...) -> None: ...
