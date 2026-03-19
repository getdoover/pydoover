from __future__ import annotations

import keyword
from collections import Counter, defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "protos" / "Doover Control API.yaml"
OUTPUT_DIR = ROOT / "pydoover" / "api" / "control"
GROUPS_PATH = OUTPUT_DIR / "_generated_groups.py"
SYNC_PATH = OUTPUT_DIR / "_generated_sync.py"
ASYNC_PATH = OUTPUT_DIR / "_generated_async.py"

EXCLUDED_PATHS = {
    "/public/applications/",
    "/manifest.webmanifest",
    "/pwa_icon/{size}/",
    "/pwa_install_screenshot/",
    "/pwa_splash/{width}/{height}/{scale}/{orientation}/",
}

BINARY_PATH_MARKERS = ("/pdf/", "/tarball/", "/zip/")


def load_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text())


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


def camelize(parts: list[str]) -> str:
    words: list[str] = []
    for part in parts:
        if not part:
            continue
        words.extend(piece for piece in part.replace("-", "_").split("_") if piece)
    return "".join(word[:1].upper() + word[1:] for word in words)


def sanitize_name(name: str) -> str:
    result = name.replace("-", "_")
    if keyword.iskeyword(result):
        result += "_"
    return result


def root_group_for(tag: str) -> str:
    return tag


def operation_remainder(operation_id: str, group_path: str) -> str:
    prefix = group_path.replace(".", "_")
    if operation_id.startswith(prefix + "_"):
        return operation_id[len(prefix) + 1 :]
    return operation_id


def group_path_for(path: str, tag: str) -> str:
    parts = [segment for segment in path.strip("/").split("/") if not segment.startswith("{")]
    if tag == "organisations":
        if len(parts) >= 2 and parts[1] in {
            "domains",
            "pending_users",
            "roles",
            "shared_profiles",
            "sharing_profiles",
            "users",
        }:
            return f"organisations.{parts[1]}"
        if len(parts) >= 2 and parts[1] == "billing":
            if len(parts) >= 3 and parts[2] in {
                "account",
                "admin",
                "agent_items",
                "app_configs",
                "device_type_configs",
                "devices",
                "group",
                "invoices",
                "metering_runs",
                "products",
                "seller_customers",
                "stripe",
                "subscriptions",
                "usage_records",
            }:
                return f"organisations.billing.{parts[2]}"
            return "organisations.billing"
        return "organisations"
    if tag == "container" and len(parts) >= 2 and parts[1] == "registry":
        return "container.registry"
    return root_group_for(tag)


def method_name_for(operation_id: str, group_path: str) -> str:
    remainder = operation_remainder(operation_id, group_path)
    if remainder == "destroy":
        return "delete"
    for suffix in ("_destroy", "_create", "_retrieve", "_update", "_partial_update"):
        if remainder.endswith(suffix):
            base = remainder[: -len(suffix)]
            if base:
                return "delete" if suffix == "_destroy" else base
    return remainder


def fallback_method_name(remainder: str) -> str:
    if remainder == "destroy":
        return "delete"
    if remainder.endswith("_destroy"):
        return remainder[: -len("_destroy")] + "_delete"
    return remainder


def param_hint(schema: dict, required: bool) -> str:
    schema_type = schema.get("type")
    if schema_type == "integer":
        base = "int"
    elif schema_type == "number":
        base = "float"
    elif schema_type == "boolean":
        base = "bool"
    elif schema_type == "array":
        base = "Sequence[Any]"
    else:
        base = "str" if schema_type == "string" else "Any"
    return base if required else f"{base} | None"


def extract_parameters(path_item: dict, operation: dict):
    merged = []
    for source in (path_item.get("parameters") or [], operation.get("parameters") or []):
        for parameter in source:
            if parameter.get("name") == "X-Doover-Organisation":
                continue
            merged.append(parameter)
    path_params = [param for param in merged if param.get("in") == "path"]
    query_params = [param for param in merged if param.get("in") == "query"]
    return path_params, query_params


