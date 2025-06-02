from ...config import Enum, Integer, String, Number, Array, Object


class ModbusType:
    SERIAL = "serial"
    TCP = "tcp"


class ModbusConfig(Object):
    def __init__(self, display_name: str = "Modbus Config"):
        super().__init__(display_name)

        self.type = Enum("Bus Type", choices=["serial", "tcp"], default="serial")
        self.name = String("Name", default="default")

        # todo: only show these if serial type is selected
        self.serial_port = String("Serial Port", default="/dev/ttyS0")
        self.serial_baud = Integer("Serial Baud", default=9600)
        # pretty sure this is unused
        self.serial_method = Enum(
            "Serial Method",
            choices=["rtu", "ascii", "socket", "tls"],
            default="rtu",
        )
        self.serial_bits = Integer("Serial Data Bits", default=8)
        self.serial_parity = Enum(
            "Serial Parity", choices=["None", "Even", "Odd"], default="None"
        )
        self.serial_stop = Integer("Serial Stop Bits", default=1)
        self.serial_timeout = Number("Serial Timeout", default=0.3)

        self.tcp_uri = String("TCP URI", default="127.0.0.1:5000")
        self.tcp_timeout = Number("TCP Timeout", default=2.0)


class ManyModbusConfig(Array):
    elements: list[ModbusConfig]

    def __init__(self, display_name: str = "Modbus Config"):
        super().__init__(display_name, element=ModbusConfig("Modbus Instance Config"))
