"""Tests for PlatformInterface.fetch_do_current.

getDOCurrentResponse returns a `current` list parallel to the requested pins,
so a single-pin request must unwrap to a bare float (matching fetch_do /
fetch_ai) while a multi-pin request keeps request order. 0.0 amps is a real
reading — an output that's on but driving nothing — so it must survive the
single-value unwrap rather than being flattened to None.

Platforms without per-output current sensing answer with success=False, which
surfaces as an HTTPError rather than a None return.
"""

import grpc
import pytest

from pydoover.docker.platform import PlatformInterface
from pydoover.models import HTTPError
from pydoover.models.generated.platform import (
    platform_iface_pb2,
    platform_iface_pb2_grpc,
)

# what the fake io board reads back on each output, in amps
BENCH = {0: 0.0, 1: 0.512, 2: 1.25, 3: 2.0}


class DOCurrentServicer(platform_iface_pb2_grpc.platformIfaceServicer):
    def __init__(self):
        self.requested = []

    async def getDOCurrent(self, request, context):
        self.requested.append(list(request.do))
        if any(pin not in BENCH for pin in request.do):
            return platform_iface_pb2.getDOCurrentResponse(
                response_header=platform_iface_pb2.ResponseHeader(
                    success=False,
                    response_code=500,
                    message="Error in get_do_current : not supported on this platform",
                ),
                current=[],
            )
        return platform_iface_pb2.getDOCurrentResponse(
            response_header=platform_iface_pb2.ResponseHeader(success=True),
            current=[BENCH[pin] for pin in request.do],
        )


async def fetch_via_server(*do: int):
    servicer = DOCurrentServicer()
    server = grpc.aio.server()
    platform_iface_pb2_grpc.add_platformIfaceServicer_to_server(servicer, server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()

    plt = PlatformInterface("test_app", f"127.0.0.1:{port}")
    try:
        return await plt.fetch_do_current(*do), servicer
    finally:
        await plt.close()
        await server.stop(grace=None)


@pytest.mark.asyncio
async def test_single_pin_returns_a_bare_float():
    current, servicer = await fetch_via_server(2)
    assert current == pytest.approx(1.25)
    assert servicer.requested == [[2]]


@pytest.mark.asyncio
async def test_multiple_pins_return_a_list_in_request_order():
    current, servicer = await fetch_via_server(3, 1, 0)
    assert current == pytest.approx([2.0, 0.512, 0.0])
    assert servicer.requested == [[3, 1, 0]]


@pytest.mark.asyncio
async def test_zero_amps_survives_the_single_value_unwrap():
    current, _ = await fetch_via_server(0)
    assert current == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_unsupported_platform_raises():
    with pytest.raises(HTTPError):
        await fetch_via_server(9)
