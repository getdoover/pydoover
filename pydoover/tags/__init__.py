from collections import OrderedDict
from typing import Any, Iterator, NoReturn, overload

from ..utils import call_maybe_async, get_is_async, maybe_async


class NotSet:
    """Sentinel used when a tag has not been assigned a value."""


class Tag:
    """Represents a single declared tag definition."""

    def __init__(self, tag_type: str, default: Any = NotSet, name: str | None = None):
        self.tag_type = tag_type
        self.name = name
        self.default = default
        self._declared_attr_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert this tag definition to its schema-style dictionary form."""
        data = {"type": self.tag_type}
        if self.default is not NotSet:
            data["default"] = self.default
        return data

    def to_schema(self) -> dict[str, Any]:
        """Alias for :meth:`to_dict` to match the rest of the declarative API."""
        return self.to_dict()

    def __repr__(self) -> str:
        return f"Tag(name={self.name!r}, tag_type={self.tag_type!r}, default={self.default!r})"

    def _raise_unbound_error(self) -> NoReturn:
        raise RuntimeError(
            "Declared Tag definitions are not runtime values. "
            "Access tags through a Tags instance."
        )

    @property
    def value(self) -> Any:
        self._raise_unbound_error()

    def get(self) -> Any:
        self._raise_unbound_error()

    def set(self, value: Any) -> Any:
        del value
        self._raise_unbound_error()

    def clear(self) -> Any:
        self._raise_unbound_error()

    def is_set(self) -> bool:
        self._raise_unbound_error()

    def increment(self, amount: int | float = 1) -> Any:
        del amount
        self._raise_unbound_error()

    def decrement(self, amount: int | float = 1) -> Any:
        del amount
        self._raise_unbound_error()

    def __str__(self) -> str:
        self._raise_unbound_error()

    def __bool__(self) -> bool:
        self._raise_unbound_error()

    def __int__(self) -> int:
        self._raise_unbound_error()

    def __float__(self) -> float:
        self._raise_unbound_error()

    def __lt__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()

    def __le__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()

    def __gt__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()

    def __ge__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()


class BoundTag:
    """Manager-backed runtime view of a declared tag.

    A ``BoundTag`` is what you interact with on a :class:`Tags` instance.
    Reads and writes are delegated to the registered tag manager.
    """

    _NUMERIC_TAG_TYPES = {"number", "integer", "float"}

    def __init__(self, tags: "Tags", declaration: "_DeclaredTag"):
        self._tags = tags
        self._declaration = declaration

    @property
    def _is_async(self) -> bool:
        return self._tags._is_async

    @property
    def name(self) -> str:
        """str: The resolved runtime name of this tag."""
        return self._declaration.name

    @property
    def tag_type(self) -> str:
        """str: The declared tag type."""
        return self._declaration.template.tag_type

    @property
    def default(self) -> Any:
        """Any: The default value returned when no runtime value exists."""
        return self._declaration.template.default
    
    @property
    def value(self) -> Any:
        """Any: Convenience alias for :meth:`get`."""
        return self.get()

    def get(self) -> Any:
        """Return the current value of this tag from the registered manager."""
        return self._tags._get_tag_value(self._declaration.attr_name)

    @maybe_async()
    def set(self, value: Any) -> None:
        """Set the current value of this tag.

        In async contexts this follows the repo's ``maybe_async`` pattern and
        should be awaited.
        """
        self._tags._set_tag_value(self._declaration.attr_name, value)

    async def set_async(self, value: Any) -> None:
        """Async variant of :meth:`set`."""
        await call_maybe_async(
            self._tags._set_tag_value_async,
            self._declaration.attr_name,
            value,
        )

    @maybe_async()
    def clear(self) -> None:
        """Reset this tag back to its declared default value."""
        self.set(self.default)

    async def clear_async(self) -> None:
        """Async variant of :meth:`clear`."""
        await self.set_async(self.default)

    def is_set(self) -> bool:
        """Return ``True`` when this tag currently has a concrete value."""
        return self.get() is not NotSet

    @maybe_async()
    def increment(self, amount: int | float = 1) -> Any:
        """Increment a numeric tag and return the new value."""
        self._validate_numeric("increment")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot increment unset tag '{self.name}'.")
        new_value = current + amount
        self.set(new_value)
        return new_value

    async def increment_async(self, amount: int | float = 1) -> Any:
        """Async variant of :meth:`increment`."""
        self._validate_numeric("increment")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot increment unset tag '{self.name}'.")
        new_value = current + amount
        await self.set_async(new_value)
        return new_value

    @maybe_async()
    def decrement(self, amount: int | float = 1) -> Any:
        """Decrement a numeric tag and return the new value."""
        self._validate_numeric("decrement")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot decrement unset tag '{self.name}'.")
        new_value = current - amount
        self.set(new_value)
        return new_value

    async def decrement_async(self, amount: int | float = 1) -> Any:
        """Async variant of :meth:`decrement`."""
        self._validate_numeric("decrement")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot decrement unset tag '{self.name}'.")
        new_value = current - amount
        await self.set_async(new_value)
        return new_value

    def _validate_numeric(self, operation: str) -> None:
        if self.tag_type not in self._NUMERIC_TAG_TYPES:
            raise TypeError(
                f"Cannot {operation} non-numeric tag '{self.name}' of type '{self.tag_type}'."
            )

    def _compare(self, other: Any, comparator):
        return comparator(self.get(), other)

    def __repr__(self) -> str:
        return f"BoundTag(name={self.name!r}, value={self.get()!r})"

    def __copy__(self):
        return self

    def __deepcopy__(self, _memo):
        return self

    def __str__(self) -> str:
        return str(self.get())

    def __bool__(self) -> bool:
        return bool(self.get())

    def __int__(self) -> int:
        return int(self.get())

    def __float__(self) -> float:
        return float(self.get())

    def __eq__(self, other: Any) -> bool:
        return self.get() == other

    def __lt__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a < b)

    def __le__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a <= b)

    def __gt__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a > b)

    def __ge__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a >= b)


class _DeclaredTag:
    def __init__(self, attr_name: str, template: Tag):
        self.attr_name = attr_name
        self.template = template

    @property
    def name(self) -> str:
        return self.template.name or self.attr_name

    @overload
    def __get__(self, instance: None, owner: type["Tags"]) -> Tag: ...

    @overload
    def __get__(self, instance: "Tags", owner: type["Tags"]) -> BoundTag: ...

    def __get__(self, instance: "Tags | None", owner: type["Tags"]) -> Tag | BoundTag:
        if instance is None:
            return self.template
        return BoundTag(instance, self)

    def __set__(self, instance: "Tags", value: Any) -> None:
        if isinstance(value, BoundTag):
            return
        instance._set_tag_value(self.attr_name, value)


class Tags:
    """Base class for declarative tag definitions.

    Subclasses declare available tags as class attributes. Instances expose
    manager-backed :class:`BoundTag` proxies and may also mutate their available
    tag set at runtime via :meth:`add_tag` and :meth:`remove_tag`.
    """

    __tag_declarations__: "OrderedDict[str, _DeclaredTag]" = OrderedDict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        declarations: "OrderedDict[str, _DeclaredTag]" = OrderedDict()
        for base in reversed(cls.__mro__[1:]):
            declarations.update(getattr(base, "__tag_declarations__", {}))

        for attr_name, value in list(cls.__dict__.items()):
            if not isinstance(value, Tag):
                continue

            value._declared_attr_name = attr_name
            declaration = _DeclaredTag(attr_name, value)
            declarations[attr_name] = declaration
            setattr(cls, attr_name, declaration)

        cls.__tag_declarations__ = declarations

    def __init__(self):
        self._manager: Any | None = None
        self._is_async = False
        # Keep runtime declaration changes isolated to this instance.
        self._tag_declarations = OrderedDict(self.__class__.__tag_declarations__)

    async def setup(self, config: Any = None) -> None:
        """Mutate this tag collection before it is bound to a manager."""
        return None

    @property
    def definitions(self) -> list[Tag]:
        """list[Tag]: The declared tag definitions for this instance."""
        return [declaration.template for declaration in self._tag_declarations.values()]

    @property
    def values(self) -> dict[str, Any]:
        """dict[str, Any]: The current manager-backed values for all declared tags."""
        return {
            declaration.name: self._get_tag_value(attr_name)
            for attr_name, declaration in self._tag_declarations.items()
            if self._get_tag_value(attr_name) is not NotSet
        }

    def register_manager(self, manager: Any) -> None:
        """Bind this tag collection to a tag manager."""
        self._manager = manager
        self._is_async = get_is_async(bool(getattr(manager, "_is_async", False)))

    def _get_declaration(self, name: str) -> _DeclaredTag | None:
        for attr_name, declaration in self._tag_declarations.items():
            if attr_name == name or declaration.name == name:
                return declaration
        return None

    def add_tag(self, name: str, tag: Tag) -> Tag:
        """Add a tag definition to this instance.

        This is primarily intended for config-dependent tag factories, where the
        available tag set needs to be customized before user code runs.
        """
        if not isinstance(tag, Tag):
            raise TypeError("add_tag expects a Tag instance.")
        if self._get_declaration(name) is not None:
            raise ValueError(f"Tag '{name}' already exists.")

        declaration = _DeclaredTag(name, tag)
        if self._get_declaration(declaration.name) is not None:
            raise ValueError(f"Tag '{declaration.name}' already exists.")

        self._tag_declarations[name] = declaration
        return declaration.template

    def remove_tag(self, name: str) -> None:
        """Remove a tag definition from this instance."""
        declaration = self._get_declaration(name)
        if declaration is None:
            raise KeyError(name)
        del self._tag_declarations[declaration.attr_name]

    def _get_tag_value(self, name: str) -> Any:
        declaration = self._get_declaration(name)
        if declaration is None:
            raise AttributeError(f"Unknown tag '{name}'")

        if self._manager is None:
            return declaration.template.default

        return self._manager.get_tag(
            declaration.name,
            default=declaration.template.default,
        )

    def _set_tag_value(self, name: str, value: Any) -> None:
        declaration = self._get_declaration(name)
        if declaration is None:
            raise AttributeError(f"Unknown tag '{name}'")
        if self._manager is None:
            raise RuntimeError("Tags manager has not been registered.")

        self._manager.set_tag(declaration.name, value)

    async def _set_tag_value_async(self, name: str, value: Any) -> None:
        declaration = self._get_declaration(name)
        if declaration is None:
            raise AttributeError(f"Unknown tag '{name}'")
        if self._manager is None:
            raise RuntimeError("Tags manager has not been registered.")

        if getattr(self._manager, "_is_async", False) and hasattr(
            self._manager, "set_tag_async"
        ):
            await self._manager.set_tag_async(declaration.name, value)
            return

        await call_maybe_async(self._manager.set_tag, declaration.name, value)

    def get(self, name: str) -> BoundTag | None:
        """Alias for :meth:`get_tag`."""
        return self.get_tag(name)

    def get_tag(self, name: str) -> BoundTag | None:
        """Return the bound runtime proxy for a tag, if it exists."""
        declaration = self._get_declaration(name)
        if declaration is None:
            return None
        return BoundTag(self, declaration)

    def get_definition(self, name: str) -> Tag | None:
        """Return the declared :class:`Tag` definition for a tag, if it exists."""
        declaration = self._get_declaration(name)
        if declaration is None:
            return None
        return declaration.template

    def update(self, values: dict[str, Any]) -> None:
        """Update multiple tag values through their bound runtime proxies."""
        for key, value in values.items():
            tag = self.get_tag(key)
            if tag is not None:
                tag.set(value)

    def to_dict(self) -> dict[str, Any]:
        """Return the current manager-backed tag values."""
        return self.values

    def to_schema(self) -> dict[str, Any]:
        """Return the schema-style definitions for the current tag set."""
        return {
            declaration.name: declaration.template.to_schema()
            for declaration in self._tag_declarations.values()
        }

    def __iter__(self) -> Iterator[BoundTag]:
        for name in self._tag_declarations:
            tag = self.get_tag(name)
            if tag is not None:
                yield tag

    def __len__(self):
        return len(self._tag_declarations)

    def __getitem__(self, item: str) -> BoundTag:
        tag = self.get_tag(item)
        if tag is None:
            raise KeyError(item)
        return tag

    def __getattr__(self, name: str) -> BoundTag:
        tag = self.get_tag(name)
        if tag is None:
            raise AttributeError(name)
        return tag

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._tag_declarations)})"
