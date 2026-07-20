import zoneinfo

from ..config import (
    Application,
    Array,
    Boolean,
    DevicesConfig,
    Enum,
    GroupsConfig,
    Integer,
    Object,
    String,
    NotSet,
)


class ManySubscriptionConfig(Array):
    def __init__(
        self,
        display_name: str = "Subscription",
        *,
        description: str = "A list of channels to subscribe to.",
        **kwargs,
    ):
        super().__init__(
            display_name,
            element=SubscriptionConfig(name="dv_proc_subscription"),
            description=description,
            name="dv_proc_subscriptions",
            **kwargs,
        )


class SubscriptionConfig(String):
    def __init__(
        self,
        display_name: str = "Channel Subscription",
        *,
        description: str = "The name of the channel to subscribe to",
        name: str = "dv_proc_subscriptions",
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            name=name,
            **kwargs,
        )


class ScheduleConfig(String):
    def __init__(
        self,
        display_name: str = "Schedule",
        *,
        description: str = "Specify a schedule to run this task.",
        allowed_modes: list[str] | None = None,
        **kwargs,
    ):
        allowed_modes = allowed_modes or ["cron", "rate", "disabled"]
        if len(allowed_modes) >= 3:
            format_value = "doover-schedule"
        else:
            format_value = "doover-schedule-" + "-".join(allowed_modes)
        super().__init__(
            display_name,
            description=description,
            format=format_value,
            name="dv_proc_schedules",
            **kwargs,
        )


class IngestionEndpointConfig(Object):
    cidr_ranges = Array(
        display_name="CIDR Ranges",
        element=String(
            "IP Range", description="IP Range, e.g. 1.234.56.78/24 or 110.220.120.1/32"
        ),
        description="Accepted CIDR ranges for incoming requests",
    )
    signing_key = String(
        display_name="Signing Key",
        description="Private SHA256 signing key for the request. "
        "While not recommended, this may be `None` if no signed hash verification is required.",
        default="",
    )
    signing_key_hash_header = String(
        display_name="SHA256 Hash Header",
        description="Header key for the hash of the signed payload (defaults to x-hmac-sha256 if signing_key is present)",
        default="x-hmac-sha256",
    )
    throttle = Integer(
        display_name="Throttle",
        description="The number of requests to allow per second. Due to internal limits, this cannot exceed 30.",
        default=10,
        maximum=30,
    )
    never_replace_token = Boolean(
        display_name="Never Replace Token",
        description="Enable this if the token is difficult to change and must never change. "
        "This is not recommended from a security standpoint, however may be necessary in some situations."
        "If this option is disabled and then enabled, a new token will be generated at that point.",
        default=False,
    )
    mini_token = Boolean(
        display_name="Mini Token",
        description="Enable this to generate a mini token for use with the ingestion endpoint. "
        "Mini tokens are ~70 bytes, compared with the ~900 bytes of a regular token. "
        "Generally, this is not advised as it adds complexity and latency to ingestion calls, "
        "however may be desirable in especially low-bandwidth and embedded environments. "
        "There is no security difference in the two tokens.",
        default=False,
    )

    def __init__(
        self,
        display_name: str = "Ingestion Endpoint",
        *,
        description: str = "Ingestion Endpoint configuration",
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            name="dv_proc_ingestion",
            **kwargs,
        )


class DataPermissions(String):
    """The permission mask granted on each device in an extended-permissions set.

    Rendered as a permission picker in the dashboard via ``format``. The value is
    a decimal bitmask string, matching how doover-control stores grants
    (``{"permission_id": "ag:123", "permission": "1099511627774"}``).

    Leave unset to grant every permission — that is what every app did before
    this field existed, so omitting it has to stay backwards compatible. ``"0"``
    grants nothing, for an app that wants ``DEVICE_MAP`` without any access to
    the devices in it.

    Note this governs only the devices resolved from ``devices`` / ``groups`` /
    ``apps_installed`` / ``all_devices``. An app's grants on its *own* agent are
    what let it function at all, and are unaffected.
    """

    def __init__(
        self,
        display_name: str = "Data Permissions",
        *,
        description: str = (
            "Permissions granted on each device this app has access to. Leave "
            "empty to grant all permissions. Set to 0 to grant none — for an app "
            "that only needs the device map, not access to the devices."
        ),
        name: str = "dd_permissions",
        **kwargs,
    ):
        # Both pinned rather than inferred: the runtime key is derived from the
        # *display name* unless `name` is given, so this would otherwise land as
        # `data_permissions` and doover-control would read the wrong key. And
        # ConfigElement assigns `self.format = format`, so a class attribute
        # would be shadowed by None.
        super().__init__(
            display_name,
            description=description,
            name=name,
            format="dd_permissions",
            **kwargs,
        )


# Optional fields apps may request alongside name/display_name in DEVICE_MAP via
# `extra_fields=` on ExtendedPermissionsConfig. Each entry is a Django ORM
# lookup path on the Device model — doover-control passes them straight to
# `.values()`, so what you put here is what app code reads out of DEVICE_MAP.
# This whitelist exists so apps fail fast at schema-build time on a typo, and
# so the allowed set is documented in one place. Keep in sync with the
# matching whitelist in doover_control/applications/models.py.
ALLOWED_EXTRA_DEVICE_FIELDS = (
    "id",
    "name",
    "display_name",
    "type__id",
    "type__name",
    "type__config",
    "group__id",
    "group__name",
    "organisation__id",
    "organisation__name",
    "latitude",
    "longitude",
    "fa_icon",
    "notes",
    "extra_config",
    # Compound entries — each expands on the doover-control side to a list of
    # dicts (active installs only). The bare name is sugar for "all sub-fields";
    # `<compound>__<subfield>` opts into a specific subset.
    "app_installs",
    "app_installs__id",
    "app_installs__name",
    "app_installs__display_name",
    "app_installs__application_id",
    "app_installs__application_name",
    "solution_installs",
    "solution_installs__id",
    "solution_installs__display_name",
    "solution_installs__solution_id",
    "solution_installs__solution_display_name",
)


