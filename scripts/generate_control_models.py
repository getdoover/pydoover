#!/usr/bin/env -S uv run

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "protos" / "Doover Control API.yaml"
OUTPUT_DIR = ROOT / "pydoover" / "models" / "control"
GENERATED_PATH = OUTPUT_DIR / "_generated.py"
INIT_PATH = OUTPUT_DIR / "__init__.py"

PREFIX_VARIANTS = ("Basic", "Slim", "Simple", "SuperBasic", "Public")
SUFFIX_VARIANTS = (
    "SuperBasic",
    "Basic",
    "Simple",
    "WithId",
    "Parent",
    "Children",
    "Detail",
)


def load_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text())


def camelize(value: str) -> str:
    parts = re.split(r"[^0-9A-Za-z]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def strip_serializer_tokens(name: str) -> str:
    return (
        name.replace("Serializer", "")
        .replace("Serialiser", "")
        .replace("Seraliser", "")
    )


def strip_version_wrappers(name: str) -> str:
    result = name
    if result.startswith("Patched"):
        result = result[len("Patched") :]
    if result.startswith("Paginated") and result.endswith("ListList"):
        result = result[len("Paginated") : -len("ListList")]
    elif result.endswith("Request"):
        result = result[: -len("Request")]
    if result.endswith("Detail"):
        result = result[: -len("Detail")]
    elif result.endswith("List"):
        result = result[: -len("List")]
    return result


def canonical_model_name(schema_name: str) -> str:
    name = strip_serializer_tokens(strip_version_wrappers(schema_name))
    changed = True
    while changed:
        changed = False
        for prefix in PREFIX_VARIANTS:
            if name.startswith(prefix) and len(name) > len(prefix):
                name = name[len(prefix) :]
                changed = True
                break
        if changed:
            continue
        for suffix in SUFFIX_VARIANTS:
            if name.endswith(suffix) and len(name) > len(suffix):
                name = name[: -len(suffix)]
                changed = True
                break
    return name or strip_serializer_tokens(schema_name)


def ref_name(schema: dict | None) -> str | None:
    if not isinstance(schema, dict):
        return None
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    all_of = schema.get("allOf")
    if isinstance(all_of, list) and len(all_of) == 1 and isinstance(all_of[0], dict):
        if "$ref" in all_of[0]:
            return all_of[0]["$ref"].rsplit("/", 1)[-1]
    return None


def is_paginated_schema(schema_name: str, schema: dict) -> bool:
    props = schema.get("properties") or {}
    return (
        schema_name.startswith("Paginated")
        and {"count", "results"}.issubset(props)
        and isinstance(props.get("results"), dict)
    )


def quote(value):
    return json.dumps(value, sort_keys=True)


class ObjectTypeRegistry:
    def __init__(self):
        self._by_signature: dict[str, str] = {}
        self._definitions: dict[str, dict[str, dict]] = {}

    def _unique_name(self, preferred: str, parent_model: str) -> str:
        candidate = preferred or f"{parent_model}Object"
        if candidate not in self._definitions:
            return candidate
        candidate = f"{parent_model}{candidate}"
        if candidate not in self._definitions:
            return candidate
        index = 2
        while f"{candidate}{index}" in self._definitions:
            index += 1
        return f"{candidate}{index}"

    def register(self, parent_model: str, field_name: str, schema: dict) -> str:
        properties = schema.get("properties") or {}
        rendered_fields = {}
        for child_name, child_schema in properties.items():
            rendered_fields[child_name] = describe_property(
                parent_model=parent_model,
                field_name=child_name,
                schema=child_schema,
                object_types=self,
            )
        signature = quote(
            {name: rendered_fields[name] for name in sorted(rendered_fields)}
        )
        existing = self._by_signature.get(signature)
        if existing:
            return existing

        preferred = (
            camelize(field_name.split("_")[-1])
            if "_" in field_name
            else camelize(field_name)
        )
        name = self._unique_name(preferred, parent_model)
        self._by_signature[signature] = name
        self._definitions[name] = rendered_fields
        return name

    @property
    def definitions(self) -> dict[str, dict[str, dict]]:
        return self._definitions


def _enum_choices(schema: dict) -> tuple[str, ...] | None:
    raw = schema.get("enum")
    if not isinstance(raw, list) or not raw:
        return None
    return tuple(str(value) for value in raw)


def describe_property(
    *,
    parent_model: str,
    field_name: str,
    schema: dict,
    object_types: ObjectTypeRegistry,
) -> dict:
    target = ref_name(schema)
    nullable = bool(schema.get("nullable", False))

    if target:
        return {
            "type": "resource",
            "nullable": nullable,
            "is_array": False,
            "ref": canonical_model_name(target),
            "choices": None,
        }

    if schema.get("type") == "array":
        items = schema.get("items") or {}
        item_ref = ref_name(items)
        if item_ref:
            return {
                "type": "resource",
                "nullable": nullable,
                "is_array": True,
                "ref": canonical_model_name(item_ref),
                "choices": None,
            }
        if items.get("type") == "object" and items.get("properties"):
            object_name = object_types.register(parent_model, field_name, items)
            return {
                "type": object_name,
                "nullable": nullable,
                "is_array": True,
                "ref": None,
                "choices": None,
            }
        return {
            "type": map_scalar_type(field_name, items),
            "nullable": nullable,
            "is_array": True,
            "ref": None,
            "choices": _enum_choices(items),
        }

    if schema.get("type") == "object" and schema.get("properties"):
        object_name = object_types.register(parent_model, field_name, schema)
        return {
            "type": object_name,
            "nullable": nullable,
            "is_array": False,
            "ref": None,
            "choices": None,
        }

    return {
        "type": map_scalar_type(field_name, schema),
        "nullable": nullable,
        "is_array": False,
        "ref": None,
        "choices": _enum_choices(schema),
    }


def map_scalar_type(field_name: str, schema: dict) -> str:
    schema_type = schema.get("type")
    if field_name == "id":
        return "SnowflakeId"
    if field_name.endswith("_id") or field_name.endswith("_ids"):
        return "id"
    if schema_type == "boolean":
        return "boolean"
    if schema_type == "integer":
        return "integer"
    if schema_type == "number":
        return "float"
    if schema_type == "object":
        return "json"
    if schema_type == "array":
        return "json"
    return "string" if schema_type == "string" else "json"


def request_methods_by_schema(spec: dict) -> dict[str, set[str]]:
    methods: dict[str, set[str]] = defaultdict(set)
    for path_item in spec.get("paths", {}).values():
        for http_method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            request = operation.get("requestBody") or {}
            for media in (request.get("content") or {}).values():
                schema = media.get("schema") or {}
                ref = ref_name(schema)
                if ref:
                    methods[ref].add(http_method.upper())
    return methods


def build_models(spec: dict):
    schemas = spec.get("components", {}).get("schemas", {})
    object_types = ObjectTypeRegistry()
    methods_by_schema = request_methods_by_schema(spec)

    model_versions: dict[str, dict[str, dict]] = defaultdict(dict)
    model_fields: dict[str, dict[str, dict]] = defaultdict(dict)
    schema_registry: dict[str, dict] = {}

    non_paginated = {
        name: schema
        for name, schema in schemas.items()
        if not is_paginated_schema(name, schema)
    }

    grouped_versions: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for schema_name, schema in non_paginated.items():
        grouped_versions[canonical_model_name(schema_name)].append(
            (schema_name, schema)
        )

    for model_name, versions in grouped_versions.items():
        all_property_names = set()
        for _, schema in versions:
            all_property_names.update((schema.get("properties") or {}).keys())

        def canonical_field_name(property_name: str) -> str:
            if property_name.endswith("_ids"):
                base = property_name[: -len("_ids")]
                if f"{base}s" in all_property_names:
                    return f"{base}s"
                if base in all_property_names:
                    return base
            if property_name.endswith("_id"):
                base = property_name[: -len("_id")]
                if base in all_property_names:
                    return base
            return property_name

        for schema_name, schema in versions:
            properties = schema.get("properties") or {}
            required_fields = set(schema.get("required") or [])
            version_fields: dict[str, dict] = {}
            for property_name, property_schema in properties.items():
                canonical_name = canonical_field_name(property_name)
                description = describe_property(
                    parent_model=model_name,
                    field_name=canonical_name,
                    schema=property_schema,
                    object_types=object_types,
                )

                existing = model_fields[model_name].get(canonical_name)
                if existing is None:
                    model_fields[model_name][canonical_name] = description
                else:
                    if (
                        existing["type"] != "resource"
                        and description["type"] == "resource"
                    ):
                        model_fields[model_name][canonical_name] = description
                    elif existing["ref"] is None and description["ref"] is not None:
                        existing["ref"] = description["ref"]
                    existing["nullable"] = (
                        existing["nullable"] or description["nullable"]
                    )
                    existing["is_array"] = (
                        existing["is_array"] or description["is_array"]
                    )
                    if not existing.get("choices") and description.get("choices"):
                        existing["choices"] = description["choices"]

                config: dict[str, object] = {}
                if property_name in required_fields:
                    config["required"] = True
                if property_name != canonical_name:
                    config["output_id"] = property_name
                nested_ref = ref_name(property_schema)
                if nested_ref:
                    config["version"] = nested_ref
                elif property_schema.get("type") == "array":
                    item_ref = ref_name((property_schema.get("items") or {}))
                    if item_ref:
                        config["version"] = item_ref
                version_fields[canonical_name] = config

            version_entry = {"fields": version_fields}
            if schema_name in methods_by_schema:
                version_entry["methods"] = sorted(methods_by_schema[schema_name])
            model_versions[model_name][schema_name] = version_entry
            schema_registry[schema_name] = {
                "kind": "model",
                "model": model_name,
                "version": schema_name,
            }

    for schema_name, schema in schemas.items():
        if not is_paginated_schema(schema_name, schema):
            continue
        results = ((schema.get("properties") or {}).get("results") or {}).get(
            "items"
        ) or {}
        item_schema = ref_name(results)
        if item_schema is None:
            continue
        schema_registry[schema_name] = {
            "kind": "page",
            "model": canonical_model_name(item_schema),
            "version": item_schema,
        }

    return object_types.definitions, model_fields, model_versions, schema_registry


def render_control_field(defn: dict) -> str:
    parts = [
        f'type="{defn["type"]}"',
        f"nullable={defn['nullable']}",
    ]
    if defn["is_array"]:
        parts.append("is_array=True")
    if defn["ref"] is not None:
        parts.append(f'ref="{defn["ref"]}"')
    if defn.get("choices"):
        parts.append(f"choices={defn['choices']!r}")
    return f"ControlField({', '.join(parts)})"


def render_python_type(defn: dict) -> str:
    if defn["type"] == "resource" and defn["ref"] is not None:
        base = defn["ref"]
    elif defn["type"] in {"string", "id"}:
        base = "str"
    elif defn["type"] == "SnowflakeId":
        base = "int"
    elif defn["type"] == "integer":
        base = "int"
    elif defn["type"] == "float":
        base = "float"
    elif defn["type"] == "boolean":
        base = "bool"
    elif defn["type"] == "json":
        base = "Any"
    else:
        base = defn["type"]

    if defn["is_array"]:
        base = f"list[{base}]"
    if defn["nullable"]:
        base = f"{base} | None"
    return base


def render_constructor_type(defn: dict) -> str:
    if defn["type"] == "resource" and defn["ref"] is not None:
        base = f"{defn['ref']} | dict[str, Any] | str | int"
    elif defn["type"] == "json":
        base = "Any"
    elif defn["type"] in {"string", "id"}:
        base = "str"
    elif defn["type"] == "SnowflakeId":
        base = "int"
    elif defn["type"] == "integer":
        base = "int"
    elif defn["type"] == "float":
        base = "float"
    elif defn["type"] == "boolean":
        base = "bool"
    else:
        base = f"{defn['type']} | dict[str, Any]"

    if defn["is_array"]:
        base = f"list[{base}]"
    return f"{base} | None"


def render_init(field_names: list[str], field_defs: dict[str, dict]) -> list[str]:
    lines = ["    def __init__(", "        self,"]
    if field_names:
        lines.append("        *,")
        for field_name in field_names:
            lines.append(
                f"        {field_name}: {render_constructor_type(field_defs[field_name])} = None,"
            )
    lines.append("    ) -> None:")
    if field_names:
        lines.append("        super().__init__(")
        for field_name in field_names:
            lines.append(f"            {field_name}={field_name},")
        lines.append("        )")
    else:
        lines.append("        super().__init__()")
    return lines


def render_object_types(object_types: dict[str, dict[str, dict]]) -> list[str]:
    blocks = []
    for name in sorted(object_types):
        blocks.append(f"class {name}(ObjectFieldType):")
        field_names = list(object_types[name])
        for field_name, definition in object_types[name].items():
            blocks.append(f"    {field_name}: {render_python_type(definition)}")
        blocks.extend(render_init(field_names, object_types[name]))
        blocks.append("    _structure = {")
        for field_name, definition in object_types[name].items():
            blocks.append(
                f'        "{field_name}": {render_control_field(definition)},'
            )
        blocks.append("    }")
        blocks.append("")
    return blocks


def render_models(
    model_fields: dict[str, dict[str, dict]], model_versions: dict[str, dict[str, dict]]
) -> list[str]:
    blocks = []
    for model_name in sorted(model_fields):
        blocks.append(f"class {model_name}(ControlModel):")
        blocks.append(f'    _model_name = "{model_name}"')
        field_names = list(model_fields[model_name])
        for field_name, definition in model_fields[model_name].items():
            blocks.append(f"    {field_name}: {render_python_type(definition)}")
        blocks.extend(render_init(field_names, model_fields[model_name]))
        blocks.append("    _field_defs = {")
        for field_name, definition in model_fields[model_name].items():
            blocks.append(
                f'        "{field_name}": {render_control_field(definition)},'
            )
        blocks.append("    }")
        blocks.append("    _versions = {")
        for version_name, version in model_versions[model_name].items():
            blocks.append(f'        "{version_name}": {{')
            if "methods" in version:
                blocks.append(f'            "methods": {version["methods"]!r},')
            blocks.append('            "fields": {')
            for field_name, config in version["fields"].items():
                blocks.append(f'                "{field_name}": {config!r},')
            blocks.append("            },")
            blocks.append("        },")
        blocks.append("    }")
        blocks.append("")
    return blocks


def build_generated_module(spec: dict) -> str:
    object_types, model_fields, model_versions, schema_registry = build_models(spec)
    model_names = sorted(model_fields)
    object_type_names = sorted(object_types)

    blocks = [
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from ._base import ControlField, ControlModel, ObjectFieldType",
        "",
        "",
    ]
    blocks.extend(render_object_types(object_types))
    blocks.extend(render_models(model_fields, model_versions))
    blocks.append(f"CONTROL_SCHEMA_REGISTRY = {schema_registry!r}")
    blocks.append("")
    blocks.append("__all__ = [")
    blocks.append('    "CONTROL_SCHEMA_REGISTRY",')
    for name in object_type_names:
        blocks.append(f'    "{name}",')
    for name in model_names:
        blocks.append(f'    "{name}",')
    blocks.append("]")
    blocks.append("")
    return "\n".join(blocks)


def build_init(spec: dict) -> str:
    object_types, model_fields, _, _ = build_models(spec)
    object_type_names = sorted(object_types)
    model_names = sorted(model_fields)
    lines = [
        "from ._base import ControlField as ControlField",
        "from ._base import ControlModel as ControlModel",
        "from ._base import ControlPage as ControlPage",
        "from ._base import ObjectFieldType as ObjectFieldType",
        "from ._base import resolve_control_schema as resolve_control_schema",
        "from ._generated import CONTROL_SCHEMA_REGISTRY as CONTROL_SCHEMA_REGISTRY",
        "from ._generated import (",
    ]
    for name in object_type_names:
        lines.append(f"    {name} as {name},")
    for name in model_names:
        lines.append(f"    {name} as {name},")
    lines.append(")")
    lines.append("")
    lines.append("__all__ = [")
    lines.append('    "CONTROL_SCHEMA_REGISTRY",')
    lines.append('    "ControlField",')
    lines.append('    "ControlModel",')
    lines.append('    "ControlPage",')
    lines.append('    "ObjectFieldType",')
    lines.append('    "resolve_control_schema",')
    for name in object_type_names:
        lines.append(f'    "{name}",')
    for name in model_names:
        lines.append(f'    "{name}",')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def main():
    spec = load_spec()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_PATH.write_text(build_generated_module(spec))
    INIT_PATH.write_text(build_init(spec))


if __name__ == "__main__":
    main()
