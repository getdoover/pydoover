from pydoover.docker.modbus.modbus_iface import ModbusInterface
from pydoover.models.generated.modbus import modbus_iface_pb2


def _values(*registers: int):
    """A real protobuf repeated field, as read_registers receives it."""
    return modbus_iface_pb2.readRegisterResponse(values=registers).values


def test_parse_register_output_empty_returns_none():
    assert ModbusInterface._parse_register_output(_values()) is None


def test_parse_register_output_single_returns_int():
    assert ModbusInterface._parse_register_output(_values(42)) == 42


def test_parse_register_output_multiple_returns_list():
    result = ModbusInterface._parse_register_output(_values(1, 2, 3))
    assert result == [1, 2, 3]
    # Must be a real list, not the protobuf repeated-field container —
    # callers validate responses with isinstance(result, list).
    assert isinstance(result, list)
