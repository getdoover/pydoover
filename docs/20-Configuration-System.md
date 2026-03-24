# Configuration System

The pydoover configuration system allows you to define typed configuration schemas for your applications. These schemas generate JSON Schema for UI forms and provide runtime access to configuration values.

## Overview

Configuration schemas are defined by subclassing `pydoover.config.Schema`. Each attribute becomes a configuration field with validation, defaults, and UI generation.

## Basic Usage

```python
from pydoover import config

class MyAppConfig(config.Schema):
    def __init__(self):
        self.poll_interval = config.Number(
            "Poll Interval",
            default=1.0,
            minimum=0.1,
            maximum=60.0,
            description="Seconds between sensor reads"
        )

        self.enabled = config.Boolean(
            "Feature Enabled",
            default=True,
            description="Enable or disable the feature"
        )

        self.mode = config.Enum(
            "Operating Mode",
            choices=["auto", "manual", "standby"],
            default="auto"
        )
```

## Accessing Configuration Values

In your application:

```python
class MyApp(Application):
    config: MyAppConfig  # Type hint for IDE support

    def setup(self):
        # Access values via .value property
        interval = self.config.poll_interval.value
        is_enabled = self.config.enabled.value
        mode = self.config.mode.value

        print(f"Poll interval: {interval}s")
        print(f"Enabled: {is_enabled}")
        print(f"Mode: {mode}")
```

## Configuration Types

### Integer

For whole numbers:

```python
config.Integer(
    "Count",
    default=10,
    minimum=0,
    maximum=100,
    exclusive_minimum=None,  # Value must be > this
    exclusive_maximum=None,  # Value must be < this
    multiple_of=None,        # Value must be multiple of this
    description="Number of items"
)
```

### Number

For floating-point numbers:

```python
config.Number(
    "Temperature Setpoint",
    default=25.0,
    minimum=-40.0,
    maximum=100.0,
    description="Target temperature in Celsius"
)
```

### Boolean

For true/false values:

```python
config.Boolean(
    "Enable Logging",
    default=True,
    description="Whether to log sensor data"
)
```

### String

For text values:

```python
config.String(
    "Device Name",
    default="sensor-1",
    length=None,      # Maximum length
    pattern=None,     # Regex pattern for validation
    description="Human-readable device identifier"
)
```

### Enum

For dropdown selections:

```python
# Simple string choices
config.Enum(
    "Mode",
    choices=["auto", "manual", "off"],
    default="auto"
)

# Using Python Enum
import enum

class OperatingMode(enum.Enum):
    AUTO = "Automatic"
    MANUAL = "Manual"
    STANDBY = "Standby"

config.Enum(
    "Mode",
    choices=OperatingMode,
    default=OperatingMode.AUTO
)
```

### Array

For lists of values:

```python
config.Array(
    "Sensor IDs",
    element=config.Integer("ID", default=0),
    min_items=1,
    max_items=10,
    unique_items=True
)
```

Accessing array values:

```python
for elem in self.config.sensor_ids.elements:
    sensor_id = elem.value
```

### Object

For nested configuration:

```python
pump_config = config.Object(
    "Pump Settings",
    collapsible=True,
    default_collapsed=False
)
pump_config.add_elements(
    config.Integer("Output Pin", default=0, minimum=0, maximum=7),
    config.Number("Flow Rate", default=10.0, description="Liters per minute")
)

# Or using attribute assignment:
class MyConfig(config.Schema):
    def __init__(self):
        self.pump = config.Object("Pump Settings")
        self.pump.output_pin = config.Integer("Output Pin", default=0)
        self.pump.flow_rate = config.Number("Flow Rate", default=10.0)
```

Accessing object values:

```python
pin = self.config.pump.output_pin.value
flow = self.config.pump.flow_rate.value
```

### Application

For referencing other Doover applications:

```python
config.Application(
    "Linked Application",
    description="Select an application to link with"
)
```

Renders as a dropdown of installed applications.

### Variable

For referencing dynamic values:

