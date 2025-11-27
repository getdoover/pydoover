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
        description: str = "Specify a schedule to run this task.",
        allowed_modes=["cron", "rate", "disabled"],
        **kwargs,
    ):
        if len(allowed_modes) >= 3:
            format = "doover-schedule"
        else:
            format = "doover-schedule-" + "-".join(allowed_modes)
        super().__init__(
            display_name, description=description, format=format, **kwargs
        )
        self._name = "dv_proc_schedules"
