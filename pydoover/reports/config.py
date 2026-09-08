"""Shared configuration for report generator applications.

Every report generator needs the same handful of config elements: which
devices it may read, when it runs, what timezone to render timestamps in,
and who the finished report gets emailed to. Defining them here means a new
report generator inherits them by subclassing :class:`ReportConfig`, rather
than re-declaring them (and, in practice, forgetting one — most often the
email destinations, leaving reports generated but never delivered).
"""

from ..config import Array, Schema, String
from ..processor.config import (
    ExtendedPermissionsConfig,
    ScheduleConfig,
    TimezoneConfig,
)


class EmailConfig(Array):
    """Email addresses the generated report is sent to."""

    def __init__(
        self,
        display_name: str = "Email Destinations",
        *,
        description: str = "Email addresses to send this report to",
        **kwargs,
    ):
        super().__init__(
            display_name,
            name="dv_emails",
            description=description,
            element=String("Email Address", name="dv_email"),
            **kwargs,
        )


class ReportConfig(Schema):
    """Base config schema for a report generator application.

    Subclass this in your report generator and add whatever app-specific
    elements you need::

        from pydoover import config
        from pydoover.reports import ReportConfig

        class MyReportConfig(ReportConfig):
            output_layout = config.Enum(
                "Output Layout", choices=["Single File", "Separate Files"]
            )
    """

    dv_proc_extended_permissions = ExtendedPermissionsConfig()
    dv_proc_schedules = ScheduleConfig(
        allowed_modes=["cron"], default="cron(0 8 1 * ?)"
    )
    dv_proc_timezone = TimezoneConfig()
    dv_emails = EmailConfig()
