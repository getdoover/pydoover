"""Tests for PlatformInterface.fetch_di_readings.

Two contracts are under test, and both are about telling "no counter" apart
from "counter reading zero":

* proto3 presence — `pulse_count` absent means the pin cannot count, present
  and 0 means it can and has not yet. An app totalising a flow meter must not
  see a phantom zero on a pin with no hardware.
* graceful degrade — an older platform interface does not know the `readings`
  field and answers with levels only. That has to come back as readings with
  counts unavailable, not as an empty list an app would index into.
"""

import asyncio

import pytest

from pydoover.docker.platform import PlatformInterface
from pydoover.docker.platform.platform_types import DIReading
from pydoover.models.generated.platform import platform_iface_pb2


def make_interface(response):
    """A PlatformInterface whose transport is replaced by a canned response."""
    iface = PlatformInterface.__new__(PlatformInterface)
    iface.requests = []

    async def fake_request(stub_call, request, **kwargs):
        iface.requests.append((stub_call, request, kwargs))
        return response

    iface.make_request = fake_request
    iface._cast_pins = lambda di: list(di)
    return iface


def fetch(iface, *pins):
    return asyncio.run(iface.fetch_di_readings(*pins))


class TestRequest:
    def test_asks_for_pulses(self):
        """Without the flag the platform skips the counter read entirely."""
        iface = make_interface(platform_iface_pb2.getDIResponse(di=[True]))
        fetch(iface, 0)
        _, request, _ = iface.requests[0]
        assert request.include_pulses is True
        assert list(request.di) == [0]


class TestPresence:
    def test_a_counting_pin(self):
        iface = make_interface(
            platform_iface_pb2.getDIResponse(
                di=[False],
                readings=[
                    platform_iface_pb2.DIReading(
                        pin=1, value=False, pulse_count=1187, pulse_rate_hz=4.25
                    )
                ],
            )
        )
        (reading,) = fetch(iface, 1)
        assert reading == DIReading(
            pin=1, value=False, pulse_count=1187, pulse_rate_hz=pytest.approx(4.25)
        )

    def test_zero_pulses_is_not_no_counter(self):
        iface = make_interface(
            platform_iface_pb2.getDIResponse(
                di=[True],
                readings=[
                    platform_iface_pb2.DIReading(pin=0, value=True, pulse_count=0)
                ],
            )
        )
        (reading,) = fetch(iface, 0)
        # 0, not None: this pin counts and has seen nothing yet.
        assert reading.pulse_count == 0
        assert reading.pulse_count is not None

    def test_a_pin_without_a_counter_reports_none(self):
        iface = make_interface(
            platform_iface_pb2.getDIResponse(
                di=[True],
                readings=[platform_iface_pb2.DIReading(pin=5, value=True)],
            )
        )
        (reading,) = fetch(iface, 5)
        assert reading.pulse_count is None
        assert reading.pulse_rate_hz is None

    def test_a_count_without_a_rate(self):
        """Platforms that count but cannot measure rate leave it unset."""
        iface = make_interface(
            platform_iface_pb2.getDIResponse(
                di=[True],
                readings=[
                    platform_iface_pb2.DIReading(pin=0, value=True, pulse_count=500)
                ],
            )
        )
        (reading,) = fetch(iface, 0)
        assert reading.pulse_count == 500
        assert reading.pulse_rate_hz is None

    def test_mixed_support_in_one_call(self):
        """A Quantum: DIO1-4 count, DIO5-8 do not."""
        iface = make_interface(
            platform_iface_pb2.getDIResponse(
                di=[True, True],
                readings=[
                    platform_iface_pb2.DIReading(pin=1, value=True, pulse_count=1187),
                    platform_iface_pb2.DIReading(pin=5, value=True),
                ],
            )
        )
        counting, not_counting = fetch(iface, 1, 5)
        assert counting.pulse_count == 1187
        assert not_counting.pulse_count is None


class TestBackwardCompatibility:
    def test_an_old_platform_interface_degrades_to_levels(self):
        """The field is unknown to it, so it answers with `di` alone.

        This must not surface as an empty list: an app doing
        `(await fetch_di_readings(1))[0]` would raise IndexError, which is a
        worse failure than "counts unavailable".
        """
        iface = make_interface(platform_iface_pb2.getDIResponse(di=[True, False, True]))
        readings = fetch(iface, 0, 1, 2)

        assert [r.pin for r in readings] == [0, 1, 2]
        assert [r.value for r in readings] == [True, False, True]
        assert all(r.pulse_count is None for r in readings)

    def test_a_failed_counter_read_degrades_the_same_way(self):
        """The platform drops readings but keeps levels when counters fail.

        Indistinguishable from an old platform interface, and it should be:
        both mean levels known, counts not.
        """
        iface = make_interface(platform_iface_pb2.getDIResponse(di=[True]))
        (reading,) = fetch(iface, 3)
        assert reading == DIReading(pin=3, value=True)

    def test_degraded_readings_keep_the_requested_pin_numbers(self):
        """Levels are positional, so the pins must be zipped back on."""
        iface = make_interface(platform_iface_pb2.getDIResponse(di=[False, True]))
        readings = fetch(iface, 6, 7)
        assert [r.pin for r in readings] == [6, 7]

    def test_a_failed_request_returns_none(self):
        iface = make_interface(None)
        assert fetch(iface, 0) is None


class TestReturnShape:
    def test_always_a_list_even_for_one_pin(self):
        """Unlike fetch_di, this never unwraps.

        A single-pin unwrap combined with per-pin optional fields makes for
        confusing call sites; always returning a list keeps them uniform.
        """
        iface = make_interface(
            platform_iface_pb2.getDIResponse(
                di=[True],
                readings=[platform_iface_pb2.DIReading(pin=0, value=True)],
            )
        )
        result = fetch(iface, 0)
        assert isinstance(result, list) and len(result) == 1
