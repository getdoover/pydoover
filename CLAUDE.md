# PyDoover

Python package for developing applications on the Doover IoT/Industrial automation platform. Enables building device applications, cloud processors, and cloud API interactions.

## Quick Reference

- **Python**: >=3.11
- **Package manager**: uv
- **Version**: single source of truth is `__version__` in `pydoover/__init__.py`. Hatchling reads it at build time (`dynamic = ["version"]` + `[tool.hatch.version]` in `pyproject.toml`). Bump it there only — do **not** add a `version` back to `[project]`.
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
├── processor/        # Cloud processor framework (event-driven Application)
├── api/              # Doover Cloud clients (auth/, control/, data/)
├── models/           # Data models for API/processor payloads (control/, data/, generated/)
├── config/           # Configuration schema system (generates JSON Schema)
├── ui/               # UI element management
│   ├── manager.py           # UIManager - orchestrates UI state
│   ├── element.py           # Base Element class
│   ├── variable.py          # Variables (read-only device values)
│   ├── interaction.py       # Actions, Sliders, Commands, Parameters
│   └── submodule.py         # Containers, Submodules, RemoteComponent
├── tags/             # TagsManager - typed key/value tag store
├── state/            # State-machine helpers (optional `transitions` dep)
├── reports/          # Report generation (Application base)
├── rpc.py            # Request/response RPC over Doover channels
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
Extend `Application` in `pydoover/processor/application.py`. Processors are event-driven — override the `on_*` handlers for the events you care about (`on_message_create`, `on_aggregate_update`, `on_deployment`, `on_schedule`, `on_ingestion_endpoint`, `on_manual_invoke`):
```python
from pydoover.processor import Application, run_app

class MyProcessor(Application):
    async def setup(self): ...
    async def on_message_create(self, event): ...

run_app(MyProcessor())
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

Core: `aiohttp`, `httpx`
Optional extras:
- `speedups`: zstandard (httpx) + backports.zstd (aiohttp, Python <3.14) — enables zstd response decoding. With these installed the API clients auto-advertise `gzip, deflate, zstd` and transparently decompress; gzip/deflate work without the extra.
- `grpc`: grpcio, protobuf
- `reports`: croniter
- `test`: jsonschema, pytest, pytest-asyncio, grpcio, protobuf, grpcio-health-checking
- `state` (state machines): `transitions` (imported lazily; falls back gracefully if absent)
