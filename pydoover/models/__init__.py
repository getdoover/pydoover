from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data import (
        Aggregate,
        AggregateUpdateEvent,
        Alarm,
        AlarmOperator,
        AlarmState,
        AgentAggregate,
        AgentNotificationResponse,
        Attachment,
        BadRequestError,
        BatchAggregateResponse,
        BatchMessageResponse,
        Channel,
        ChannelID,
        ChannelSyncEvent,
        ConnectionConfig,
        ConnectionDetail,
        ConnectionDetermination,
        ConnectionStatus,
        ConnectionSubscription,
        ConnectionSubscriptionLog,
        ConnectionType,
        DataPoint,
        DeploymentEvent,
        DooverAPIError,
        DooverConnectionStatus,
        EventSubscription,
        File,
        ForbiddenError,
        HTTPError,
        IngestionEndpointEvent,
        ManualInvokeEvent,
        Message,
        MessageCreateEvent,
        MessageUpdateEvent,
        NotFoundError,
        Notification,
        NotificationEndpoint,
        NotificationSeverity,
        NotificationSubscription,
        NotificationSubscriptionEndpoint,
        NotificationType,
        OneShotMessage,
        ProcessorTokenResponse,
        ScheduleEvent,
        SubscriptionInfo,
        TimeseriesResponse,
        TokenRefreshError,
        TurnCredential,
        UnauthorizedError,
    )

__all__ = [
    "Aggregate",
    "AggregateUpdateEvent",
    "Alarm",
    "AlarmOperator",
    "AlarmState",
    "AgentAggregate",
    "AgentNotificationResponse",
    "Attachment",
    "BatchAggregateResponse",
    "BatchMessageResponse",
    "Channel",
    "ChannelID",
    "ChannelSyncEvent",
    "DataPoint",
    "ConnectionConfig",
    "ConnectionDetail",
    "ConnectionDetermination",
    "ConnectionStatus",
    "ConnectionSubscription",
    "ConnectionSubscriptionLog",
    "ConnectionType",
    "BadRequestError",
    "DooverAPIError",
    "DeploymentEvent",
    "DooverConnectionStatus",
    "EventSubscription",
    "File",
    "ForbiddenError",
    "IngestionEndpointEvent",
    "ManualInvokeEvent",
    "HTTPError",
    "Message",
    "MessageCreateEvent",
    "MessageUpdateEvent",
    "NotFoundError",
    "Notification",
    "NotificationEndpoint",
    "NotificationSeverity",
    "NotificationSubscription",
    "NotificationSubscriptionEndpoint",
    "NotificationType",
    "OneShotMessage",
    "ProcessorTokenResponse",
    "ScheduleEvent",
    "SubscriptionInfo",
    "TimeseriesResponse",
    "TokenRefreshError",
    "TurnCredential",
    "UnauthorizedError",
]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    data_module = import_module(".data", __name__)
    value = getattr(data_module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
