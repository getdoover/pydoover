import logging

import grpc

from ..utils import get_is_async

log = logging.getLogger(__name__)


class GRPCInterface:
    """Represents a generic gRPC interface for making requests to a gRPC server.

    This class is designed to be subclassed for specific gRPC services, providing
    a common interface for making synchronous and asynchronous requests.
    """

    stub = NotImplemented

    def __init__(
        self, app_key: str, uri: str, is_async: bool = False, timeout: int = 7
    ):
        self.app_key = app_key
        self.uri = uri
        self._is_async = get_is_async(is_async)
        self.timeout = timeout

    def make_request(self, stub_call, request, *args, **kwargs):
        try:
            with grpc.insecure_channel(self.uri) as channel:
                stub = self.stub(channel)
                response = getattr(stub, stub_call)(request, timeout=self.timeout)
                return self.process_response(stub_call, response, *args, **kwargs)
        except Exception as e:
            log.exception(f"Error making {self.__class__.__name__} request: {e}")
            return None

    async def make_request_async(self, stub_call, request, *args, **kwargs):
        try:
            async with grpc.aio.insecure_channel(self.uri) as channel:
                stub = self.stub(channel)
                response = await getattr(stub, stub_call)(request, timeout=self.timeout)
                return self.process_response(stub_call, response, *args, **kwargs)
        except Exception as e:
            log.exception(f"Error making {self.__class__.__name__} request: {e}")
            return None

    def process_response(self, stub_call: str, response, *args, **kwargs):
        if response is None:
            logging.warning(
                f"Error processing response for {self.__class__.__name__}.{stub_call}: response was None"
            )
            return None

        if response.response_header.success is False:
            # fixme: some classes (modbus, dda) have response_message instead of message (e.g camera, platform)
            message = getattr(response.response_header, "message", None) or getattr(
                response.response_header, "response_message", None
            )
            log.warning(
                f"Error processing {stub_call} response "
                f"({self.__class__.__name__}.{stub_call}): {message}"
            )
            return None

        return response
