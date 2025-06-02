import inspect
import re

from typing import Any

from .element import Element


NAME_VALIDATOR = re.compile(r"^[a-zA-Z0-9_-]+$")


class Container(Element):
    """Represents a container for UI elements, such as a submodule or application.

    This class can hold multiple child elements and provides methods to manage them.

    Generally, this class is not called by a user directly, but rather through the `Submodule` or `Application` classes.

    Parameters
    ----------
    name: str
        The name of the container, used for identification.
    display_name: str
        The display name of the container, used for user interface representation.
    children: list[Element]
        A list of child elements contained within this container.
    status_icon: str, optional
        An icon representing the status of the container, if applicable.
    auto_add_elements: bool
        If True, automatically adds all elements defined in the container to its children.

    Attributes
    ----------
    status_icon: str
        The icon representing the status of the container, if applicable.
    """

    type = "uiContainer"

    def __init__(
        self,
        name,
        display_name=None,
        children: list[Element] = None,
        status_icon: str = None,
        auto_add_elements: bool = True,
        **kwargs,
    ):
        super().__init__(name, display_name, **kwargs)

        self._default_position = 101
        self._max_position = self._default_position

        # A list of doover_ui_elements
        self._children = dict()
        self.add_children(*children or [])

        self.status_icon = status_icon

        self._register_interactions()
        if auto_add_elements:
            self.add_children(
                *[
                    e
                    for name, e in inspect.getmembers(
                        self, predicate=lambda e: isinstance(e, Element)
                    )
                ]
            )

    def _register_interactions(self):
        for name, func in inspect.getmembers(
            self, predicate=lambda f: inspect.ismethod(f) and hasattr(f, "_ui_type")
        ):
            item = func._ui_type(**func._ui_kwargs)
            item.callback = func
            setattr(self, func.__name__, item)

    def to_dict(self):
        result = super().to_dict()

        if self.status_icon is not None:
            result["statusIcon"] = self.status_icon

        result["children"] = {name: c.to_dict() for name, c in self._children.items()}
        return result

    def get_diff(
        self,
        other: dict[str, Any],
        remove: bool = True,
        retain_fields: list | None = None,
    ) -> dict[str, Any] | None:
        retain_fields = retain_fields or []
        res = super().get_diff(other, remove=remove, retain_fields=retain_fields) or {}
        # this will account for all the "normal" attributes, but not the children, since dicts aren't hashable
        # (ie. you can't do dict1 == dict2 to see if they're equal)
        other_children = other.get("children", {})
        this_children = {name: c for name, c in self._children.items()}

        children_diff = dict()
        if remove:
            children_diff.update(
                {k: None for k in other_children if k not in this_children}
            )  # to_remove

        for name, child in this_children.items():
            try:
                diff = child.get_diff(
                    other_children[name], remove=remove, retain_fields=retain_fields
                )
                if diff is not None:
                    children_diff[name] = diff
            except KeyError:
                children_diff[name] = child.to_dict()

        if children_diff:
            res["children"] = children_diff

        if len(res) == 0:
            return None

        return res

    @property
    def children(self) -> list[Element]:
        """Returns a list of child elements contained within this container."""
        return list(self._children.values())

    def set_children(self, children: list[Element]):
        """Sets the children of this container to a new list of elements.


        This will clear the existing children and replace them with the new ones.

        Warnings
        ---------
        This method should generally not be used by a user, instead use `add_children` to add elements to the container.
        Elements should generally never be removed from a container - instead, set them to `hidden=True`.


        Parameters
        ----------
        children: list[Element]
            A list of child elements to set as the new children of this container.
        """
        self._children.clear()
        self._max_position = self._default_position
        self.add_children(*children)

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

    def get_element(self, element_name: str) -> Element | None:
        """Retrieves a child element by its name from this container.

        This will recursively look through all children and their children to find the element.
        """
        try:
            return self._children[element_name]
        except KeyError:
            pass

        for element in self._children.values():
            if isinstance(element, Container):
                elem = element.get_element(element_name)
                if elem is not None:
                    return elem


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
        name: str,
        display_name: str,
        children: list[Element] = None,
        status: str = None,
        is_collapsed: bool = False,
        **kwargs,
    ):
        super().__init__(name, display_name, children, **kwargs)

        self.status = status or kwargs.pop("status_string", None)
        self.collapsed = is_collapsed or kwargs.pop("collapsed", False)

    def to_dict(self):
        result = super().to_dict()
        if self.status is not None:
            result["statusString"] = self.status
        result["defaultOpen"] = not self.collapsed

        return result


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
        self.variant = kwargs.pop("variant", None)
        super().__init__(*args, **kwargs)

    def to_dict(self):
        result = super().to_dict()
        if self.variant is not None:
            result["variant"] = self.variant
        return result
