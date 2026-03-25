# Application Framework

The Application framework is the core of pydoover for building device applications. It provides a structured way to create applications that run on Doover-enabled devices.

## Overview

The `Application` class in `pydoover/docker/application.py` is the base class for all Doover device applications. It handles:

- Connection to the Device Agent (cloud sync)
- Platform interface (hardware I/O)
- Modbus interface (industrial protocols)
- UI management
- Configuration injection
- Tag/channel communication
- Lifecycle management

## Basic Usage

```python
from pydoover.docker import Application, run_app
from pydoover.config import Schema

class MyConfig(Schema):
    pass

class MyApp(Application):
    config: MyConfig  # Type hint for IDE support

    def setup(self):
        """Called once after initialization."""
        pass

    def main_loop(self):
        """Called repeatedly every loop_target_period seconds."""
        pass

if __name__ == "__main__":
    run_app(MyApp(config=MyConfig()))
```

## Application Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config` | `Schema` | Configuration schema instance |
| `device_agent` | `DeviceAgentInterface` | Cloud communication interface |
| `platform_iface` | `PlatformInterface` | Hardware I/O interface |
| `modbus_iface` | `ModbusInterface` | Modbus protocol interface |
| `ui_manager` | `UIManager` | User interface manager |
| `app_key` | `str` | Unique application identifier |
| `app_display_name` | `str` | Human-readable app name |
| `loop_target_period` | `float` | Target loop interval (default: 1s) |
| `name` | `str` | Application name (default: class name) |

## Lifecycle Methods

### `setup()`

Called once after the application connects to the Device Agent and receives its configuration.

```python
async def setup(self):
    # Initialize UI elements
    self.set_ui([
        ui.NumericVariable("temp", "Temperature")
    ])

    # Set initial tags
    self.set_tag("app_ready", True)

    # Subscribe to channels
    self.subscribe_to_channel("external_data", self.on_external_data)
```

**Note:** Can be `async` or synchronous.

### `main_loop()`

Called repeatedly at `loop_target_period` intervals (default: 1 second).

```python
async def main_loop(self):
    # Read sensors
    temp = self.get_ai(0)

    # Update UI
    self.ui_manager.get_element("temp").current_value = temp

    # Publish tags
    self.set_tag("temperature", temp)
```

**Note:** Avoid blocking operations. Use `async`/`await` for I/O.

### `on_shutdown_at(dt: datetime)`

Called when a shutdown is scheduled. Override to perform cleanup.

```python
async def on_shutdown_at(self, dt: datetime):
    log.info(f"Shutdown scheduled at {dt}")
    # Save state, close connections, etc.
```

### `check_can_shutdown() -> bool`

Called to check if the application can safely shutdown.

```python
async def check_can_shutdown(self) -> bool:
    # Check if safe to shutdown
    if self.get_do(0) == 1:  # Engine running
        return False
    return True
```

## Application State

### Ready State

```python
# Check if app is ready
if self.is_ready:
    print("App is ready")

# Wait for app to be ready (in async context)
await self.wait_until_ready()
```

### Device Agent Status

```python
# Check if DDA is available
if self.get_is_dda_available():
    print("DDA is available")

# Check if DDA is online (connected to cloud)
if self.get_is_dda_online():
    print("DDA is online")

# Check if DDA has ever been online
if self.get_has_dda_been_online():
    print("DDA has been online")
```

## Configuration

Configuration is defined via a `Schema` subclass and injected automatically:

```python
from pydoover import config

class MyConfig(config.Schema):
    def __init__(self):
        self.poll_rate = config.Number("Poll Rate", default=1.0)
        self.threshold = config.Integer("Threshold", default=100)

class MyApp(Application):
    config: MyConfig

    def setup(self):
        # Access config values
        rate = self.config.poll_rate.value
        thresh = self.config.threshold.value
```

See [[20-Configuration-System]] for full details.

## UI Management

### Setting UI Elements

```python
def setup(self):
    self.set_ui([
        ui.NumericVariable("temp", "Temperature"),
        ui.TextVariable("status", "Status"),
        ui.Action("refresh", "Refresh Data")
    ])
```

### Accessing UI Elements

```python
# Get an element by name
temp_var = self.ui_manager.get_element("temp")
temp_var.current_value = 25.5

# Update a variable directly
self.ui_manager.update_variable("temp", 25.5)
```

### Commands and Interactions

```python
# Get a command value
mode = self.get_command("mode")

# Coerce (set) a command value
self.coerce_command("mode", "auto")
```

