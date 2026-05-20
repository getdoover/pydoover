from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .application import Application, run_app
    from .device_agent import DeviceAgentInterface, MockDeviceAgentInterface
    from .modbus import ModbusInterface, ModbusConfig, ManyModbusConfig
    from .platform import PlatformInterface, PulseCounter

_LAZY_ATTRS = {
    "Application": (".application", "Application"),
    "run_app": (".application", "run_app"),
    "DeviceAgentInterface": (".device_agent", "DeviceAgentInterface"),
    "MockDeviceAgentInterface": (".device_agent", "MockDeviceAgentInterface"),
    "ModbusInterface": (".modbus", "ModbusInterface"),
    "ModbusConfig": (".modbus", "ModbusConfig"),
    "ManyModbusConfig": (".modbus", "ManyModbusConfig"),
    "PlatformInterface": (".platform", "PlatformInterface"),
    "PulseCounter": (".platform", "PulseCounter"),
}

__all__ = list(_LAZY_ATTRS)


def __getattr__(name):
    try:
        module_path, attr_name = _LAZY_ATTRS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None

    from importlib import import_module

    module = import_module(module_path, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals()) + list(_LAZY_ATTRS))
