# Configuration Types Reference

Complete reference for all configuration types available in `pydoover.config`.

## Type Hierarchy

```
ConfigElement (base)
├── Integer
│   └── Number
├── Boolean
├── String
├── Enum
├── Array
├── Object
└── Application
```

## Common Parameters

All configuration types accept these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `display_name` | `str` | Required | Label shown in UI (first positional arg) |
| `default` | varies | `NotSet` | Default value; if `NotSet`, field is required |
| `description` | `str` | `None` | Help text shown in UI |
| `hidden` | `bool` | `False` | Hide from UI |
| `deprecated` | `bool` | `None` | Mark as deprecated |
| `position` | `int` | auto | Order in UI (auto-assigned if not specified) |

## Integer

Whole number values.

```python
from pydoover import config

config.Integer(
    "Port Number",           # display_name
    default=8080,            # default value
    minimum=1,               # inclusive minimum
    maximum=65535,           # inclusive maximum
    exclusive_minimum=None,  # value must be > this
    exclusive_maximum=None,  # value must be < this
    multiple_of=None,        # value must be multiple of this
    description="TCP port to listen on"
)
```

### Examples

```python
# Basic integer
self.count = config.Integer("Item Count", default=10)

# With range
self.port = config.Integer(
    "Port",
    default=8080,
    minimum=1024,
    maximum=65535,
    description="Port must be between 1024 and 65535"
)

# Required (no default)
self.device_id = config.Integer("Device ID")

# Multiple of constraint
self.interval = config.Integer(
    "Interval",
    default=60,
    multiple_of=15,
    description="Must be a multiple of 15 seconds"
)
```

### Value Access

```python
port = self.config.port.value  # Returns int
```

## Number

Floating-point values. Inherits from Integer.

```python
config.Number(
    "Temperature",
    default=25.0,
    minimum=-40.0,
    maximum=100.0,
    description="Temperature in Celsius"
)
```

### Examples

```python
# Basic number
self.threshold = config.Number("Threshold", default=0.5)

# With precision constraints
self.voltage = config.Number(
    "Voltage",
    default=24.0,
    minimum=0.0,
    maximum=48.0
)

# Scientific values
self.coefficient = config.Number(
    "Calibration Coefficient",
    default=1.0,
    minimum=0.001,
    maximum=1000.0
)
```

### Value Access

```python
temp = self.config.threshold.value  # Returns float
```

## Boolean

True/False values.

```python
config.Boolean(
    "Enable Feature",
    default=True,
    description="Enable or disable this feature"
)
```

### Examples

```python
# Simple toggle
self.enabled = config.Boolean("Enabled", default=True)

# Feature flags
self.debug_mode = config.Boolean(
    "Debug Mode",
    default=False,
    description="Enable verbose logging"
)

self.auto_restart = config.Boolean(
    "Auto Restart",
    default=True,
    description="Automatically restart on failure"
)
```

### Value Access

```python
if self.config.enabled.value:
    do_something()
```

## String

Text values.

```python
config.String(
    "Device Name",
    default="sensor-1",
    length=None,        # Maximum length (None = unlimited)
    pattern=None,       # Regex pattern for validation
    description="Human-readable device name"
)
```

### Examples

```python
# Simple string
self.name = config.String("Name", default="default")

# With length limit
self.serial = config.String(
    "Serial Number",
    length=20,
    description="Device serial number (max 20 chars)"
)

# With pattern validation
self.ip_address = config.String(
    "IP Address",
    default="192.168.1.1",
    pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
    description="IPv4 address"
)

# Required string
self.api_key = config.String(
    "API Key",
    description="Required API key for authentication"
)
```

### Value Access

```python
name = self.config.name.value  # Returns str
```

## Enum

Selection from predefined choices. Renders as dropdown in UI.

```python
config.Enum(
    "Mode",
    choices=["auto", "manual", "off"],
    default="auto",
    description="Operating mode selection"
)
```

### Using String Choices

```python
self.mode = config.Enum(
    "Mode",
    choices=["auto", "manual", "standby"],
    default="auto"
)

self.priority = config.Enum(
    "Priority",
    choices=["low", "medium", "high", "critical"],
    default="medium"
)
```

### Using Python Enum

```python
import enum

class OperatingMode(enum.Enum):
    AUTO = "Automatic"
    MANUAL = "Manual"
    STANDBY = "Standby"

self.mode = config.Enum(
    "Mode",
    choices=OperatingMode,
    default=OperatingMode.AUTO
)
```

### Using Objects with __str__

```python
class Priority:
    def __init__(self, name, level):
        self.name = name
        self.level = level

    def __str__(self):
        return self.name

class PriorityLevel(enum.Enum):
    LOW = Priority("Low", 1)
    MEDIUM = Priority("Medium", 2)
    HIGH = Priority("High", 3)

self.priority = config.Enum(
    "Priority",
    choices=PriorityLevel,
    default=PriorityLevel.MEDIUM
)

# Access the level
level = self.config.priority.value.level  # Returns 2
```

