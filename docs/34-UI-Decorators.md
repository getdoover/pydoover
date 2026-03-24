# UI Decorators Reference

Decorators provide a clean, declarative way to define UI interactions and their callbacks.

## Available Decorators

| Decorator | Purpose |
|-----------|---------|
| `@ui.action` | Define a button with callback |
| `@ui.slider` | Define a slider with callback |
| `@ui.state_command` | Define a dropdown with callback |
| `@ui.hidden_value` | Define hidden state with callback |
| `@ui.warning_indicator` | Define warning with callback |
| `@ui.callback` | Generic callback for any interaction |

## @ui.action

Define a button that triggers the decorated function.

```python
from pydoover import ui

@ui.action(
    name="start",
    display_name="Start",
    colour=ui.Colour.green,
    requires_confirm=True,
    **kwargs  # Additional Element options
)
async def on_start(self, new_value):
    # Handle button click
    pass
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | `None` | Button label |
| `colour` | `Colour` | `blue` | Button color |
| `requires_confirm` | `bool` | `True` | Show confirmation |

### Examples

```python
class MyApp(Application):
    @ui.action("start", "Start Process", colour=ui.Colour.green)
    async def on_start(self, new_value):
        log.info("Start button clicked")
        await self.start_process()

    @ui.action("stop", "Stop", colour=ui.Colour.red, requires_confirm=False)
    async def on_stop(self, new_value):
        await self.stop_process()

    @ui.action("refresh", "Refresh Data")
    def on_refresh(self, new_value):
        # Can also be synchronous
        self.refresh_data()
```

## @ui.slider

Define a slider that calls the decorated function on change.

```python
@ui.slider(
    name="speed",
    display_name="Speed",
    min_val=0,
    max_val=100,
    step_size=5,
    dual_slider=True,
    inverted=False,
    icon=None,
    **kwargs
)
async def on_speed(self, new_value):
    pass
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | `None` | Slider label |
| `min_val` | `int` | `0` | Minimum value |
| `max_val` | `int` | `100` | Maximum value |
| `step_size` | `float` | `0.1` | Step increment |
| `dual_slider` | `bool` | `True` | Show value handle |
| `inverted` | `bool` | `True` | Invert direction |
| `icon` | `str` | `None` | Icon name |

### Examples

```python
class MyApp(Application):
    @ui.slider("volume", "Volume", min_val=0, max_val=100, step_size=5)
    async def on_volume(self, new_value):
        self.set_volume(new_value)

    @ui.slider(
        "temperature",
        "Temperature Setpoint",
        min_val=15,
        max_val=35,
        step_size=0.5
    )
    async def on_temp_setpoint(self, new_value):
        self.target_temperature = new_value
        self.set_tag("setpoint", new_value)
```

## @ui.state_command

Define a dropdown selection with callback.

```python
@ui.state_command(
    name="mode",
    display_name="Mode",
    user_options=[
        ui.Option("auto", "Automatic"),
        ui.Option("manual", "Manual")
    ],
    **kwargs
)
async def on_mode(self, new_value):
    pass
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique identifier |
| `display_name` | `str` | `None` | Dropdown label |
| `user_options` | `list[Option]` | Required | Choices |

### Examples

```python
class MyApp(Application):
    @ui.state_command(
        "mode", "Operating Mode",
        user_options=[
            ui.Option("auto", "Automatic"),
            ui.Option("manual", "Manual"),
            ui.Option("off", "Off")
        ]
    )
    async def on_mode_change(self, new_value):
        log.info(f"Mode changed to {new_value}")
        if new_value == "auto":
            await self.enable_auto_mode()
        elif new_value == "off":
            await self.shutdown()

    @ui.state_command(
        "priority", "Alert Priority",
        user_options=[
            ui.Option("low", "Low"),
            ui.Option("medium", "Medium"),
            ui.Option("high", "High")
        ]
    )
    def on_priority(self, new_value):
        self.alert_priority = new_value
```

## @ui.hidden_value

Define hidden state storage with callback.

```python
@ui.hidden_value(name="internal_state", **kwargs)
async def on_state_change(self, new_value):
    pass
```

### Examples

```python
class MyApp(Application):
    @ui.hidden_value("session_id")
    async def on_session(self, new_value):
        log.info(f"Session updated: {new_value}")

    @ui.hidden_value("last_command")
    async def on_last_command(self, new_value):
        # Process external command
        await self.process_command(new_value)
```

## @ui.warning_indicator

Define a warning indicator with dismissal callback.

```python
@ui.warning_indicator(
    name="low_battery",
    display_name="Low Battery",
    can_cancel=True,
    **kwargs
)
async def on_warning_dismiss(self, new_value):
    pass
```

### Examples

```python
class MyApp(Application):
    @ui.warning_indicator("overtemp", "Temperature Warning", can_cancel=True)
    async def on_overtemp_dismiss(self, new_value):
        log.info("Temperature warning dismissed")
        self.warning_acknowledged = True
```

## @ui.callback

Generic callback decorator for any interaction. Supports pattern matching.

```python
@ui.callback(
    pattern="interaction_name",  # or re.Pattern
    global_interaction=False
)
async def on_callback(self, element, new_value):
    pass
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `str` or `re.Pattern` | Name or pattern to match |
| `global_interaction` | `bool` | Don't prepend app key |

