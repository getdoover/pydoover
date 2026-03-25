# Tutorial: Building UI Elements

This tutorial walks through creating a comprehensive UI for a Doover application.

## Goal

Create a UI that includes:
- Numeric displays with ranges
- Text status indicators
- Control buttons
- Sliders for adjustment
- Dropdown selections
- Organized submodules

## Step 1: Basic UI Structure

Create `app_ui.py`:

```python
from pydoover import ui

def create_ui() -> list[ui.Element]:
    """Create all UI elements for the application."""
    return [
        # Main display elements
        create_status_section(),

        # Control section
        create_control_section(),

        # Settings section
        create_settings_section(),

        # Notifications
        ui.AlertStream()
    ]
```

## Step 2: Status Display Section

```python
def create_status_section() -> ui.Submodule:
    """Create the status display section."""
    return ui.Submodule(
        "status", "System Status",
        children=[
            # Main temperature display with color ranges
            ui.NumericVariable(
                "temperature",
                "Temperature (°C)",
                precision=1,
                ranges=[
                    ui.Range("Cold", -20, 10, ui.Colour.blue),
                    ui.Range("Normal", 10, 35, ui.Colour.green),
                    ui.Range("Warm", 35, 50, ui.Colour.yellow),
                    ui.Range("Hot", 50, 100, ui.Colour.red)
                ],
                log_threshold=0.5,
                default_zoom="24h",
                help_str="Current system temperature"
            ),

            # Pressure gauge
            ui.NumericVariable(
                "pressure",
                "Pressure (PSI)",
                precision=1,
                ranges=[
                    ui.Range("Low", 0, 20, ui.Colour.yellow),
                    ui.Range("Normal", 20, 80, ui.Colour.green),
                    ui.Range("High", 80, 100, ui.Colour.red)
                ]
            ),

            # Flow rate
            ui.NumericVariable(
                "flow_rate",
                "Flow Rate (L/min)",
                precision=2
            ),

            # Text status
            ui.TextVariable(
                "status_text",
                "System Status",
                curr_val="Initializing..."
            ),

            # Boolean indicators
            ui.BooleanVariable(
                "pump_running",
                "Pump Running",
                log_threshold=0
            ),

            ui.BooleanVariable(
                "alarm_active",
                "Alarm Active",
                log_threshold=0
            ),

            # Last update timestamp
            ui.DateTimeVariable(
                "last_update",
                "Last Reading"
            )
        ],
        status="OK"
    )
```

## Step 3: Control Section

```python
def create_control_section() -> ui.Submodule:
    """Create the control section with buttons and commands."""
    return ui.Submodule(
        "controls", "Controls",
        children=[
            # Operating mode selector
            ui.StateCommand(
                "mode",
                "Operating Mode",
                user_options=[
                    ui.Option("auto", "Automatic", position=0),
                    ui.Option("manual", "Manual", position=1),
                    ui.Option("standby", "Standby", position=2)
                ],
                default="standby"
            ),

            # Speed control slider
            ui.Slider(
                "speed",
                "Pump Speed (%)",
                min_val=0,
                max_val=100,
                step_size=5,
                default=50
            ),

            # Control buttons
            ui.Action(
                "start",
                "Start System",
                colour=ui.Colour.green,
                requires_confirm=True
            ),

            ui.Action(
                "stop",
                "Stop System",
                colour=ui.Colour.red,
                requires_confirm=True
            ),

            ui.Action(
                "emergency_stop",
                "EMERGENCY STOP",
                colour=ui.Colour.red,
                requires_confirm=False
            ),

            ui.Action(
                "refresh",
                "Refresh Data",
                colour=ui.Colour.blue,
                requires_confirm=False
            )
        ]
    )
```

## Step 4: Settings Section

```python
def create_settings_section() -> ui.Submodule:
    """Create settings section (collapsed by default)."""
    return ui.Submodule(
        "settings", "Advanced Settings",
        is_collapsed=True,
        children=[
            # Threshold sliders
            ui.Slider(
                "temp_threshold",
                "Temperature Alert Threshold",
                min_val=30,
                max_val=80,
                step_size=1,
                default=50
            ),

            ui.Slider(
                "pressure_threshold",
                "Pressure Alert Threshold",
                min_val=50,
                max_val=100,
                step_size=5,
                default=80
            ),

            # Log level selection
            ui.StateCommand(
                "log_level",
                "Log Level",
                user_options=[
                    ui.Option("debug", "Debug"),
                    ui.Option("info", "Info"),
                    ui.Option("warning", "Warning"),
                    ui.Option("error", "Error")
                ],
                default="info"
            ),

            # Hidden value for internal state
            ui.HiddenValue("session_id")
        ]
    )
```

## Step 5: Update Functions

