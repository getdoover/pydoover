from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Generic, Self, TypeVar, overload

from ..config import Schema
from ..tags import BoundTag, NotSet, Tag, Tags


_TAG_TYPE_MAP = {
    "number": "number",
    "integer": "number",
    "float": "number",
    "string": "string",
    "boolean": "boolean",
    "bool": "boolean",
    "array": "array",
    "list": "array",
    "object": "object",
    "dict": "object",
}
_SKIP_BIND_ATTRS = {"parent", "_manager"}


class _MissingDefault:
    def __copy__(self):
        return self

    def __deepcopy__(self, _memo):
        return self


_MISSING = _MissingDefault()
ElementT = TypeVar("ElementT")


class UITagBinding:
    def __init__(
        self,
        tag_name: str,
        tag_type: str | None = None,
        default_value: Any = _MISSING,
    ):
        self.tag_name = tag_name
        self.tag_type = _TAG_TYPE_MAP.get(tag_type, tag_type) if tag_type else tag_type
        self.default_value = default_value

    def __copy__(self):
        return type(self)(
            self.tag_name,
            tag_type=self.tag_type,
            default_value=self.default_value,
        )

    def __deepcopy__(self, memo):
        return type(self)(
            copy.deepcopy(self.tag_name, memo),
            tag_type=copy.deepcopy(self.tag_type, memo),
            default_value=copy.deepcopy(self.default_value, memo),
        )

    def to_lookup(self) -> str:
        result = f"$tag.{self.tag_name}"
        if self.tag_type is not None:
            result += f":{self.tag_type}"
        if not _is_missing_default(self.default_value):
            if self.tag_type is None:
                result += ":string"
            result += f":{json.dumps(self.default_value, separators=(',', ':'))}"
        return result


class _DeclaredElement(Generic[ElementT]):
    def __init__(self, attr_name: str, template: ElementT):
        self.attr_name = attr_name
        self.template = template

    @overload
    def __get__(self, instance: None, owner: type["UI"]) -> ElementT: ...

    @overload
    def __get__(self, instance: "UI", owner: type["UI"]) -> ElementT: ...

    def __get__(self, instance: "UI | None", owner: type["UI"]) -> ElementT:
        if instance is None:
            return self.template
        return instance._elements[self.attr_name]

    def __set__(self, instance: "UI", value: ElementT) -> None:
        from .element import Element

        if not isinstance(value, Element):
            raise TypeError("ui.UI attributes must be Element instances.")
        instance._elements[self.attr_name] = value


