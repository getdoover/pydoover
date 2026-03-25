# UI Variables Reference

Variables are read-only UI elements that display values from your application. Users cannot modify them directly.

## Variable Types

| Type | Purpose | Value Type |
|------|---------|------------|
| `NumericVariable` | Numbers with ranges | `int`, `float` |
| `TextVariable` | Text strings | `str` |
| `BooleanVariable` | True/False indicators | `bool` |
| `DateTimeVariable` | Timestamps | `datetime`, `int` |

## Base Variable Class

All variables inherit from `Variable`:

```python
from pydoover.ui import Variable

Variable(
    name="var_name",           # Unique identifier
    display_name="Display",    # Label in UI
    var_type="float",          # Type hint
    curr_val=None,             # Initial value
    precision=None,            # Decimal places
    ranges=[],                 # Color ranges
    earliest_data_time=None,   # For charts
    default_zoom=None,         # Chart zoom
    log_threshold=None,        # Change threshold for logging
    # Common Element options:
    help_str=None,             # Help tooltip
    hidden=False,              # Hide from UI
    position=None              # Order in UI
)
```

## NumericVariable

For displaying numeric values with optional color coding.

```python
from pydoover import ui

ui.NumericVariable(
    name="temperature",
    display_name="Temperature",
    curr_val=25.5,
    precision=1,
    ranges=[
        ui.Range("Cold", 0, 15, ui.Colour.blue),
        ui.Range("Normal", 15, 30, ui.Colour.green),
        ui.Range("Hot", 30, 100, ui.Colour.red)
    ],
    form=ui.Widget.gauge,      # Display widget
    earliest_data_time=datetime(2024, 1, 1),
    default_zoom="24h",
    log_threshold=0.5
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | Required | UI label |
| `curr_val` | `float/int` | `None` | Initial value |
| `precision` | `int` | `None` | Decimal places |
| `ranges` | `list[Range]` | `[]` | Color ranges |
| `form` | `Widget` | `None` | Display widget |
| `earliest_data_time` | `datetime` | `None` | Chart start |
| `default_zoom` | `str` | `None` | Chart zoom level |
| `log_threshold` | `float` | `None` | Log on change |

### Examples

```python
# Basic numeric
temp = ui.NumericVariable("temp", "Temperature")

# With precision
voltage = ui.NumericVariable(
    "voltage", "Voltage",
    curr_val=24.567,
    precision=2  # Shows 24.57
)

# With ranges
pressure = ui.NumericVariable(
    "pressure", "Pressure (PSI)",
    ranges=[
        ui.Range("Low", 0, 20, ui.Colour.yellow),
        ui.Range("Normal", 20, 80, ui.Colour.green),
        ui.Range("High", 80, 100, ui.Colour.red)
    ]
)

# With gauge widget
level = ui.NumericVariable(
    "level", "Tank Level",
    form=ui.Widget.gauge
)
```

## TextVariable

For displaying text values.

```python
ui.TextVariable(
    name="status",
    display_name="Status",
    curr_val="Running"
)
```

### Examples

```python
# Simple text
status = ui.TextVariable("status", "Status", curr_val="OK")

