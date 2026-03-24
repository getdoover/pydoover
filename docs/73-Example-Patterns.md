# Common Patterns and Best Practices

This document covers common patterns and best practices for building Doover applications with pydoover.

## Application Structure

### Separate UI Definition

Keep UI in a dedicated file:

```python
# app_ui.py
from pydoover import ui

def create_ui() -> list[ui.Element]:
    return [
        ui.NumericVariable("value", "Value"),
        ui.Action("refresh", "Refresh")
    ]

def update_ui(manager, data):
    manager.get_element("value").current_value = data["value"]
```

```python
# application.py
from .app_ui import create_ui, update_ui

class MyApp(Application):
    async def setup(self):
        self.set_ui(create_ui())

    async def main_loop(self):
        data = self.read_sensors()
        update_ui(self.ui_manager, data)
```

### State Machine Integration

For complex state logic:

```python
from pydoover.state import StateMachine

class AppState(StateMachine):
    states = ["idle", "running", "paused", "error"]
    transitions = [
        {"trigger": "start", "source": "idle", "dest": "running"},
        {"trigger": "pause", "source": "running", "dest": "paused"},
        {"trigger": "resume", "source": "paused", "dest": "running"},
        {"trigger": "stop", "source": ["running", "paused"], "dest": "idle"},
        {"trigger": "error", "source": "*", "dest": "error"},
        {"trigger": "reset", "source": "error", "dest": "idle"}
    ]

    def __init__(self, app):
        super().__init__(
            states=self.states,
            transitions=self.transitions,
            initial="idle"
        )
        self.app = app

    async def on_enter_running(self):
        self.app.set_do(0, True)
        self.app.set_tag("state", "running")

    async def on_enter_idle(self):
        self.app.set_do(0, False)
        self.app.set_tag("state", "idle")
```

Usage:
```python
class MyApp(Application):
    async def setup(self):
        self.state = AppState(self)

    @ui.callback("start_button")
    async def on_start(self, element, value):
        await self.state.start()

    @ui.callback("stop_button")
    async def on_stop(self, element, value):
        await self.state.stop()
```

## Configuration Patterns

### Computed Properties

```python
class MyConfig(config.Schema):
    def __init__(self):
        self._voltage = config.Number("Voltage", default=24.0)
        self._current = config.Number("Current", default=1.0)

    @property
    def power(self):
        return self._voltage.value * self._current.value
```

### Modbus Configuration

```python
from pydoover.docker.modbus import ModbusConfig

class MyConfig(config.Schema):
    def __init__(self):
        # Inherit standard modbus settings
        self.modbus = ModbusConfig()

        # Add device-specific settings
        self.slave_id = config.Integer("Modbus Slave ID", default=1)
```

## UI Patterns

### Dynamic UI Updates

```python
async def main_loop(self):
    # Update visibility based on mode
    mode = self.get_command("mode")

    advanced_panel = self.ui_manager.get_element("advanced_settings")
    if advanced_panel:
        advanced_panel.hidden = (mode != "advanced")
```

### Conditional Colors

```python
def get_status_color(self, value):
    if value < 20:
        return ui.Colour.blue
    elif value < 80:
        return ui.Colour.green
    else:
        return ui.Colour.red

# Use in UI
action = ui.Action(
    "status_indicator",
    "Status",
    colour=self.get_status_color(current_value)
)
```

### Submodule Organization

```python
def create_ui():
    return [
        # Main readings always visible
        ui.NumericVariable("main_temp", "Temperature"),

        # Group related controls
        ui.Submodule(
            "pump_controls",
            "Pump Controls",
            children=[
                ui.BooleanVariable("pump_status", "Status"),
                ui.Action("start_pump", "Start"),
                ui.Action("stop_pump", "Stop")
            ],
            is_collapsed=False
        ),

        # Advanced settings hidden by default
        ui.Submodule(
            "advanced",
            "Advanced Settings",
            children=[
                ui.Slider("pid_p", "P Gain"),
                ui.Slider("pid_i", "I Gain"),
                ui.Slider("pid_d", "D Gain")
            ],
            is_collapsed=True
        )
    ]
```

## Communication Patterns

### Inter-App Communication via Tags

```python
# Publisher app
class SensorApp(Application):
    async def main_loop(self):
        temp = self.read_temperature()
        self.set_tag("temperature", temp)
        self.set_tag("timestamp", time.time())
```

