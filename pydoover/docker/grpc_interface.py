import asyncio
import logging

import grpc

try:
    from grpc_health.v1 import health_pb2, health_pb2_grpc
except ImportError:
    from ..models.generated.health import health_pb2, health_pb2_grpc
from ..models.exceptions import DooverAPIError, HTTPError, NotFoundError

log = logging.getLogger(__name__)


class GRPCInterface:
    """Represents a generic gRPC interface for making requests to a gRPC server.

    This class is designed to be subclassed for specific gRPC services, providing
    a common interface for making asynchronous requests.
    """

    stub = NotImplemented

    def __init__(self, app_key: str, uri: str, service_name: str, timeout: int = 7):
        self.app_key = app_key
        self.uri = uri
        self.timeout = timeout
        self.service_name = service_name

    async def make_request(self, stub_call, request, *args, **kwargs):
        try:
            async with grpc.aio.insecure_channel(self.uri) as channel:
                stub = self.stub(channel)
                response = await getattr(stub, stub_call)(request, timeout=self.timeout)
                return self.process_response(stub_call, response, *args, **kwargs)
        except (DooverAPIError, HTTPError):
            raise
        except Exception as e:
            log.exception(f"Error making {self.__class__.__name__} request: {e}")
            raise DooverAPIError(
                f"gRPC request failed ({self.__class__.__name__}.{stub_call}): {e}"
            ) from e

    def process_response(self, stub_call: str, response, *args, **kwargs):
        if response is None:
            raise DooverAPIError(
                f"Empty response for {self.__class__.__name__}.{stub_call}"
            )

        if response.response_header.success is False:
            message = (
                getattr(response.response_header, "message", None)
                or getattr(response.response_header, "response_message", None)
                or "Unknown error"
            )
            code = getattr(response.response_header, "response_code", None) or 500

            if code == 404:
                raise NotFoundError(message)
            else:
                raise HTTPError(code, message)

        return response

    async def health_check(self):
        try:
            async with grpc.aio.insecure_channel(self.uri) as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                resp = await stub.Check(
                    health_pb2.HealthCheckRequest(service=self.service_name)
                )
                if resp.status == health_pb2.HealthCheckResponse.SERVING:
                    log.debug("Server is healthy.")
                    return True
                elif resp.status == health_pb2.HealthCheckResponse.NOT_SERVING:
                    log.debug("Server is unhealthy.")
                    return False
        except Exception as e:
            log.exception(f"Error making healthcheck request: {e}")
            return False

    async def wait_until_healthy(self, interval: float = 1.0):
        # responsibility of client to cancel this after x seconds / minutes
        while True:
            if await self.health_check():
                return True

            await asyncio.sleep(interval)
