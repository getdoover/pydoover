import inspect
import re

from .misc import NotSet
from .declarative import normalize_ui_value
from .element import Element


NAME_VALIDATOR = re.compile(r"^[a-zA-Z0-9_-]+$")


class Container(Element):
    """Represents a container for UI elements, such as a submodule or application.

    This class can hold multiple child elements and provides methods to manage them.

    Generally, this class is not called by a user directly, but rather through the `Submodule` or `Application` classes.

    Parameters
    ----------
    display_name: str
        The display name of the container, used for user interface representation.
    children: list[Element]
        A list of child elements contained within this container.
    """

    type = "uiContainer"

    def __init__(
        self,
        display_name: str,
        children: list[Element] = None,
        **kwargs,
    ):
        super().__init__(display_name, **kwargs)

        self._default_position = 101
        self._max_position = self._default_position

        # A list of doover_ui_elements
        self._children = dict()
        self.add_children(*children or [])

        self.add_children(
            *[
                e
                for name, e in inspect.getmembers(
                    self, predicate=lambda e: isinstance(e, Element)
                )
            ]
        )

    def to_dict(self):
        result = super().to_dict()
        result["children"] = {name: c.to_dict() for name, c in self._children.items()}
        return normalize_ui_value(result)

    def add_children(self, *children: Element):
        """Adds one or more child elements to this container.

        This method will automatically assign a position to each child if it does not already have one.

        Warnings
        --------
        You should generally only call this method once during setup of the container,
        when you generate all elements and add them at once. Old applications may call this multiple times during setup,
        but that is not the suggested best practice going forward.

        Parameters
        ----------
        *children
            Child elements to add to this container. They must be of type :class:`pydoover.ui.Element`
        """

        # if not hasattr(self, "_default_position"):
        #     self._default_position = 101
        # if not hasattr(self, "_max_position"):
        #     self._max_position = self._default_position

        for c in children:
            if not isinstance(c, Element):
                continue

            name = c.name.strip()
            if not NAME_VALIDATOR.match(name):
                raise RuntimeError(
                    f"Invalid name '{name}' for element '{c}'. Valid characters include letters, numbers, and underscores."
                )

            self._children[name] = c
            c.parent = self

            if not c.position:
                c.position = self._max_position
                self._max_position += 1

        return self

    def remove_children(self, *children: Element):
        """Removes one or more child elements from this container.

        Warnings
        --------
        Best practice prefers setting `hidden=True` on elements instead of removing them from the container.

        Parameters
        ----------
        *children
            Child elements to remove from this container. They must be of type :class:`pydoover.ui.Element`
        """
        for c in children:
            try:
                if c.name in self._children:
                    del self._children[c.name]
            except KeyError:
                pass

        ## for all self._children, call remove_children on them
        for c in self._children.values():
            if isinstance(c, Container):
                c.remove_children(*children)

    def clear_children(self):
        """Clears all child elements from this container.

        You probably don't want or need to call this method.
        """
        self._children.clear()


class Submodule(Container):
    """Represents a submodule within a UI application, which can contain other elements and has a status.

    Submodules are useful for grouping logical components of an application together,
    but be careful not to overuse them as they can be burdensome on a user!

    Parameters
    ----------
    name: str
        The name of the submodule, used for identification.
    display_name: str
        The display name of the submodule, used for user interface representation.
    children: list[Element], optional
        A list of child elements contained within this submodule. Defaults to an empty list.
    status: str, optional
        A status string representing the current state of the submodule. Defaults to None.
    is_collapsed: bool, optional
        Whether the submodule is initially collapsed in the UI. Defaults to False.
    """

    type = "uiSubmodule"

    def __init__(
        self,
        display_name: str,
        children: list[Element] = None,
        status: str = NotSet,
        is_collapsed: bool = False,
        **kwargs,
    ):
        super().__init__(display_name, children, **kwargs)

        self.status = status
        self.is_collapsed = is_collapsed

    def to_dict(self):
        result = super().to_dict()
        if self.status is not None:
            result["statusString"] = self.status
        result["defaultOpen"] = not self.is_collapsed

        return normalize_ui_value(result)


class Application(Container):
    """Represents a UI application element.

    This is generally not invoked by the user, but is used to represent and store all UI elements for an application.

    Attributes
    ----------
    variant: str, optional
        The variant of the application, used to display applications differently.
        Defaults to `stacked`. Valid options are `stacked`, `submodule`.
    """

    type = "uiApplication"

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop("variant", NotSet)
        super().__init__(*args, **kwargs)

    def to_dict(self):
        result = super().to_dict()
        if self.variant is not NotSet:
            result["variant"] = self.variant
        return normalize_ui_value(result)


class RemoteComponent(Container):
    """Represents a remote component in the UI.

    Parameters
    ----------
    name: str
        The name of the remote component.
    display_name: str
        The display name of the remote component.
    component_url: str
        The URL of the remote component.
    """

    type = "uiRemoteComponent"

    def __init__(
        self,
        display_name: str,
        component_url: str,
        children: list[Element] = None,
        **kwargs,
    ):
        super().__init__(display_name, children, **kwargs)
        self.component_url = component_url
        self.kwargs = kwargs

    def to_dict(self):
        res = super().to_dict()
        res.update(self.kwargs)
        return normalize_ui_value(res)


class TabContainer(Element):
    type = "uiTabs"

    def __init__(self, children: list[Element], **kwargs):
        self.children = children
        super().__init__(**kwargs)

    def to_dict(self):
        res = super().to_dict()
        res["children"] = {c.name: c.to_dict() for c in self.children}
        return normalize_ui_value(res)