def request_schema_info(operation: dict, schemas: dict[str, dict]):
    request = operation.get("requestBody") or {}
    content = request.get("content") or {}
    if not content:
        return None
    schema = None
    media_types = list(content)
    if "application/json" in content:
        schema = content["application/json"].get("schema") or {}
    else:
        schema = next(iter(content.values())).get("schema") or {}
    schema_name = ref_name(schema)
    body_mode = "json"
    binary_fields: set[str] = set()
    if set(media_types) == {"multipart/form-data"}:
        body_mode = "multipart"
    if schema_name and schema_name in schemas:
        for field_name, field_schema in (schemas[schema_name].get("properties") or {}).items():
            if field_schema.get("format") == "binary":
                binary_fields.add(field_name)
        if binary_fields:
            body_mode = "multipart"
    return {
        "schema_name": schema_name,
        "required": bool(request.get("required")),
        "body_mode": body_mode,
        "binary_fields": sorted(binary_fields),
    }


def response_info(path: str, operation: dict):
    responses = operation.get("responses") or {}
    success_code = next(
        (code for code in ("200", "201", "202", "204") if code in responses),
        next(iter(responses.keys()), "200"),
    )
    response = responses.get(success_code) or {}
    content = response.get("content") or {}

    if any(marker in path for marker in BINARY_PATH_MARKERS):
        return {"kind": "bytes", "schema_name": None, "item_schema": None}
    if success_code == "204":
        return {"kind": "none", "schema_name": None, "item_schema": None}
    if not content:
        return {"kind": "none", "schema_name": None, "item_schema": None}

    media_schema = None
    if "application/json" in content:
        media_schema = content["application/json"].get("schema") or {}
    else:
        media_schema = next(iter(content.values())).get("schema") or {}

    schema_name = ref_name(media_schema)
    if schema_name:
        if schema_name.startswith("Paginated"):
            return {"kind": "page", "schema_name": schema_name, "item_schema": None}
        return {"kind": "model", "schema_name": schema_name, "item_schema": None}

    if media_schema.get("type") == "array":
        item_schema = ref_name(media_schema.get("items") or {})
        if item_schema:
            return {"kind": "list_model", "schema_name": None, "item_schema": item_schema}
        return {"kind": "raw", "schema_name": None, "item_schema": None}

    return {"kind": "raw", "schema_name": None, "item_schema": None}


def collect_operations(spec: dict):
    schemas = spec.get("components", {}).get("schemas", {})
    operations = []
    for path, path_item in spec.get("paths", {}).items():
        if path in EXCLUDED_PATHS:
            continue
        for http_method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags") or []
            if not tags:
                continue
            tag = tags[0]
            group_path = group_path_for(path, tag)
            method_name = method_name_for(operation["operationId"], group_path)
            path_params, query_params = extract_parameters(path_item, operation)
            operations.append(
                {
                    "operation_id": operation["operationId"],
                    "http_method": http_method.upper(),
                    "path": path,
                    "group_path": group_path,
                    "remainder": operation_remainder(operation["operationId"], group_path),
                    "method_name": method_name,
                    "path_params": path_params,
                    "query_params": query_params,
                    "request": request_schema_info(operation, schemas),
                    "response": response_info(path, operation),
                }
            )
    return operations


def build_group_tree(group_paths: set[str]) -> dict[str, dict]:
    tree: dict[str, dict] = {}
    for group_path in sorted(group_paths):
        parts = group_path.split(".")
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
    return tree


def expand_group_paths(group_paths: set[str]) -> list[str]:
    expanded: set[str] = set()
    for group_path in group_paths:
        parts = group_path.split(".")
        for index in range(len(parts)):
            expanded.add(".".join(parts[: index + 1]))
    return sorted(expanded)


def child_groups_for(group_paths: list[str]) -> dict[str, list[str]]:
    children: dict[str, list[str]] = defaultdict(list)
    for group_path in group_paths:
        parts = group_path.split(".")
        if len(parts) == 1:
            continue
        children[".".join(parts[:-1])].append(group_path)
    for child_list in children.values():
        child_list.sort()
    return children


