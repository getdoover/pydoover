"""Tests for PlatformInterface.fetch_image / set_image / subscribe_image.

The image is indexed by flat channel. A channel that is not good keeps its
index and is listed in a sparse status map with the reason, so a caller checks
`valid()` / `quality()` rather than trusting a 0.0. Pulse counts and rates are
maps because only some DIs have them; absent means none, not zero. A quality
this client does not know reads as FAULT, never as GOOD.
"""

import asyncio
from contextlib import asynccontextmanager

import grpc
import pytest

from pydoover.docker.platform import ChannelQuality, PlatformInterface, ProcessImage
from pydoover.models.generated.platform import (
    platform_iface_pb2 as pb,
)
from pydoover.models.generated.platform import (
    platform_iface_pb2_grpc,
)


def image_response(sequence=7):
    return pb.getImageResponse(
        response_header=pb.ResponseHeader(success=True),
        di=[True, False, False],
        do=[False, True],
        ai=[4.123456789012, 2.1],
        ao=[10.0],
        di_status={
            2: pb.ChannelStatus(
                quality=pb.CHANNEL_QUALITY_OFFLINE, detail="no data yet"
            )
        },
        ai_status={
            1: pb.ChannelStatus(quality=pb.CHANNEL_QUALITY_UNDER_RANGE),
        },
        do_status={0: pb.ChannelStatus(quality=99)},
        di_count={0: 0, 1: 1234},
        di_rate_hz={1: 2.5},
        devices=[
            pb.DeviceImageStatus(
                index=-1,
                name="master (sim)",
                online=True,
                age_ms=12,
                timestamp_ms=1793000000000,
            ),
            pb.DeviceImageStatus(
                index=1, name="slave 1 (wago)", online=False, last_error="timed out"
            ),
        ],
        sequence=sequence,
    )


class ImageServicer(platform_iface_pb2_grpc.platformIfaceServicer):
    def __init__(self):
        self.writes = []
        self.rate = None

    async def getImage(self, request, context):
        return image_response()

    async def setImage(self, request, context):
        self.writes.append(
            (
                list(request.do),
                list(request.do_value),
                list(request.ao),
                list(request.ao_value),
            )
        )
        return pb.setImageResponse(
            response_header=pb.ResponseHeader(success=True), failed_ao=[5]
        )

    async def subscribeImage(self, request, context):
        self.rate = request.max_rate_hz if request.HasField("max_rate_hz") else None
        for seq in (1, 2, 3):
            yield image_response(sequence=seq)


@asynccontextmanager
async def serving():
    servicer = ImageServicer()
    server = grpc.aio.server()
    platform_iface_pb2_grpc.add_platformIfaceServicer_to_server(servicer, server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    client = PlatformInterface("test_app", f"127.0.0.1:{port}")
    try:
        yield client, servicer
    finally:
        await client.close()
        await server.stop(grace=None)


@pytest.mark.asyncio
async def test_fetch_image_keeps_indices_and_reports_quality():
    async with serving() as (client, _):
        image = await client.fetch_image()
    assert isinstance(image, ProcessImage)
    assert image.di == [True, False, False]
    assert image.do == [False, True]
    assert image.ai[0] == 4.123456789012, "doubles, not floats"

    assert image.valid("DI", 0) and not image.valid("di", 2)
    assert image.quality("DI", 2) is ChannelQuality.OFFLINE
    assert image.di_status[2].detail == "no data yet"
    assert image.quality("AI", 1) is ChannelQuality.UNDER_RANGE
    assert image.ai[1] == 2.1, "an out-of-range reading keeps its value"
    assert image.quality("DO", 0) is ChannelQuality.FAULT, (
        "an unknown quality is not good"
    )
    assert image.valid("AO", 0)

    assert image.di_count == {0: 0, 1: 1234}
    assert image.di_rate_hz == {1: 2.5}

    master, slave = image.devices
    assert (master.index, master.online, master.age_ms, master.timestamp_ms) == (
        -1,
        True,
        12,
        1793000000000,
    )
    assert (slave.online, slave.age_ms, slave.last_error, slave.timestamp_ms) == (
        False,
        None,
        "timed out",
        None,
    )
    assert image.sequence == 7


@pytest.mark.asyncio
async def test_set_image_sends_parallel_lists_and_reports_failures():
    async with serving() as (client, servicer):
        failed = await client.set_image(do={0: True, 2: False}, ao={5: 12.5})
    assert servicer.writes == [([0, 2], [True, False], [5], [12.5])]
    assert failed == ([], [5])


@pytest.mark.asyncio
async def test_subscribe_image_delivers_each_message():
    seen = []
    done = asyncio.Event()

    def on_image(image):
        seen.append(image.sequence)
        if len(seen) == 3:
            done.set()

    async with serving() as (client, servicer):
        task = client.subscribe_image(on_image, max_rate_hz=10)
        await asyncio.wait_for(done.wait(), timeout=5)
        task.cancel()
    assert seen[:3] == [1, 2, 3]
    assert servicer.rate == pytest.approx(10)
