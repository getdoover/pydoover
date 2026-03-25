# UI System Overview

The pydoover UI system provides a declarative way to build user interfaces for Doover applications. UI elements are defined in Python and automatically synchronized with the Doover web platform.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Doover Cloud                       │
│  ┌──────────────┐    ┌──────────────┐              │
│  │  ui_state    │    │   ui_cmds    │              │
│  │  (channel)   │    │  (channel)   │              │
│  └──────┬───────┘    └──────┬───────┘              │
└─────────┼────────────────────┼──────────────────────┘
          │                    │
          ▼                    ▼
┌─────────────────────────────────────────────────────┐
│                    UIManager                         │
│  ┌──────────────────────────────────────────────┐  │
│  │  Variables    │  Interactions  │  Containers  │  │
│  │  (read-only)  │  (user input)  │  (grouping)  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Core Concepts

### Element Types

| Category | Purpose | Examples |
|----------|---------|----------|
| **Variables** | Display values (read-only) | NumericVariable, TextVariable |
| **Interactions** | Accept user input | Action, Slider, StateCommand |
| **Containers** | Group elements | Submodule, Container |
| **Special** | Platform features | AlertStream, Multiplot, ConnectionInfo |

### Data Flow

1. **Variables**: App sets value → UI displays it
2. **Interactions**: User changes value → App receives callback

## Quick Start

```python
from pydoover import ui

# In your Application class:
def setup(self):
    self.set_ui([
        # Read-only variable
        ui.NumericVariable("temp", "Temperature", precision=1),

        # User interaction
        ui.Action("refresh", "Refresh Data", colour=ui.Colour.blue),

        # Dropdown selection
        ui.StateCommand("mode", "Mode", user_options=[
            ui.Option("auto", "Automatic"),
            ui.Option("manual", "Manual")
        ])
    ])
```

## UIManager

The `UIManager` is the central orchestrator for UI state.

### Access Methods

```python
# Get element by name
temp_var = self.ui_manager.get_element("temp")

# Update variable value
self.ui_manager.update_variable("temp", 25.5)

# Get interaction value
mode = self.ui_manager.get_interaction("mode")

# Coerce (set) interaction value
self.ui_manager.coerce_command("mode", "auto")
```

### Setting UI

```python
# Set all UI elements (replaces existing)
self.set_ui([...])

# Add children
self.ui_manager.add_children(
    ui.NumericVariable("new_var", "New Variable")
)

# Remove children
self.ui_manager.remove_children(element_to_remove)
```

### Status and Icons

```python
# Set status icon for the app
self.set_ui_status_icon("warning")  # or "error", "ok", etc.

# Set display name
self.ui_manager.set_display_name("My App v2")
```

## Variables (Read-Only)

Variables display values that the application sets.

### NumericVariable

```python
ui.NumericVariable(
    name="temperature",
    display_name="Temperature",
    curr_val=25.5,           # Initial value
    precision=1,             # Decimal places
    ranges=[                 # Color coding
        ui.Range("Low", 0, 15, ui.Colour.blue),
        ui.Range("Normal", 15, 30, ui.Colour.green),
        ui.Range("High", 30, 50, ui.Colour.red)
    ],
    earliest_data_time=None, # For historical charts
    default_zoom="1h",       # Chart zoom level
    log_threshold=0.5        # Log when change exceeds this
)
```

### TextVariable

```python
ui.TextVariable(
    name="status",
    display_name="Status",
    curr_val="Running"
)
```

### BooleanVariable

```python
ui.BooleanVariable(
    name="active",
    display_name="System Active",
    curr_val=True,
    log_threshold=0  # Log every change
)
```

### DateTimeVariable

```python
from datetime import datetime

ui.DateTimeVariable(
    name="last_update",
    display_name="Last Updated",
    curr_val=datetime.now()
)
```

### Updating Variables

```python
# Method 1: Direct assignment
temp_var = self.ui_manager.get_element("temperature")
temp_var.current_value = 26.3

# Method 2: update() method
temp_var.update(26.3, force_log=True)

# Method 3: Through manager
self.ui_manager.update_variable("temperature", 26.3, critical=True)
```

## Interactions (User Input)

Interactions accept input from users.

### Action (Button)

```python
ui.Action(
    name="start_pump",
    display_name="Start Pump",
    colour=ui.Colour.green,
    requires_confirm=True,  # Show confirmation dialog
    disabled=False
)
```

### Slider

```python
ui.Slider(
    name="speed",
    display_name="Speed Setting",
    min_val=0,
    max_val=100,
    step_size=5,
    dual_slider=True,   # Show current value handle
    inverted=False,
    icon="speed",
    colours="blue,green,red"
)
```

### StateCommand (Dropdown)

```python
ui.StateCommand(
    name="operating_mode",
    display_name="Operating Mode",
    user_options=[
        ui.Option("auto", "Automatic", position=0),
        ui.Option("manual", "Manual", position=1),
        ui.Option("off", "Off", position=2)
    ],
    default="auto"
)
```

### HiddenValue

For internal state not shown to users:

```python
ui.HiddenValue(name="internal_counter")
```

### Handling Interactions

