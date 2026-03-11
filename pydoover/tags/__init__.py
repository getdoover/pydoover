from collections import OrderedDict
from typing import Any

from ..utils import call_maybe_async, get_is_async, maybe_async


class NotSet:
    """Sentinel used when a tag has not been assigned a value."""


class Tag:
    """Represents a single declared tag definition."""

    def __init__(self, tag_type: str, default: Any = NotSet, name: str | None = None):
        self.tag_type = tag_type
        self.name = name
        self.default = default

    def to_dict(self) -> dict[str, Any]:
        data = {"type": self.tag_type}
        if self.default is not NotSet:
            data["default"] = self.default
        return data

    def to_schema(self) -> dict[str, Any]:
        return self.to_dict()

    def __repr__(self) -> str:
        return f"Tag(name={self.name!r}, tag_type={self.tag_type!r}, default={self.default!r})"


class BoundTag:
    """Manager-backed runtime view of a declared tag."""

    _NUMERIC_TAG_TYPES = {"number", "integer", "float"}

    def __init__(self, tags: "Tags", declaration: "_DeclaredTag"):
        self._tags = tags
        self._declaration = declaration

    @property
    def _is_async(self) -> bool:
        return self._tags._is_async

    @property
    def name(self) -> str:
        return self._declaration.name

    @property
    def tag_type(self) -> str:
        return self._declaration.template.tag_type

    @property
    def default(self) -> Any:
        return self._declaration.template.default
    
    @property
    def value(self) -> Any:
        return self.get()

    def get(self) -> Any:
        return self._tags._get_tag_value(self._declaration.attr_name)

    @maybe_async()
    def set(self, value: Any) -> None:
        self._tags._set_tag_value(self._declaration.attr_name, value)

    async def set_async(self, value: Any) -> None:
        await call_maybe_async(
            self._tags._set_tag_value_async,
            self._declaration.attr_name,
            value,
        )

    @maybe_async()
    def clear(self) -> None:
        self.set(self.default)

    async def clear_async(self) -> None:
        await self.set_async(self.default)

    def is_set(self) -> bool:
        return self.get() is not NotSet

    @maybe_async()
    def increment(self, amount: int | float = 1) -> Any:
        self._validate_numeric("increment")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot increment unset tag '{self.name}'.")
        new_value = current + amount
        self.set(new_value)
        return new_value

    async def increment_async(self, amount: int | float = 1) -> Any:
        self._validate_numeric("increment")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot increment unset tag '{self.name}'.")
        new_value = current + amount
        await self.set_async(new_value)
        return new_value

    @maybe_async()
    def decrement(self, amount: int | float = 1) -> Any:
        self._validate_numeric("decrement")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot decrement unset tag '{self.name}'.")
        new_value = current - amount
        self.set(new_value)
        return new_value

    async def decrement_async(self, amount: int | float = 1) -> Any:
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

    def __get__(self, instance, owner):
        if instance is None:
            return self.template
        return BoundTag(instance, self)

    def __set__(self, instance, value):
        if isinstance(value, BoundTag):
            return
        instance._set_tag_value(self.attr_name, value)


class Tags:
    """Base class for declarative tag definitions."""

    __tag_declarations__: "OrderedDict[str, _DeclaredTag]" = OrderedDict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        declarations: "OrderedDict[str, _DeclaredTag]" = OrderedDict()
        for base in reversed(cls.__mro__[1:]):
            declarations.update(getattr(base, "__tag_declarations__", {}))

        for attr_name, value in list(cls.__dict__.items()):
            if not isinstance(value, Tag):
                continue

            declaration = _DeclaredTag(attr_name, value)
            declarations[attr_name] = declaration
            setattr(cls, attr_name, declaration)

        cls.__tag_declarations__ = declarations

    def __init__(self):
        self._manager = None
        self._is_async = False

    @property
    def definitions(self) -> list[Tag]:
        return [declaration.template for declaration in self.__tag_declarations__.values()]

    @property
    def values(self) -> dict[str, Any]:
        return {
            declaration.name: self._get_tag_value(attr_name)
            for attr_name, declaration in self.__tag_declarations__.items()
            if self._get_tag_value(attr_name) is not NotSet
        }

    def register_manager(self, manager) -> None:
        self._manager = manager
        self._is_async = get_is_async(getattr(manager, "_is_async", None))

    def _get_declaration(self, name: str) -> _DeclaredTag | None:
        for attr_name, declaration in self.__tag_declarations__.items():
            if attr_name == name or declaration.name == name:
                return declaration
        return None

    def _get_tag_value(self, name: str):
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

    def get(self, name: str) -> Tag | None:
        return self.get_tag(name)

    def get_tag(self, name: str) -> BoundTag | None:
        declaration = self._get_declaration(name)
        if declaration is None:
            return None
        return BoundTag(self, declaration)

    def get_definition(self, name: str) -> Tag | None:
        declaration = self._get_declaration(name)
        if declaration is None:
            return None
        return declaration.template

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            tag = self.get_tag(key)
            if tag is not None:
                tag.set(value)

    def to_dict(self) -> dict[str, Any]:
        return self.values

    def to_schema(self) -> dict[str, Any]:
        return {
            declaration.name: declaration.template.to_schema()
            for declaration in self.__tag_declarations__.values()
        }

    def __iter__(self):
        return iter(self.get_tag(name) for name in self.__tag_declarations__)

    def __len__(self):
        return len(self.__tag_declarations__)

    def __getitem__(self, item: str) -> Tag:
        tag = self.get_tag(item)
        if tag is None:
            raise KeyError(item)
        return tag

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self.__tag_declarations__)})"
