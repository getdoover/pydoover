from typing import Any

from .notification import NotificationEndpoint, NotificationSubscription


class AgentNotificationResponse:
    def __init__(
        self,
        subscriptions: list[NotificationSubscription],
        subscribers: list[NotificationSubscription],
        endpoints: list[NotificationEndpoint],
    ):
        self.subscriptions = subscriptions
        self.subscribers = subscribers
        self.endpoints = endpoints

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            subscriptions=[
                NotificationSubscription.from_dict(s) for s in data["subscriptions"]
            ],
            subscribers=[
                NotificationSubscription.from_dict(s) for s in data["subscribers"]
            ],
            endpoints=[NotificationEndpoint.from_dict(e) for e in data["endpoints"]],
        )

    def to_dict(self):
        return {
            "subscriptions": [s.to_dict() for s in self.subscriptions],
            "subscribers": [s.to_dict() for s in self.subscribers],
            "endpoints": [e.to_dict() for e in self.endpoints],
        }
