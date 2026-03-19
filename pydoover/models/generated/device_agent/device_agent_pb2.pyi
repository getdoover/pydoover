from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RequestHeader(_message.Message):
    __slots__ = ("app_id",)
    APP_ID_FIELD_NUMBER: _ClassVar[int]
    app_id: str
    def __init__(self, app_id: _Optional[str] = ...) -> None: ...

class ResponseHeader(_message.Message):
    __slots__ = ("success", "cloud_synced", "cloud_ready", "response_code", "response_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    CLOUD_SYNCED_FIELD_NUMBER: _ClassVar[int]
    CLOUD_READY_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    cloud_synced: bool
    cloud_ready: bool
    response_code: int
    response_message: str
    def __init__(self, success: bool = ..., cloud_synced: bool = ..., cloud_ready: bool = ..., response_code: _Optional[int] = ..., response_message: _Optional[str] = ...) -> None: ...

class MessageDetails(_message.Message):
    __slots__ = ("message_id", "channel_name", "payload", "timestamp")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    channel_name: str
    payload: str
    timestamp: str
    def __init__(self, message_id: _Optional[str] = ..., channel_name: _Optional[str] = ..., payload: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class ChannelDetails(_message.Message):
    __slots__ = ("channel_name", "aggregate")
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    channel_name: str
    aggregate: str
    def __init__(self, channel_name: _Optional[str] = ..., aggregate: _Optional[str] = ...) -> None: ...

class AgentDetails(_message.Message):
    __slots__ = ("agent_id", "agent_name", "channels")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_NAME_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    agent_name: str
    channels: _containers.RepeatedCompositeFieldContainer[ChannelDetails]
    def __init__(self, agent_id: _Optional[str] = ..., agent_name: _Optional[str] = ..., channels: _Optional[_Iterable[_Union[ChannelDetails, _Mapping]]] = ...) -> None: ...

class TestCommsRequest(_message.Message):
    __slots__ = ("header", "message")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    message: str
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., message: _Optional[str] = ...) -> None: ...

class TestCommsResponse(_message.Message):
    __slots__ = ("response_header", "response")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    response: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., response: _Optional[str] = ...) -> None: ...

class MessageDetailsRequest(_message.Message):
    __slots__ = ("header", "message_id")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    message_id: str
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., message_id: _Optional[str] = ...) -> None: ...

class MessageDetailsResponse(_message.Message):
    __slots__ = ("response_header", "message")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    message: MessageDetails
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., message: _Optional[_Union[MessageDetails, _Mapping]] = ...) -> None: ...

class ChannelDetailsRequest(_message.Message):
    __slots__ = ("header", "channel_name")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ...) -> None: ...

class ChannelDetailsResponse(_message.Message):
    __slots__ = ("response_header", "channel")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    channel: ChannelDetails
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., channel: _Optional[_Union[ChannelDetails, _Mapping]] = ...) -> None: ...

class ChannelSubscriptionRequest(_message.Message):
    __slots__ = ("header", "channel_name")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ...) -> None: ...

class ChannelSubscriptionResponse(_message.Message):
    __slots__ = ("response_header", "channel", "message")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    channel: ChannelDetails
    message: MessageDetails
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., channel: _Optional[_Union[ChannelDetails, _Mapping]] = ..., message: _Optional[_Union[MessageDetails, _Mapping]] = ...) -> None: ...

class ChannelWriteRequest(_message.Message):
    __slots__ = ("header", "channel_name", "message_payload", "save_log", "max_age", "max_age_f")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    SAVE_LOG_FIELD_NUMBER: _ClassVar[int]
    MAX_AGE_FIELD_NUMBER: _ClassVar[int]
    MAX_AGE_F_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    message_payload: str
    save_log: bool
    max_age: int
    max_age_f: float
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ..., message_payload: _Optional[str] = ..., save_log: bool = ..., max_age: _Optional[int] = ..., max_age_f: _Optional[float] = ...) -> None: ...

class DebugInfoRequest(_message.Message):
    __slots__ = ("header",)
    HEADER_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ...) -> None: ...

class ChannelWriteResponse(_message.Message):
    __slots__ = ("response_header", "message_id")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    message_id: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., message_id: _Optional[str] = ...) -> None: ...

class DebugChannelState(_message.Message):
    __slots__ = ("channel_name", "active", "local_updated_at", "cloud_updated_at")
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    LOCAL_UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    CLOUD_UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    channel_name: str
    active: bool
    local_updated_at: float
    cloud_updated_at: float
    def __init__(self, channel_name: _Optional[str] = ..., active: bool = ..., local_updated_at: _Optional[float] = ..., cloud_updated_at: _Optional[float] = ...) -> None: ...

class DebugPendingMessage(_message.Message):
    __slots__ = ("channel_name", "app_key", "save_log", "payload", "publish_in")
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    APP_KEY_FIELD_NUMBER: _ClassVar[int]
    SAVE_LOG_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_IN_FIELD_NUMBER: _ClassVar[int]
    channel_name: str
    app_key: str
    save_log: bool
    payload: str
    publish_in: int
    def __init__(self, channel_name: _Optional[str] = ..., app_key: _Optional[str] = ..., save_log: bool = ..., payload: _Optional[str] = ..., publish_in: _Optional[int] = ...) -> None: ...

