"""Tests for PlatformInterface.fetch_location and Location.from_response.

getLocationResponse carries the fix as flat optional fields (latitude,
longitude, ...) rather than a nested `location` message; fetch_location must
map those to a Location, and a missing latitude/longitude (no fix) must map
to None rather than a Location at proto-default (0, 0).
"""

import grpc
import pytest

from pydoover.docker.platform import Location, PlatformInterface
from pydoover.models.generated.platform import (
    platform_iface_pb2,
    platform_iface_pb2_grpc,
)


def make_fix_response(**overrides) -> platform_iface_pb2.getLocationResponse:
    fields = {
        "latitude": -27.5725937,
        "longitude": 152.358719,
        "altitude_m": 87.5,
        "accuracy_m": 5.6,
        "speed_mps": 0.0,
        "sat_count": 11,
        "timestamp": "2026-07-23T03:19:33+00:00",
    }
    fields.update(overrides)
    return platform_iface_pb2.getLocationResponse(
        response_header=platform_iface_pb2.ResponseHeader(success=True),
        **{k: v for k, v in fields.items() if v is not None},
    )


class TestLocationFromResponse:
    def test_full_fix(self):
        location = Location.from_response(make_fix_response())
        assert location is not None
        assert location.latitude == pytest.approx(-27.5725937)
        assert location.longitude == pytest.approx(152.358719)
        assert location.altitude_m == pytest.approx(87.5)
        assert location.accuracy_m == pytest.approx(5.6)
        assert location.speed_mps == 0.0
        assert location.sat_count == 11
        assert location.timestamp == "2026-07-23T03:19:33+00:00"

    def test_unset_optional_fields_are_none_not_proto_defaults(self):
        location = Location.from_response(make_fix_response(heading_deg=None))
        assert location is not None
        assert location.heading_deg is None

    def test_no_fix_returns_none(self):
        response = platform_iface_pb2.getLocationResponse(
            response_header=platform_iface_pb2.ResponseHeader(success=True)
        )
        assert Location.from_response(response) is None

    def test_partial_coordinates_return_none(self):
        assert Location.from_response(make_fix_response(latitude=None)) is None
        assert Location.from_response(make_fix_response(longitude=None)) is None

    def test_none_response_returns_none(self):
        assert Location.from_response(None) is None


class LocationServicer(platform_iface_pb2_grpc.platformIfaceServicer):
    def __init__(self, response: platform_iface_pb2.getLocationResponse):
        self.response = response

    async def getLocation(self, request, context):
        return self.response


async def fetch_via_server(
    response: platform_iface_pb2.getLocationResponse,
) -> Location | None:
    server = grpc.aio.server()
    platform_iface_pb2_grpc.add_platformIfaceServicer_to_server(
        LocationServicer(response), server
    )
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()

    plt = PlatformInterface("test_app", f"127.0.0.1:{port}")
    try:
        return await plt.fetch_location()
    finally:
        await plt.close()
        await server.stop(grace=None)


@pytest.mark.asyncio
async def test_fetch_location_returns_location_from_flat_response():
    location = await fetch_via_server(make_fix_response())
    assert isinstance(location, Location)
    assert location.latitude == pytest.approx(-27.5725937)
    assert location.longitude == pytest.approx(152.358719)
    assert location.accuracy_m == pytest.approx(5.6)


@pytest.mark.asyncio
async def test_fetch_location_returns_none_without_fix():
    response = platform_iface_pb2.getLocationResponse(
        response_header=platform_iface_pb2.ResponseHeader(success=True)
    )
    assert await fetch_via_server(response) is None
