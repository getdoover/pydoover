from ...config import String, Integer, Array


class ManySubscriptionConfig(Array):
    def __init__(
        self,
        display_name: str = "Subscription",
        *,
        description: str = "A list of channels to subscribe to.",
        **kwargs,
    ):
        element = SubscriptionConfig()
        element._name = "dv_proc_subscription"
        super().__init__(
            display_name, element=element, description=description, **kwargs
        )
        self._name = "dv_proc_subscriptions"


class SubscriptionConfig(String):
    def __init__(
        self,
        display_name: str = "Channel Subscription",
        *,
        description: str = "The name of the channel to subscribe to",
        **kwargs,
    ):
        super().__init__(display_name, description=description, **kwargs)
        self._name = "dv_proc_subscriptions"


class ScheduleConfig(String):
    def __init__(
        self,
        display_name: str = "Schedule",
        *,
        description: str = "The interval in minutes to run the task. 0 to disable.",
        **kwargs,
    ):
        super().__init__(
            display_name, description=description, **kwargs
        )
        self._name = "dv_proc_schedules"
