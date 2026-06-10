"""Tests for persistent-channel reuse in GRPCInterface.

Unary requests share one channel; a stale channel (server restarted under
us) must fail fast and heal via a single retry on a fresh channel, never
wedging the client.
"""

import asyncio

import grpc
import pytest

from pydoover.docker.device_agent import DeviceAgentInterface
from pydoover.models.data.exceptions import DooverAPIError
from pydoover.models.generated.device_agent import (
    device_agent_pb2,
    device_agent_pb2_grpc,
)


class EchoServicer(device_agent_pb2_grpc.deviceAgentServicer):
    async def TestComms(self, request, context):
        return device_agent_pb2.TestCommsResponse(
            response_header=device_agent_pb2.ResponseHeader(
                success=True, cloud_synced=True, cloud_ready=True, response_code=200
            ),
            response=request.message,
        )


async def start_server(port: int = 0) -> tuple[grpc.aio.Server, int]:
    server = grpc.aio.server()
    device_agent_pb2_grpc.add_deviceAgentServicer_to_server(EchoServicer(), server)
    port = server.add_insecure_port(f"127.0.0.1:{port}")
    await server.start()
    return server, port


@pytest.mark.asyncio
async def test_channel_is_reused_across_requests():
    server, port = await start_server()
    client = DeviceAgentInterface(
        app_key="t", dda_uri=f"127.0.0.1:{port}", dda_timeout=2
    )
    try:
        req = device_agent_pb2.TestCommsRequest(message="one")
        await client.make_request("TestComms", req)
        first_channel = client._channel
        assert first_channel is not None

        await client.make_request("TestComms", req)
        assert client._channel is first_channel
    finally:
        await client.close()
        await server.stop(None)


@pytest.mark.asyncio
async def test_survives_server_restart():
    server, port = await start_server()
    client = DeviceAgentInterface(
        app_key="t", dda_uri=f"127.0.0.1:{port}", dda_timeout=2
    )
    req = device_agent_pb2.TestCommsRequest(message="hi")
    try:
        resp = await client.make_request("TestComms", req)
        assert resp.response == "hi"

        # Kill the server: the call must fail fast (well under the deadline
        # budget of two attempts), not hang.
        await server.stop(None)
        await server.wait_for_termination()
        with pytest.raises(DooverAPIError):
            await asyncio.wait_for(client.make_request("TestComms", req), timeout=5)

        # Server comes back on the same port: the client must heal without
        # being recreated.
        server, bound = await start_server(port)
        assert bound == port, "test harness failed to re-bind the port"
        resp = await client.make_request("TestComms", req)
        assert resp.response == "hi"
    finally:
        await client.close()
        await server.stop(None)


@pytest.mark.asyncio
async def test_close_discards_channel():
    server, port = await start_server()
    client = DeviceAgentInterface(
        app_key="t", dda_uri=f"127.0.0.1:{port}", dda_timeout=2
    )
    try:
        await client.make_request(
            "TestComms", device_agent_pb2.TestCommsRequest(message="x")
        )
        assert client._channel is not None
        await client.close()
        assert client._channel is None
    finally:
        await server.stop(None)
