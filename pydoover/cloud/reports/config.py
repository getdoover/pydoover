from ...config import String, Array

class ReportDevicesConfig(Array):
    def __init__(
        self,
        display_name: str = "Devices",
        *,
        description: str = "A list of devices to generate reports for.",
        **kwargs,
    ):
        element = String("Device", pattern="\d+")
        element._name = "dv_rprt_devices"
        super().__init__(
            display_name, element=element, description=description, **kwargs
        )
        self._name = "dv_rprt_devices"