```python
from datetime import datetime

def update_status(
    manager: ui.UIManager,
    temp: float,
    pressure: float,
    flow: float,
    status: str,
    pump_on: bool,
    alarm: bool
):
    """Update all status display elements."""
    # Update numeric values
    manager.update_variable("temperature", temp)
    manager.update_variable("pressure", pressure)
    manager.update_variable("flow_rate", flow)

    # Update text
    status_var = manager.get_element("status_text")
    if status_var:
        status_var.current_value = status

    # Update booleans
    manager.update_variable("pump_running", pump_on)
    manager.update_variable("alarm_active", alarm)

    # Update timestamp
    dt_var = manager.get_element("last_update")
    if dt_var:
        dt_var.current_value = datetime.now()

    # Update submodule status
    status_module = manager.get_element("status")
    if status_module and hasattr(status_module, "status"):
        if alarm:
            status_module.status = "ALARM"
        elif pump_on:
            status_module.status = "Running"
        else:
            status_module.status = "Idle"
```

## Step 6: Application Integration

```python
from pydoover.docker import Application
from pydoover import ui
from .app_ui import create_ui, update_status

class MyApplication(Application):
    async def setup(self):
        # Set up UI
        self.set_ui(create_ui())

        # Register callbacks
        self.ui_manager.register_callbacks(self)

    async def main_loop(self):
        # Read sensors
        temp = self.scale_ai(0, -20, 100)
        pressure = self.scale_ai(1, 0, 100)
        flow = self.scale_ai(2, 0, 50)

        # Determine status
        pump_on = self.get_do(0)
        alarm = temp > self.get_command("temp_threshold")

        if alarm:
            status = "HIGH TEMPERATURE"
            self.set_ui_status_icon("warning")
        elif pump_on:
            status = "Running normally"
            self.set_ui_status_icon("ok")
        else:
            status = "System idle"
            self.set_ui_status_icon("ok")

        # Update UI
        update_status(
            self.ui_manager,
            temp, pressure, flow,
            status, pump_on, alarm
        )

        # Handle comms
        await self.ui_manager.handle_comms_async()

    def scale_ai(self, channel, min_val, max_val):
        raw = self.get_ai(channel)
        return min_val + (raw / 4095.0) * (max_val - min_val)

    # UI Callbacks

    @ui.callback("mode")
    async def on_mode_change(self, element, value):
        log.info(f"Mode changed to: {value}")
        self.set_tag("operating_mode", value)

    @ui.callback("speed")
    async def on_speed_change(self, element, value):
        if self.get_command("mode") == "manual":
            # Scale to DAC output
            self.set_ao(0, int(value * 40.95))

    @ui.callback("start")
    async def on_start(self, element, value):
        self.set_do(0, True)
        await self.ui_manager.send_notification_async("System started")

    @ui.callback("stop")
    async def on_stop(self, element, value):
        self.set_do(0, False)
        await self.ui_manager.send_notification_async("System stopped")

    @ui.callback("emergency_stop")
    async def on_emergency(self, element, value):
        self.set_do(0, False)
        self.set_ao(0, 0)
        await self.ui_manager.send_notification_async("EMERGENCY STOP ACTIVATED")

    @ui.callback("refresh")
    async def on_refresh(self, element, value):
        log.info("Manual refresh requested")
```

## Step 7: Dynamic UI

### Show/Hide Elements

```python
async def main_loop(self):
    mode = self.get_command("mode")

    # Show speed slider only in manual mode
    speed_slider = self.ui_manager.get_element("speed")
    if speed_slider:
        speed_slider.hidden = (mode != "manual")
```

### Update Button States

```python
# Disable start when already running
start_btn = self.ui_manager.get_element("start")
if start_btn:
    start_btn.disabled = self.get_do(0)

# Disable stop when not running
stop_btn = self.ui_manager.get_element("stop")
if stop_btn:
    stop_btn.disabled = not self.get_do(0)
```

### Update Submodule Status

```python
controls = self.ui_manager.get_element("controls")
if controls:
    if self.get_command("mode") == "auto":
        controls.status = "Auto Mode Active"
    else:
        controls.status = "Manual Control"
```

## Best Practices

1. **Organize logically** - Group related elements in submodules
2. **Use appropriate precision** - Don't show unnecessary decimal places
3. **Color code ranges** - Help users quickly assess values
4. **Collapse advanced settings** - Keep the main view simple
5. **Provide feedback** - Update status text and icons
6. **Use confirmations wisely** - For destructive actions only
7. **Keep labels short** - But descriptive

---

See Also:
- [[30-UI-System-Overview|UI System Overview]]
- [[31-UI-Variables|UI Variables]]
- [[32-UI-Interactions|UI Interactions]]
- [[33-UI-Containers|UI Containers]]

#tutorial #ui #elements #pydoover
