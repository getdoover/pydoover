# PyDoover Quick Reference

A quick reference card for common pydoover patterns and imports.

## Common Imports

```python
# Device Application
from pydoover.docker import Application, run_app

# Configuration
from pydoover import config
from pydoover.config import Schema, Integer, Number, String, Boolean, Enum, Array, Object

# UI Elements
from pydoover import ui
from pydoover.ui import (
    # Variables (read-only display)
    NumericVariable, TextVariable, BooleanVariable, DateTimeVariable,
    # Interactions
    Action, Slider, StateCommand, HiddenValue,
    # Containers
    Container, Submodule, RemoteComponent,
    # Helpers
    Range, Colour, Option,
    # Decorators
    action, slider, state_command, callback, hidden_value,
    # Special elements
    AlertStream, Multiplot, ConnectionInfo
)

# Cloud API
from pydoover.cloud.api import Client, Channel, Message, Agent
from pydoover.cloud.processor import ProcessorBase

# State Machine
from pydoover.state import StateMachine
```

## Application Template

```python
from pydoover.docker import Application, run_app
from pydoover.config import Schema

class MyConfig(Schema):
    def __init__(self):
        self.setting = config.Integer("My Setting", default=10)

class MyApp(Application):
    config: MyConfig

    def setup(self):
        # Runs once at startup
        self.set_ui([...])

    def main_loop(self):
        # Runs every loop_target_period (default: 1s)
        pass

if __name__ == "__main__":
    run_app(MyApp(config=MyConfig()))
```

## Configuration Types

| Type | Python Type | Example |
|------|-------------|---------|
| `Integer` | `int` | `config.Integer("Count", default=0, minimum=0)` |
| `Number` | `float` | `config.Number("Temperature", default=20.5)` |
| `String` | `str` | `config.String("Name", default="default")` |
| `Boolean` | `bool` | `config.Boolean("Enabled", default=True)` |
| `Enum` | `list[str]` | `config.Enum("Mode", choices=["A","B"], default="A")` |
| `Array` | `list` | `config.Array("Items", element=config.String(""))` |
| `Object` | `dict` | `config.Object("Settings")` |
| `Application` | `str` | `config.Application("Linked App")` |

## UI Element Quick Reference

### Variables (Read-only)

```python
NumericVariable("temp", "Temperature", curr_val=25.5, precision=1,
                ranges=[Range("Normal", 20, 30, Colour.green)])

TextVariable("status", "Status", curr_val="Running")

BooleanVariable("active", "Active", curr_val=True)

DateTimeVariable("last_update", "Last Update", curr_val=datetime.now())
```

### Interactions

```python
# Button
Action("start", "Start", colour=Colour.green, requires_confirm=True)

# Slider
Slider("speed", "Speed", min_val=0, max_val=100, step_size=5)

# Dropdown
StateCommand("mode", "Mode", user_options=[
    Option("auto", "Automatic"),
    Option("manual", "Manual")
])

# Hidden value (for internal state)
HiddenValue("internal_state")
```

### Decorators

```python
@ui.action("start_btn", "Start", colour=Colour.green)
def on_start(self, new_value):
    pass

@ui.slider("speed", "Speed", min_val=0, max_val=100)
def on_speed_change(self, new_value):
    pass

@ui.callback("my_command")
def on_command(self, element, new_value):
    pass
```

## Tag Operations

```python
# Set a tag for current app
self.set_tag("my_tag", value)

# Set a tag for another app
self.set_tag("other_tag", value, app_key="other-app-key")

# Set a global tag
self.set_global_tag("global_flag", True)

# Get tags
value = self.get_tag("my_tag")
value = self.get_tag("other_tag", app_key="other-app-key")
value = self.get_global_tag("global_flag")

# Subscribe to tag changes
self.subscribe_to_tag("my_tag", self.on_tag_change)
```

## Channel Operations

```python
# Publish to channel
self.publish_to_channel("my_channel", {"data": value})

# Subscribe to channel
self.subscribe_to_channel("my_channel", self.on_channel_update)

# Get channel aggregate (last known state)
aggregate = self.get_channel_aggregate("my_channel")
```

## Hardware I/O

```python
# Digital I/O
di_value = self.get_di(0)        # Read digital input 0
self.set_do(0, True)             # Set digital output 0 high
self.schedule_do(0, False, 5.0)  # Set DO 0 low after 5 seconds

# Analog I/O
ai_value = self.get_ai(0)        # Read analog input 0
self.set_ao(0, 4096)             # Set analog output 0
self.schedule_ao(0, 0, 5.0)      # Set AO 0 to 0 after 5 seconds
```

## Modbus Operations

```python
# Read registers
values = self.read_modbus_registers(
    address=0,
    count=10,
    register_type="holding",  # "input", "holding", "coil", "discrete"
    modbus_id=1,
    bus_id="default"
)

# Write registers
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
    callback=self.on_modbus_update,
    poll_secs=1.0
)
```

## Colours

```python
from pydoover.ui import Colour

Colour.red      # "#F44336"
Colour.pink     # "#E91E63"
Colour.purple   # "#9C27B0"
Colour.blue     # "#2196F3"
Colour.cyan     # "#00BCD4"
Colour.teal     # "#009688"
Colour.green    # "#4CAF50"
Colour.lime     # "#CDDC39"
Colour.yellow   # "#FFEB3B"
Colour.amber    # "#FFC107"
Colour.orange   # "#FF9800"
Colour.brown    # "#795548"
Colour.grey     # "#9E9E9E"
```

## CLI Commands

```bash
# Application management
doover app create <name>     # Create new app from template
doover app run               # Run app with docker-compose
doover app build             # Build Docker image
doover app publish           # Publish to Doover cloud
doover app test              # Run tests

# Schema management
doover config-schema export  # Export config to doover_config.json

# Account
doover login                 # Authenticate with Doover
doover logout                # Clear credentials
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_KEY` | Application identifier | Required |
| `DDA_URI` | Device Agent URI | `localhost:50051` |
| `PLT_URI` | Platform Interface URI | `localhost:50053` |
| `MODBUS_URI` | Modbus Interface URI | `localhost:50054` |
| `DEBUG` | Enable debug logging | `0` |
| `HEALTHCHECK_PORT` | Healthcheck HTTP port | `49200` |

---

#quick-reference #cheatsheet #pydoover
