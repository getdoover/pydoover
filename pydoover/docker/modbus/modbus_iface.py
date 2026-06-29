import asyncio
import logging
import warnings
from collections.abc import Coroutine, Callable

import grpc

from .config import ModbusConfig, ModbusType, ManyModbusConfig
from ...models.generated.modbus import modbus_iface_pb2, modbus_iface_pb2_grpc
from ..grpc_interface import GRPCInterface
from ...utils import call_maybe_async
from ...cli.decorators import command as cli_command
from ...config import Schema

log = logging.getLogger(__name__)
ReadRegisterSubscriptionCallback = (
    Callable[[list[int]], None] | Coroutine[[list[int]], None]
)


def two_words_to_32bit_float(word1: int, word2: int, swap: bool = False):
    """Convert two 16-bit words to a 32-bit float."""
    if swap:
        word1, word2 = word2, word1
    return word1 + (word2 * 65536)


class ModbusInterface(GRPCInterface):
    """ModbusInterface is a gRPC interface for interacting with modbus devices.

    It allows for opening and closing modbus buses, reading and writing registers, and subscribing to register updates.
    It is designed to be used with the modbus_iface gRPC service.

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
        service_name: str = "doover.ModbusInterface",
        timeout: int = 7,
        config: Schema = None,
    ):
        super().__init__(app_key, modbus_uri, service_name, timeout)

        self.subscription_tasks = []
        self._setup_task = None

        self.config = config
        self.config_complete = False

    async def setup(self):
        # Buses are no longer pre-opened here. read_registers/write_registers
        # carry their bus's connection settings (resolved from config by bus name,
        # or passed explicitly), so the modbus interface opens them on demand. This
        # removes the need for openBus; see _resolve_bus_settings.
        self.config_complete = True
        config = (
            getattr(self.config, "modbus_config", None)
            if self.config is not None
            else None
        )
        if config is None:
            log.info("No modbus interfaces defined in config")

    def process_response(self, stub_call: str, response, *args, **kwargs):
        # Hand a failed response back to the caller — read/write check success
        # themselves, and the bus opens on demand from the settings each request
        # carries, so there's nothing to reconfigure. Defer to the base otherwise.
        if response is not None and not response.response_header.success:
            return response
        return super().process_response(stub_call, response, *args, **kwargs)

    async def close(self):
        log.info("Closing modbus interface")
        for task in self.subscription_tasks:
            task.cancel()
        await super().close()

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

    @staticmethod
    def _settings_from_elem(elem) -> dict:
        """Build a request's bus_settings sub-message from a ModbusConfig element."""
        try:
            bus_type = ModbusType(elem.type.value)
        except ValueError:
            return {}
        if bus_type is ModbusType.SERIAL:
            return {
                "serial_settings": modbus_iface_pb2.serialBusSettings(
                    port=elem.serial_port.value,
                    baud=elem.serial_baud.value,
                    modbus_method=elem.serial_method.value,
                    data_bits=elem.serial_bits.value,
                    parity=elem.serial_parity.value,
                    stop_bits=elem.serial_stop.value,
                    timeout=elem.serial_timeout.value,
                )
            }
        if bus_type is ModbusType.TCP:
            ip, port = elem.tcp_uri.value.split(":")
            return {
                "ethernet_settings": modbus_iface_pb2.ethernetBusSettings(
                    ip=ip, port=int(port), timeout=elem.tcp_timeout.value
                )
            }
        return {}

    def _resolve_bus_settings(self, bus=None) -> dict:
        """Connection settings attached to every read/write so the bus opens on
        demand. There is no bus id: an explicit ``bus`` (a ModbusConfig element)
        is used if given, otherwise the bus configured in the application config.
        With several configured buses, pass ``bus`` to select one.
        """
        if bus is not None:
            return self._settings_from_elem(bus)

        config = (
            getattr(self.config, "modbus_config", None)
            if self.config is not None
            else None
        )
        if isinstance(config, ModbusConfig):
            return self._settings_from_elem(config)
        if isinstance(config, ManyModbusConfig):
            elems = list(config.elements)
            if len(elems) == 1:
                return self._settings_from_elem(elems[0])
            if len(elems) > 1:
                log.warning("Multiple modbus buses configured; pass bus= to select one")
        return {}

    @cli_command()
    async def open_bus(
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
        """Open a modbus bus.

        .. deprecated::
            Buses now open on demand: pass connection settings to
            :meth:`read_registers` / :meth:`write_registers` (via ``bus`` or the
            application config) instead of pre-opening.
        """
        warnings.warn(
            "open_bus is deprecated; pass bus settings to read_registers/"
            "write_registers (buses open on demand).",
            DeprecationWarning,
            stacklevel=2,
        )
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

        resp = await self.make_request("openBus", req)
        return resp.response_header.success

    @cli_command()
    async def close_bus(self, bus_id: str = "default") -> bool:
        """Close a modbus bus.

        .. deprecated::
            Buses are pooled by the modbus interface and no longer need explicit
            closing; see :meth:`read_registers`.
        """
        warnings.warn(
            "close_bus is deprecated; buses are managed by the modbus interface.",
            DeprecationWarning,
            stacklevel=2,
        )
        req = modbus_iface_pb2.closeBusRequest(bus_id=str(bus_id))
        resp = await self.make_request("closeBus", req)
        return resp.response_header.success and resp.bus_status.open

    def _validate_read_register_resp(self, resp):
        try:
            if not resp.response_header.success:
                log.error("Error reading/writing registers")
                return False
            return True
        except Exception as e:
            log.error("Error validating read register response: " + str(e))
            return False

    @cli_command()
    async def fetch_bus_status(self, bus_id: str = "default") -> bool:
        """Get the status of a modbus bus.

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
        resp = await self.make_request("busStatus", req)
        return resp.response_header.success and resp.bus_status.open

    @staticmethod
    def _parse_register_output(values):
        if len(values) == 0:
            return None
        if len(values) == 1:
            return values[0]
        return values

    @cli_command()
    async def read_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        configure_bus: bool = True,
        bus=None,
        retries: int | None = None,
    ) -> int | list[int] | None:
        """Read registers from a modbus bus.

        Examples
        --------
        >>> self.modbus_iface.read_registers(bus_id="default", modbus_id=1, start_address=0, num_registers=10)


        Parameters
        ----------
        bus_id : str, optional
            Deprecated and ignored — kept for backwards compatibility. The bus is
            identified by its configured connection settings, not an id.
        modbus_id : int, optional
            The modbus ID of the device to read registers from (default is 1)
        start_address : int, optional
            The starting address of the registers to read (default is 0)
        num_registers : int, optional
            The number of registers to read (default is 1)
        register_type : int, optional
            The type of registers to read (default is 4, which is typically holding registers)
        configure_bus : bool, optional
            Deprecated and ignored — the bus opens on demand from the request settings.
        bus : ModbusConfig, optional
            The bus to read from. If omitted, the bus configured in the application
            config is used; pass this to select one when several are configured.
        retries : int, optional
            How many times the interface retries on failure. ``0`` fails fast (no
            retry) — useful when a failure is expected/normal. Left unset, the
            interface applies its default.

        Returns
        -------
        int | list[int] | None
            The values read from the registers.
            If only one register is read, returns an int.
            If multiple registers are read, returns a list of ints.
            If the response failed, returns None.
        """
        req = modbus_iface_pb2.readRegisterRequest(
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            count=num_registers,
            **self._resolve_bus_settings(bus),
            **({} if retries is None else {"retries": retries}),
        )
        resp = await self.make_request("readRegisters", req)
        return resp and self._parse_register_output(resp.values)

    @cli_command()
    async def write_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        values: list[int] = None,
        register_type: int = 4,
        configure_bus: bool = True,
        bus=None,
        retries: int | None = None,
    ) -> bool:
        """Write values to registers on a modbus bus.

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
            Deprecated and ignored — kept for backwards compatibility.
        modbus_id: int
            The modbus ID of the device to write registers to (default is 1)
        start_address: int
            The starting address of the registers to write (default is 0)
        values: list[int]
            Register values to write
        register_type: int
            The type of registers to write (default is 4, which is typically holding registers)
        configure_bus: bool
            Deprecated and ignored — the bus opens on demand from the request settings.
        bus : ModbusConfig, optional
            The bus to write to. If omitted, the bus configured in the application
            config is used; pass this to select one when several are configured.
        retries : int, optional
            How many times the interface retries on failure. ``0`` fails fast.
            Left unset, the interface applies its default.

        Returns
        -------
        bool
            True if the write operation was successful, False otherwise.
        """
        values = values or []
        req = modbus_iface_pb2.writeRegisterRequest(
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            values=values,
            **self._resolve_bus_settings(bus),
            **({} if retries is None else {"retries": retries}),
        )
        resp = await self.make_request("writeRegisters", req)
        return resp and self._validate_read_register_resp(resp)

    def add_read_register_subscription(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        poll_secs: int = 3,
        callback: ReadRegisterSubscriptionCallback = None,
        bus=None,
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
                    bus=bus,
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
        bus=None,
    ):
        try:
            async with grpc.aio.insecure_channel(self.uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                request = modbus_iface_pb2.readRegisterSubscriptionRequest(
                    modbus_id=modbus_id,
                    register_type=register_type,
                    **self._resolve_bus_settings(bus),
                    address=start_address,
                    count=num_registers,
                    poll_secs=poll_secs,
                )

                try:
                    async for response in stub.readRegisterSubscription(request):
                        success = response.response_header.success
                        if not self._validate_read_register_resp(response):
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
    async def test_comms(self, message: str = "Comms Check Message") -> str | None:
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
        return await self.make_request(
            "testComms",
            modbus_iface_pb2.testCommsRequest(message=message),
            response_field="response",
        )


modbus_iface = ModbusInterface