class DebugInfoResponse(_message.Message):
    __slots__ = ("response_header", "active_callbacks", "wss_callbacks", "wss_aggregates", "wss_subscriptions", "channels", "pending_messages", "wss_connected")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_CALLBACKS_FIELD_NUMBER: _ClassVar[int]
    WSS_CALLBACKS_FIELD_NUMBER: _ClassVar[int]
    WSS_AGGREGATES_FIELD_NUMBER: _ClassVar[int]
    WSS_SUBSCRIPTIONS_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    PENDING_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    WSS_CONNECTED_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    active_callbacks: _containers.RepeatedScalarFieldContainer[str]
    wss_callbacks: _containers.RepeatedScalarFieldContainer[str]
    wss_aggregates: _containers.RepeatedScalarFieldContainer[str]
    wss_subscriptions: _containers.RepeatedScalarFieldContainer[str]
    channels: _containers.RepeatedCompositeFieldContainer[DebugChannelState]
    pending_messages: _containers.RepeatedCompositeFieldContainer[DebugPendingMessage]
    wss_connected: bool
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., active_callbacks: _Optional[_Iterable[str]] = ..., wss_callbacks: _Optional[_Iterable[str]] = ..., wss_aggregates: _Optional[_Iterable[str]] = ..., wss_subscriptions: _Optional[_Iterable[str]] = ..., channels: _Optional[_Iterable[_Union[DebugChannelState, _Mapping]]] = ..., pending_messages: _Optional[_Iterable[_Union[DebugPendingMessage, _Mapping]]] = ..., wss_connected: bool = ...) -> None: ...

class TempAPITokenRequest(_message.Message):
    __slots__ = ("header",)
    HEADER_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ...) -> None: ...

class TempAPITokenResponse(_message.Message):
    __slots__ = ("response_header", "token", "valid_until", "endpoint")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    VALID_UNTIL_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    token: str
    valid_until: str
    endpoint: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., token: _Optional[str] = ..., valid_until: _Optional[str] = ..., endpoint: _Optional[str] = ...) -> None: ...

class TurnCredentialRequest(_message.Message):
    __slots__ = ("header", "camera_name")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CAMERA_NAME_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    camera_name: str
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., camera_name: _Optional[str] = ...) -> None: ...

class TurnCredential(_message.Message):
    __slots__ = ("username", "credential", "ttl", "expires_at", "uris")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    CREDENTIAL_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    URIS_FIELD_NUMBER: _ClassVar[int]
    username: str
    credential: str
    ttl: int
    expires_at: int
    uris: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, username: _Optional[str] = ..., credential: _Optional[str] = ..., ttl: _Optional[int] = ..., expires_at: _Optional[int] = ..., uris: _Optional[_Iterable[str]] = ...) -> None: ...

class TurnCredentialResponse(_message.Message):
    __slots__ = ("response_header", "turn_credential")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    TURN_CREDENTIAL_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    turn_credential: TurnCredential
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., turn_credential: _Optional[_Union[TurnCredential, _Mapping]] = ...) -> None: ...

class File(_message.Message):
    __slots__ = ("filename", "content_type", "data", "size_bytes")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    filename: str
    content_type: str
    data: bytes
    size_bytes: int
    def __init__(self, filename: _Optional[str] = ..., content_type: _Optional[str] = ..., data: _Optional[bytes] = ..., size_bytes: _Optional[int] = ...) -> None: ...

class Attachment(_message.Message):
    __slots__ = ("filename", "content_type", "size_bytes", "url")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    filename: str
    content_type: str
    size_bytes: int
    url: str
    def __init__(self, filename: _Optional[str] = ..., content_type: _Optional[str] = ..., size_bytes: _Optional[int] = ..., url: _Optional[str] = ...) -> None: ...

class ChannelID(_message.Message):
    __slots__ = ("agent_id", "name")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    agent_id: int
    name: str
    def __init__(self, agent_id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ("message_id", "author_id", "channel", "data", "attachments")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    ATTACHMENTS_FIELD_NUMBER: _ClassVar[int]
    message_id: int
    author_id: int
    channel: ChannelID
    data: _struct_pb2.Struct
    attachments: _containers.RepeatedCompositeFieldContainer[Attachment]
    def __init__(self, message_id: _Optional[int] = ..., author_id: _Optional[int] = ..., channel: _Optional[_Union[ChannelID, _Mapping]] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., attachments: _Optional[_Iterable[_Union[Attachment, _Mapping]]] = ...) -> None: ...

class GetMessageRequest(_message.Message):
    __slots__ = ("header", "channel_name", "message_id")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    message_id: int
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ..., message_id: _Optional[int] = ...) -> None: ...

class GetMessageResponse(_message.Message):
    __slots__ = ("response_header", "message")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    message: Message
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., message: _Optional[_Union[Message, _Mapping]] = ...) -> None: ...

