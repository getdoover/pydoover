from ...config import Array, Enum, Integer, Number, Object, String


class ModbusType:
    SERIAL = "serial"
    TCP = "tcp"


class ModbusConfig(Object):
    type = Enum("Bus Type", choices=["serial", "tcp"], default="serial")
    name = String("Name", default="default")

    # TODO: only show these when serial type is selected.
    serial_port = String("Serial Port", default="/dev/ttyAMA0")
    serial_baud = Integer("Serial Baud", default=9600)
    serial_method = Enum(
        "Serial Method",
        choices=["rtu", "ascii", "socket", "tls"],
        default="rtu",
    )
    serial_bits = Integer("Serial Data Bits", default=8)
    serial_parity = Enum(
        "Serial Parity", choices=["None", "Even", "Odd"], default="None"
    )
    serial_stop = Integer("Serial Stop Bits", default=1)
    serial_timeout = Number("Serial Timeout", default=0.3)

    tcp_uri = String("TCP URI", default="127.0.0.1:5000")
    tcp_timeout = Number("TCP Timeout", default=2.0)

    def __init__(self, display_name: str = "Modbus Config"):
        super().__init__(display_name)


class ManyModbusConfig(Array):
    elements: list[ModbusConfig]

    def __init__(self, display_name: str = "Modbus Config"):
        super().__init__(display_name, element=ModbusConfig("Modbus Instance Config"))
