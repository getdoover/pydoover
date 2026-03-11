from __future__ import annotations

import copy
import inspect
import json
from collections import OrderedDict
from typing import Any, Callable

from pydoover.tags import BoundTag, NotSet, Tag, Tags


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
_MISSING = object()


class UITagBinding:
    def __init__(
        self,
        tag_name: str,
        tag_type: str | None = None,
        default_value: Any = _MISSING,
    ):
        self.tag_name = tag_name
        self.tag_type = _TAG_TYPE_MAP.get(tag_type, tag_type)
        self.default_value = default_value

    def to_lookup(self) -> str:
        result = f"$tag.{self.tag_name}"
        if self.tag_type is not None:
            result += f":{self.tag_type}"
        if self.default_value is not _MISSING:
            if self.tag_type is None:
                result += ":string"
            result += f":{json.dumps(self.default_value, separators=(',', ':'))}"
        return result


class _DeclaredElement:
    def __init__(self, attr_name: str, template):
        self.attr_name = attr_name
        self.template = template

    def __get__(self, instance, owner):
        if instance is None:
            return self.template
        return instance._elements[self.attr_name]

    def __set__(self, instance, value):
        from .element import Element

        if not isinstance(value, Element):
            raise TypeError("ui.UI attributes must be Element instances.")
        instance._elements[self.attr_name] = value


class UI:
    __ui_declarations__: "OrderedDict[str, _DeclaredElement]" = OrderedDict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        from .element import Element

        declarations: "OrderedDict[str, _DeclaredElement]" = OrderedDict()
        for base in reversed(cls.__mro__[1:]):
            declarations.update(getattr(base, "__ui_declarations__", {}))

        for attr_name, value in list(cls.__dict__.items()):
            if not isinstance(value, Element):
                continue

            declaration = _DeclaredElement(attr_name, value)
            declarations[attr_name] = declaration
            setattr(cls, attr_name, declaration)

        cls.__ui_declarations__ = declarations

    def __init__(self):
        self._elements: "OrderedDict[str, Any]" = OrderedDict(
            (name, copy.deepcopy(declaration.template))
            for name, declaration in self.__class__.__ui_declarations__.items()
        )

    @property
    def children(self) -> list[Any]:
        return list(self._elements.values())

    def to_elements(self) -> list[Any]:
        return self.children

    def add_element(self, name: str, element):
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

    def bind_tags(self, tags: Tags | None) -> "UI":
        visited: set[int] = set()
        for element in self._elements.values():
            _bind_value(element, tags=tags, visited=visited)
        return self


UIFactory = Callable[..., UI | None]


def is_tag_reference(value: Any) -> bool:
    if isinstance(value, (UITagBinding, BoundTag, Tag)):
        return True
    if isinstance(value, dict):
        return any(is_tag_reference(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(is_tag_reference(v) for v in value)
    return False


def resolve_ui_factory(factory: UIFactory, config: Any, tags: Tags | None) -> UI | None:
    params = list(inspect.signature(factory).parameters.values())
    positional = [
        param
        for param in params
        if param.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]

    if any(param.kind is inspect.Parameter.VAR_POSITIONAL for param in params):
        return factory(config, tags)

    if len(positional) >= 2:
        return factory(config, tags)

    if len(positional) == 1:
        return factory(config)

    return factory()


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
            key: normalize_ui_value(item, field_name=key)
            for key, item in value.items()
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
        tag_name=tag.name,
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

    return _binding_from_tag(resolved)


def _binding_from_tag(tag: Tag) -> UITagBinding:
    return UITagBinding(
        tag_name=_get_tag_name(tag),
        tag_type=tag.tag_type,
        default_value=_normalize_default(tag.default),
    )


def _get_tag_name(tag: Tag) -> str:
    tag_name = tag.name or getattr(tag, "_declared_attr_name", None)
    if not tag_name:
        raise ValueError("Unable to resolve a name for UI tag reference.")
    return tag_name


def _normalize_default(value: Any) -> Any:
    if value is NotSet:
        return _MISSING
    return value
