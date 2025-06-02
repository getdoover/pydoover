import asyncio
import logging
import time
import json

from collections.abc import Iterable, Coroutine
from typing import Callable

import grpc

from .grpc_stubs import platform_iface_pb2, platform_iface_pb2_grpc
from .types import Location, Event
from ..grpc_interface import GRPCInterface
from ...utils import maybe_async, call_maybe_async, deprecated
from ...cli.decorators import command as cli_command

log = logging.getLogger(__name__)
PulseCounterCallback = (
    Callable[[int, bool, int, int, str], None]
    | Coroutine[[int, bool, int, int, str], None]
)


class PulseCounter:
    """PulseCounter object for counting pulses on a digital input pin.

    This is generally not created manually, but rather through the PlatformInterface's `get_new_pulse_counter` method.

    Attributes
    ----------
    platform_iface : PlatformInterface
        The platform interface to use for communication.
    pin : int
        The digital input pin number to listen for pulses on.
    edge : str
        The edge to listen for pulses on. Can be "rising", "falling", or "both".
    callback : Callable[[int, bool, int, int, str], Any]
        A callback function to call when a pulse is received. The function should take the following arguments:
            - pin: int - The pin number the pulse was received on.
            - di_value: bool - The value of the digital input pin (1 for high, 0 for low).
            - dt_secs: int - The time since the last pulse in seconds.
            - count: int - The total number of pulses received.
            - edge: str - The edge that the pulse was received on ("rising" or "falling").
        This function can be synchronous or asynchronous.
    rate_window_secs : int
        The size of the window in seconds for which the rate of pulses is calculated.
    count : int
        The total number of pulses received.
    pulse_timestamps : list[float]
        A list of timestamps for each pulse received.
    receiving_pulses : bool
        Whether the PulseCounter is currently receiving pulses.

    """

    def __init__(
        self,
        plt_iface: "PlatformInterface",
        pin: int,
        edge: str = "rising",
        callback: PulseCounterCallback = None,
        rate_window_secs: int = 60,
        auto_start: bool = True,
    ):
        self.platform_iface = plt_iface
        self.pin = pin
        self.edge = edge
        self.callback = callback
        self.rate_window_secs = rate_window_secs
        self.count = 0

        self.start_time = time.time()
        self.pulse_grace_period = (
            0.2  # Need to ignore pulses for a short period after starting
        )
        self.pulse_timestamps = []

        self.receiving_pulses = False
        self.receiving_events = False

        if auto_start:
            self.start_listener_pulses()

    @deprecated("Replaced with PulseCounter.start_listener_pulses")
    def start_listener(self):
        self.start_listener_pulses()

    def start_listener_pulses(self):
        """Start listening for pulses on the digital input pin."""
        # Check each pulse counter is only used for a single type of pulse
        if self.receiving_events:
            log.error("Using a pulse counter for both pulses and offline events")
            return
        self.receiving_pulses = True

        self.start_time = time.time()
        self.platform_iface.start_di_pulse_listener(
            self.pin, self.receive_pulse, edge=self.edge, start_count=self.count
        )

    def update_events(self):
        """Listen for offline events for a digital input pin.

        This is **not** compatible with a PulseCounter that is already receiving pulses.
        """
        # Check each pulse counter is only used for a single type of pulse
        if self.receiving_pulses:
            log.error("Using a pulse counter for both pulses and offline events")
            return
        self.receiving_events = True
        self.receive_events(
            self.platform_iface.get_di_events(
                self.pin, self.edge, include_system_events=True
            )
        )

    def add_existing_events(self, time_stamps):
        # Check each pulse counter is only used for a single type of pulse
        if self.receiving_pulses:
            log.error("Using a pulse counter for both pulses and offline events")
            return
        self.receiving_events = True

        self.pulse_timestamps += time_stamps
        self.count = len(self.pulse_timestamps)

    async def receive_pulse(self, di, di_value, dt_secs, counter, edge):
        """Receive active pulses on the digital input pin.

        This is **not** compatible with a PulseCounter that is already receiving events.
        """
        # Check each pulse counter is only used for a single type of pulse
        if self.receiving_events:
            log.error("Using a pulse counter for both pulses and offline events")
            return
        self.receiving_pulses = True

        if time.time() - self.start_time < self.pulse_grace_period:
            log.info(f"Ignoring pulse on di={di} with dt={dt_secs}s")
            return

        log.info(f"Received pulse on di={di} with dt={dt_secs}s")
        self.count += 1
        self.pulse_timestamps += [time.time()]
        if self.callback is not None:
            await call_maybe_async(
                self.callback, self.pin, di_value, dt_secs, self.count, edge
            )

    def receive_events(self, events):
        # Check each pulse counter is only used for a single type of pulse
        if self.receiving_pulses:
            log.error("Using a pulse counter for both pulses and offline events")
            return
        self.receiving_events = True

        for event in events:
            edge = ""
            di_value = 0
            if event.event == "DI_R":
                di_value = 1
                edge = "rising"
            elif event.event == "DI_F":
                edge = "falling"
            elif event.event == "VI":
                event = "VI"
            else:  # Could be a system event
                self.handle_system_event(event)
                continue

            timestamp = event.time / 1000 or time.time()
            dt_secs = 0
            if len(self.pulse_timestamps) > 0:
                if timestamp <= self.pulse_timestamps[-1] + 0.01:
                    log.warning(
                        f"Ignoring old event on di={event.pin} t={timestamp} latest event: {self.pulse_timestamps[-1]}"
                    )
                    continue
                dt_secs = timestamp - self.pulse_timestamps[-1]
            log.info(f"Received event on di={event.pin} with t={dt_secs}s")
            self.count += 1
            self.pulse_timestamps += [timestamp]
            if self.callback is not None:
                self.callback(self.pin, di_value, dt_secs, timestamp, self.count, edge)

    def handle_system_event(self, event: str):
        """This is called when a system event occurs. You can override this to handle system events as needed."""

    @deprecated("Use get_pulses_in_window to not damage record of pulses/events")
    def clean_pulse_timestamps(self):
        if len(self.pulse_timestamps) == 0:
            return

        ## Remove timestamps older than the rate window
        while (
            len(self.pulse_timestamps) > 0
            and self.pulse_timestamps[0] < time.time() - self.rate_window_secs
        ):
            self.pulse_timestamps.pop(0)

    def get_pulses_in_window(self):
        if len(self.pulse_timestamps) == 0:
            return []

        pulses = []
        ## Remove timestamps older than the rate window
        for timestamp in self.pulse_timestamps:
            if timestamp > self.pulse_timestamps[-1] - self.rate_window_secs:
                pulses.append(timestamp)
        return pulses

    def set_rate_window(self, rate_window_secs):
        self.rate_window_secs = rate_window_secs

    def get_rate_window(self):
        return self.rate_window_secs

    def get_pulses_per_minute(self):
        pulses = self.get_pulses_in_window()
        return len(pulses) * 60 / self.rate_window_secs

    def set_counter(self, counter):
        self.count = counter

    def get_counter(self):
        return self.count


