from .element import Element
from .submodule import Container


class Camera(Container):
    """Represents a camera element in the UI.

    Parameters
    ----------
    name: str
        The name of the camera.
    display_name: str, optional
        The display name of the camera.
    uri: str, optional
        The URI for the camera feed.
    output_type: str, optional
        The type of output (e.g., 'mp4').
    mp4_output_length: int, optional
        The length of the MP4 output in seconds.
    wake_delay: int, optional
        The delay before the camera wakes up, in seconds.
    children: list[:class:`Element`], optional
        Optional child elements of the camera.
    """

    type = "uiCamera"

    def __init__(
        self,
        name,
        display_name: str = None,
        uri: str = None,
        output_type: str = None,
        mp4_output_length: int = None,
        wake_delay: int = 5,
        children: list[Element] | None = None,
        **kwargs,
    ):
        super().__init__(
            name,
            display_name,
            children=children,
            **kwargs,
            is_available=None,
            help_str=None,
        )
        # fixme: do we need to specify is_available and help_str to be None?

        self.uri = uri
        self.output_type = output_type
        self.mp4_output_length = mp4_output_length
        self.wake_delay = wake_delay

    def to_dict(self):
        # Need to override the to_dict method and ensure that if the children field is an empty dict, it is removed
        result = super().to_dict()
        if not self.children:
            result.pop("children", None)
        return result


class CameraHistory(Camera):
    """Represents a camera history element in the UI."""

    type = "uiCameraFeed"
