from .element import Element


class CameraLiveView(Element):
    type = "uiCameraLiveView"

    def __init__(
        self,
        camera_name: str,
        stream_name: str,
        allow_ptz_control: bool,
        display_name: str = "Live View",
        name: str = "History",
        **kwargs,
    ):
        self.stream_name = stream_name
        self.camera_name = camera_name
        self.allow_ptz_control = allow_ptz_control
        self.presets = []
        self.active_preset = None
        super().__init__(name=name, display_name=display_name, **kwargs)

    def to_dict(self):
        res = super().to_dict()
        res["cameraName"] = self.camera_name
        res["streamName"] = self.stream_name
        res["ptzControl"] = self.allow_ptz_control
        res["presets"] = self.presets
        res["activePreset"] = self.active_preset
        return res


class CameraHistory(Element):
    type = "uiCameraHistory"

    def __init__(
        self,
        camera_name: str,
        display_name: str = "History",
        name: str = "history",
        **kwargs,
    ):
        self.camera_name = camera_name
        self.presets = []
        self.active_preset = None
        super().__init__(name=name, display_name=display_name, **kwargs)

    def to_dict(self):
        res = super().to_dict()
        res["cameraName"] = self.camera_name
        res["ptzControl"] = True
        res["presets"] = self.presets
        res["activePreset"] = self.active_preset
        return res
