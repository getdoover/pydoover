from ...config import String, Array, Enum
import zoneinfo

class DevicesConfig(Array):
    def __init__(
        self,
        display_name: str = "Devices",
        *,
        description: str = "A list of devices to generate reports for.",
        **kwargs,
    ):
        element = String("Device", pattern="\d+", format="doover-device")
        element._name = "dv_proc_devices"
        super().__init__(
            display_name, element=element, description=description, **kwargs
        )
        self._name = "dv_proc_devices"
        
class TimezoneConfig(Enum):
    
    def __init__(
        self,
        display_name: str = "Timezone",
        *,
        description: str = "The timezone to use for the report.",
        default="Australia/Brisbane",
        **kwargs,
    ):
        choices = list(zoneinfo.available_timezones())
        super().__init__(display_name, choices=choices, description=description, default=default, **kwargs)
        self._name = "dv_proc_timezone"