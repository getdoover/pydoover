# UI Interactions Reference

Interactions are UI elements that accept user input. When users interact with them, your application receives callbacks.

## Interaction Types

| Type | UI Element | Purpose |
|------|-----------|---------|
| `Action` | Button | Trigger actions |
| `Slider` | Slider | Numeric input |
| `StateCommand` | Dropdown | Selection from options |
| `HiddenValue` | None | Hidden state storage |
| `WarningIndicator` | Warning badge | Dismissible warnings |

## Base Interaction Class

All interactions inherit from `Interaction`:

```python
from pydoover.ui import Interaction

Interaction(
    name="interaction_name",   # Unique identifier
    display_name="Display",    # Label in UI
    current_value=None,        # Current value
    default=None,              # Default value
    callback=None,             # Function called on change
    transform_check=None,      # Value transformer
    show_activity=None,        # Show in activity log
    # Common Element options:
    help_str=None,
    hidden=False,
    position=None
)
```

## Action

Button that triggers an action when clicked.

```python
from pydoover import ui

ui.Action(
    name="start_pump",
    display_name="Start Pump",
    colour=ui.Colour.green,
    requires_confirm=True,
    disabled=False
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | Required | Button label |
| `colour` | `Colour` | `blue` | Button color |
| `requires_confirm` | `bool` | `True` | Show confirmation dialog |
| `disabled` | `bool` | `False` | Disable button |

### Examples

```python
# Basic button
refresh = ui.Action("refresh", "Refresh Data")

# Colored button
start = ui.Action(
    "start", "Start",
    colour=ui.Colour.green,
    requires_confirm=True
)

# Danger button (no confirm for quick access)
emergency = ui.Action(
    "emergency_stop", "EMERGENCY STOP",
    colour=ui.Colour.red,
    requires_confirm=False
)

# Disabled button
unavailable = ui.Action(
    "export", "Export Data",
    disabled=True
)
```

### Handling Action Clicks

```python
# Method 1: Callback in constructor
def on_start(new_value):
    print("Start clicked!")

action = ui.Action("start", "Start", callback=on_start)

# Method 2: Decorator
@ui.action("start", "Start", colour=ui.Colour.green)
async def on_start(self, new_value):
    await self.start_process()

# Method 3: @ui.callback decorator
@ui.callback("start")
async def on_start_click(self, element, new_value):
    pass