```python
# Subscriber app
class ControlApp(Application):
    async def setup(self):
        self.subscribe_to_tag(
            "temperature",
            self.on_temp_update,
            app_key="sensor_app"
        )

    async def on_temp_update(self, tag_key, new_value):
        if new_value > self.config.threshold.value:
            self.activate_cooling()
```

### Channel for Complex Data

```python
# Publisher
class DataApp(Application):
    async def main_loop(self):
        data = {
            "readings": [
                {"name": "temp1", "value": 25.5},
                {"name": "temp2", "value": 26.3}
            ],
            "timestamp": time.time()
        }
        self.publish_to_channel("sensor_readings", data)
```

```python
# Subscriber
class ProcessorApp(Application):
    async def setup(self):
        self.subscribe_to_channel("sensor_readings", self.on_readings)

    async def on_readings(self, channel_name, data):
        for reading in data.get("readings", []):
            self.process_reading(reading)
```

## Error Handling

### Graceful Degradation

```python
async def main_loop(self):
    # Try primary sensor
    try:
        temp = await self.modbus_iface.read_registers_async(
            bus_id="default",
            modbus_id=1,
            start_address=0,
            num_registers=1,
            register_type="input"
        )
        self.ui_manager.update_variable("temperature", temp[0] / 10)
        self.ui_manager.update_variable("status", "OK")
    except Exception as e:
        log.error(f"Sensor read failed: {e}")
        self.ui_manager.update_variable("status", "SENSOR ERROR")
        self.set_ui_status_icon("error")
```

### Retry Logic

```python
async def read_with_retry(self, address, count, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.modbus_iface.read_registers_async(
                bus_id="default",
                modbus_id=self.config.slave_id.value,
                start_address=address,
                num_registers=count,
                register_type="holding"
            )
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            log.warning(f"Read failed, retry {attempt + 1}/{max_retries}")
            await asyncio.sleep(0.5)
```

## Performance Patterns

### Batch Tag Updates

```python
# Instead of multiple set_tag calls:
self.set_tag("temp1", 25.5)
self.set_tag("temp2", 26.3)
self.set_tag("temp3", 24.8)

# Use set_tags for atomic update:
self.set_tags({
    "temp1": 25.5,
    "temp2": 26.3,
    "temp3": 24.8
})
```

### Conditional Logging

```python
async def main_loop(self):
    temp = self.read_temperature()

    # Only force log when value changes significantly
    force_log = abs(temp - self._last_temp) > 1.0
    self._last_temp = temp

    self.ui_manager.update_variable("temperature", temp)
    await self.ui_manager.push_async(record_log=force_log)
```

### Loop Timing

```python
class MyApp(Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loop_target_period = 0.5  # 500ms loop

    async def main_loop(self):
        # Fast operations only
        self.quick_update()
```

## Testing Patterns

### Test Mode

```python
@pytest.mark.asyncio
async def test_application():
    app = MyApp(config=MyConfig(), test_mode=True)
    task = asyncio.create_task(run_app(app, start=False))

    await app.wait_until_ready()

    # Manually trigger loop iterations
    await app.next()
    assert app.get_tag("initialized") == True

    await app.next()
    # Check state after second loop

    task.cancel()
```

### Mock Interfaces

```python
class MockPlatformInterface:
    def __init__(self):
        self.di_values = [False] * 8
        self.ai_values = [0] * 8

    def get_di(self, channel):
        return self.di_values[channel]

    def get_ai(self, channel):
        return self.ai_values[channel]

# In test
app = MyApp(
    config=MyConfig(),
    platform_iface=MockPlatformInterface()
)
```

## Shutdown Patterns

### Graceful Shutdown

```python
class MyApp(Application):
    async def on_shutdown_at(self, dt):
        log.info(f"Shutdown scheduled for {dt}")

        # Save current state
        await self.save_state()

        # Stop processes safely
        await self.stop_pump()

        # Force final log
        self.force_log_on_shutdown = True

    async def check_can_shutdown(self) -> bool:
        # Check if pump is running
        if self.get_do(0):
            log.warning("Cannot shutdown - pump running")
            return False
        return True
```

---

> [!tip] Best Practice
> Always test your application in simulator mode before deploying to real hardware.

See Also:
- [[10-Application-Framework|Application Framework]]
- [[61-State-Machine|State Machine]]
- [[70-Tutorial-Basic-App|Basic App Tutorial]]

#patterns #best-practices #pydoover
