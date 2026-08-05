"""Tests for PlatformInterface.fetch_io_details and the IoDetails types.

getIoDetails reports the flat IO namespace grouped by owning device (master
first, then slaves in index order). Against a server that predates the RPC,
fetch_io_details must fall back to getIoTable and synthesize a single
anonymous master device, so consuming apps have one code path.
"""

import json

import grpc
import pytest

from pydoover.docker.platform import IoChannel, IoDetails, PlatformInterface
from pydoover.models.generated.platform import (
    platform_iface_pb2,
    platform_iface_pb2_grpc,
)


def make_details_response() -> platform_iface_pb2.getIoDetailsResponse:
    return platform_iface_pb2.getIoDetailsResponse(
        response_header=platform_iface_pb2.ResponseHeader(success=True),
        devices=[
            platform_iface_pb2.IoDeviceDetail(
                name="master",
                type="doovit",
                index=0,
                is_master=True,
                online=True,
                channels=[
                    platform_iface_pb2.IoChannelDetail(
                        channel=0,
                        device_channel=0,
                        io_type="DI",
                        supports_events=True,
                        supports_pulse_counter=True,
                        supports_di_config=True,
                    ),
                    platform_iface_pb2.IoChannelDetail(
                        channel=0,
                        device_channel=0,
                        io_type="AI",
                        kind="voltage",
                        units="V",
                    ),
                ],
            ),
            platform_iface_pb2.IoDeviceDetail(
                name="rack1",
                type="moxa1212",
                index=1,
                is_master=False,
                online=True,
                channels=[
                    platform_iface_pb2.IoChannelDetail(
                        channel=4, device_channel=0, io_type="DI"
                    ),
                ],
            ),
        ],
    )


class TestIoDetailsFromResponse:
    def test_devices_and_channels(self):
        details = IoDetails.from_response(make_details_response())
        assert details is not None
        assert [d.name for d in details.devices] == ["master", "rack1"]
        assert details.master is not None and details.master.type == "doovit"
        assert details.devices[1].index == 1
        assert details.devices[1].channels[0].device_channel == 0
        assert details.devices[1].channels[0].channel == 4

    def test_channels_flat_order_across_devices(self):
        details = IoDetails.from_response(make_details_response())
        assert [c.channel for c in details.channels("DI")] == [0, 4]
        assert details.master.channels_of("AI")[0].units == "V"

    def test_unset_optional_fields_are_none_not_proto_defaults(self):
        details = IoDetails.from_response(make_details_response())
        slave_di = details.devices[1].channels[0]
        assert slave_di.kind is None
        assert slave_di.units is None
        assert slave_di.supports_events is False

    def test_none_response_returns_none(self):
        assert IoDetails.from_response(None) is None


class TestIoDetailsFromIoTable:
    def test_synthesizes_single_master_device(self):
        details = IoDetails.from_io_table(
            {"DI": [0, 1], "DO": [0], "AI": [], "AO": [0]}
        )
        assert len(details.devices) == 1
        assert details.master is not None and details.master.is_master
        assert [c.channel for c in details.channels("DI")] == [0, 1]
        assert details.channels("AI") == []

    def test_synthesized_channels_have_no_metadata_or_capabilities(self):
        details = IoDetails.from_io_table({"DI": [0]})
        channel = details.channels("DI")[0]
        assert isinstance(channel, IoChannel)
        assert channel.kind is None and channel.units is None
        assert not channel.supports_events
        assert not channel.supports_pulse_counter
        assert not channel.supports_di_config


class DetailsServicer(platform_iface_pb2_grpc.platformIfaceServicer):
    def __init__(self, response: platform_iface_pb2.getIoDetailsResponse):
        self.response = response

    async def getIoDetails(self, request, context):
        return self.response


class LegacyIoTableServicer(platform_iface_pb2_grpc.platformIfaceServicer):
    """Simulates a server that predates getIoDetails: only getIoTable is
    implemented, so getIoDetails hits the generated UNIMPLEMENTED default."""

    def __init__(self, io_table: dict):
        self.io_table = io_table

    async def getIoTable(self, request, context):
        return platform_iface_pb2.getIoTableResponse(
            response_header=platform_iface_pb2.ResponseHeader(success=True),
            io_table=json.dumps(self.io_table),
        )


async def fetch_via_server(servicer) -> IoDetails | None:
    server = grpc.aio.server()
    platform_iface_pb2_grpc.add_platformIfaceServicer_to_server(servicer, server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()

    plt = PlatformInterface("test_app", f"127.0.0.1:{port}")
    try:
        return await plt.fetch_io_details()
    finally:
        await plt.close()
        await server.stop(grace=None)


@pytest.mark.asyncio
async def test_fetch_io_details_returns_structured_layout():
    details = await fetch_via_server(DetailsServicer(make_details_response()))
    assert isinstance(details, IoDetails)
    assert [d.name for d in details.devices] == ["master", "rack1"]
    assert [c.channel for c in details.channels("DI")] == [0, 4]


@pytest.mark.asyncio
async def test_fetch_io_details_falls_back_to_io_table_on_unimplemented():
    details = await fetch_via_server(
        LegacyIoTableServicer({"DI": [0, 1, 2], "DO": [0], "AI": [0], "AO": []})
    )
    assert isinstance(details, IoDetails)
    assert len(details.devices) == 1
    assert details.master is not None and details.master.type == ""
    assert [c.channel for c in details.channels("DI")] == [0, 1, 2]