class UI:
    __ui_declarations__: dict[str, _DeclaredElement] = dict()

    def __init_subclass__(
        cls,
        display_name: str = "$config.APP_DISPLAY_NAME",
        hidden: bool | str = "$config.hidden",
        position: int | str = "$config.position",
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)

        from .element import Element

        declarations: dict[str, _DeclaredElement] = dict()
        for base in reversed(cls.__mro__[1:]):
            declarations.update(getattr(base, "__ui_declarations__", {}))

        for attr_name, value in list(cls.__dict__.items()):
            if not isinstance(value, Element):
                continue

            declaration = _DeclaredElement(attr_name, value)
            declarations[attr_name] = declaration
            setattr(cls, attr_name, declaration)

        cls.__ui_declarations__ = declarations

        if display_name.startswith("$"):
            display_name = f"{display_name}:string"
        if isinstance(hidden, str):
            if not hidden.startswith("$"):
                raise ValueError(
                    "If `hidden` is a `str` it must start with `$` to represent a variable."
                )
            hidden = f"{hidden}:boolean:false"
        if isinstance(position, str) and not position.startswith("$"):
            if not position.startswith("$"):
                raise ValueError(
                    "If `position` is a `str` it must start with `$` to represent a variable."
                )
            position = f"{position}:number:50"

        cls.display_name = display_name
        cls.hidden = hidden
        cls.position = position

    def __init__(self, config: Schema, tags: Tags):
        self.config = config
        self.tags = tags

        self._elements: dict[str, Any] = dict(
            (name, copy.deepcopy(declaration.template))
            for name, declaration in self.__class__.__ui_declarations__.items()
        )

    @property
    def is_static(self):
        return self.setup.__func__ is not UI.setup

    async def setup(self, config: Any = None, tags: Tags | None = None) -> None:
        """Mutate this UI instance before it is bound and installed."""
        return None

    def to_dict(self):
        return {
            "displayString": self.display_name,
            "hidden": self.hidden,
            "position": self.position,
            "type": "uiApplication",
            "children": {e.name: e.to_dict() for e in self._elements.values()},
        }

    def export(self, fp: Path, app_name: str):
        if not self.is_static:
            raise RuntimeError(
                "Cannot statically generate a ui schema that has a `setup` override."
            )

        if fp.exists():
            data = json.loads(fp.read_text())
        else:
            data = {}

        try:
            data[app_name]["ui_schema"] = self.to_dict()
        except KeyError:
            data[app_name] = {"ui_schema": self.to_dict()}

        fp.write_text(json.dumps(data, indent=4))

    @property
    def children(self) -> list[Any]:
        return list(self._elements.values())

    def to_elements(self) -> list[Any]:
        return self.children

    def add_element(self, name: str, element: Any) -> Any:
        from .element import Element

        if not isinstance(element, Element):
            raise TypeError("add_element expects an Element instance.")
        self._elements[name] = element
        setattr(self, name, element)
        return element

    def remove_element(self, name: str) -> None:
        try:
            del self._elements[name]
        except KeyError as exc:
            raise KeyError(name) from exc
        self.__dict__.pop(name, None)

    def bind_tags(self, tags: Tags | None) -> Self:
        visited: set[int] = set()
        for element in self._elements.values():
            _bind_value(element, tags=tags, visited=visited)
        return self

    def __getattr__(self, name: str) -> Any:
        try:
            return self._elements[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def tag_ref(
    tag: BoundTag | Tag | UITagBinding | str,
    tag_type: str | None = None,
    default_value: Any = _MISSING,
) -> UITagBinding:
    if isinstance(tag, UITagBinding):
        return copy.deepcopy(tag)
    if isinstance(tag, BoundTag):
        return _binding_from_bound_tag(tag)
    if isinstance(tag, Tag):
        binding = _binding_from_tag(tag)
        if tag_type is None and _is_missing_default(default_value):
            return binding
        return UITagBinding(
            binding.tag_name,
            tag_type=tag_type or binding.tag_type,
            default_value=(
                binding.default_value
                if _is_missing_default(default_value)
                else default_value
            ),
        )
    return UITagBinding(tag, tag_type=tag_type, default_value=default_value)


bind_tag = tag_ref


def is_tag_reference(value: Any) -> bool:
    if isinstance(value, (UITagBinding, BoundTag, Tag)):
        return True
    if isinstance(value, dict):
        return any(is_tag_reference(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(is_tag_reference(v) for v in value)
    return False


def normalize_ui_value(value: Any, field_name: str | None = None) -> Any:
    if isinstance(value, UITagBinding):
        if field_name == "name":
            raise ValueError("UI field 'name' cannot reference a tag.")
        return value.to_lookup()

    if isinstance(value, BoundTag):
        return normalize_ui_value(_binding_from_bound_tag(value), field_name=field_name)

    if isinstance(value, Tag):
        return normalize_ui_value(_binding_from_tag(value), field_name=field_name)

    if isinstance(value, dict):
        return {
            key: normalize_ui_value(item, field_name=key) for key, item in value.items()
        }

    if isinstance(value, list):
        return [normalize_ui_value(item) for item in value]

    if isinstance(value, tuple):
        return tuple(normalize_ui_value(item) for item in value)

    if isinstance(value, set):
        return {normalize_ui_value(item) for item in value}

    return value


def _bind_value(value: Any, tags: Tags | None, visited: set[int]) -> Any:
    if isinstance(value, UITagBinding):
        return value

    if isinstance(value, BoundTag):
        return _binding_from_bound_tag(value)

    if isinstance(value, Tag):
        return _binding_from_declared_tag(value, tags)

    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = _bind_value(item, tags=tags, visited=visited)
        return value

    if isinstance(value, dict):
        for key, item in list(value.items()):
            value[key] = _bind_value(item, tags=tags, visited=visited)
        return value

    if isinstance(value, tuple):
        return tuple(_bind_value(item, tags=tags, visited=visited) for item in value)

    if isinstance(value, set):
        return {_bind_value(item, tags=tags, visited=visited) for item in value}

    if not hasattr(value, "__dict__"):
        return value

    obj_id = id(value)
    if obj_id in visited:
        return value
    visited.add(obj_id)

    for attr_name, attr_value in vars(value).items():
        if attr_name in _SKIP_BIND_ATTRS or callable(attr_value):
            continue
        setattr(value, attr_name, _bind_value(attr_value, tags=tags, visited=visited))
    return value


def _binding_from_bound_tag(tag: BoundTag) -> UITagBinding:
    return UITagBinding(
        tag_name=_qualify_tag_name(tag.name, getattr(tag._tags, "_app_key", None)),
        tag_type=tag.tag_type,
        default_value=_normalize_default(tag.default),
    )


def _binding_from_declared_tag(tag: Tag, tags: Tags | None) -> UITagBinding:
    tag_name = _get_tag_name(tag)
    if tags is None:
        raise ValueError(
            f"UI tag reference '{tag_name}' requires application tags to be configured."
        )

    resolved = tags.get_definition(tag_name)
    if resolved is None:
        raise ValueError(
            f"UI tag reference '{tag_name}' is not available in the resolved application tags."
        )

    return _binding_from_tag(resolved, app_key=getattr(tags, "_app_key", None))


def _binding_from_tag(tag: Tag, app_key: str | None = None) -> UITagBinding:
    return UITagBinding(
        tag_name=_qualify_tag_name(_get_tag_name(tag), app_key),
        tag_type=tag.tag_type,
        default_value=_normalize_default(tag.default),
    )


def _get_tag_name(tag: Tag) -> str:
    tag_name = tag.name or getattr(tag, "_declared_attr_name", None)
    if not tag_name:
        raise ValueError("Unable to resolve a name for UI tag reference.")
    return tag_name


def _qualify_tag_name(tag_name: str, app_key: str | None) -> str:
    if not app_key or tag_name.startswith(f"{app_key}."):
        return tag_name
    return f"{app_key}.{tag_name}"


def _normalize_default(value: Any) -> Any:
    if value is NotSet:
        return _MISSING
    return value


def _is_missing_default(value: Any) -> bool:
    return value is _MISSING or isinstance(value, _MissingDefault)