### Value Access

```python
# String choices
mode = self.config.mode.value  # Returns "auto"

# Enum choices
mode = self.config.mode.value  # Returns OperatingMode.AUTO
mode_name = self.config.mode.value.value  # Returns "Automatic"
```

## Array

List of values.

```python
config.Array(
    "Sensor IDs",
    element=config.Integer("ID", default=0),
    min_items=1,
    max_items=10,
    unique_items=True,
    description="List of sensor identifiers"
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `element` | `ConfigElement` | Type of array elements |
| `min_items` | `int` | Minimum number of items |
| `max_items` | `int` | Maximum number of items |
| `unique_items` | `bool` | Require unique values |

> **Note:** `default` is not allowed for Array types.

### Examples

```python
# Array of integers
self.sensor_ids = config.Array(
    "Sensor IDs",
    element=config.Integer("ID"),
    min_items=1,
    max_items=8
)

# Array of strings
self.allowed_ips = config.Array(
    "Allowed IPs",
    element=config.String("IP Address"),
    unique_items=True
)

# Array of objects
self.schedules = config.Array(
    "Schedules",
    element=config.Object("Schedule")
)
```

### Value Access

```python
# Iterate over elements
for elem in self.config.sensor_ids.elements:
    sensor_id = elem.value
    print(f"Sensor: {sensor_id}")

# Get as list
ids = [e.value for e in self.config.sensor_ids.elements]
```

## Object

Nested configuration structure.

```python
pump_settings = config.Object(
    "Pump Settings",
    collapsible=True,
    default_collapsed=False,
    additional_elements=True
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collapsible` | `bool` | `True` | Can be collapsed in UI |
| `default_collapsed` | `bool` | `False` | Initially collapsed |
| `additional_elements` | `bool` | `True` | Allow undefined keys |

> **Note:** `default` is not allowed for Object types.

### Adding Elements

```python
# Method 1: add_elements()
self.pump = config.Object("Pump Settings")
self.pump.add_elements(
    config.Integer("Output Pin", default=0),
    config.Number("Flow Rate", default=10.0)
)

# Method 2: Attribute assignment
self.pump = config.Object("Pump Settings")
self.pump.output_pin = config.Integer("Output Pin", default=0)
self.pump.flow_rate = config.Number("Flow Rate", default=10.0)
```

### Nested Objects

```python
self.settings = config.Object("Settings")
self.settings.network = config.Object("Network Settings")
self.settings.network.ip = config.String("IP Address", default="192.168.1.1")
self.settings.network.port = config.Integer("Port", default=8080)
```

### Value Access

```python
pin = self.config.pump.output_pin.value
flow = self.config.pump.flow_rate.value

# Nested
ip = self.config.settings.network.ip.value
```

## Application

Reference to another Doover application. Renders as dropdown of installed apps.

```python
config.Application(
    "Linked Application",
    description="Select an application to communicate with"
)
```

### Examples

```python
# Link to another app
self.data_source = config.Application(
    "Data Source",
    description="Application providing sensor data"
)

# Optional link
self.backup_app = config.Application(
    "Backup Application",
    default=None,  # Makes it optional
    description="Optional backup data source"
)
```

### Value Access

```python
app_key = self.config.data_source.value  # Returns app key string

# Use to get tags from linked app
if app_key:
    data = self.get_tag("sensor_data", app_key=app_key)
```

## Variable

Reference to a dynamic value from another configuration.

```python
config.Variable(
    scope="other_app",
    name="setting_name"
)
```

### Usage

Used as default values that reference other app settings:

```python
self.threshold = config.Number(
    "Threshold",
    default=config.Variable("sensor_app", "max_reading")
)
```

### String Representation

```python
var = config.Variable("app", "setting")
str(var)  # Returns "$app.setting"
```

## Required vs Optional

```python
# Required - no default, must be provided
self.api_key = config.String("API Key")

# Optional - has default value
self.timeout = config.Integer("Timeout", default=30)

# Optional - explicitly None default
self.backup = config.Application("Backup", default=None)
```

## Hidden Fields

```python
# Hidden from UI but still configurable via API
self.internal_key = config.String(
    "Internal Key",
    default="default-key",
    hidden=True
)
```

## Deprecated Fields

```python
self.old_setting = config.Integer(
    "Old Setting",
    default=0,
    deprecated=True,
    description="Deprecated: Use 'new_setting' instead"
)
```

---

See Also:
- [[20-Configuration-System|Configuration System]]
- [[22-Config-Schema-Export|Schema Export]]
- [[10-Application-Framework|Application Framework]]

#config #types #reference #pydoover
