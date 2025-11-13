from ...config import String, Integer, Array, Schema, Object, Enum

SCHEDULE_FREQUENCIES = [
    "Hourly",
    "Daily",
    "Weekly",
    "Monthly",
    "Quarterly",
    "Never"
]

class ReportConfig(Object):
    def __init__(self, display_name: str = "Multiplot Config"):
        super().__init__(display_name)
        
        self.devices = Array(
            "Devices",
            element=String("Device", pattern="\d+"),
            description="The list of devices to generate reports for.",
        )
        
        self.schedule_id = String(
            "Schedule",
            description="The name of the schedule to generate reports for.",
            default=None,
        )
        
        self.period_start = Integer(
            "Period From",
            description="The start of the period to generate reports for.",
            default=None,
        )
        
        self.period_end = Integer(
            "Period To",
            description="The end of the period to generate reports for.",
        )
        
        self.report_id = String(
            "Report Id",
            pattern="\d+",
            description="The Id of the report to generate.",
        )
        
        self.schedule_frequency = Enum("Colour", choices=SCHEDULE_FREQUENCIES, default="Never")
