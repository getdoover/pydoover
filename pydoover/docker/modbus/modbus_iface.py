import asyncio
import logging
from collections.abc import Coroutine, Callable

from typing import Union

import grpc

from .config import ModbusConfig, ModbusType, ManyModbusConfig
from .grpc_stubs import modbus_iface_pb2, modbus_iface_pb2_grpc
from ..grpc_interface import GRPCInterface
from ...utils import call_maybe_async, maybe_async
from ...cli.decorators import command as cli_command, ignore_alias
from ...config import Schema

log = logging.getLogger(__name__)
ReadRegisterSubscriptionCallback = Union[
    Callable[[list[int]], None], Coroutine[[list[int]], None]
]


def two_words_to_32bit_float(word1: int, word2: int, swap: bool = False):
    """Convert two 16-bit words to a 32-bit float."""
    if swap:
        word1, word2 = word2, word1
    return word1 + (word2 * 65536)


class ModbusInterface(GRPCInterface):
    """ModbusInterface is a gRPC interface for interacting with modbus devices.

    It allows for opening and closing modbus buses, reading and writing registers, and subscribing to register updates.
    It is designed to be used with the modbus_iface gRPC service.

    It supports both synchronous and asynchronous operations, depending on the context of the application.

    Attributes
    ----------
    config : Schema
        Configuration schema for the modbus interface, containing modbus bus definitions.
        This is loaded from application config automatically and should be specified in your `app_config.py` file.
    """

    stub = modbus_iface_pb2_grpc.modbusIfaceStub

    def __init__(
        self,
        app_key: str,
        modbus_uri: str = "127.0.0.1:50054",
        is_async: bool = None,
        config: Schema = None,
    ):
        super().__init__(app_key, modbus_uri, is_async)

        self.subscription_tasks = []

        self.config = config
        self.config_complete = False

    async def setup(self):
        self.config_complete = False
        try:
            config = self.config.modbus_config
        except AttributeError:
            log.info("No modbus interfaces defined in config")
            self.config_complete = True
            return

        if isinstance(config, ModbusConfig):
            elems: list[ModbusConfig] = [config]
        elif isinstance(config, ManyModbusConfig):
            elems: list[ModbusConfig] = config.elements
        else:
            log.warning(f"Unsupported modbus config type: {type(config)}")
            self.config_complete = True
            return

        for elem in elems:
            log.info(f"Setting up modbus bus: {elem}")
            if elem.type.value == ModbusType.SERIAL:
                await self.open_bus_async(
                    elem.type.value,
                    elem.name.value,
                    elem.serial_port.value,
                    elem.serial_baud.value,
                    elem.serial_method.value,
                    elem.serial_bits.value,
                    elem.serial_parity.value,
                    elem.serial_stop.value,
                    elem.serial_timeout.value,
                )
            elif elem.type.value == ModbusType.TCP:
                await self.open_bus_async(
                    elem.type.value,
                    elem.name.value,
                    tcp_uri=elem.tcp_uri.value,
                    tcp_timeout=elem.tcp_timeout.value,
                )
            else:
                log.warning(
                    f"Invalid bus type: {elem.type.value}. Expected 'serial' or 'tcp'."
                )

        self.config_complete = True

    def process_response(self, stub_call: str, response, *args, **kwargs):
        resp = super().process_response(stub_call, response, *args, **kwargs)

        if response.response_header.success:
            log.debug("Response was OK. Nothing to process...")
            return resp

        # only for some of the calls we want to ensure a bus is available (e.g. read/write registers)
        # this will fix it for next run but not the current one...
        try:
            configure_bus = kwargs["configure_bus"]
            bus_id = kwargs["bus_id"]
        except KeyError:
            log.debug(
                "Response was not OK, but no bus_id or configure_bus provided. Nothing to do..."
            )
            return resp

        self.ensure_bus_available(bus_id, response.response_header, configure_bus)
        return resp

    def ensure_bus_available(self, bus_id, response_header, configure: bool = True):
        ## if not config_complete, wait for setup to complete
        if not self.config_complete:
            log.debug("Waiting for modbus setup to complete")
            return False

        ## check the bus status from the response and if the bus does not exist, and configure is True, rerun the setup
        for b in response_header.bus_status:
            if b.bus_id == bus_id:
                return b.open

        log.warning(f"Bus {bus_id} not found in response")
        if configure:
            log.info("Reconfiguring modbus iface")
            _t = asyncio.create_task(self.setup())

        return True

    async def close(self):
        log.info("Closing modbus interface")
        for task in self.subscription_tasks:
            task.cancel()

    @staticmethod
    def _get_bus_request(
        bus_type="serial",
        name="default",
        serial_port="/dev/ttyS0",
        serial_baud=9600,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
        tcp_uri="127.0.0.1:5000",
        tcp_timeout=2,
    ):
        if bus_type not in ("serial", "tcp"):
            log.error("Invalid bus type: " + str(bus_type))
            return None

        kwargs = {"bus_id": str(name)}

        if bus_type == "serial":
            kwargs["serial_settings"] = modbus_iface_pb2.serialBusSettings(
                port=serial_port,
                baud=serial_baud,
                modbus_method=serial_method,
                data_bits=serial_bits,
                parity=serial_parity,
                stop_bits=serial_stop,
                timeout=serial_timeout,
            )
        elif bus_type == "tcp":
            ip, port = tcp_uri.split(":")
            kwargs["ethernet_settings"] = modbus_iface_pb2.ethernetBusSettings(
                ip=ip, port=int(port), timeout=tcp_timeout
            )
        else:
            log.error("Invalid bus type: " + str(bus_type))
            return None

        return modbus_iface_pb2.openBusRequest(**kwargs)

    @cli_command()
    @maybe_async()
    def open_bus(
        self,
        bus_type="serial",
        name="default",
        serial_port="/dev/ttyS0",
        serial_baud=9600,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
        tcp_uri="127.0.0.1:5000",
        tcp_timeout=2,
    ) -> bool:
        req = self._get_bus_request(
            bus_type,
            name,
            serial_port,
            serial_baud,
            serial_method,
            serial_bits,
            serial_parity,
            serial_stop,
            serial_timeout,
            tcp_uri,
            tcp_timeout,
        )
        if req is None:
            return

        resp = self.make_request("openBus", req)
        return resp.response_header.success

    async def open_bus_async(
        self,
        bus_type="serial",
        name="default",
        serial_port="/dev/ttyS0",
        serial_baud=9600,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
        tcp_uri="127.0.0.1:5000",
        tcp_timeout=2,
    ) -> bool:
        req = self._get_bus_request(
            bus_type,
            name,
            serial_port,
            serial_baud,
            serial_method,
            serial_bits,
            serial_parity,
            serial_stop,
            serial_timeout,
            tcp_uri,
            tcp_timeout,
        )
        if req is None:
            return False

        resp = await self.make_request_async("openBus", req)
        return resp.response_header.success

    @cli_command()
    @maybe_async()
    def close_bus(self, bus_id: str = "default") -> bool:
        req = modbus_iface_pb2.closeBusRequest(bus_id=str(bus_id))
        resp = self.make_request("closeBus", req)
        return resp.response_header.success and resp.bus_status.open

    async def close_bus_async(self, bus_id: str = "default") -> bool:
        req = modbus_iface_pb2.closeBusRequest(bus_id=str(bus_id))
        resp = await self.make_request_async("closeBus", req)
        return resp.response_header.success and resp.bus_status.open

    def _validate_read_register_resp(self, resp, bus_id, configure_bus):
        try:
            if not resp.response_header.success:
                log.error("Error reading registers from bus " + str(bus_id))
                return False
            # return self.ensure_bus_availabe(bus_id, resp.response_header, configure_bus)
            return True
        except Exception as e:
            log.error("Error validating read register response: " + str(e))
            return False

    @cli_command()
    @maybe_async()
    def get_bus_status(self, bus_id: str = "default") -> bool:
        """Get the status of a modbus bus.

        .. note:: This method can be called in both sync and asynchronous contexts.

        Parameters
        ----------
        bus_id : str, optional
            The bus ID to fetch an OK status for

        Returns
        -------
        bool
            True if the bus is open, False otherwise.
        """
        req = modbus_iface_pb2.busStatusRequest(bus_id=str(bus_id))
        resp = self.make_request("busStatus", req)
        return resp.response_header.success and resp.bus_status.open

    async def get_bus_status_async(self, bus_id: str = "default") -> bool:
        req = modbus_iface_pb2.busStatusRequest(bus_id=str(bus_id))
        resp = await self.make_request_async("busStatus", req)
        return resp.response_header.success and resp.bus_status.open

    getBusStatus = ignore_alias(get_bus_status)
    getBusStatus_async = get_bus_status_async

    @staticmethod
    def _parse_register_output(values):
        if len(values) == 0:
            return None
        if len(values) == 1:
            return values[0]
        return values

    @cli_command()
    @maybe_async()
    def read_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        configure_bus: bool = True,
    ) -> int | list[int] | None:
        """Read registers from a modbus bus.

        .. note:: This method can be called in both sync and asynchronous contexts.

        Examples
        --------
        >>> self.modbus_iface.read_registers(bus_id="default", modbus_id=1, start_address=0, num_registers=10)


        Parameters
        ----------
        bus_id : str, optional
            The bus ID to read registers from (default is "default")
        modbus_id : int, optional
            The modbus ID of the device to read registers from (default is 1)
        start_address : int, optional
            The starting address of the registers to read (default is 0)
        num_registers : int, optional
            The number of registers to read (default is 1)
        register_type : int, optional
            The type of registers to read (default is 4, which is typically holding registers)
        configure_bus : bool, optional
            Whether to configure the bus if it is not available (default is True)

        Returns
        -------
        int | list[int] | None
            The values read from the registers.
            If only one register is read, returns an int.
            If multiple registers are read, returns a list of ints.
            If the response failed, returns None.
        """
        req = modbus_iface_pb2.readRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            count=num_registers,
        )
        resp = self.make_request(
            "readRegisters", req, bus_id=bus_id, configure_bus=configure_bus
        )
        return resp and self._parse_register_output(resp.values)

    async def read_registers_async(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        configure_bus: bool = True,
    ) -> int | list[int] | None:
        req = modbus_iface_pb2.readRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            count=num_registers,
        )
        resp = await self.make_request_async(
            "readRegisters", req, bus_id=bus_id, configure_bus=configure_bus
        )
        return resp and self._parse_register_output(resp.values)

    @cli_command()
    @maybe_async()
    def write_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        values: list[int] = None,
        register_type: int = 4,
        configure_bus: bool = True,
    ) -> bool:
        """Write values to registers on a modbus bus.

        .. note:: This method can be called in both sync and asynchronous contexts.

        Examples
        --------
        >>> self.modbus_iface.write_registers(
        ...     bus_id="my_bus",
        ...     modbus_id=1,
        ...     start_address=0,
        ...     values=[100, 200, 300],
        ...     register_type=4,
        ...     configure_bus=True,
        ... )

        Parameters
        ----------
        bus_id: str
            The bus ID to write registers to (default is "default")
        modbus_id: int
            The modbus ID of the device to write registers to (default is 1)
        start_address: int
            The starting address of the registers to write (default is 0)
        values: list[int]
            Register values to write
        register_type: int
            The type of registers to write (default is 4, which is typically holding registers)
        configure_bus: bool
            Whether to configure the bus if it is not available (default is True)

        Returns
        -------
        bool
            True if the write operation was successful, False otherwise.
        """
        values = values or []
        req = modbus_iface_pb2.writeRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            values=values,
        )
        resp = self.make_request(
            "writeRegisters", req, bus_id=bus_id, configure_bus=configure_bus
        )
        return resp and self._validate_read_register_resp(resp, bus_id, configure_bus)

    async def write_registers_async(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        values: list[int] = None,
        register_type: int = 4,
        configure_bus: bool = True,
    ) -> bool:
        values = values or []
        req = modbus_iface_pb2.writeRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            values=values,
        )
        resp = await self.make_request_async(
            "writeRegisters", req, bus_id=bus_id, configure_bus=configure_bus
        )
        return resp and self._validate_read_register_resp(resp, bus_id, configure_bus)

    def add_read_register_subscription(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        poll_secs: int = 3,
        callback: ReadRegisterSubscriptionCallback = None,
    ):
        """Add a subscription to read registers from a modbus bus.

        This method creates a subcscription that will periodically read registers from the specified modbus device and
        invoke the provided callback when a read request succeeds.

        The provided callback can be a regular function or a coroutine.

        Examples
        --------

        >>> def my_callback(values: list[int]):
        ...     print("Received new register values:", values)
        >>> self.modbus_iface.add_read_register_subscription(
        ...     bus_id="my_bus",
        ...     modbus_id=1,
        ...     start_address=0,
        ...     num_registers=10,
        ...     callback=my_callback,
        ... )


        Parameters
        ----------
        bus_id : str, optional
            The bus ID to read registers from (default is "default")
        modbus_id : int, optional
            The modbus ID of the device to read registers from (default is 1)
        start_address : int, optional
            The starting address of the registers to read (default is 0)
        num_registers : int, optional
            The number of registers to read (default is 1)
        register_type : int, optional
            The type of registers to read (default is 4, which is typically holding registers)
        poll_secs : int, optional
            The polling interval in seconds for the subscription (default is 3 seconds)
        callback : Callback
            The callback function to invoke when a read request succeeds.
            This accepts a list of integers representing the register values.
            If only one register is read, this will be a single integer.
            This callback can be a regular function or a coroutine.

        """

        if callback is None:
            log.error("No callback provided for read register subscription")
            return None

        try:
            new_task = asyncio.create_task(
                self.run_read_register_subscription_task(
                    bus_id=str(bus_id),
                    modbus_id=modbus_id,
                    start_address=start_address,
                    num_registers=num_registers,
                    register_type=register_type,
                    poll_secs=poll_secs,
                    callback=callback,
                )
            )

            self.subscription_tasks.append(new_task)
            new_task.add_done_callback(self.subscription_tasks.remove)
            return new_task

        except Exception as e:
            log.error("Error adding read register subscription: " + str(e))
            return None

    async def run_read_register_subscription_task(
        self,
        bus_id: str,
        modbus_id: int,
        start_address: int,
        num_registers: int,
        register_type: int,
        poll_secs: int,
        callback: ReadRegisterSubscriptionCallback,
        configure_bus: bool = True,
    ):
        try:
            async with grpc.aio.insecure_channel(self.uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                request = modbus_iface_pb2.readRegisterSubscriptionRequest(
                    bus_id=str(bus_id),
                    modbus_id=modbus_id,
                    register_type=register_type,
                    address=start_address,
                    count=num_registers,
                    poll_secs=poll_secs,
                )

                try:
                    async for response in stub.readRegisterSubscription(request):
                        success = response.response_header.success
                        if not self._validate_read_register_resp(
                            response, bus_id, configure_bus
                        ):
                            values = None
                        elif len(response.values) == 1:
                            values = response.values[0]
                        else:
                            values = response.values

                        log.debug(
                            f"Received new modbus subscription result on bus {bus_id}, for modbus_id {modbus_id}, result={success}"
                        )
                        if callback is not None:
                            await call_maybe_async(callback, values)

                except Exception as e:
                    log.error("Error in read register subscription task: " + str(e))
                    return None

        except Exception as e:
            log.error("Error in read register subscription task: " + str(e))
            return None

    @cli_command()
    def test_comms(self, message: str = "Comms Check Message") -> str | None:
        """Test connection by sending a basic echo response to modbus interface container.

        Parameters
        ----------
        message : str
            Message to send to modbus interface to have echo'd as a response

        Returns
        -------
        str
            The response from modbus interface.
        """
        return self.make_request(
            "testComms",
            modbus_iface_pb2.testCommsRequest(message=message),
            response_field="response",
        )


modbus_iface = ModbusInterface