```

## Slider

Numeric input via slider control.

```python
ui.Slider(
    name="speed",
    display_name="Speed",
    min_val=0,
    max_val=100,
    step_size=5,
    dual_slider=True,
    inverted=False,
    icon=None,
    colours=None
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | `None` | Slider label |
| `min_val` | `int` | `0` | Minimum value |
| `max_val` | `int` | `100` | Maximum value |
| `step_size` | `float` | `0.1` | Step increment |
| `dual_slider` | `bool` | `True` | Show current value handle |
| `inverted` | `bool` | `True` | Invert direction |
| `icon` | `str` | `None` | Icon name |
| `colours` | `str` | `None` | Color gradient |

### Examples

```python
# Basic slider
volume = ui.Slider("volume", "Volume", min_val=0, max_val=100)

# Fine-grained slider
temperature = ui.Slider(
    "setpoint", "Temperature Setpoint",
    min_val=15,
    max_val=35,
    step_size=0.5
)

# Percentage slider
power = ui.Slider(
    "power", "Power Level",
    min_val=0,
    max_val=100,
    step_size=10
)
```

### Handling Slider Changes

```python
# Method 1: Decorator
@ui.slider("speed", "Speed", min_val=0, max_val=100)
async def on_speed_change(self, new_value):
    self.set_motor_speed(new_value)

# Method 2: @ui.callback
@ui.callback("speed")
async def on_speed(self, element, new_value):
    self.set_motor_speed(new_value)
```

## StateCommand

Dropdown selection from predefined options.

```python
ui.StateCommand(
    name="mode",
    display_name="Operating Mode",
    user_options=[
        ui.Option("auto", "Automatic"),
        ui.Option("manual", "Manual"),
        ui.Option("off", "Off")
    ],
    default="auto"
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | `None` | Dropdown label |
| `user_options` | `list[Option]` | Required | Available choices |
| `default` | `Any` | `None` | Default selection |

### Option Class

```python
ui.Option(
    name="value",           # Internal value
    display_name="Label",   # Shown to user
    position=0              # Order in list
)
```

### Examples

```python
# Basic dropdown
mode = ui.StateCommand(
    "mode", "Mode",
    user_options=[
        ui.Option("auto", "Automatic"),
        ui.Option("manual", "Manual")
    ]
)

# With positions
priority = ui.StateCommand(
    "priority", "Priority",
    user_options=[
        ui.Option("low", "Low Priority", position=0),
        ui.Option("medium", "Medium Priority", position=1),
        ui.Option("high", "High Priority", position=2),
        ui.Option("critical", "Critical", position=3)
    ],
    default="medium"
)
```

### Handling Selection Changes

```python
# Method 1: Decorator
@ui.state_command("mode", "Mode", user_options=[
    ui.Option("auto", "Auto"),
    ui.Option("manual", "Manual")
])
async def on_mode_change(self, new_value):
    if new_value == "auto":
        self.enable_auto_mode()

# Method 2: @ui.callback
@ui.callback("mode")
async def on_mode(self, element, new_value):
    self.current_mode = new_value
```

## HiddenValue

Stores values without displaying in UI. Useful for internal state.

```python
ui.HiddenValue(name="internal_counter")
```

### Examples

```python
# Store internal state
last_command = ui.HiddenValue("last_command_id")

# Session data
session = ui.HiddenValue("session_token")
```

### Handling Hidden Value Changes

```python
@ui.hidden_value("internal_state")
async def on_internal_state(self, new_value):
    self.process_state_change(new_value)

# Or via @ui.callback
@ui.callback("internal_state")
async def on_state(self, element, new_value):
    pass
```

## WarningIndicator

Dismissible warning badge.

```python
ui.WarningIndicator(
    name="low_battery",
    display_name="Low Battery Warning",
    can_cancel=True
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `can_cancel` | `bool` | `True` | User can dismiss |

### Examples

```python
# Dismissible warning
warning = ui.WarningIndicator(
    "low_battery", "Low Battery",
    can_cancel=True
)

# Non-dismissible critical warning
critical = ui.WarningIndicator(
    "system_error", "System Error",
    can_cancel=False
)
```

## Getting and Setting Values

### Get Current Value

```python
# Through UIManager
mode = self.ui_manager.get_interaction("mode")
current = mode.current_value

# Convenience method
mode_value = self.get_command("mode")
```

### Set (Coerce) Value

```python
# Through interaction
mode = self.ui_manager.get_interaction("mode")
mode.coerce("manual")

# Through UIManager
self.ui_manager.coerce_command("mode", "manual")

# Convenience method
self.coerce_command("mode", "manual")

# Critical update (immediate sync)
mode.coerce("manual", critical=True)
```

## Transform and Validation

Custom value transformation before callbacks:

```python
def validate_speed(new_value):
    if new_value is None:
        return 0
    return max(0, min(100, new_value))

slider = ui.Slider(
    "speed", "Speed",
    transform_check=validate_speed
)
```

## Activity Logging

Control whether interaction appears in activity log:

```python
# Always show in activity log
action = ui.Action("important", "Important Action", show_activity=True)

# Never show
internal = ui.Slider("internal", "Internal", show_activity=False)

# Use default (site setting)
normal = ui.Action("normal", "Normal", show_activity=None)
```

## Complete Example

```python
from pydoover import ui

def create_control_ui():
    return [
        # Mode selection
        ui.StateCommand(
            "mode", "Operating Mode",
            user_options=[
                ui.Option("auto", "Automatic", position=0),
                ui.Option("manual", "Manual", position=1),
                ui.Option("standby", "Standby", position=2)
            ],
            default="standby"
        ),

        # Speed control
        ui.Slider(
            "speed", "Motor Speed (%)",
            min_val=0,
            max_val=100,
            step_size=5,
            default=50
        ),

        # Control buttons
        ui.Action(
            "start", "Start Motor",
            colour=ui.Colour.green,
            requires_confirm=True
        ),

        ui.Action(
            "stop", "Stop Motor",
            colour=ui.Colour.red,
            requires_confirm=False
        ),

        ui.Action(
            "emergency", "EMERGENCY STOP",
            colour=ui.Colour.red,
            requires_confirm=False
        ),

        # Hidden state
        ui.HiddenValue("last_command_time"),

        # Warning indicator
        ui.WarningIndicator(
            "overtemp", "Motor Overtemperature",
            can_cancel=True
        )
    ]


class MotorController(Application):
    @ui.callback("mode")
    async def on_mode_change(self, element, new_value):
        self.set_tag("operating_mode", new_value)

    @ui.callback("speed")
    async def on_speed_change(self, element, new_value):
        self.set_ao(0, int(new_value * 40.95))

    @ui.callback("start")
    async def on_start(self, element, new_value):
        await self.start_motor()

    @ui.callback("stop")
    async def on_stop(self, element, new_value):
        await self.stop_motor()
```

---

See Also:
- [[30-UI-System-Overview|UI System Overview]]
- [[31-UI-Variables|UI Variables]]
- [[34-UI-Decorators|UI Decorators]]

#ui #interactions #reference #pydoover
