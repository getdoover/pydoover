import asyncio
import logging
from typing import ClassVar

import grpc

try:
    from grpc_health.v1 import health_pb2, health_pb2_grpc
except ImportError:
    from ..models.generated.health import health_pb2, health_pb2_grpc
from ..models import DooverAPIError, HTTPError, NotFoundError

log = logging.getLogger(__name__)


class GRPCInterface:
    """Represents a generic gRPC interface for making requests to a gRPC server.

    This class is designed to be subclassed for specific gRPC services, providing
    a common interface for making asynchronous requests.

    Unary requests share one persistent channel rather than paying a TCP +
    HTTP/2 handshake per call (~3x per-call latency on loopback, more on
    constrained devices). If the channel has gone stale — most commonly the
    server restarting under us — the call fails fast with ``UNAVAILABLE`` and
    is retried once on a freshly built channel, which is exactly the old
    channel-per-request behaviour. Every call carries a deadline, so a
    half-dead connection costs at most one timeout before the channel is
    rebuilt; a wedged channel can never permanently wedge the client.
    """

    stub = NotImplemented

    # Keepalive only pings while calls are in flight
    # (grpc.keepalive_permit_without_calls stays 0): gRPC servers GOAWAY
    # clients that ping an idle connection more than once per 5 minutes by
    # default, so idle-channel health is handled by the retry-on-fresh-channel
    # path instead of pings.
    _CHANNEL_OPTIONS = [
        ("grpc.keepalive_time_ms", 10_000),
        ("grpc.keepalive_timeout_ms", 5_000),
        ("grpc.initial_reconnect_backoff_ms", 100),
        ("grpc.max_reconnect_backoff_ms", 2_000),
        # Without this, channels share subchannels from a process-global pool,
        # so a "fresh" channel built after a failure inherits the old broken
        # subchannel — still in reconnect backoff with a cached refusal — and
        # the heal-after-restart retry fails too. A local pool makes a rebuilt
        # channel genuinely reconnect.
        ("grpc.use_local_subchannel_pool", 1),
    ]

    # Options for long-lived server-streaming subscription calls (channel
    # event streams, pulse counters, register subscriptions). Unlike the
    # unary channel above, a subscription stream is a single call that stays
    # in flight for its entire lifetime, and its blocking read() surfaces
    # nothing when the peer silently disappears — without keepalive pings
    # the reconnect loops around these streams can never fire, and the
    # subscription goes permanently deaf while the process looks healthy.
    # (Seen in the field: apps stopped receiving ui_cmds RPCs until their
    # container was recreated.)
    #
    # The stream is receive-only, so pings never accompany outgoing data:
    # max_pings_without_data=0 is required, or the transport stops pinging
    # after two quiet intervals and the wedge becomes undetectable again.
    # The 60s cadence is tuned for our Rust device agent, which does not
    # police ping frequency. A strict C-core/Go server (default: no more
    # than one no-data ping per 5 minutes) would GOAWAY this cadence on a
    # quiet stream — that surfaces as an error and the reconnect loop
    # recovers, i.e. periodic churn rather than silent deafness — but
    # revisit the cadence if these options are ever pointed at such a
    # server.
    _STREAM_CHANNEL_OPTIONS: ClassVar[list[tuple[str, int]]] = [
        ("grpc.keepalive_time_ms", 60_000),
        ("grpc.keepalive_timeout_ms", 5_000),
        ("grpc.http2.max_pings_without_data", 0),
        ("grpc.initial_reconnect_backoff_ms", 100),
        ("grpc.max_reconnect_backoff_ms", 2_000),
        ("grpc.use_local_subchannel_pool", 1),
    ]

    def __init__(self, app_key: str, uri: str, service_name: str, timeout: int = 7):
        self.app_key = app_key
        self.uri = uri
        self.timeout = timeout
        self.service_name = service_name

        self._channel: grpc.aio.Channel | None = None
        self._channel_stub = None
        self._channel_lock = asyncio.Lock()

    async def _get_stub(self):
        async with self._channel_lock:
            if self._channel is None:
                self._channel = grpc.aio.insecure_channel(
                    self.uri, options=self._CHANNEL_OPTIONS
                )
                self._channel_stub = self.stub(self._channel)
            return self._channel_stub

    async def _discard_channel(self):
        """Drop the shared channel so the next call builds a fresh one.

        The old channel is closed in the background with a grace period so
        any concurrent in-flight calls on it can finish rather than being
        cancelled out from under their callers.
        """
        async with self._channel_lock:
            channel, self._channel, self._channel_stub = self._channel, None, None
        if channel is not None:
            close_task = asyncio.ensure_future(channel.close(grace=self.timeout))
            close_task.add_done_callback(lambda t: t.exception())

    async def make_request(self, stub_call, request, *args, **kwargs):
        try:
            try:
                stub = await self._get_stub()
                response = await getattr(stub, stub_call)(request, timeout=self.timeout)
            except grpc.aio.AioRpcError as e:
                # The channel itself is suspect (server restarted under us, or
                # the connection went half-dead and the deadline fired) — not
                # an application error. Rebuild; retry only the fail-fast case
                # so a genuinely slow server doesn't double its worst-case
                # latency.
                if e.code() not in (
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                ):
                    raise
                await self._discard_channel()
                if e.code() is not grpc.StatusCode.UNAVAILABLE:
                    raise
                stub = await self._get_stub()
                response = await getattr(stub, stub_call)(request, timeout=self.timeout)
            return self.process_response(stub_call, response, *args, **kwargs)
        except (DooverAPIError, HTTPError):
            raise
        except Exception as e:
            log.exception(f"Error making {self.__class__.__name__} request: {e}")
            raise DooverAPIError(
                f"gRPC request failed ({self.__class__.__name__}.{stub_call}): {e}"
            ) from e

    async def close(self):
        await self._discard_channel()

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
