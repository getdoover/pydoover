# UI Containers Reference

Containers group UI elements together for organization and presentation.

## Container Types

| Type | Purpose |
|------|---------|
| `Container` | Base container (generic grouping) |
| `Submodule` | Collapsible section with status |
| `Application` | Root container for app (internal) |
| `RemoteComponent` | Embed external web component |

## Container (Base)

Base class for grouping elements.

```python
from pydoover import ui

ui.Container(
    name="sensors",
    display_name="Sensors",
    children=[
        ui.NumericVariable("temp", "Temperature"),
        ui.NumericVariable("humidity", "Humidity")
    ],
    status_icon="ok",
    auto_add_elements=True
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | `None` | Container label |
| `children` | `list[Element]` | `[]` | Child elements |
| `status_icon` | `str` | `None` | Status icon |
| `auto_add_elements` | `bool` | `True` | Auto-add class attributes |

### Managing Children

```python
container = ui.Container("group", "My Group")

# Add children
container.add_children(
    ui.NumericVariable("var1", "Variable 1"),
    ui.NumericVariable("var2", "Variable 2")
)

# Remove children
container.remove_children(var1)

# Set children (replaces all)
container.set_children([
    ui.NumericVariable("new_var", "New Variable")
])

# Clear all children
container.clear_children()

# Get children
children = container.children  # Returns list

# Get specific child
element = container.get_element("var1")

# Get all elements recursively
all_elements = container.get_all_elements()

