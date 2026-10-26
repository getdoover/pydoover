"""Tests for PlatformInterface.fetch_image / set_image / subscribe_image.

The image is indexed by flat channel. A channel whose device is offline keeps
its index (the value is a placeholder) and is listed as invalid, so a caller
must check `valid()` rather than trust a 0.0. Pulse counts are a map because
only some DIs have one; absent means no counter, not zero.
"""

import asyncio
from contextlib import asynccontextmanager

import grpc
import pytest

from pydoover.docker.platform import PlatformInterface, ProcessImage
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
        ai=[4.5, 0.0],
        ao=[10.0],
        invalid_di=[2],
        invalid_ai=[1],
        di_count={0: 0, 1: 1234},
        devices=[
            pb.DeviceImageStatus(index=-1, name="master (sim)", online=True, age_ms=12),
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
async def test_fetch_image_keeps_indices_and_flags_invalid():
    async with serving() as (client, _):
        image = await client.fetch_image()
    assert isinstance(image, ProcessImage)
    assert image.di == [True, False, False]
    assert image.do == [False, True]
    assert image.valid("DI", 0) and not image.valid("di", 2)
    assert not image.valid("AI", 1) and image.valid("AO", 0)
    assert image.di_count == {0: 0, 1: 1234}
    assert 2 not in image.di_count
    master, slave = image.devices
    assert (master.index, master.online, master.age_ms, master.last_error) == (
        -1,
        True,
        12,
        None,
    )
    assert (slave.online, slave.age_ms, slave.last_error) == (False, None, "timed out")
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