```python
# Method 1: @ui.callback decorator
@ui.callback("start_pump")
async def on_start_pump(self, element, new_value):
    print(f"Start pump pressed: {new_value}")
    self.set_do(0, True)

# Method 2: Callback in element definition
def setup(self):
    action = ui.Action("stop", "Stop")
    action.callback = self.on_stop
    self.set_ui([action])

async def on_stop(self, new_value):
    self.set_do(0, False)
```

## Containers

Containers group related UI elements.

### Submodule

```python
ui.Submodule(
    name="pump_controls",
    display_name="Pump Controls",
    children=[
        ui.NumericVariable("flow_rate", "Flow Rate"),
        ui.Action("start", "Start Pump"),
        ui.Action("stop", "Stop Pump")
    ],
    status="Running",     # Status text
    is_collapsed=False    # Initial state
)
```

### Container

Base container class:

```python
ui.Container(
    name="sensors",
    display_name="Sensors",
    children=[...],
    status_icon="ok"
)
```

### RemoteComponent

Embed external web components:

```python
ui.RemoteComponent(
    name="custom_chart",
    display_name="Custom Chart",
    component_url="https://example.com/chart-component"
)
```

## Decorators

Decorators provide a clean way to define interactions.

### @ui.action

```python
@ui.action("emergency_stop", "Emergency Stop", colour=ui.Colour.red, requires_confirm=False)
async def on_emergency_stop(self, new_value):
    await self.shutdown_all()
```

### @ui.slider

```python
@ui.slider("fan_speed", "Fan Speed", min_val=0, max_val=100, step_size=10)
async def on_fan_speed(self, new_value):
    self.set_ao(0, int(new_value * 40.95))  # Scale to 0-4095
```

### @ui.state_command

```python
@ui.state_command("mode", "Mode", user_options=[
    ui.Option("auto", "Automatic"),
    ui.Option("manual", "Manual")
])
async def on_mode_change(self, new_value):
    if new_value == "auto":
        self.enable_auto_mode()
```

### @ui.callback

Generic callback for any interaction:

```python
import re

# Single element
@ui.callback("specific_button")
def on_button(self, element, new_value):
    pass

# Pattern matching
@ui.callback(re.compile(r"do_\d+_toggle"))
def on_any_do_toggle(self, element, new_value):
    # element.name will be "do_0_toggle", "do_1_toggle", etc.
    pass

# Global interaction (not namespaced to app)
@ui.callback("camera_get_now", global_interaction=True)
def on_camera_get(self, element, new_value):
    pass
```

## Helpers

### Range

Color ranges for numeric variables:

```python
ui.Range(
    name="Normal",
    start=20,
    end=30,
    colour=ui.Colour.green
)
```

### Option

Options for StateCommand:

```python
ui.Option(
    name="value",           # Internal value
    display_name="Display", # Shown to user
    position=0              # Order in list
)
```

### Colour

Predefined colors:

```python
ui.Colour.red      # "#F44336"
ui.Colour.green    # "#4CAF50"
ui.Colour.blue     # "#2196F3"
ui.Colour.yellow   # "#FFEB3B"
ui.Colour.orange   # "#FF9800"
ui.Colour.purple   # "#9C27B0"
ui.Colour.cyan     # "#00BCD4"
ui.Colour.teal     # "#009688"
ui.Colour.pink     # "#E91E63"
ui.Colour.lime     # "#CDDC39"
ui.Colour.amber    # "#FFC107"
ui.Colour.brown    # "#795548"
ui.Colour.grey     # "#9E9E9E"
```

## Special Elements

### AlertStream

Enable notification banner:

```python
ui.AlertStream()  # Uses default name "significantEvent"
```

### Multiplot

Multi-series chart:

```python
ui.Multiplot(
    name="sensor_chart",
    display_name="Sensor History",
    series=["temp", "humidity", "pressure"],
    series_colours=[ui.Colour.red, ui.Colour.blue, ui.Colour.green],
    series_active=[True, True, False],
    default_zoom="24h"
)
```

### ConnectionInfo

Connection status indicator:

```python
ui.ConnectionInfo(
    connection_type=ui.ConnectionType.periodic,
    connection_period=60,  # seconds
    next_connection=None,
    offline_after=180,     # Show offline after 3 min
    allowed_misses=2
)
```

## Element Visibility

```python
# Hide an element
element.hidden = True

# Conditional display (evaluated client-side)
element.conditions = {
    "show_when": {"mode": "advanced"}
}
```

## Best Practices

1. **Define UI in `app_ui.py`** - Keep UI separate from application logic
2. **Use descriptive names** - Names are identifiers in the system
3. **Group related elements** - Use Submodules for organization
4. **Set appropriate precisions** - Avoid unnecessary decimal places
5. **Use color ranges** - Help users quickly assess values
6. **Use decorators** - Cleaner than manual callback assignment

---

See Also:
- [[31-UI-Variables|Variables Reference]]
- [[32-UI-Interactions|Interactions Reference]]
- [[33-UI-Containers|Containers Reference]]
- [[34-UI-Decorators|Decorators Reference]]

#ui #interface #pydoover #elements
