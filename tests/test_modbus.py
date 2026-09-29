import pytest

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


class _RecordingInterface(ModbusInterface):
    """Captures the gRPC call instead of sending it."""

    def __init__(self, success=True):
        super().__init__("test_app", "127.0.0.1:50054")
        self.calls = []
        self._success = success

    async def make_request(self, stub_call, request, *args, **kwargs):
        self.calls.append((stub_call, request))
        return modbus_iface_pb2.writeSingleRegisterResponse(
            response_header=modbus_iface_pb2.responseHeader(success=self._success)
        )


@pytest.mark.asyncio
async def test_write_single_register_sends_single_register_rpc():
    iface = _RecordingInterface()
    ok = await iface.write_single_register(modbus_id=3, address=135, value=22)
    assert ok is True
    ((stub_call, req),) = iface.calls
    assert stub_call == "writeSingleRegister"
    assert isinstance(req, modbus_iface_pb2.writeSingleRegisterRequest)
    assert (req.modbus_id, req.register_type, req.address, req.value) == (3, 4, 135, 22)
    assert not req.HasField("retries")


@pytest.mark.asyncio
async def test_write_single_register_coil_and_retries():
    iface = _RecordingInterface()
    await iface.write_single_register(address=7, value=True, register_type=1, retries=0)
    ((_, req),) = iface.calls
    assert (req.register_type, req.address, req.value) == (1, 7, 1)
    assert req.HasField("retries") and req.retries == 0


@pytest.mark.asyncio
async def test_write_single_register_reports_failure():
    iface = _RecordingInterface(success=False)
    assert await iface.write_single_register(address=1, value=1) is False


def test_write_registers_rpc_unchanged():
    # writeSingleRegister is additive: the multi-write RPC and message keep
    # their shape so existing interfaces and apps are unaffected.
    fields = [f.name for f in modbus_iface_pb2.writeRegisterRequest.DESCRIPTOR.fields]
    assert fields == [
        "bus_id",
        "modbus_id",
        "register_type",
        "address",
        "values",
        "serial_settings",
        "ethernet_settings",
        "retries",
    ]
