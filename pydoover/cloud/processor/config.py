from ...config import String, Integer, Array, Object, Boolean


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


class IngestionEndpointConfig(Object):
    def __init__(
        self,
        display_name: str = "Ingestion Endpoint",
        *,
        description: str = "Ingestion Endpoint configuration",
        **kwargs,
    ):
        super().__init__(display_name, description=description, **kwargs)

        self._name = "dv_proc_ingestion"

        self.cidr_ranges = Array(
            element=String("IP Range, e.g. 1.234.56.78/24 or 110.220.120.1/32"),
            display_name="CIDR Ranges",
            description="Accepted CIDR ranges for incoming requests",
        )
        self.signing_key = String(
            display_name="Signing Key",
            description="Private SHA256 signing key for the request. "
            "While not recommended, this may be `None` if no signed hash verification is required.",
        )
        self.signing_key_hash_header = String(
            display_name="SHA256 Hash Header",
            description="Header key for the hash of the signed payload (defaults to x-hmac-sha256 if signing_key is present)",
            default="x-hmac-sha256",
        )
        self.throttle = Integer(
            display_name="Throttle",
            description="The number of requests to allow per second. Due to internal limits, this cannot exceed 30.",
            default=10,
            maximum=30,
        )

        self.never_replace_token = Boolean(
            display_name="Never Replace Token",
            description="Set this to `True` if the token is difficult to change and must never change. "
            "This is not recommended from a security standpoint, however may be necessary in some situations."
            "If this option is disabled and then enabled, a new token will be generated at that point.",
            default=False,
        )
