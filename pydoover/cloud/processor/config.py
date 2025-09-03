from ...config import String, Integer


class SubscriptionConfig(String):
    def __init__(
        self,
        display_name: str = "Subscription",
        *,
        description: str = "The name of the channel to subscribe to.",
        **kwargs,
    ):
        super().__init__(display_name, description=description, **kwargs)


class ScheduleConfig(Integer):
    def __init__(
        self,
        display_name: str = "Schedule",
        *,
        minimum: int = 0,
        description: str = "The interval in seconds to run the task. 0 to disable.",
        **kwargs,
    ):
        super().__init__(
            display_name, minimum=minimum, description=description, **kwargs
        )