class PlatformInterface(GRPCInterface):
    """Docker interface for interacting with the platform interface container.

    This interface allows you to interact with the platform interface gRPC service, providing access to device IO.

    Some implementations are platform-specific, and it is your responsibility to ensure that all hardware that your
    application is compatible with implements the methods you are trying to fetch. Most methods will return `None`
    if they are not supported or you pass a bad input.

    An example of bad input is requesting Digital Input #10 on a Doovit that only supports 4.
    """

    stub = platform_iface_pb2_grpc.platformIfaceStub

    def __init__(
        self, app_key: str, plt_uri: str = "localhost:50053", is_async: bool = False
    ):
        super().__init__(app_key, plt_uri, is_async)
        self.pulse_counter_listeners = []

    async def close(self):
        log.info("Closing platform interface...")
        for listener in self.pulse_counter_listeners:
            listener.cancel()

    def process_response(self, stub_call: str, response, **kwargs):
        response = super().process_response(stub_call, response, **kwargs)

        try:
            response_field = kwargs.pop("response_field")
        except KeyError:
            return response

        res = getattr(response, response_field, None)
        if isinstance(res, Iterable) and not isinstance(
            res, str
        ):  # don't iterate over strings
            res = list(res)

        if isinstance(res, list) and len(res) == 1:
            return res[0]

        return res

    def get_new_pulse_counter(
        self,
        di: int,
        edge: str = "rising",
        callback: PulseCounterCallback = None,
        rate_window_secs: int = 20,
        auto_start: bool = True,
    ) -> PulseCounter:
        """Create a new Pulse Counter for counting pulses on a digital input pin.

        Examples
        --------

        Basic pulse counter::

            def pulse_callback(di, di_value, dt_secs, count, edge):
                print(f"Pulse on di={di} with value={di_value}, dt={dt_secs}s, count={count}, edge={edge}")

            counter = self.platform_interface.get_new_pulse_counter(0, "rising", callback=pulse_callback)


        Parameters
        ----------
        di: int
            Digital input pin to listen for pulses on.
        edge: "rising" or "falling" or "both"
            The edge to listen for pulses on.
        callback : Callable
            Callback function to call when a pulse is received.
            The function should take the following arguments
            - di: int - The pin number the pulse was received on.
            - di_value: bool - The value of the digital input pin (1 for high, 0 for low).
            - dt_secs: int - The time since the last pulse in seconds.
            - count: int - The total number of pulses received.
            - edge: str - The edge that the pulse was received on ("rising" or "falling").
            The callback can be synchronous or asynchronous.

        rate_window_secs: int
            The size of window for which the rate of pulses is calculated. Default is 20.
        auto_start: bool
            Whether to automatically start listening for pulses. Default is True.
        """

        return PulseCounter(
            self,
            di,
            edge=edge,
            callback=callback,
            rate_window_secs=rate_window_secs,
            auto_start=auto_start,
        )

    def get_new_event_counter(
        self,
        di: int,
        edge: str = "rising",
        callback: PulseCounterCallback = None,
        rate_window_secs: int = 20,
        auto_collect: bool = True,
    ) -> PulseCounter:
        """Create a new Pulse Counter for counting events.

        Examples
        --------

        Basic event counter::

            counter = self.platform_interface.get_new_event_counter(0, "rising")
            print(counter.get_counter())
            print(counter.get_pulses_per_minute())


        Parameters
        ----------
        di : int
            Pin number to check events for.
        edge : "rising" or "falling" or "both"
            The edge to listen to evenets on.
        callback : PulseCounterCallback
            Callback called when an event is processed.
        rate_window_secs : int = 20
            The size of window for which the rate of events is calculated.
        auto_collect : bool = True
            Whether to automatically collect the events from the platform interface.

        Returns
        -------
        PulseCounter
            The pulse counter object for the given pin.
        """
        counter = PulseCounter(
            self,
            di,
            edge=edge,
            callback=callback,
            rate_window_secs=rate_window_secs,
            auto_start=False,
        )
        if auto_collect:
            counter.update_events()
        return counter

    def start_di_pulse_listener(
        self, di: int, callback, edge: str = "rising", start_count: int = 0
    ):
        ## Callback should be a function that takes the following arguments:
        ## di, di_value, dt_secs, counter, edge

        listener = asyncio.create_task(
            self.recv_di_pulses(di, callback, edge=edge, start_count=start_count)
        )
        self.pulse_counter_listeners.append(listener)
        listener.add_done_callback(self.pulse_counter_listeners.remove)

    async def recv_di_pulses(
        self, di: int, callback, edge: str = "rising", start_count: int = 0
    ):
        counter = start_count
        active_callbacks = set()

        while True:
            try:
                # Setup the connection to the platform interface
                async with grpc.aio.insecure_channel(self.uri) as channel:
                    channel_stream = platform_iface_pb2_grpc.platformIfaceStub(
                        channel
                    ).startPulseCounter(
                        platform_iface_pb2.pulseCounterRequest(di=di, edge=edge)
                    )

                    while True:
                        response: platform_iface_pb2.pulseCounterResponse = (
                            await channel_stream.read()
                        )
                        if response is None or response == grpc.aio.EOF:
                            log.info(f"pulseCounter for di={di} ended.")
                            break

                        log.debug(f"Received response from pulseCounter for di={di}")
                        if (
                            hasattr(response, "dt_secs")
                            and response.dt_secs is not None
                            and response.dt_secs > 0
                        ):
                            ## Increment the counter
                            counter += 1
                            ## Call the callback function with the response
                            task = await call_maybe_async(
                                callback,
                                di,
                                response.value,
                                response.dt_secs,
                                counter,
                                edge,
                                as_task=True,
                            )
                            if task:
                                active_callbacks.add(task)
                                task.add_done_callback(active_callbacks.remove)

            except asyncio.CancelledError:
                log.info(f"pulseCounter for di={di} cancelled.")
                break

            except StopAsyncIteration:
                log.info(f"pulseCounter for di={di} ended.")
                break

            except Exception as e:
                log.error(f"Error receiving pulse for di={di}: {e}", exc_info=e)
                # await asyncio.sleep(1)

            ## Loop again
            await asyncio.sleep(1)

        ## Wait for all active callbacks to finish
        while active_callbacks:
            await asyncio.wait(active_callbacks, timeout=1)

    @staticmethod
    def _cast_pins(pins):
        if isinstance(pins, int):
            return [pins]
        elif isinstance(pins, list):
            return pins
        else:
            raise ValueError(
                f"Invalid type for pins: {type(pins)}. Must be int or list."
            )
            # log.error(f"Invalid type for pins: {type(pins)}. Must be int or list."
            # return None

    @staticmethod
    def _cast_values(values):
        if isinstance(values, int):
            return [bool(values)]
        elif isinstance(values, list):
            return [bool(v) for v in values]
        else:
            raise ValueError(
                f"Invalid type for values: {type(values)}. Must be bool or list."
            )

    @staticmethod
    def _cast_ao_values(values):
        if isinstance(values, int):
            return [float(values)]
        elif isinstance(values, float):
            return [values]
        elif isinstance(values, list):
            return [float(v) for v in values]
        else:
            raise ValueError(
                f"Invalid type for values: {type(values)}. Must be float or list."
            )

    def _cast_ao_pin_values(self, pins, values):
        pins = self._cast_pins(pins)
        values = self._cast_ao_values(values)

        if len(pins) != len(values):
            if len(values) == 1:
                values = [values[0]] * len(pins)
            else:
                raise ValueError(
                    "Analogue output and value lists are not the same length."
                )

        return pins, values

    def _cast_pin_values(self, pins, values):
        pins = self._cast_pins(pins)
        values = self._cast_values(values)

        if len(pins) != len(values):
            if len(values) == 1:
                values = [values[0]] * len(pins)
            else:
                raise ValueError(
                    "Digital output and value lists are not the same length."
                )

        return pins, values

    @cli_command()
    def test_comms(self, message: str = "Comms Check Message") -> str | None:
        """Test connection by sending a basic echo response to platform interface container.

        Parameters
        ----------
        message : str
            Message to send to platform interface to have echo'd as a response

        Returns
        -------
        str
            The response from platform interface.
        """
        return self.make_request(
            "TestComms",
            platform_iface_pb2.TestCommsRequest(message=message),
            response_field="response",
        )

    @cli_command()
    @maybe_async()
    def get_di(self, *di: int) -> bool | list[bool]:
        """Get digital input values.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Get a single digital input pin value::

            pin1 = await self.platform_iface.get_di(1)

        Get digital input pins 1, 2 and 3 in the same transaction::

            pin1, pin2, pin3 = await self.platform_iface.get_di(1, 2, 3)

        Parameters
        ----------
        *di
            Pin numbers to get the values of. Can be one or more integers.

        Returns
        -------
        bool | list[bool]
            Returns one or more booleans where True means the pin is high (1) and False means the pin is low (0).
            If you requested one pin, returns a single value.
            If you requested more than one pin, returns a list of values.
            Returns None if the request failed.
        """
        pins = self._cast_pins(di)
        return self.make_request(
            "getDI", platform_iface_pb2.getDIRequest(di=pins), response_field="di"
        )

    async def get_di_async(self, *di: int) -> bool | list[bool]:
        pins = self._cast_pins(di)
        return await self.make_request_async(
            "getDI", platform_iface_pb2.getDIRequest(di=pins), response_field="di"
        )

    @cli_command()
    @maybe_async()
    def get_ai(self, *ai: int) -> float | list[float]:
        """Get analogue input values.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Get a single analogue input pin value::

            pin1 = await self.platform_iface.get_ai(1)

        Get analogue input pins 1, 2 and 3 in the same transaction::

            pin1, pin2, pin3 = await self.platform_iface.get_ai(1, 2, 3)

        Parameters
        ----------
        *ai
            Pin numbers to get the values of. Can be one or more integer pin mumber.

        Returns
        -------
        float | list[float]
            If you requested one analog input, returns a single value.
            If you requested more than one pin, returns a list of values.
            Returns None if the request failed.
        """
        # Above section is to facilitate the following:
        # get_ai(1)
        # get_ai([1,4,2])

        # Proposal: get_ai(*pins)
        # allows for get_ai(1, 2, 3) or get_ai(1) or get_ai(*[1, 2, 3])

        pins = self._cast_pins(ai)
        return self.make_request(
            "getAI", platform_iface_pb2.getAIRequest(ai=pins), response_field="ai"
        )

    async def get_ai_async(self, *ai: int) -> float | list[float]:
        pins = self._cast_pins(ai)
        return await self.make_request_async(
            "getAI", platform_iface_pb2.getAIRequest(ai=pins), response_field="ai"
        )

    @cli_command()
    @maybe_async()
    def get_do(self, *do: int) -> list[bool] | None:
        """Get digital output values.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Get a single digital output pin value::

            await self.platform_iface.get_do(1)


        Get digital output pins 1, 2 and 3 in the same transaction::

            await self.platform_iface.get_do(1, 2, 3)

        Parameters
        ----------
        *do
            Pin numbers to get the values of. Can be one or more integers.

        Returns
        -------
        bool | list[bool]
            If you requested one, returns a single value.
            If you requested more than one pin, returns a list of values.
            Returns None if the request failed.
        """
        pins = self._cast_pins(do)
        return self.make_request(
            "getDO", platform_iface_pb2.getDORequest(do=pins), response_field="do"
        )

    async def get_do_async(self, *do: int) -> float | list[float]:
        pins = self._cast_pins(do)
        return await self.make_request_async(
            "getDO", platform_iface_pb2.getDORequest(do=pins), response_field="do"
        )

    @cli_command()
    @maybe_async()
    def set_do(self, do: int | list[int], value: int | list[int]) -> list[bool] | None:
        """Set digital output values.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Set a single digital output pin value::

            await self.platform_iface.set_do(1, True)

        Set digital output pin 2 to low and 3 to high in a single transaction::

            await self.platform_iface.set_do([2, 3], [False, True])

        Parameters
        ----------
        do : Union[int, list[int]]
            Pin numbers to set the values of. Can be a single pin number or a list of pin numbers.
        value : Union[int, list[int]]
            Values to set the pins to. Can be a single value or a list of values.
            If a single value is provided, all pins will be set to that value.

        .. note::
            The length of the `do` and `value` lists must be the same!

        Returns
        -------
        list[bool]
            A list of digital output values that were set.
            This should ordinarily return all `True` values.
            Returns None if the request failed.
        """
        pins, values = self._cast_pin_values(do, value)
        return self.make_request(
            "setDO",
            platform_iface_pb2.setDORequest(do=pins, value=values),
            response_field="do",
        )

    async def set_do_async(self, do, value):
        pins, values = self._cast_pin_values(do, value)
        return await self.make_request_async(
            "setDO",
            platform_iface_pb2.setDORequest(do=pins, value=values),
            response_field="do",
        )

    @cli_command()
    @maybe_async()
    def schedule_do(
        self, do: int | list[int], value: bool | list[bool], in_secs: int
    ) -> None:
        """Schedule digital output values.

        This is similar to `set_do`, but schedules the change in a specified number of seconds.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Schedule a single digital output pin to be set high in 10 seconds::

            await self.platform_iface.schedule_do(1, True, 10)  # Set digital output pin 1 to high in 10 seconds


        Schedule multiple pins in 5 seconds::

            await self.platform_iface.schedule_do([2, 3], [False, True], 5)

        Parameters
        ----------
        do : Union[int, list[int]]
            Pin numbers to set the values of. Can be a single pin number or a list of pin numbers.
        value : Union[bool, list[bool]]
            Values to set the pins to. Can be a single value or a list of values.
            If a single value is provided, all pins will be set to that value.
        in_secs : int
            Time in seconds to schedule the change in digital output values. Must be positive.
        """
        if not isinstance(in_secs, int) or in_secs < 0:
            raise ValueError(
                f"Invalid value for in_secs: {in_secs}. Must be a positive integer."
            )

        pins, values = self._cast_pin_values(do, value)

        # Above section is to facilitate the following:
        # schedule_do(1, 1, 1) => [1],[1],1
        # schedule_do([1,4,2], 0, 1) => [1,4,2], [0,0,0], 1
        # schedule_do([1,4,2], [0,1,0], 1) => [1,4,2], [0,1,0], 1

        return self.make_request(
            "scheduleDO",
            platform_iface_pb2.scheduleDORequest(
                do=pins, value=values, time_secs=in_secs
            ),
            response_field="do",
        )

    async def schedule_do_async(
        self, do: int | list[int], value: bool | list[bool], in_secs: int
    ) -> None:
        if not isinstance(in_secs, int) or in_secs < 0:
            raise ValueError(
                f"Invalid value for in_secs: {in_secs}. Must be a positive integer."
            )

        pins, values = self._cast_pin_values(do, value)
        return await self.make_request_async(
            "scheduleDO",
            platform_iface_pb2.scheduleDORequest(
                do=pins, value=values, time_secs=in_secs
            ),
            response_field="do",
        )

    @cli_command()
    @maybe_async()
    def get_ao(self, *ao: int) -> float | list[float]:
        """Get analogue output values.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Get a single analogue output pin value::

            pin1 = await self.platform_iface.get_ao(1)

        Get analogue output pins 1, 2 and 3 in the same transaction::

            await self.platform_iface.get_ao(1, 2, 3)

        Parameters
        ----------
        *ao
            Pin numbers to get the values of. Must be an integer.

        Returns
        -------
        tuple[float] | float
            If you requested multiple pins, returns a tuple of values.
            Otherwise, returns a single float.
            If the request failed, returns None.
        """
        pins = self._cast_pins(ao)
        return self.make_request(
            "getAO", platform_iface_pb2.getAORequest(ao=pins), response_field="ao"
        )

    async def get_ao_async(self, *ao: int) -> float | list[float]:
        pins = self._cast_pins(ao)
        return await self.make_request_async(
            "getAO", platform_iface_pb2.getAORequest(ao=pins), response_field="ao"
        )

    @cli_command()
    @maybe_async()
    def set_ao(
        self, ao: int | list[int], value: float | list[float]
    ) -> list[bool] | None:
        """Set analogue output values.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Set a single analogue output pin 1 to 3.3V::

            await self.platform_iface.set_ao(1, 3.3)

        Set analogue output pins 2 and 3 to 1.5V and 2.5V in a single transaction::

            await self.platform_iface.set_ao([2, 3], [1.5, 2.5])


        Parameters
        ----------
        ao : int or list[int]
            Pin numbers to set the values of. Can be a single pin number or a list of pin numbers.

        value : bool or list[bool]
            Values to set the pins to. Can be a single value or a list of values.
            If a single value is provided, all pins will be set to that value.

        Returns
        -------
        list[bool]
            List of boolean values indicating whether the analogue outputs were set successfully.
        """

        # if not isinstance(value, list):
        #     value = [value]
        pins, values = self._cast_ao_pin_values(ao, value)
        return self.make_request(
            "setAO",
            platform_iface_pb2.setAORequest(ao=pins, value=values),
            response_field="ao",
        )

    async def set_ao_async(
        self, ao: int | list[int], value: float | list[float]
    ) -> list[bool]:
        pins, values = self._cast_ao_pin_values(ao, value)
        return await self.make_request_async(
            "setAO",
            platform_iface_pb2.setAORequest(ao=pins, value=values),
            response_field="ao",
        )

    @cli_command()
    @maybe_async()
    def schedule_ao(
        self, ao: int | list[int], value: bool | list[bool], in_secs: int
    ) -> None:
        """Schedule analogue output values.

        This is similar to `set_ao`, but schedules the change in a specified number of seconds.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Schedule a single analogue output pin 1 to be set to 3.3V in 10 seconds::

            await self.platform_iface.schedule_ao(1, 3.3, 10)  # Set analogue output pin 1 to 3.3V in 10 seconds


        Schedule multiple analogue output pins in 5 seconds::

            await self.platform_iface.schedule_ao([2, 3], [1.5, 2.5], 5)  # Set analogue output pins 2 and 3 to 1.5V and 2.5V respectively.


        Parameters
        ----------
        ao : int or list[int]
            Pin numbers to set the values of. Can be a single pin number or a list of pin numbers.
        value : float or list[float]
            Values to set the pins to. Can be a single value or a list of values.
            If a single value is provided, all pins will be set to that value.
        in_secs : int
            Time in seconds to schedule the change in analogue output values. Must be positive.
        """
        if not isinstance(in_secs, int) or in_secs < 0:
            raise ValueError(
                f"Invalid value for in_secs: {in_secs}. Must be a positive integer."
            )

        pins, values = self._cast_ao_pin_values(ao, value)

        # Above section is to facilitate the following:
        # schedule_ao(1, 1, 1) => [1],[1],1
        # schedule_ao([1,4,2], 0, 1) => [1,4,2], [0,0,0], 1
        # schedule_ao([1,4,2], [0,1,0], 1) => [1,4,2], [0,1,0], 1
        return self.make_request(
            "scheduleAO",
            platform_iface_pb2.scheduleAORequest(
                ao=pins, value=values, time_secs=in_secs
            ),
            response_field="ao",
        )

    async def schedule_ao_async(
        self, ao: int | list[int], value: bool | list[bool], in_secs: int
    ) -> None:
        if not isinstance(in_secs, int) or in_secs < 0:
            raise ValueError(
                f"Invalid value for in_secs: {in_secs}. Must be a positive integer."
            )

        pins, values = self._cast_ao_pin_values(ao, value)
        return await self.make_request_async(
            "scheduleAO",
            platform_iface_pb2.scheduleAORequest(
                ao=pins, value=values, time_secs=in_secs
            ),
            response_field="ao",
        )

    @cli_command()
    @maybe_async()
    def get_system_voltage(self) -> float:
        """Get the system input voltage.

        This is the voltage supplied to the system, typically from a power supply or battery.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Get the system input voltage::

            voltage = await self.platform_iface.get_system_voltage()


        Returns
        -------
        float
            The system input voltage in volts. Returns None if the request failed.
        """
        return self.make_request(
            "getInputVoltage",
            platform_iface_pb2.getInputVoltageRequest(),
            response_field="voltage",
        )

    async def get_system_voltage_async(self) -> float:
        return await self.make_request_async(
            "getInputVoltage",
            platform_iface_pb2.getInputVoltageRequest(),
            response_field="voltage",
        )

    @cli_command()
    @maybe_async()
    def get_system_temperature(self) -> float:
        """Get the system temperature.

        On a Doovit, this is the temperature of the Raspberry Pi CM4.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Print the system temperature::

            temperature = await self.platform_iface.get_system_temperature()
            print(f"System temperature: {temperature}°C")


        Returns
        -------
        float
            The system temperature in degrees Celsius. Returns None if the request failed.
        """
        return self.make_request(
            "getTemperature",
            platform_iface_pb2.getTemperatureRequest(),
            response_field="temperature",
        )

    async def get_system_temperature_async(self):
        return await self.make_request_async(
            "getTemperature",
            platform_iface_pb2.getTemperatureRequest(),
            response_field="temperature",
        )

    @cli_command()
    @maybe_async()
    def get_location(self) -> Location:
        """Get the device location.

        Doovits with 4G cards generally implement this using the ModemManager (mmcli).

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Print the current location::

            location = await self.platform_iface.get_location()
            print(f"Latitude: {location.latitude}, Longitude: {location.longitude}, Altitude: {location.altitude}")


        Returns
        -------
        :class:`pydoover.docker.platform.Location`
            The location of the device.
            Returns None if the request failed.
        """
        return self.make_request(
            "getLocation",
            platform_iface_pb2.getLocationRequest(),
            response_field="location",
        )

    async def get_location_async(self) -> Location:
        return await self.make_request_async(
            "getLocation",
            platform_iface_pb2.getLocationRequest(),
            response_field="location",
        )

    @cli_command()
    @maybe_async()
    def reboot(self):
        """Reboot the device.

        You should **not** call this method directly, instead see
        [guide for shutting down](https://docs.doover.com/guide/app-shutdown)
        for more information on how to safely initiate a shutdown in an application.
        """
        return self.make_request("reboot", platform_iface_pb2.rebootRequest())

    async def reboot_async(self):
        # fixme: should these have async varients?
        return await self.make_request_async(
            "reboot", platform_iface_pb2.rebootRequest()
        )

    @cli_command()
    @maybe_async()
    def shutdown(self):
        """Shutdown the device.

        You should **not** call this method directly, instead see
        [guide for shutting down](https://docs.doover.com/guide/app-shutdown)
        for more information on how to safely initiate a shutdown in an application.
        """
        return self.make_request("shutdown", platform_iface_pb2.shutdownRequest())

    async def shutdown_async(self):
        # fixme: as above
        return await self.make_request_async(
            "shutdown", platform_iface_pb2.shutdownRequest()
        )

    @cli_command()
    @maybe_async()
    def get_immunity_seconds(self) -> float:
        """Get the number of seconds the device is immune for.

        Immunity is the time for which the device will ignore any shutdown requests.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Examples
        --------

        Print the number of seconds the device is immune for::

            immunity_secs = await self.platform_iface.get_immunity_seconds()
            print(f"Device immune for: {immunity_secs} seconds")


        Returns
        -------
        float
            The number of seconds the device is immune for.
        """
        return self.make_request(
            "getShutdownImmunity",
            platform_iface_pb2.getShutdownImmunityRequest(),
            response_field="immunity_secs",
        )

    async def get_immunity_seconds_async(self):
        return await self.make_request_async(
            "getShutdownImmunity",
            platform_iface_pb2.getShutdownImmunityRequest(),
            response_field="immunity_secs",
        )

    @maybe_async()
    def schedule_startup(self, time_secs: int) -> None:
        return self.make_request(
            "scheduleStartup",
            platform_iface_pb2.scheduleStartupRequest(time_secs=time_secs),
            response_field="time_secs",
        )

    async def schedule_startup_async(self, time_secs: int) -> None:
        return await self.make_request_async(
            "scheduleStartup",
            platform_iface_pb2.scheduleStartupRequest(time_secs=time_secs),
            response_field="time_secs",
        )

    @cli_command()
    @maybe_async()
    def schedule_shutdown(self, time_secs: int) -> None:
        return self.make_request(
            "scheduleShutdown",
            platform_iface_pb2.scheduleShutdownRequest(time_secs=time_secs),
            response_field="time_secs",
        )

    async def schedule_shutdown_async(self, time_secs: int) -> None:
        return await self.make_request_async(
            "scheduleShutdown",
            platform_iface_pb2.scheduleShutdownRequest(time_secs=time_secs),
            response_field="time_secs",
        )

    @cli_command()
    @maybe_async()
    def get_io_table(self):
        res = self.make_request(
            "getIoTable",
            platform_iface_pb2.getIoTableRequest(),
            response_field="io_table",
        )
        # result = json.loads("".join(self.make_request("getIoTable", platform_iface_pb2.getIoTableRequest())))
        if res is None:
            return None
        string = ""
        for i in res:
            string += i
        result = json.loads(string)
        return result

    async def get_io_table_async(self):
        res = await self.make_request_async(
            "getIoTable",
            platform_iface_pb2.getIoTableRequest(),
            response_field="io_table",
        )
        # result = json.loads("".join(await self.make_request_async("getIoTable", platform_iface_pb2.getIoTableRequest())))
        if res is None:
            return None
        string = ""
        for i in res:
            string += i
        result = json.loads(string)
        return result

    @cli_command()
    @maybe_async()
    def sync_rtc(self):
        """Synchronize the real-time clock (RTC) with the system (network) time.

        For Doovits, you shouldn't need to do this as this is handled automatically by `doovitd`.

        .. note:: This method can be used in both synchronous and asynchronous contexts.
        """
        return self.make_request("syncRtcTime", platform_iface_pb2.syncRtcTimeRequest())

    async def sync_rtc_async(self):
        return await self.make_request(
            "syncRtcTime", platform_iface_pb2.syncRtcTimeRequest()
        )

    @maybe_async()
    def get_events(self, events_from: int = 0):
        """Get all events.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Parameters
        ----------
        events_from : None or int
            Starting event id or timestamp (in milliseconds), defaults to all availible.

        Returns
        -------
        List[:class:`pydoover.docker.platform.Event`]
            List of events.
        """
        return self.make_request(
            "getEvents",
            platform_iface_pb2.getEventsRequest(events_from=events_from),
            response_field="events",
        )

    async def get_events_async(self, events_from=0):
        return await self.make_request_async(
            "getEvents",
            platform_iface_pb2.getEventsRequest(events_from=events_from),
            response_field="events",
        )

    @cli_command()
    @maybe_async()
    def get_di_events(
        self,
        di_pin: int,
        edge: str,
        include_system_events: bool = False,
        events_from: int = 0,
    ) -> list[Event]:
        """Get digital input events.

        .. note:: This method can be used in both synchronous and asynchronous contexts.

        Parameters
        ----------
        di_pin : int
            Pin number to check events for.
        edge : "rising" or "falling" or "both"
            The edge to listen to events on.
        include_system_events : bool = False
            Whether to include system events like for a doovit the cm4 turning on and off or the io board starting up.
        events_from : None or int
            Starting event id or timestamp (in milliseconds), defaults to all availible.

        Returns
        -------
        List[:class:`pydoover.docker.platform.Event`]
            List of events for the given digital input pin.
        """
        rising = False
        falling = False
        if edge == "rising":
            rising = True
        elif edge == "falling":
            falling = True
        elif edge == "both":
            rising = True
            falling = True
        return self.make_request(
            "getDIEvents",
            platform_iface_pb2.getDIEventsRequest(
                pin=di_pin,
                rising=rising,
                falling=falling,
                include_system_events=include_system_events,
                events_from=events_from,
            ),
        )

    async def get_di_events_async(
        self,
        di_pin: int,
        edge: str,
        include_system_events: bool = False,
        events_from: int = 0,
    ) -> list[Event]:
        rising = False
        falling = False
        if edge == "rising":
            rising = True
        elif edge == "falling":
            falling = True
        elif edge == "both":
            rising = True
            falling = True
        return await self.make_request_async(
            "getDIEvents",
            platform_iface_pb2.getDIEventsRequest(
                pin=di_pin,
                rising=rising,
                falling=falling,
                include_system_events=include_system_events,
                events_from=events_from,
            ),
            response_field="events",
        )


platform_iface = PlatformInterface
pulse_counter = PulseCounter
