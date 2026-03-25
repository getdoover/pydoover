# Project Structure Overview

This document describes the structure of the pydoover package and the recommended structure for Doover applications.

## PyDoover Package Structure

```
pydoover/
├── cli/              # CLI tool (entry point: `pydoover` command)
│   ├── cli.py             # Main CLI entry point
│   ├── decorators.py      # CLI decorators
│   ├── parsers.py         # Argument parsers
│   └── sub_section.py     # Sub-command sections
│
├── docker/           # Device application framework
│   ├── application.py     # Application base class (setup, main_loop)
│   ├── device_agent/      # Device Agent gRPC interface (cloud sync)
│   │   ├── device_agent.py
│   │   └── grpc_stubs/    # Generated protobuf files
│   ├── platform/          # Platform gRPC interface (hardware I/O)
│   │   ├── platform.py
│   │   └── grpc_stubs/
│   └── modbus/            # Modbus RTU/TCP interface
│       ├── modbus_iface.py
│       ├── config.py
│       └── grpc_stubs/
│
├── config/           # Configuration schema system
│   └── __init__.py        # Schema, Integer, String, Boolean, etc.
│
├── ui/               # UI element management
│   ├── manager.py         # UIManager - orchestrates UI state
│   ├── element.py         # Base Element class
│   ├── variable.py        # Variables (read-only device values)
│   ├── interaction.py     # Actions, Sliders, Commands, Parameters
│   ├── submodule.py       # Containers, Submodules, RemoteComponent
│   ├── camera.py          # Camera-related UI elements
│   ├── parameter.py       # Parameter input elements
│   └── misc.py            # Colour, Range, Option helpers
│
├── cloud/
│   ├── api/               # REST API client for Doover Cloud
│   │   ├── client.py      # Main API client
│   │   ├── agent.py       # Agent class
│   │   ├── channel.py     # Channel, Task, Processor classes
│   │   ├── message.py     # Message class
│   │   ├── application.py # Application metadata
│   │   ├── config.py      # ConfigManager for credentials
│   │   └── exceptions.py  # HTTP exceptions
│   └── processor/         # Cloud processor framework
│       └── base.py        # ProcessorBase class
│
├── reports/          # Report generation
│   ├── base.py            # Report base class
│   ├── data.py            # Data handling
│   ├── json_flatten.py    # JSON flattening utilities
│   └── xlsx_base.py       # Excel export
│
├── state/            # State machine (from transitions library)
│   └── __init__.py        # StateMachine wrapper
│
└── utils/            # Utility functions
    ├── utils.py           # General utilities
    ├── diff.py            # Dict diff/merge operations
    ├── alarm.py           # Alarm handling
    ├── kalman.py          # Kalman filter implementation
    ├── pid.py             # PID controller
    └── deprecator.py      # Deprecation warnings
```

## Recommended Application Structure

When building a Doover application, follow this structure:

```
my-app/
├── src/my_app/
│   ├── __init__.py        # Entry point with main()
│   ├── application.py     # Application class (extends Application)
│   ├── app_config.py      # Configuration schema (extends Schema)
│   ├── app_ui.py          # UI element definitions
│   └── app_state.py       # Optional: State machine definitions
│
├── simulators/
│   ├── docker-compose.yml # Local development orchestration
│   └── sample/            # Optional: simulator apps
│       └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   └── test_application.py
│
├── doover_config.json     # Generated app metadata (don't edit manually)
├── pyproject.toml         # Project dependencies
├── Dockerfile             # Container build file
├── README.md
└── .gitignore
```

## Key File Descriptions

### `__init__.py` (Entry Point)

```python
from pydoover.docker import run_app
from .application import MyApplication
from .app_config import MyConfig

def main():
    run_app(MyApplication(config=MyConfig()))

if __name__ == "__main__":
    main()
```

### `application.py`

```python
from pydoover.docker import Application
from pydoover import ui
from .app_config import MyConfig
from .app_ui import create_ui, update_ui

class MyApplication(Application):
    config: MyConfig

    async def setup(self):
        self.set_ui(create_ui())
        # Initialize state, start background tasks

    async def main_loop(self):
        # Read sensors, process data
        update_ui(self.ui_manager, data)

    @ui.callback("some_command")
    async def on_command(self, element, new_value):
        # Handle user interaction
        pass
```

### `app_config.py`

```python
from pydoover import config

class MyConfig(config.Schema):
    def __init__(self):
        self.poll_interval = config.Number(
            "Poll Interval",
            default=1.0,
            minimum=0.1,
            description="Seconds between sensor reads"
        )

def export():
    """Export schema to doover_config.json"""
    import pathlib
    cfg = MyConfig()
    cfg.export(pathlib.Path("doover_config.json"), "my_app")

if __name__ == "__main__":
    export()
```

### `app_ui.py`

```python
from pydoover import ui

def create_ui() -> list[ui.Element]:
    return [
        ui.NumericVariable("temperature", "Temperature", precision=1,
            ranges=[
                ui.Range("Low", 0, 15, ui.Colour.blue),
                ui.Range("Normal", 15, 30, ui.Colour.green),
                ui.Range("High", 30, 50, ui.Colour.red)
            ]),
        ui.TextVariable("status", "Status"),
        ui.Action("refresh", "Refresh", colour=ui.Colour.blue)
    ]

def update_ui(manager: ui.UIManager, data: dict):
    manager.get_element("temperature").current_value = data["temp"]
    manager.get_element("status").current_value = data["status"]
```

### `app_state.py` (Optional)

```python
from pydoover.state import StateMachine

class AppState(StateMachine):
    states = ["idle", "running", "error"]
    transitions = [
        {"trigger": "start", "source": "idle", "dest": "running"},
        {"trigger": "stop", "source": "running", "dest": "idle"},
        {"trigger": "fail", "source": "*", "dest": "error"},
        {"trigger": "reset", "source": "error", "dest": "idle"}
    ]

    def __init__(self):
        super().__init__(states=self.states, transitions=self.transitions, initial="idle")

    async def on_enter_running(self):
        print("Started running")

    async def on_enter_error(self):
        print("Error occurred")
```

## doover_config.json

This file is **generated**, not manually edited. It contains:

```json
{
    "my_app": {
        "display_name": "My Application",
        "app_type": "docker",
        "visibility": "private",
        "config_schema": { ... },  // Generated from app_config.py
        "dependencies": [],
        "container_image": {
            "repository": "registry.example.com/my_app",
            "tag": "latest"
        }
    }
}
```

Export with:
```bash
doover config-schema export
# or
python -m my_app.app_config
```

## Docker Setup

### Dockerfile

```dockerfile
FROM doover/device_base:latest

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN uv sync --no-dev

ENTRYPOINT ["uv", "run", "python", "-m", "my_app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  device_agent:
    image: doover/device_agent:latest
    environment:
      - AGENT_ID=${AGENT_ID:-test-agent}
    ports:
      - "50051:50051"

  platform:
    image: doover/platform_simulator:latest
    ports:
      - "50053:50053"

  my_app:
    build:
      context: ..
      dockerfile: Dockerfile
    environment:
      - APP_KEY=my_app
      - DDA_URI=device_agent:50051
      - PLT_URI=platform:50053
    depends_on:
      - device_agent
      - platform
```

---

See Also:
- [[01-Getting-Started|Getting Started]]
- [[10-Application-Framework|Application Framework]]
- [[20-Configuration-System|Configuration System]]

#project-structure #architecture #pydoover
