from collections import OrderedDict
from typing import Any


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
        return instance._get_tag_value(self.attr_name)

    def __set__(self, instance, value):
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

    def get(self, name: str) -> Tag | None:
        declaration = self._get_declaration(name)
        if declaration is None:
            return None
        return declaration.template

    get_tag = get

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            tag = self.get(key)
            if tag is not None:
                tag.value = value

    def to_dict(self) -> dict[str, Any]:
        return self.values

    def to_schema(self) -> dict[str, Any]:
        return {
            declaration.name: declaration.template.to_schema()
            for declaration in self.__tag_declarations__.values()
        }

    def __iter__(self):
        return iter(self.definitions)

    def __len__(self):
        return len(self.__tag_declarations__)

    def __getitem__(self, item: str) -> Tag:
        tag = self.get(item)
        if tag is None:
            raise KeyError(item)
        return tag

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self.__tag_declarations__)})"