# Get elements by type
variables = container.get_all_elements(type_filter=ui.Variable)
```

## Submodule

Collapsible section for organizing related controls.

```python
ui.Submodule(
    name="pump_controls",
    display_name="Pump Controls",
    children=[
        ui.BooleanVariable("pump_status", "Running"),
        ui.Action("start_pump", "Start"),
        ui.Action("stop_pump", "Stop")
    ],
    status="Running",
    is_collapsed=False
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | Required | Section title |
| `children` | `list[Element]` | `[]` | Child elements |
| `status` | `str` | `None` | Status text |
| `is_collapsed` | `bool` | `False` | Initially collapsed |

### Examples

```python
# Basic submodule
pump = ui.Submodule(
    "pump", "Pump Controls",
    children=[
        ui.BooleanVariable("running", "Running"),
        ui.Action("start", "Start"),
        ui.Action("stop", "Stop")
    ]
)

# With status
pump = ui.Submodule(
    "pump", "Pump Controls",
    children=[...],
    status="Running at 100%"
)

# Initially collapsed
advanced = ui.Submodule(
    "advanced", "Advanced Settings",
    children=[
        ui.Slider("pid_p", "P Gain"),
        ui.Slider("pid_i", "I Gain"),
        ui.Slider("pid_d", "D Gain")
    ],
    is_collapsed=True
)

# Nested submodules
main = ui.Submodule(
    "main", "Main Controls",
    children=[
        ui.NumericVariable("temp", "Temperature"),
        ui.Submodule(
            "details", "Details",
            children=[
                ui.TextVariable("model", "Model"),
                ui.TextVariable("serial", "Serial")
            ],
            is_collapsed=True
        )
    ]
)
```

### Updating Status

```python
# Get the submodule
pump = self.ui_manager.get_element("pump")

# Update status
pump.status = "Running at 75%"

# Update collapsed state
pump.collapsed = True
```

## Application Container

Internal container representing the entire app. Created automatically by UIManager.

```python
# Generally not created directly
# Used internally:
ui.Application(
    name="my_app",
    display_name="My Application",
    variant="stacked"  # or "submodule"
)
```

### Variants

| Variant | Description |
|---------|-------------|
| `stacked` | Normal app display (default) |
| `submodule` | Displayed as submodule of parent |

### Setting Variant

```python
# In application setup
self.ui_manager.set_variant(ui.ApplicationVariant.stacked)
self.ui_manager.set_variant(ui.ApplicationVariant.submodule)
```

## RemoteComponent

Embed external web components.

```python
ui.RemoteComponent(
    name="custom_chart",
    display_name="Custom Chart",
    component_url="https://example.com/chart-component.js",
    children=[]  # Can contain data elements
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | Required | Component title |
| `component_url` | `str` | Required | URL to component |
| `children` | `list[Element]` | `[]` | Data elements |

### Example

```python
# Embed custom visualization
chart = ui.RemoteComponent(
    "live_chart",
    "Live Data Chart",
    component_url="https://components.example.com/live-chart.js",
    children=[
        ui.HiddenValue("chart_config"),
        ui.NumericVariable("chart_data", "Data")
    ]
)
```

## Class-Based Containers

Define containers as classes for reusability:

```python
class PumpControls(ui.Submodule):
    def __init__(self, pump_id: int):
        super().__init__(
            name=f"pump_{pump_id}",
            display_name=f"Pump {pump_id}"
        )

        # Auto-added as children when auto_add_elements=True
        self.running = ui.BooleanVariable(
            f"pump_{pump_id}_running",
            "Running"
        )
        self.speed = ui.NumericVariable(
            f"pump_{pump_id}_speed",
            "Speed (%)"
        )

        # Define interactions
        @ui.action(f"pump_{pump_id}_start", "Start")
        def start(self, value):
            pass

# Usage
pump1 = PumpControls(1)
pump2 = PumpControls(2)

self.set_ui([pump1, pump2])
```

## Organizing UI

### Flat Structure

```python
def create_ui():
    return [
        ui.NumericVariable("temp", "Temperature"),
        ui.NumericVariable("humidity", "Humidity"),
        ui.Action("refresh", "Refresh")
    ]
```

### Grouped Structure

```python
def create_ui():
    return [
        ui.Submodule(
            "readings", "Sensor Readings",
            children=[
                ui.NumericVariable("temp", "Temperature"),
                ui.NumericVariable("humidity", "Humidity")
            ]
        ),
        ui.Submodule(
            "controls", "Controls",
            children=[
                ui.Action("refresh", "Refresh"),
                ui.StateCommand("mode", "Mode", user_options=[...])
            ]
        )
    ]
```

### Nested Structure

```python
def create_ui():
    return [
        ui.Submodule(
            "system", "System",
            children=[
                ui.NumericVariable("uptime", "Uptime"),

                ui.Submodule(
                    "sensors", "Sensors",
                    children=[
                        ui.NumericVariable("temp", "Temperature"),
                        ui.NumericVariable("humidity", "Humidity")
                    ]
                ),

                ui.Submodule(
                    "outputs", "Outputs",
                    children=[
                        ui.BooleanVariable("pump", "Pump"),
                        ui.BooleanVariable("fan", "Fan")
                    ],
                    is_collapsed=True
                )
            ]
        )
    ]
```

## Complete Example

```python
from pydoover import ui

def create_complete_ui():
    return [
        # Main status area (always visible)
        ui.NumericVariable(
            "main_temp", "System Temperature",
            precision=1,
            ranges=[
                ui.Range("Normal", 0, 60, ui.Colour.green),
                ui.Range("High", 60, 80, ui.Colour.red)
            ]
        ),
        ui.TextVariable("system_status", "Status"),

        # Pump controls section
        ui.Submodule(
            "pumps", "Pump Controls",
            status="All pumps normal",
            children=[
                ui.Submodule(
                    "pump1", "Pump 1",
                    children=[
                        ui.BooleanVariable("pump1_running", "Running"),
                        ui.NumericVariable("pump1_speed", "Speed (%)"),
                        ui.Action("pump1_start", "Start", colour=ui.Colour.green),
                        ui.Action("pump1_stop", "Stop", colour=ui.Colour.red)
                    ]
                ),
                ui.Submodule(
                    "pump2", "Pump 2",
                    children=[
                        ui.BooleanVariable("pump2_running", "Running"),
                        ui.NumericVariable("pump2_speed", "Speed (%)"),
                        ui.Action("pump2_start", "Start", colour=ui.Colour.green),
                        ui.Action("pump2_stop", "Stop", colour=ui.Colour.red)
                    ]
                )
            ]
        ),

        # Advanced settings (collapsed by default)
        ui.Submodule(
            "advanced", "Advanced Settings",
            is_collapsed=True,
            children=[
                ui.Slider("threshold", "Alert Threshold", min_val=0, max_val=100),
                ui.StateCommand(
                    "log_level", "Log Level",
                    user_options=[
                        ui.Option("debug", "Debug"),
                        ui.Option("info", "Info"),
                        ui.Option("warning", "Warning"),
                        ui.Option("error", "Error")
                    ]
                )
            ]
        ),

        # Notification support
        ui.AlertStream()
    ]
```

---

See Also:
- [[30-UI-System-Overview|UI System Overview]]
- [[31-UI-Variables|UI Variables]]
- [[32-UI-Interactions|UI Interactions]]

#ui #containers #submodules #reference #pydoover