class GetMessagesRequest(_message.Message):
    __slots__ = ("header", "channel_name", "before", "after", "limit", "field_names")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    BEFORE_FIELD_NUMBER: _ClassVar[int]
    AFTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAMES_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    before: int
    after: int
    limit: int
    field_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ..., before: _Optional[int] = ..., after: _Optional[int] = ..., limit: _Optional[int] = ..., field_names: _Optional[_Iterable[str]] = ...) -> None: ...

class GetMessagesResponse(_message.Message):
    __slots__ = ("response_header", "messages")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ...) -> None: ...

class CreateMessageRequest(_message.Message):
    __slots__ = ("header", "channel_name", "data", "files", "timestamp")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    data: _struct_pb2.Struct
    files: _containers.RepeatedCompositeFieldContainer[File]
    timestamp: int
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., files: _Optional[_Iterable[_Union[File, _Mapping]]] = ..., timestamp: _Optional[int] = ...) -> None: ...

class CreateMessageResponse(_message.Message):
    __slots__ = ("response_header", "message_id")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    message_id: int
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., message_id: _Optional[int] = ...) -> None: ...

class UpdateMessageRequest(_message.Message):
    __slots__ = ("header", "channel_name", "message_id", "data", "files", "clear_attachments", "replace_data")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    CLEAR_ATTACHMENTS_FIELD_NUMBER: _ClassVar[int]
    REPLACE_DATA_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    message_id: str
    data: _struct_pb2.Struct
    files: _containers.RepeatedCompositeFieldContainer[File]
    clear_attachments: bool
    replace_data: bool
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ..., message_id: _Optional[str] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., files: _Optional[_Iterable[_Union[File, _Mapping]]] = ..., clear_attachments: bool = ..., replace_data: bool = ...) -> None: ...

class UpdateMessageResponse(_message.Message):
    __slots__ = ("response_header", "message")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    message: Message
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., message: _Optional[_Union[Message, _Mapping]] = ...) -> None: ...

class Aggregate(_message.Message):
    __slots__ = ("data", "attachments", "last_updated")
    DATA_FIELD_NUMBER: _ClassVar[int]
    ATTACHMENTS_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATED_FIELD_NUMBER: _ClassVar[int]
    data: _struct_pb2.Struct
    attachments: _containers.RepeatedCompositeFieldContainer[Attachment]
    last_updated: int
    def __init__(self, data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., attachments: _Optional[_Iterable[_Union[Attachment, _Mapping]]] = ..., last_updated: _Optional[int] = ...) -> None: ...

class UpdateAggregateRequest(_message.Message):
    __slots__ = ("header", "channel_name", "data", "files", "clear_attachments", "replace_data", "max_age_secs", "save_log")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    CLEAR_ATTACHMENTS_FIELD_NUMBER: _ClassVar[int]
    REPLACE_DATA_FIELD_NUMBER: _ClassVar[int]
    MAX_AGE_SECS_FIELD_NUMBER: _ClassVar[int]
    SAVE_LOG_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    data: _struct_pb2.Struct
    files: _containers.RepeatedCompositeFieldContainer[File]
    clear_attachments: bool
    replace_data: bool
    max_age_secs: float
    save_log: bool
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., files: _Optional[_Iterable[_Union[File, _Mapping]]] = ..., clear_attachments: bool = ..., replace_data: bool = ..., max_age_secs: _Optional[float] = ..., save_log: bool = ...) -> None: ...

class UpdateAggregateResponse(_message.Message):
    __slots__ = ("response_header", "aggregate")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    aggregate: Aggregate
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., aggregate: _Optional[_Union[Aggregate, _Mapping]] = ...) -> None: ...

class ChannelEventSubscriptionRequest(_message.Message):
    __slots__ = ("header", "channel_name")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ...) -> None: ...

class ChannelEventSubscriptionResponse(_message.Message):
    __slots__ = ("response_header", "event_name", "channel_name", "data")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    EVENT_NAME_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    event_name: str
    channel_name: str
    data: _struct_pb2.Struct
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., event_name: _Optional[str] = ..., channel_name: _Optional[str] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class GetAggregateRequest(_message.Message):
    __slots__ = ("header", "channel_name")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    channel_name: str
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., channel_name: _Optional[str] = ...) -> None: ...

class GetAggregateResponse(_message.Message):
    __slots__ = ("response_header", "aggregate")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    aggregate: Aggregate
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., aggregate: _Optional[_Union[Aggregate, _Mapping]] = ...) -> None: ...

class FetchAttachmentRequest(_message.Message):
    __slots__ = ("header", "attachment")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    ATTACHMENT_FIELD_NUMBER: _ClassVar[int]
    header: RequestHeader
    attachment: Attachment
    def __init__(self, header: _Optional[_Union[RequestHeader, _Mapping]] = ..., attachment: _Optional[_Union[Attachment, _Mapping]] = ...) -> None: ...

class FetchAttachmentResponse(_message.Message):
    __slots__ = ("response_header", "file")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    file: File
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., file: _Optional[_Union[File, _Mapping]] = ...) -> None: ...
