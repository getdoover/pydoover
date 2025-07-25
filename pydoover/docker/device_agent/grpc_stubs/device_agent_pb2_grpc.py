# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

from . import device_agent_pb2 as grpc__stubs_dot_device__agent__pb2

GRPC_GENERATED_VERSION = '1.65.1'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.66.0'
SCHEDULED_RELEASE_DATE = 'August 6, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in grpc_stubs/device_agent_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class deviceAgentStub(object):
    """The doover device agent service definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.TestComms = channel.unary_unary(
                '/device_agent.deviceAgent/TestComms',
                request_serializer=grpc__stubs_dot_device__agent__pb2.TestCommsRequest.SerializeToString,
                response_deserializer=grpc__stubs_dot_device__agent__pb2.TestCommsResponse.FromString,
                _registered_method=True)
        self.GetChannelDetails = channel.unary_unary(
                '/device_agent.deviceAgent/GetChannelDetails',
                request_serializer=grpc__stubs_dot_device__agent__pb2.ChannelDetailsRequest.SerializeToString,
                response_deserializer=grpc__stubs_dot_device__agent__pb2.ChannelDetailsResponse.FromString,
                _registered_method=True)
        self.GetChannelSubscription = channel.unary_stream(
                '/device_agent.deviceAgent/GetChannelSubscription',
                request_serializer=grpc__stubs_dot_device__agent__pb2.ChannelSubscriptionRequest.SerializeToString,
                response_deserializer=grpc__stubs_dot_device__agent__pb2.ChannelSubscriptionResponse.FromString,
                _registered_method=True)
        self.WriteToChannel = channel.unary_unary(
                '/device_agent.deviceAgent/WriteToChannel',
                request_serializer=grpc__stubs_dot_device__agent__pb2.ChannelWriteRequest.SerializeToString,
                response_deserializer=grpc__stubs_dot_device__agent__pb2.ChannelWriteResponse.FromString,
                _registered_method=True)
        self.GetDebugInfo = channel.unary_unary(
                '/device_agent.deviceAgent/GetDebugInfo',
                request_serializer=grpc__stubs_dot_device__agent__pb2.DebugInfoRequest.SerializeToString,
                response_deserializer=grpc__stubs_dot_device__agent__pb2.DebugInfoResponse.FromString,
                _registered_method=True)
        self.GetTempAPIToken = channel.unary_unary(
                '/device_agent.deviceAgent/GetTempAPIToken',
                request_serializer=grpc__stubs_dot_device__agent__pb2.TempAPITokenRequest.SerializeToString,
                response_deserializer=grpc__stubs_dot_device__agent__pb2.TempAPITokenResponse.FromString,
                _registered_method=True)


class deviceAgentServicer(object):
    """The doover device agent service definition.
    """

    def TestComms(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetChannelDetails(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetChannelSubscription(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def WriteToChannel(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDebugInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetTempAPIToken(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_deviceAgentServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'TestComms': grpc.unary_unary_rpc_method_handler(
                    servicer.TestComms,
                    request_deserializer=grpc__stubs_dot_device__agent__pb2.TestCommsRequest.FromString,
                    response_serializer=grpc__stubs_dot_device__agent__pb2.TestCommsResponse.SerializeToString,
            ),
            'GetChannelDetails': grpc.unary_unary_rpc_method_handler(
                    servicer.GetChannelDetails,
                    request_deserializer=grpc__stubs_dot_device__agent__pb2.ChannelDetailsRequest.FromString,
                    response_serializer=grpc__stubs_dot_device__agent__pb2.ChannelDetailsResponse.SerializeToString,
            ),
            'GetChannelSubscription': grpc.unary_stream_rpc_method_handler(
                    servicer.GetChannelSubscription,
                    request_deserializer=grpc__stubs_dot_device__agent__pb2.ChannelSubscriptionRequest.FromString,
                    response_serializer=grpc__stubs_dot_device__agent__pb2.ChannelSubscriptionResponse.SerializeToString,
            ),
            'WriteToChannel': grpc.unary_unary_rpc_method_handler(
                    servicer.WriteToChannel,
                    request_deserializer=grpc__stubs_dot_device__agent__pb2.ChannelWriteRequest.FromString,
                    response_serializer=grpc__stubs_dot_device__agent__pb2.ChannelWriteResponse.SerializeToString,
            ),
            'GetDebugInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.GetDebugInfo,
                    request_deserializer=grpc__stubs_dot_device__agent__pb2.DebugInfoRequest.FromString,
                    response_serializer=grpc__stubs_dot_device__agent__pb2.DebugInfoResponse.SerializeToString,
            ),
            'GetTempAPIToken': grpc.unary_unary_rpc_method_handler(
                    servicer.GetTempAPIToken,
                    request_deserializer=grpc__stubs_dot_device__agent__pb2.TempAPITokenRequest.FromString,
                    response_serializer=grpc__stubs_dot_device__agent__pb2.TempAPITokenResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'device_agent.deviceAgent', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('device_agent.deviceAgent', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class deviceAgent(object):
    """The doover device agent service definition.
    """

    @staticmethod
    def TestComms(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/device_agent.deviceAgent/TestComms',
            grpc__stubs_dot_device__agent__pb2.TestCommsRequest.SerializeToString,
            grpc__stubs_dot_device__agent__pb2.TestCommsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetChannelDetails(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/device_agent.deviceAgent/GetChannelDetails',
            grpc__stubs_dot_device__agent__pb2.ChannelDetailsRequest.SerializeToString,
            grpc__stubs_dot_device__agent__pb2.ChannelDetailsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetChannelSubscription(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/device_agent.deviceAgent/GetChannelSubscription',
            grpc__stubs_dot_device__agent__pb2.ChannelSubscriptionRequest.SerializeToString,
            grpc__stubs_dot_device__agent__pb2.ChannelSubscriptionResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def WriteToChannel(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/device_agent.deviceAgent/WriteToChannel',
            grpc__stubs_dot_device__agent__pb2.ChannelWriteRequest.SerializeToString,
            grpc__stubs_dot_device__agent__pb2.ChannelWriteResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetDebugInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/device_agent.deviceAgent/GetDebugInfo',
            grpc__stubs_dot_device__agent__pb2.DebugInfoRequest.SerializeToString,
            grpc__stubs_dot_device__agent__pb2.DebugInfoResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetTempAPIToken(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/device_agent.deviceAgent/GetTempAPIToken',
            grpc__stubs_dot_device__agent__pb2.TempAPITokenRequest.SerializeToString,
            grpc__stubs_dot_device__agent__pb2.TempAPITokenResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
