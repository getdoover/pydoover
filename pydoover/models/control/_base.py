from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Generic, TypeVar, cast


@dataclass(frozen=True, slots=True)
class ControlField:
    type: str
    nullable: bool
    is_array: bool = False
    ref: str | None = None
    version: str | None = None


_MODEL_REGISTRY: dict[str, type["ControlModel"]] = {}
_OBJECT_TYPE_REGISTRY: dict[str, type["ObjectFieldType"]] = {}


def _coerce_scalar(field: ControlField, value: Any) -> Any:
    if value is None:
        return None

    if field.type in {"string", "json"}:
        return value
    if field.type == "boolean":
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return bool(value)
    if field.type in {"integer", "SnowflakeId"}:
        if value == "":
            return None
        return int(value)
    if field.type == "float":
        if value == "":
            return None
        return float(value)
    if field.type == "id":
        return str(value)
    return value


def _normalise_field_name(name: str) -> str:
    return name.rstrip("?")


class ObjectFieldType:
    _structure: ClassVar[dict[str, ControlField]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ != "ObjectFieldType":
            _OBJECT_TYPE_REGISTRY[cls.__name__] = cls

    def __init__(self, **kwargs: Any):
        unexpected = sorted(set(kwargs) - set(self._structure))
        if unexpected:
            joined = ", ".join(unexpected)
            raise TypeError(f"Unexpected field(s) for {type(self).__name__}: {joined}")

        for name, field in self._structure.items():
            setattr(self, name, _convert_field_value(field, kwargs.get(name)))

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        if data is None:
            return None
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise TypeError(
                f"{cls.__name__}.from_dict expected dict, got {type(data).__name__}"
            )
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, field in self._structure.items():
            value = getattr(self, name, None)
            if value is None:
                continue
            result[name] = _dump_field_value(field, value)
        return result

    def __repr__(self) -> str:
        parts = []
        for name in self._structure:
            value = getattr(self, name, None)
            if value is not None:
                parts.append(f"{name}={value!r}")
        joined = ", ".join(parts)
        return f"{type(self).__name__}({joined})"


def _convert_field_value(field: ControlField, value: Any) -> Any:
    if value is None:
        return None

    if field.is_array:
        if not isinstance(value, list):
            raise TypeError(f"Expected list for field, got {type(value).__name__}")
        item_field = ControlField(
            type=field.type,
            nullable=field.nullable,
            is_array=False,
            ref=field.ref,
            version=field.version,
        )
        return [_convert_field_value(item_field, item) for item in value]

    if field.type == "resource" and field.ref:
        model = _MODEL_REGISTRY[field.ref]
        if isinstance(value, model):
            return value
        if isinstance(value, dict):
            if field.version:
                return model.from_version(field.version, value)
            return model.from_dict(value)
        model_fields = getattr(model, "_field_defs", {})
        if "id" in model_fields:
            return model(id=value)
        return value

    if field.ref and field.type in _OBJECT_TYPE_REGISTRY:
        object_type = _OBJECT_TYPE_REGISTRY[field.type]
        if isinstance(value, object_type):
            return value
        return object_type.from_dict(value)

    if field.type in _OBJECT_TYPE_REGISTRY:
        object_type = _OBJECT_TYPE_REGISTRY[field.type]
        if isinstance(value, object_type):
            return value
        return object_type.from_dict(value)

    return _coerce_scalar(field, value)


def _dump_field_value(field: ControlField, value: Any) -> Any:
    if value is None:
        return None

    if field.is_array:
        item_field = ControlField(
            type=field.type,
            nullable=field.nullable,
            is_array=False,
            ref=field.ref,
            version=field.version,
        )
        return [_dump_field_value(item_field, item) for item in value]

    if field.type == "resource" and isinstance(value, ControlModel):
        if field.version:
            return value.to_version(field.version)
        return value.to_dict()

    if field.type in _OBJECT_TYPE_REGISTRY and isinstance(value, ObjectFieldType):
        return value.to_dict()

    return value


class ControlModel:
    _model_name: ClassVar[str | None] = None
    _field_defs: ClassVar[dict[str, ControlField]] = {}
    _versions: ClassVar[dict[str, dict[str, Any]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._model_name:
            _MODEL_REGISTRY[cls._model_name] = cls

    def __init__(self, **kwargs: Any):
        unexpected = sorted(set(kwargs) - set(self._field_defs))
        if unexpected:
            joined = ", ".join(unexpected)
            raise TypeError(f"Unexpected field(s) for {type(self).__name__}: {joined}")

        for name, field in self._field_defs.items():
            setattr(self, name, _convert_field_value(field, kwargs.get(name)))

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        if data is None:
            return None
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise TypeError(
                f"{cls.__name__}.from_dict expected dict, got {type(data).__name__}"
            )
        return cls(**data)

    @classmethod
    def from_version(cls, version_name: str, data: dict[str, Any] | None):
        if data is None:
            return None
        if not isinstance(data, dict):
            raise TypeError(
                f"{cls.__name__}.from_version expected dict, got {type(data).__name__}"
            )
        version = cls._versions.get(version_name)
        if version is None:
            raise KeyError(f"Unknown version {version_name!r} for {cls.__name__}")

        kwargs: dict[str, Any] = {}
        for field_name, config in (version.get("fields") or {}).items():
            if config.get("exclude"):
                continue
            source_key = config.get("output_id")
            raw_value = data.get(field_name)
            if raw_value is None and source_key:
                raw_value = data.get(source_key)
            if raw_value is None:
                if config.get("required"):
                    if field_name in data:
                        raw_value = data[field_name]
                    elif source_key and source_key in data:
                        raw_value = data[source_key]
                    else:
                        raise TypeError(
                            f"Missing required field {field_name!r} for version {version_name!r}"
                        )
                else:
                    continue

            field = cls._field_defs[field_name]
            nested_version = config.get("version")
            if nested_version:
                field = ControlField(
                    type=field.type,
                    nullable=field.nullable,
                    is_array=field.is_array,
                    ref=field.ref,
                    version=nested_version,
                )
            kwargs[field_name] = _convert_field_value(field, raw_value)
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, field in self._field_defs.items():
            value = getattr(self, name, None)
            if value is None:
                continue
            result[name] = _dump_field_value(field, value)
        return result

    def to_version(self, version_name: str, *, method: str | None = None) -> dict[str, Any]:
        version = type(self)._versions.get(version_name)
        if version is None:
            raise KeyError(f"Unknown version {version_name!r} for {type(self).__name__}")

        methods = version.get("methods")
        if method is not None and methods is not None and method.upper() not in methods:
            allowed = ", ".join(sorted(methods))
            raise ValueError(
                f"Version {version_name!r} for {type(self).__name__} only supports {allowed}"
            )

        result: dict[str, Any] = {}
        for field_name, config in (version.get("fields") or {}).items():
            if config.get("exclude"):
                continue

            value = getattr(self, field_name, None)
            if value is None:
                if config.get("required"):
                    raise TypeError(
                        f"Missing required field {field_name!r} for version {version_name!r}"
                    )
                continue

            field = type(self)._field_defs[field_name]
            nested_version = config.get("version")
            output_key = config.get("output_id", field_name)

            if field.type == "resource":
                if nested_version:
                    if field.is_array:
                        result[output_key] = [
                            item.to_version(nested_version)
                            if isinstance(item, ControlModel)
                            else item
                            for item in value
                        ]
                    else:
                        result[output_key] = (
                            value.to_version(nested_version)
                            if isinstance(value, ControlModel)
                            else value
                        )
                    continue
                if config.get("output_id"):
                    if field.is_array:
                        result[output_key] = [
                            getattr(item, "id", item)
                            for item in value
                        ]
                    else:
                        result[output_key] = getattr(value, "id", value)
                    continue

            if field.type in _OBJECT_TYPE_REGISTRY or field.ref:
                result[output_key] = _dump_field_value(field, value)
                continue

            if field.is_array and field.type == "json":
                result[output_key] = list(value)
                continue

            result[output_key] = _dump_field_value(field, value)

        return result

    def __repr__(self) -> str:
        parts = []
        for name in self._field_defs:
            value = getattr(self, name, None)
            if value is not None:
                parts.append(f"{name}={value!r}")
        joined = ", ".join(parts)
        return f"{type(self).__name__}({joined})"


T = TypeVar("T")


class ControlPage(Generic[T]):
    def __init__(
        self,
        *,
        count: int,
        results: list[T],
        next: str | None = None,
        previous: str | None = None,
    ):
        self.count = int(count)
        self.results = list(results)
        self.next = next
        self.previous = previous

    @classmethod
    def from_dict(cls, data: dict[str, Any], item_type: type[T]):
        if not isinstance(data, dict):
            raise TypeError(
                f"ControlPage.from_dict expected dict, got {type(data).__name__}"
            )
        results = data.get("results") or []
        from_dict = getattr(item_type, "from_dict", None)
        if callable(from_dict):
            loader = cast(Callable[[dict[str, Any]], T], from_dict)
            parsed = [loader(item) for item in results]
        else:
            parsed = cast(list[T], list(results))
        return cls(
            count=data.get("count", 0),
            next=data.get("next"),
            previous=data.get("previous"),
            results=parsed,
        )

    def to_dict(self) -> dict[str, Any]:
        results = []
        for item in self.results:
            to_dict = getattr(item, "to_dict", None)
            if callable(to_dict):
                results.append(cast(Callable[[], dict[str, Any]], to_dict)())
            else:
                results.append(item)
        return {
            "count": self.count,
            "next": self.next,
            "previous": self.previous,
            "results": results,
        }

    def __repr__(self) -> str:
        return (
            f"ControlPage(count={self.count!r}, next={self.next!r}, "
            f"previous={self.previous!r}, results={self.results!r})"
        )


def resolve_control_schema(schema_name: str) -> dict[str, Any]:
    from ._generated import CONTROL_SCHEMA_REGISTRY

    return CONTROL_SCHEMA_REGISTRY[schema_name]