# Longer text
message = ui.TextVariable(
    "last_error",
    "Last Error",
    curr_val="No errors",
    help_str="Most recent error message"
)
```

## BooleanVariable

For displaying true/false states.

```python
ui.BooleanVariable(
    name="pump_running",
    display_name="Pump Running",
    curr_val=False,
    log_threshold=0  # Log every change
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_threshold` | `float` | `0` | `0` = log every change, `None` = never log |

### Examples

```python
# Basic boolean
active = ui.BooleanVariable("active", "System Active", curr_val=True)

# With logging
pump_status = ui.BooleanVariable(
    "pump_running",
    "Pump Running",
    curr_val=False,
    log_threshold=0  # Log every state change
)

# Without logging
transient = ui.BooleanVariable(
    "processing",
    "Processing",
    log_threshold=None  # Don't log changes
)
```

## DateTimeVariable

For displaying timestamps.

```python
from datetime import datetime

ui.DateTimeVariable(
    name="last_update",
    display_name="Last Updated",
    curr_val=datetime.now()
)
```

### Value Types

```python
# datetime object
dt_var = ui.DateTimeVariable(
    "last_seen", "Last Seen",
    curr_val=datetime.now()
)

# Unix timestamp (int)
dt_var = ui.DateTimeVariable(
    "last_seen", "Last Seen",
    curr_val=1704067200  # Jan 1, 2024
)
```

## Ranges

Color-coded ranges for numeric variables.

```python
ui.Range(
    name="Normal",       # Range name
    start=20,            # Start value (inclusive)
    end=30,              # End value (inclusive)
    colour=ui.Colour.green
)
```

### Creating Ranges

```python
# Individual ranges
low = ui.Range("Low", 0, 20, ui.Colour.blue)
normal = ui.Range("Normal", 20, 80, ui.Colour.green)
high = ui.Range("High", 80, 100, ui.Colour.red)

# Use in variable
temp = ui.NumericVariable(
    "temp", "Temperature",
    ranges=[low, normal, high]
)

# Inline definition
temp = ui.NumericVariable(
    "temp", "Temperature",
    ranges=[
        ui.Range("Low", 0, 20, ui.Colour.blue),
        ui.Range("Normal", 20, 80, ui.Colour.green),
        ui.Range("High", 80, 100, ui.Colour.red)
    ]
)
```

### Range Tips

- Ranges should cover the full expected value range
- Ranges can overlap (first match wins)
- Gaps show as default (no color)

## Updating Variables

### Direct Property

```python
temp_var = self.ui_manager.get_element("temperature")
temp_var.current_value = 26.5
```

### update() Method

```python
temp_var.update(26.5)

# Force log this update
temp_var.update(26.5, force_log=True)
```

### Through UIManager

```python
# Simple update
self.ui_manager.update_variable("temperature", 26.5)

# Critical update (triggers immediate push)
self.ui_manager.update_variable("temperature", 26.5, critical=True)
```

## Logging Behavior

### log_threshold

Controls when value changes are logged:

```python
# Log when change exceeds 0.5
ui.NumericVariable("temp", "Temp", log_threshold=0.5)
# Change from 25.0 to 25.3 → not logged
# Change from 25.0 to 25.6 → logged

# Log every change
ui.NumericVariable("temp", "Temp", log_threshold=0)

# Never auto-log
ui.NumericVariable("temp", "Temp", log_threshold=None)
```

### has_pending_log_request()

Check if variable wants to log:

```python
if temp_var.has_pending_log_request():
    # Variable has changed enough to warrant logging
    pass
```

### clear_log_request()

Clear pending log flag:

```python
temp_var.clear_log_request()
```

## Charts and History

### earliest_data_time

Sets the start of historical data:

```python
from datetime import datetime

ui.NumericVariable(
    "temp", "Temperature",
    earliest_data_time=datetime(2024, 1, 1)
)
```

### default_zoom

Sets default chart zoom level:

```python
ui.NumericVariable(
    "temp", "Temperature",
    default_zoom="1h"   # 1 hour
    # Options: "1h", "6h", "12h", "24h", "7d", "30d"
)
```

## Complete Example

```python
from pydoover import ui
from datetime import datetime

def create_sensor_ui():
    return [
        # Main temperature display
        ui.NumericVariable(
            name="temperature",
            display_name="Temperature (°C)",
            precision=1,
            ranges=[
                ui.Range("Cold", -20, 10, ui.Colour.blue),
                ui.Range("Cool", 10, 20, ui.Colour.cyan),
                ui.Range("Normal", 20, 30, ui.Colour.green),
                ui.Range("Warm", 30, 40, ui.Colour.yellow),
                ui.Range("Hot", 40, 60, ui.Colour.red)
            ],
            log_threshold=0.5,
            default_zoom="24h",
            help_str="Current sensor temperature"
        ),

        # Humidity percentage
        ui.NumericVariable(
            name="humidity",
            display_name="Humidity (%)",
            precision=0,
            ranges=[
                ui.Range("Low", 0, 30, ui.Colour.yellow),
                ui.Range("Optimal", 30, 70, ui.Colour.green),
                ui.Range("High", 70, 100, ui.Colour.blue)
            ]
        ),

        # Sensor status
        ui.TextVariable(
            name="sensor_status",
            display_name="Sensor Status",
            curr_val="Initializing..."
        ),

        # Connection indicator
        ui.BooleanVariable(
            name="connected",
            display_name="Sensor Connected",
            curr_val=False,
            log_threshold=0
        ),

        # Last reading time
        ui.DateTimeVariable(
            name="last_reading",
            display_name="Last Reading",
            curr_val=datetime.now()
        )
    ]
```

---

See Also:
- [[30-UI-System-Overview|UI System Overview]]
- [[32-UI-Interactions|UI Interactions]]
- [[34-UI-Decorators|UI Decorators]]

#ui #variables #reference #pydoover