See [[30-UI-System-Overview]] for full details.

## Tags

Tags are key-value pairs shared between applications.

### Setting Tags

```python
# Set a tag for current app
self.set_tag("temperature", 25.5)

# Set a tag for another app
self.set_tag("external_value", 100, app_key="other-app")

# Set a global tag (shared across all apps)
self.set_global_tag("system_status", "running")

# Async versions
await self.set_tag_async("temperature", 25.5)
await self.set_global_tag_async("system_status", "running")
```

### Getting Tags

```python
# Get current app's tag
temp = self.get_tag("temperature")
temp = self.get_tag("temperature", default=0)

# Get another app's tag
value = self.get_tag("external_value", app_key="other-app")

# Get global tag
status = self.get_global_tag("system_status")
```

### Subscribing to Tags

```python
def setup(self):
    self.subscribe_to_tag("external_signal", self.on_signal_change)
    self.subscribe_to_tag(
        "other_tag",
        self.on_other_tag,
        app_key="other-app"
    )

async def on_signal_change(self, tag_key: str, new_value):
    print(f"{tag_key} changed to {new_value}")
```

## Channels

Channels are message queues for pub/sub communication.

```python
# Subscribe to a channel
self.subscribe_to_channel("sensor_data", self.on_sensor_data)

# Publish to a channel
self.publish_to_channel("output_data", {"value": 100})

# Get channel aggregate (last known state)
aggregate = self.get_channel_aggregate("sensor_data")
```

## Hardware I/O

### Digital I/O

```python
# Read digital input
di_value = self.get_di(0)  # Returns bool

# Read digital output state
do_value = self.get_do(0)

# Set digital output
self.set_do(0, True)   # Set high
self.set_do(0, False)  # Set low

# Schedule digital output
self.schedule_do(0, False, 5.0)  # Set low after 5 seconds
```

### Analog I/O

```python
# Read analog input (0-4095 typically)
ai_value = self.get_ai(0)

# Read analog output state
ao_value = self.get_ao(0)

# Set analog output
self.set_ao(0, 2048)

# Schedule analog output
self.schedule_ao(0, 0, 5.0)  # Set to 0 after 5 seconds
```

## Modbus

```python
# Read holding registers
values = self.read_modbus_registers(
    address=0,
    count=10,
    register_type="holding",
    modbus_id=1,
    bus_id="default"
)

# Write holding registers
self.write_modbus_registers(
    address=0,
    values=[100, 200],
    register_type="holding",
    modbus_id=1
)

# Subscribe to register changes
self.add_new_modbus_read_subscription(
    address=0,
    count=10,
    register_type="holding",
    callback=self.on_modbus_data,
    poll_secs=1.0
)
```

See [[53-Modbus-Interface]] for full details.

## Shutdown

```python
# Request system shutdown
self.request_shutdown()

# Async version
await self.request_shutdown_async()
```

## Test Mode

For testing, use `test_mode=True`:

```python
async def test_my_app():
    app = MyApp(config=MyConfig(), test_mode=True)
    asyncio.create_task(run_app(app, start=False))

    await app.wait_until_ready()

    # Manually advance main loop
    await app.next()
    await app.next()
```

## run_app() Function

```python
from pydoover.docker import run_app

run_app(
    app=MyApp(config=MyConfig()),
    start=True,              # Run blocking (False returns coroutine)
    setup_logging=True,      # Configure logging
    log_formatter=None,      # Custom log formatter
    log_filters=None         # Custom log filters
)
```

### Command Line Arguments

`run_app()` automatically parses:

| Argument | Env Var | Description |
|----------|---------|-------------|
| `--app-key` | `APP_KEY` | Application identifier |
| `--dda-uri` | `DDA_URI` | Device Agent URI |
| `--plt-uri` | `PLT_URI` | Platform Interface URI |
| `--modbus-uri` | `MODBUS_URI` | Modbus Interface URI |
| `--remote-dev` | `REMOTE_DEV` | Remote device hostname |
| `--config-fp` | `CONFIG_FP` | Config file override |
| `--healthcheck-port` | `HEALTHCHECK_PORT` | HTTP healthcheck port |
| `--debug` | `DEBUG` | Enable debug logging |

---

See Also:
- [[11-Application-Lifecycle|Application Lifecycle Details]]
- [[12-Tags-and-Channels|Tags and Channels]]
- [[20-Configuration-System|Configuration System]]
- [[30-UI-System-Overview|UI System]]

#application #framework #pydoover #device
