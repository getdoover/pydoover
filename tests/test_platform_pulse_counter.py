"""Which pulseCounter stream messages count as a pulse.

The stream carries two things that both arrive with no useful ``dt_secs``, and
they must be told apart:

* the **handshake** the server sends as soon as the stream opens, carrying only
  ``di``. It is not a pulse and must never be counted.
* a **real edge whose gap is unknown**. The firmware measures ``dt_secs`` as the
  time since the previous edge on that channel, so it has nothing to measure on
  the first edge, or after a dropped transition, and sends ``0.0``.

Proto3 presence separates them: the handshake leaves the field unset, a real
zero sets it. Testing ``dt_secs > 0`` instead conflates the two and silently
eats the first pulse of every burst -- which, for an app where the pulse COUNT
is the payload (a vending terminal pulsing a product number), is not a lost
tick but the wrong product sold.
"""

import asyncio
from contextlib import asynccontextmanager

import grpc

from pydoover.docker.platform import platform as platform_module
from pydoover.docker.platform import PlatformInterface
from pydoover.models.generated.platform import platform_iface_pb2


def handshake(di=3):
    """What the server yields the moment the stream opens. Not a pulse."""
    return platform_iface_pb2.pulseCounterResponse(di=di)


def edge(dt_secs, di=3, value=True):
    return platform_iface_pb2.pulseCounterResponse(di=di, value=value, dt_secs=dt_secs)


def drive(monkeypatch, messages):
    """Run recv_di_pulses over a canned stream; return the callback's pulses."""

    class FakeStream:
        def __init__(self):
            self._left = list(messages)

        async def read(self):
            if self._left:
                return self._left.pop(0)
            # Ending the stream ends the read loop; cancelling ends the
            # reconnect loop around it.
            raise asyncio.CancelledError

    class FakeStub:
        def __init__(self, channel):
            pass

        def startPulseCounter(self, request):
            return FakeStream()

    @asynccontextmanager
    async def fake_channel(*args, **kwargs):
        yield object()

    monkeypatch.setattr(grpc.aio, "insecure_channel", fake_channel)
    monkeypatch.setattr(
        platform_module.platform_iface_pb2_grpc, "platformIfaceStub", FakeStub
    )

    seen = []

    def callback(di, di_value, dt_secs, count, edge_):
        seen.append({"di": di, "dt_secs": dt_secs, "count": count})

    iface = PlatformInterface.__new__(PlatformInterface)
    iface.uri = "unused"
    asyncio.run(iface.recv_di_pulses(3, callback, edge="falling"))
    return seen


def test_the_opening_handshake_is_not_a_pulse(monkeypatch):
    """It carries no dt_secs at all. Counting it invents a pulse per connect."""
    assert drive(monkeypatch, [handshake()]) == []


def test_an_edge_with_an_unknown_gap_is_still_a_pulse(monkeypatch):
    """⚠️ The regression. dt_secs=0.0 is the FIRST edge, not a non-event.

    The firmware has no previous edge to measure against and sends 0.0. A
    ``> 0`` test drops it, so the first pulse of a burst disappears.
    """
    seen = drive(monkeypatch, [handshake(), edge(0.0)])
    assert [p["dt_secs"] for p in seen] == [0.0], "the first edge was swallowed"
    assert seen[0]["count"] == 1


def test_a_burst_keeps_every_pulse_including_the_first(monkeypatch):
    """The count IS the payload for a terminal pulsing a product number."""
    seen = drive(monkeypatch, [handshake(), edge(0.0), edge(0.2), edge(0.2)])
    assert [p["count"] for p in seen] == [1, 2, 3]


def test_the_counter_resumes_from_start_count(monkeypatch):
    """A reconnect must not restart the customer's product number at one."""

    class FakeStream:
        def __init__(self):
            self._left = [handshake(), edge(0.0)]

        async def read(self):
            if self._left:
                return self._left.pop(0)
            raise asyncio.CancelledError

    class FakeStub:
        def __init__(self, channel):
            pass

        def startPulseCounter(self, request):
            return FakeStream()

    @asynccontextmanager
    async def fake_channel(*args, **kwargs):
        yield object()

    monkeypatch.setattr(grpc.aio, "insecure_channel", fake_channel)
    monkeypatch.setattr(
        platform_module.platform_iface_pb2_grpc, "platformIfaceStub", FakeStub
    )

    seen = []
    iface = PlatformInterface.__new__(PlatformInterface)
    iface.uri = "unused"
    asyncio.run(
        iface.recv_di_pulses(
            3, lambda *a: seen.append(a[3]), edge="falling", start_count=7
        )
    )
    assert seen == [8]