```python
config.Variable(
    scope="other_app",
    name="some_setting"
)
```

Used as default values that reference other app settings.

## Common Options

All configuration types support:

| Option | Type | Description |
|--------|------|-------------|
| `display_name` | `str` | Label shown in UI (first positional arg) |
| `default` | varies | Default value (required if not nullable) |
| `description` | `str` | Help text shown in UI |
| `hidden` | `bool` | Hide from UI (default: False) |
| `deprecated` | `bool` | Mark as deprecated |
| `position` | `int` | Order in UI (auto-assigned) |

## Required vs Optional

Fields without a `default` are required:

```python
# Required - must be provided
self.api_key = config.String("API Key")

# Optional - has default
self.timeout = config.Integer("Timeout", default=30)
```

## Exporting Schema

Export your schema to `doover_config.json`:

```python
# In app_config.py
def export():
    import pathlib
    cfg = MyAppConfig()
    cfg.export(pathlib.Path("doover_config.json"), "my_app")

if __name__ == "__main__":
    export()
```

Or use the CLI:

```bash
doover config-schema export
```

## Generated JSON Schema

The schema generates JSON Schema (Draft 2020-12):

```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "",
    "title": "Application Config",
    "type": "object",
    "properties": {
        "poll_interval": {
            "title": "Poll Interval",
            "type": "number",
            "default": 1.0,
            "minimum": 0.1,
            "maximum": 60.0,
            "description": "Seconds between sensor reads"
        },
        "enabled": {
            "title": "Feature Enabled",
            "type": "boolean",
            "default": true
        }
    },
    "required": ["api_key"],
    "additionalElements": true
}
```

## Deployment Configuration

Configuration values are injected at runtime from the deployment configuration:

1. Application starts
2. Connects to Device Agent
3. Waits for `deployment_config` channel
4. Injects values into `Schema` instance
5. `setup()` is called

## Custom Validation

Add custom validation in a property:

```python
class MyConfig(config.Schema):
    def __init__(self):
        self._threshold_low = config.Integer("Low Threshold", default=10)
        self._threshold_high = config.Integer("High Threshold", default=90)

    @property
    def threshold_range(self):
        low = self._threshold_low.value
        high = self._threshold_high.value
        if low >= high:
            raise ValueError("Low threshold must be less than high")
        return (low, high)
```

## Complete Example

```python
from pydoover import config
import enum

class PumpMode(enum.Enum):
    CONTINUOUS = "Continuous"
    INTERMITTENT = "Intermittent"
    MANUAL = "Manual Only"

class PumpControlConfig(config.Schema):
    def __init__(self):
        # Basic settings
        self.pump_mode = config.Enum(
            "Pump Mode",
            choices=PumpMode,
            default=PumpMode.CONTINUOUS,
            description="How the pump operates"
        )

        self.output_pin = config.Integer(
            "Digital Output",
            default=0,
            minimum=0,
            maximum=7,
            description="DO pin connected to pump relay"
        )

        # Timing settings
        self.on_duration = config.Number(
            "On Duration",
            default=30.0,
            minimum=1.0,
            description="Seconds to run pump (intermittent mode)"
        )

        self.off_duration = config.Number(
            "Off Duration",
            default=60.0,
            minimum=1.0,
            description="Seconds between pump cycles"
        )

        # Advanced settings (hidden by default)
        self.advanced = config.Object(
            "Advanced Settings",
            collapsible=True,
            default_collapsed=True
        )
        self.advanced.startup_delay = config.Number(
            "Startup Delay",
            default=5.0,
            description="Delay before first pump cycle"
        )

def export():
    import pathlib
    cfg = PumpControlConfig()
    cfg.export(pathlib.Path("doover_config.json"), "pump_control")

if __name__ == "__main__":
    export()
```

---

See Also:
- [[21-Config-Types|Configuration Types Reference]]
- [[22-Config-Schema-Export|Schema Export Details]]
- [[10-Application-Framework|Application Framework]]

#configuration #schema #pydoover
