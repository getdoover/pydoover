# Configuration Schema Export

This document covers exporting your configuration schema to `doover_config.json` for deployment.

## Overview

The configuration schema defined in Python generates a JSON Schema that:
- Powers the configuration UI in the Doover web platform
- Validates configuration values
- Documents available settings

## Export Methods

### Method 1: CLI (Recommended)

```bash
# From project root
doover config-schema export
```

This finds your `app_config.py` and exports to `doover_config.json`.

### Method 2: Python Script

```python
# In app_config.py
from pydoover import config
import pathlib

class MyConfig(config.Schema):
    def __init__(self):
        self.setting = config.Integer("Setting", default=10)

def export():
    cfg = MyConfig()
    cfg.export(pathlib.Path("doover_config.json"), "my_app")

if __name__ == "__main__":
    export()
```

Run with:
```bash
python -m my_app.app_config
# or
python src/my_app/app_config.py
```

### Method 3: Programmatic

```python
from pathlib import Path
from my_app.app_config import MyConfig

config = MyConfig()
config.export(Path("doover_config.json"), "my_app_key")
```

## Export Parameters

```python
config.export(
    fp: pathlib.Path,    # Path to doover_config.json
    app_name: str        # Application key
)
```

## Generated Structure

The export creates/updates `doover_config.json`:

```json
{
    "my_app": {
        "config_schema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "",
            "title": "Application Config",
            "type": "object",
            "properties": {
                "setting_name": {
                    "title": "Setting Name",
                    "type": "integer",
                    "default": 10,
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Help text here",
                    "x-name": "setting_name",
                    "x-hidden": false,
                    "x-position": 0
                }
            },
            "required": ["required_field"],
            "additionalElements": true
        }
    }
}
```

## JSON Schema Mapping

### Type Mappings

| Python Type | JSON Schema Type |
|-------------|-----------------|
| `Integer` | `"type": "integer"` |
| `Number` | `"type": "number"` |
| `Boolean` | `"type": "boolean"` |
| `String` | `"type": "string"` |
| `Enum` | `"enum": [...]` |
| `Array` | `"type": "array"` |
| `Object` | `"type": "object"` |
| `Application` | `"type": "string", "format": "doover-application"` |

### Extended Properties

Custom properties prefixed with `x-`:

| Property | Purpose |
|----------|---------|
| `x-name` | Internal field name |
| `x-hidden` | Hide from UI |
| `x-position` | Order in UI |
| `x-collapsible` | Object can collapse |
| `x-defaultCollapsed` | Object starts collapsed |

## Complete doover_config.json

A full configuration file includes more than just the schema:

```json
{
    "my_app": {
        "display_name": "My Application",
        "app_type": "docker",
        "visibility": "private",
        "config_schema": { ... },
        "dependencies": [
            "modbus_interface"
        ],
        "container_image": {
            "repository": "registry.example.com/my_app",
            "tag": "latest"
        },
        "build_args": {
            "platforms": "linux/amd64,linux/arm64"
        }
    }
}
```

### Non-Schema Fields

These are typically set manually or by the CLI:

| Field | Description |
|-------|-------------|
| `display_name` | Human-readable name |
| `app_type` | `"docker"` or `"processor"` |
| `visibility` | `"private"` or `"public"` |
| `dependencies` | List of required app keys |
| `container_image` | Docker registry info |
| `build_args` | Build configuration |

## Schema Validation

### Required Fields

Fields without a default are required:

```python
# Required (no default)
self.api_key = config.String("API Key")

# Generated schema includes in "required" array
```

### Validation Constraints

```python
self.port = config.Integer(
    "Port",
    default=8080,
    minimum=1024,
    maximum=65535
)
```

Generates:
```json
{
    "port": {
        "type": "integer",
        "default": 8080,
        "minimum": 1024,
        "maximum": 65535
    }
}
```

## Multiple Apps

If your project has multiple apps, each gets its own key:

```python
# app1_config.py
class App1Config(config.Schema):
    ...

# app2_config.py
class App2Config(config.Schema):
    ...

# Export both
App1Config().export(Path("doover_config.json"), "app1")
App2Config().export(Path("doover_config.json"), "app2")
```

Results in:
```json
{
    "app1": { "config_schema": { ... } },
    "app2": { "config_schema": { ... } }
}
```

## Best Practices

### 1. Version Control Schema

Always commit `doover_config.json`:

```bash
git add doover_config.json
git commit -m "Update configuration schema"
```

### 2. Export on Change

Re-export when schema changes:

```bash
# Add to CI/CD or pre-commit hook
doover config-schema export
```

### 3. Validate Before Deploy

```bash
# Validate schema syntax
doover config-schema validate
```

### 4. Document Fields

Always include descriptions:

```python
self.threshold = config.Number(
    "Alert Threshold",
    default=80.0,
    minimum=0.0,
    maximum=100.0,
    description="Percentage threshold for triggering alerts. "
                "Values above this will generate notifications."
)
```

## Troubleshooting

### Schema Not Updating

```bash
# Force regeneration
rm doover_config.json
doover config-schema export
```

### Import Errors

Ensure your config module is importable:

```bash
# Test import
python -c "from my_app.app_config import MyConfig; print(MyConfig())"
```

### Invalid JSON

Validate JSON syntax:

```bash
python -m json.tool doover_config.json
```

---

See Also:
- [[20-Configuration-System|Configuration System]]
- [[21-Config-Types|Configuration Types]]
- [[03-Project-Structure|Project Structure]]

#config #export #schema #json #pydoover