def class_name(group_path: str, suffix: str) -> str:
    return camelize(group_path.split(".")) + suffix


def render_signature(operation: dict) -> tuple[str, list[tuple[str, str]]]:
    params = []
    param_mappings = []
    for parameter in operation["path_params"]:
        name = parameter["name"]
        var_name = sanitize_name(name)
        params.append(f"{var_name}: {param_hint(parameter.get('schema') or {}, True)}")
        param_mappings.append((name, var_name))

    request = operation["request"]
    if request is not None:
        if request["required"]:
            params.append("body: Any")
        else:
            params.append("body: Any | None = None")

    for parameter in operation["query_params"]:
        name = parameter["name"]
        var_name = sanitize_name(name)
        params.append(f"{var_name}: {param_hint(parameter.get('schema') or {}, False)} = None")
        param_mappings.append((name, var_name))

    params.append("organisation_id: int | None = None")
    return ", ".join(params), param_mappings


def render_method(operation: dict, async_mode: bool) -> list[str]:
    signature, param_mappings = render_signature(operation)
    method_line = f"    {'async ' if async_mode else ''}def {operation['method_name']}(self"
    if signature:
        method_line += f", {signature}"
    method_line += "):"
    lines = [method_line]

    path_expr = operation["path"]
    for original, variable in param_mappings:
        path_expr = path_expr.replace("{" + original + "}", "{" + variable + "}")
    lines.append(f'        path = f"{path_expr}"')

    if operation["query_params"]:
        lines.append("        params = {")
        for parameter in operation["query_params"]:
            var_name = sanitize_name(parameter["name"])
            lines.append(f'            "{parameter["name"]}": {var_name},')
        lines.append("        }")
    else:
        lines.append("        params = None")

    request = operation["request"]
    response = operation["response"]
    binary_fields = request["binary_fields"] if request else []
    call_prefix = "await " if async_mode else ""
    lines.append(f"        return {call_prefix}self._root._execute(")
    lines.append(f'            "{operation["http_method"]}",')
    lines.append("            path,")
    lines.append("            params=params,")
    if request is not None:
        lines.append("            body=body,")
        lines.append(f'            body_schema={request["schema_name"]!r},')
        lines.append(f'            body_mode="{request["body_mode"]}",')
        lines.append(f"            binary_fields={binary_fields!r},")
    else:
        lines.append("            body=None,")
        lines.append("            body_schema=None,")
        lines.append('            body_mode="json",')
        lines.append("            binary_fields=None,")
    lines.append("            organisation_id=organisation_id,")
    lines.append(f'            response_kind="{response["kind"]}",')
    lines.append(f"            response_schema={response['schema_name']!r},")
    lines.append(f"            item_schema={response['item_schema']!r},")
    lines.append("        )")
    lines.append("")
    return lines