class ExtendedPermissionsConfig(Object):
    devices = DevicesConfig(
        description="List of devices to grant extended permissions to."
    )
    groups = GroupsConfig()
    apps_installed = Array(
        display_name="Apps Installed",
        element=Application("Application"),
        description="Permission will be given to any devices which have any of the apps listed installed.",
    )
    all_devices = Boolean(
        display_name="All Devices",
        description="Permission will be given for all devices in this organisation. This is a very far-reaching permission to grant!",
        default=False,
    )
    dd_permissions = DataPermissions(hidden=True, default=None)

    """
    If `default_device_group` is True, the permissions will default to the group that the device is in. Useful to mimic doover 1.0 behaviour.

    `extra_fields` opts the app into additional per-device entries in DEVICE_MAP.
    `name` and `display_name` are always included; anything in `extra_fields`
    must be a member of `ALLOWED_EXTRA_DEVICE_FIELDS`, or a sub-key lookup on
    the JSON `extra_config` / `type__config` fields (e.g.
    `extra_config__battery_voltage_tag`). Pick the minimum set the app actually
    consumes — every requested field costs a column (and `type_name` forces a
    join) at deployment build time, multiplied by every device the processor
    has permission for.
    """

    def __init__(
        self,
        default_device_group: bool = NotSet,
        extra_fields: list[str] | None = None,
    ):
        super().__init__(
            "Devices",
            description="Give Permission to access devices.",
            name="dv_proc_extended_permissions",
        )

        self.default_device_group = default_device_group

        if extra_fields is not None:
            invalid = [
                f
                for f in extra_fields
                if f not in ALLOWED_EXTRA_DEVICE_FIELDS
                and not f.startswith(("extra_config__", "type__config__"))
            ]
            if invalid:
                raise ValueError(
                    f"Unknown extra_fields {invalid!r}; allowed: "
                    f"{sorted(ALLOWED_EXTRA_DEVICE_FIELDS)}"
                )
        self.extra_fields = extra_fields

    def to_dict(self):
        res = super().to_dict()
        if self.default_device_group is not NotSet:
            res["x-defaultDeviceGroup"] = self.default_device_group
        if self.extra_fields is not None:
            res["x-extraDeviceFields"] = list(self.extra_fields)
        return res


class TimezoneConfig(Enum):
    def __init__(
        self,
        display_name: str = "Timezone",
        *,
        description: str = "The timezone to use for the report.",
        default="Australia/Brisbane",
        **kwargs,
    ):
        super().__init__(
            display_name,
            choices=list(sorted(zoneinfo.available_timezones())),
            description=description,
            default=default,
            name="dv_proc_timezone",
            **kwargs,
        )


class SerialNumberConfig(String):
    def __init__(
        self,
        display_name: str = "Serial Number",
        *,
        description: str = "Device Serial Number",
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            name="dv_serial_number",
            **kwargs,
        )


class EgressChannelConfig(String):
    """Egress channel for integrations.

    The integration will subscribe to this channel on all devices associated.

    Generally, you should set a default in the app so users don't have to worry about this.
    """

    def __init__(
        self,
        display_name: str = "Egress Channel",
        *,
        description: str = "Channel to subscribe on every device configured.",
        hidden: bool = True,
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            name="dv_egress_channel",
            hidden=hidden,
            **kwargs,
        )


class InvocationPublishTarget(Object):
    """One destination for the per-invocation summary message."""

    agent_id = String(
        "Agent ID",
        default=None,
        description="Agent to post the invocation summary on behalf of. Defaults to this agent.",
    )
    channel = String(
        "Channel",
        description="Channel name on the target agent.",
    )

    def __init__(
        self,
        display_name: str = "Invocation Publish Target",
        **kwargs,
    ):
        super().__init__(
            display_name, name="inv_target", additional_elements=False, **kwargs
        )


class ProcessorConfig(Object):
    """Framework-level runtime config for processor invocations.

    Delivered via ``deployment_config["dv_proc_config"]``. Users can also
    embed this in their app schema to surface the fields in the Doover UI
    and set app-level defaults; per-install overrides then merge in via
    the normal deployment-config flow.
    """

    log_level = Enum(
        "Log Level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        description="Default log level for the root logger after setup.",
        name="log_level",
    )
    log_overrides = Object(
        "Log Level Overrides",
        additional_elements=True,
        default={},
        description="Per-logger level overrides, e.g. {'pydoover.api': 'WARNING'}.",
        name="log_overrides",
    )
    inv_targets = Array(
        "Invocation Publish Targets",
        element=InvocationPublishTarget(),
        default=[{"agent_id": None, "channel": "dv-proc-inv-$app_id"}],
        description="Agents/channels to fan the invocation summary out to. Empty = disabled.",
        name="inv_targets",
    )
    live_logs = Boolean(
        "Live Logs",
        default=False,
        hidden=True,
        description="Stream log records to a Doover channel during the invocation so they "
        "can be tailed live from the CLI or web UI. Intended for app development; "
        "leave disabled in production (adds per-invocation latency and channel writes).",
        name="live_logs",
    )

    def __init__(
        self,
        display_name: str = "Processor Config",
        *,
        description: str = "Framework-level processor runtime config.",
        **kwargs,
    ):
        super().__init__(
            display_name,
            description=description,
            name="dv_proc_config",
            additional_elements=False,
            **kwargs,
        )
