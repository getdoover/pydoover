# PyDoover

Python package (v0.4.18) for developing applications on the Doover IoT/Industrial automation platform. Enables building device applications, cloud processors, and cloud API interactions.

## Quick Reference

- **Python**: >=3.11
- **Package manager**: uv
- **Linting/Formatting**: Ruff (run `ruff check` and `ruff format`)
- **Tests**: `pytest` (with pytest-asyncio, strict mode)
- **Docs**: Sphinx at `/docs/source/`

## Project Structure

```
pydoover/
├── cli/              # CLI tool (entry point: `pydoover` command)
├── docker/           # Device application framework
│   ├── application.py       # Application base class (setup, main_loop)
│   ├── device_agent/        # Device Agent gRPC interface (cloud sync)
│   ├── platform/            # Platform gRPC interface (hardware I/O)
│   └── modbus/              # Modbus RTU/TCP interface
├── config/           # Configuration schema system (generates JSON Schema)
├── ui/               # UI element management
│   ├── manager.py           # UIManager - orchestrates UI state
│   ├── element.py           # Base Element class
│   ├── variable.py          # Variables (read-only device values)
│   ├── interaction.py       # Actions, Sliders, Commands, Parameters
│   └── submodule.py         # Containers, Submodules, RemoteComponent
├── cloud/
│   ├── api/          # REST API client for Doover Cloud
│   └── processor/    # Cloud processor framework (ProcessorBase)
├── reports/          # Report generation (Excel export)
└── utils/            # Utilities (Kalman filter, PID, diff/merge, etc.)
```

## Key Patterns

### Device Applications
Extend `Application` class in `pydoover/docker/application.py`:
```python
from pydoover.docker import Application, run_app

class MyApp(Application):
    def setup(self): ...
    def main_loop(self): ...

run_app(MyApp(config=Schema()))
```

### Cloud Processors
Extend `ProcessorBase` in `pydoover/cloud/processor/base.py`:
```python
from pydoover.cloud.processor import ProcessorBase

class MyProcessor(ProcessorBase):
    def process(self): ...
```

### Configuration Schemas
Define in `pydoover/config/`:
```python
from pydoover.config import Schema, Integer, String, Object

class MyConfig(Schema):
    setting = Integer(default=10, minimum=0)
    name = String(default="example")
```

### UI Elements
UI elements use a position counter system. All elements inherit from `Element` base class in `ui/element.py`. Key classes:
- `Variable`, `NumericVariable`, `TextVariable` - read-only values
- `Action`, `Slider`, `StateCommand`, `Parameter` - interactions
- `Container`, `Submodule` - hierarchical organization

## gRPC Interfaces

Three gRPC interfaces in `docker/`:
- **DeviceAgentInterface**: Cloud sync, channels, subscriptions
- **PlatformInterface**: Digital/Analog I/O, PWM, pulse counters
- **ModbusInterface**: Modbus RTU/TCP register operations

Proto files are in each interface directory with generated stubs in `grpc_stubs/`.

## Commands

```bash
# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Build docs
cd docs && make html

# CLI usage
pydoover platform <method> [args]
pydoover device_agent <method> [args]
pydoover modbus <method> [args]
```

## Dependencies

Core: `aiohttp`, `requests`
Optional extras:
- `grpc`: grpcio, protobuf
- `reports`: pytz, tzlocal, xlsxwriter
- `test`: jsonschema, pytest, pytest-asyncio