def render_generated_module(operations: list[dict], async_mode: bool) -> str:
    suffix = "AsyncGroup" if async_mode else "SyncGroup"
    executor = "_AsyncControlExecutor" if async_mode else "_SyncControlExecutor"
    mixin_name = "AsyncControlClientGroups" if async_mode else "ControlClientGroups"
    blocks = [
        "from __future__ import annotations",
        "",
        "from typing import Any, Sequence",
        "",
        f"from ._base import {executor}, _ControlGroupBase",
        "",
        "",
    ]

    by_group: dict[str, list[dict]] = defaultdict(list)
    for operation in operations:
        by_group[operation["group_path"]].append(operation)

    all_group_paths = expand_group_paths({operation["group_path"] for operation in operations})
    child_groups = child_groups_for(all_group_paths)
    root_groups = [group_path for group_path in all_group_paths if "." not in group_path]

    blocks.append(f"class {mixin_name}:")
    for group_path in root_groups:
        blocks.append(f"    {group_path}: {class_name(group_path, suffix)}")
    if async_mode:
        blocks.append("")
        blocks.append("    async def _execute(self, *args: Any, **kwargs: Any) -> Any:")
        blocks.append("        raise NotImplementedError")
    else:
        blocks.append("")
        blocks.append("    def _execute(self, *args: Any, **kwargs: Any) -> Any:")
        blocks.append("        raise NotImplementedError")
    if not root_groups:
        blocks.append("    pass")
    blocks.append("")

    for group_path in all_group_paths:
        blocks.append(f"class {class_name(group_path, suffix)}(_ControlGroupBase[{executor}]):")
        group_ops = by_group.get(group_path) or []
        child_paths = child_groups.get(group_path, [])
        for child_path in child_paths:
            attr = child_path.rsplit(".", 1)[-1]
            blocks.append(f"    {attr}: {class_name(child_path, suffix)}")
        if child_paths:
            blocks.append("")
        if not group_ops:
            if not child_paths:
                blocks.append("    pass")
                blocks.append("")
            continue
        counts = Counter(operation["method_name"] for operation in group_ops)
        seen = set()
        for operation in sorted(group_ops, key=lambda item: (item["method_name"], item["operation_id"])):
            unique_operation = dict(operation)
            method_name = unique_operation["method_name"]
            if counts[method_name] > 1:
                unique_operation["method_name"] = fallback_method_name(
                    unique_operation["remainder"]
                )
            if unique_operation["method_name"] in seen:
                unique_operation["method_name"] = sanitize_name(unique_operation["operation_id"])
            else:
                unique_operation["method_name"] = sanitize_name(unique_operation["method_name"])
            seen.add(unique_operation["method_name"])
            blocks.extend(render_method(unique_operation, async_mode))

    attach_name = "_attach_async_groups" if async_mode else "_attach_sync_groups"
    blocks.append(f"def {attach_name}(root: {mixin_name}):")
    created = set()
    for group_path in all_group_paths:
        parts = group_path.split(".")
        for index in range(len(parts)):
            partial = ".".join(parts[: index + 1])
            if partial in created:
                continue
            created.add(partial)
            current = "root"
            if index:
                current += "." + ".".join(parts[:index])
            attr = parts[index]
            blocks.append(
                f"    {current}.{attr} = {class_name(partial, suffix)}(root)"
            )
    blocks.append("")
    blocks.append(f"OPERATION_COUNT = {len(operations)}")
    blocks.append("")
    blocks.append("__all__ = [")
    blocks.append(f'    "{mixin_name}",')
    blocks.append(f'    "{attach_name}",')
    blocks.append('    "OPERATION_COUNT",')
    for group_path in all_group_paths:
        blocks.append(f'    "{class_name(group_path, suffix)}",')
    blocks.append("]")
    blocks.append("")
    return "\n".join(blocks)


def build_groups_module(operations: list[dict]) -> str:
    group_tree = build_group_tree({operation["group_path"] for operation in operations})
    lines = []
    lines.append(f"GROUP_TREE = {group_tree!r}")
    lines.append("")
    lines.append(f"EXCLUDED_PATHS = {sorted(EXCLUDED_PATHS)!r}")
    lines.append(f"INCLUDED_OPERATION_IDS = {[op['operation_id'] for op in operations]!r}")
    lines.append(f"OPERATION_COUNT = {len(operations)}")
    lines.append("")
    lines.append("__all__ = [")
    lines.append('    "EXCLUDED_PATHS",')
    lines.append('    "GROUP_TREE",')
    lines.append('    "INCLUDED_OPERATION_IDS",')
    lines.append('    "OPERATION_COUNT",')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def main():
    spec = load_spec()
    operations = collect_operations(spec)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GROUPS_PATH.write_text(build_groups_module(operations) + "\n")
    SYNC_PATH.write_text(render_generated_module(operations, async_mode=False) + "\n")
    ASYNC_PATH.write_text(render_generated_module(operations, async_mode=True) + "\n")


if __name__ == "__main__":
    main()