### String Pattern

```python
class MyApp(Application):
    @ui.callback("my_button")
    async def on_button(self, element, new_value):
        log.info(f"Button {element.name} clicked: {new_value}")
```

### Regex Pattern

```python
import re

class MyApp(Application):
    # Match any DI toggle
    @ui.callback(re.compile(r"di_\d+_toggle"))
    async def on_di_toggle(self, element, new_value):
        # Extract DI number from name
        match = re.match(r"di_(\d+)_toggle", element.name)
        di_num = int(match.group(1))
        log.info(f"DI {di_num} toggled to {new_value}")

    # Match any DO control
    @ui.callback(re.compile(r"do_\d+"))
    async def on_do_change(self, element, new_value):
        pass
```

### Global Interactions

For interactions not namespaced to your app:

```python
class MyApp(Application):
    # Camera "Get Now" is a global interaction
    @ui.callback("camera_get_now", global_interaction=True)
    async def on_camera_request(self, element, new_value):
        await self.capture_camera_image()

    # Global pattern match
    @ui.callback(re.compile(r"global_param_\d+"), global_interaction=True)
    async def on_global_param(self, element, new_value):
        pass
```

## Registration

Decorated methods are automatically registered during setup:

```python
class MyApp(Application):
    async def setup(self):
        # Decorators are auto-registered
        # But you can also manually register
        self.ui_manager.register_interactions(self)
        self.ui_manager.register_callbacks(self)
```

## Callback Signature

### Interaction Decorators

`@ui.action`, `@ui.slider`, `@ui.state_command`, `@ui.hidden_value`:

```python
async def callback(self, new_value):
    # new_value is the new interaction value
    pass
```

### @ui.callback Decorator

```python
async def callback(self, element, new_value):
    # element is the Interaction object
    # new_value is the new value
    pass
```

## Accessing Decorated Interactions

After setup, decorated interactions become UI elements:

```python
class MyApp(Application):
    @ui.action("start", "Start")
    async def on_start(self, value):
        pass

    async def setup(self):
        # After setup, self.on_start becomes an Action
        # Can access via:
        action = self.ui_manager.get_interaction("my_app_start")

        # Or via the attribute (transformed)
        action = self.on_start  # Now an Action object
```

## Best Practices

### 1. Use Decorators for Simple Interactions

```python
# Good - clear and concise
@ui.action("refresh", "Refresh")
async def on_refresh(self, value):
    await self.refresh_data()
```

### 2. Use @ui.callback for Pattern Matching

```python
# Good - handles multiple similar interactions
@ui.callback(re.compile(r"sensor_\d+_reset"))
async def on_sensor_reset(self, element, value):
    sensor_id = int(re.search(r"\d+", element.name).group())
    await self.reset_sensor(sensor_id)
```

### 3. Combine with Manual Elements

```python
async def setup(self):
    # Mix decorators with manual elements
    self.set_ui([
        ui.NumericVariable("temp", "Temperature"),
        ui.TextVariable("status", "Status"),
        # Decorated interactions auto-added
    ])

@ui.action("refresh", "Refresh")
async def on_refresh(self, value):
    pass
```

### 4. Error Handling

```python
@ui.action("risky_action", "Do Something Risky")
async def on_risky(self, value):
    try:
        await self.risky_operation()
    except Exception as e:
        log.error(f"Operation failed: {e}")
        await self.ui_manager.send_notification_async(
            f"Operation failed: {e}"
        )
```

## Complete Example

```python
import re
from pydoover import ui
from pydoover.docker import Application

class PumpController(Application):
    @ui.state_command(
        "mode", "Operating Mode",
        user_options=[
            ui.Option("auto", "Automatic"),
            ui.Option("manual", "Manual"),
            ui.Option("off", "Off")
        ]
    )
    async def on_mode(self, new_value):
        log.info(f"Mode: {new_value}")
        self.set_tag("mode", new_value)

        if new_value == "off":
            await self.stop_all_pumps()

    @ui.slider("speed", "Pump Speed", min_val=0, max_val=100, step_size=5)
    async def on_speed(self, new_value):
        if self.get_command("mode") == "manual":
            self.set_ao(0, int(new_value * 40.95))

    @ui.action("start", "Start Pump", colour=ui.Colour.green)
    async def on_start(self, value):
        self.set_do(0, True)
        self.set_tag("pump_running", True)

    @ui.action("stop", "Stop Pump", colour=ui.Colour.red)
    async def on_stop(self, value):
        self.set_do(0, False)
        self.set_tag("pump_running", False)

    @ui.action("emergency", "EMERGENCY STOP", colour=ui.Colour.red, requires_confirm=False)
    async def on_emergency(self, value):
        await self.emergency_stop()

    # Handle all pump-related callbacks
    @ui.callback(re.compile(r"pump_\d+_"))
    async def on_any_pump(self, element, value):
        log.debug(f"Pump interaction: {element.name} = {value}")

    @ui.hidden_value("external_command")
    async def on_external_command(self, value):
        if value == "start":
            await self.on_start(None)
        elif value == "stop":
            await self.on_stop(None)
```

---

See Also:
- [[30-UI-System-Overview|UI System Overview]]
- [[32-UI-Interactions|UI Interactions]]
- [[73-Example-Patterns|Common Patterns]]

#ui #decorators #callbacks #reference #pydoover
