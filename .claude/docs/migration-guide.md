# Doover-2 App Migration Guide

Instructions for migrating a pydoover device application from the old API to the new doover-2 declarative API.

## Overview of Changes

The doover-2 branch introduces three new declarative systems:
- **Config**: Class-level attribute declarations (no more `__init__` assignments)
- **Tags**: New `Tags` class replaces `set_tags_async()`
- **UI**: New `ui.UI` subclass replaces manual `UIManager.add_children()`

## Step-by-Step Migration

### 1. Config Schema (`app_config.py`)

**Before** (old — elements declared in `__init__`):
```python
from pydoover import config

class MyConfig(config.Schema):
    def __init__(self):
        self.setting = config.Integer("Setting", default=10, description="...")
        self.name = config.String("Name", description="...")

        # Nested objects used add_elements()
        alarm = config.Object("Alarm", description="...")
        alarm.add_elements(
            config.Number("Threshold", default=0.0),
            config.Boolean("Enabled", default=False),
        )
```

**After** (new — class-level declarations):
```python
from pydoover import config

class AlarmConfig(config.Object):
    threshold = config.Number("Threshold", default=0.0)
    enabled = config.Boolean("Enabled", default=False)

class MyConfig(config.Schema):
    setting = config.Integer("Setting", default=10, description="...")
    name = config.String("Name", description="...")
    alarm = AlarmConfig("Alarm", description="...")
```

Key changes:
- Move ALL `config.Integer(...)`, `config.String(...)`, etc. from `__init__` body to **class-level attributes**
- Remove `__init__` entirely (unless you have custom `@property` methods — those stay on the class)
- For `config.Object` with `add_elements()`: create a **subclass** of `config.Object` with class-level element attributes, then instantiate that subclass as a class attribute on the Schema
- The new `Schema.__init_subclass__` auto-discovers `ConfigElement` instances in `cls.__dict__` — `__init__` assignments are invisible to it
- `export()` is now a **classmethod** — call `MyConfig.export(...)` not `MyConfig().export(...)`
- `to_schema()` is also a classmethod now — `MyConfig.to_schema()` not `MyConfig().to_schema()`

### 2. Create Tags File (`app_tags.py`) — NEW FILE

Create a new file declaring your application's tags. Tags represent the runtime state values your app produces.

```python
from pydoover.tags import Tag, Tags

class MyAppTags(Tags):
    value = Tag("number", default=None)
    raw_value = Tag("number", default=None)
    status = Tag("string", default="idle")
    enabled = Tag("boolean", default=False)
```

Tag types: `"number"`, `"integer"`, `"float"`, `"string"`, `"boolean"`, `"array"`, `"object"`

Every value your app previously passed to `set_tags_async()` needs a corresponding `Tag` declaration here.

### 3. UI (`app_ui.py`)

**Before** (old — plain class with manual management):
```python
from pydoover import ui

class MyUI:
    def __init__(self, config):
        self.config = config
        self.reading = ui.NumericVariable(
            "reading",
            f"{config.name.value} ({config.units.value})"
        )

    def fetch(self):
        return [self.reading]

    def update(self, value):
        self.reading.update(value)
```

**After** (new — `ui.UI` subclass with tag binding):
```python
from pydoover import ui
from .app_tags import MyAppTags

class MyUI(ui.UI):
    reading = ui.NumericVariable(
        "Reading",
        value=MyAppTags.value,  # Bind to tag — auto-updates when tag changes
    )

    async def setup(self):
        # Dynamic display names that depend on config values go here
        self.reading.display_name = f"{self.config.name.value} ({self.config.units.value})"
```

Key changes:
- Subclass `ui.UI` instead of a plain class
- Declare UI elements as **class-level attributes**
- Bind element values to tags by passing the **Tag class attribute** (e.g., `MyAppTags.value`) as the `value=` parameter — this creates an automatic binding so the UI updates whenever the tag is set
- Remove `fetch()` method — framework handles element registration
- Remove `update()` method — tag bindings auto-update the UI
- If display names depend on runtime config values, set them in `async def setup(self)` (the framework calls this after config is injected). `self.config` and `self.tags` are available in `setup()`
- For `NumericVariable`, the value parameter is `value=` (not `curr_val=`)

### 4. Application (`application.py`)

**Before** (old):
```python
from pydoover.docker import Application
from .app_config import MyConfig
from .app_ui import MyUI

class MyApp(Application):
    config: MyConfig  # type hint only

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = time.time()
        self.ui = None

    async def setup(self):
        self.ui = MyUI(self.config)
        self.ui_manager.add_children(*self.ui.fetch())
        # ... other setup

    async def main_loop(self):
        value = read_sensor()
        self.ui.update(value)
        await self.set_tags_async({"value": value, "raw_value": raw})
```

**After** (new):
```python
from pydoover.docker import Application
from .app_config import MyConfig
from .app_tags import MyAppTags
from .app_ui import MyUI

class MyApp(Application):
    config_cls = MyConfig
    tags_cls = MyAppTags
    ui_cls = MyUI

    async def setup(self):
        self.started = time.time()
        # ... other setup (no UI wiring needed)

    async def main_loop(self):
        value = read_sensor()
        await self.tags.value.set(value)
        await self.tags.raw_value.set(raw)
```

Key changes:
- Add **class attributes**: `config_cls`, `tags_cls`, `ui_cls` pointing to your classes
- Remove custom `__init__` — move any state init (like `self.started`) into `setup()`
- Remove `self.ui = MyUI(self.config)` and `self.ui_manager.add_children(...)` from `setup()` — the framework instantiates and wires up UI automatically
- Remove `self.ui.update(...)` calls from `main_loop()` — tag bindings handle this
- Replace `await self.set_tags_async({"key": val, ...})` with individual `await self.tags.<name>.set(val)` calls
- `self.config` is still available and works the same way for reading config values

### 5. Entry Point (`__init__.py`)

**Before**:
```python
from pydoover.docker import run_app
from .application import MyApp
from .app_config import MyConfig

def main():
    run_app(MyApp(config=MyConfig()))
```

**After**:
```python
from pydoover.docker import run_app
from .application import MyApp

def main():
    run_app(MyApp())
```

Remove the `config=` constructor argument — config is now handled via `config_cls` class attribute.

### 6. Tests (`tests/test_imports.py`)

Update tests to verify the new patterns:

```python
def test_import_app():
    from my_app.application import MyApp
    assert MyApp
    assert MyApp.config_cls is not None
    assert MyApp.tags_cls is not None
    assert MyApp.ui_cls is not None

def test_config():
    from my_app.app_config import MyConfig
    schema = MyConfig.to_schema()  # classmethod now, no instance needed
    assert isinstance(schema, dict)
    assert len(schema["properties"]) > 0

def test_tags():
    from my_app.app_tags import MyAppTags
    assert MyAppTags

def test_ui():
    from my_app.app_ui import MyUI
    from pydoover.ui import UI
    assert issubclass(MyUI, UI)
```

### 7. CI & Docker — Install git for uv git dependencies

The `spaneng/doover_device_base` image does not include git. Since pydoover is installed as a git dependency (`pydoover @ git+https://...@doover-2`), git must be available wherever `uv sync` runs. This affects two places:

#### CI test workflow (`.github/workflows/run-tests.yml`)

Add a git install step before checkout:

```yaml
steps:
  - name: Install git
    run: apt-get update && apt-get install -y git

  - uses: actions/checkout@v4
  # ... rest of steps
```

#### Dockerfile

Add a git install in the builder stage, before any `uv sync` commands:

```dockerfile
FROM base_image AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# ... rest of build steps
```

This only affects the builder stage — git is not needed in the final runtime image.

### 8. Interface Method Renames (`sensor.py` and any hardware/gRPC code)

The doover-2 branch renames many methods across the gRPC interfaces. Search your app code for any of the old method names and replace them.

#### PlatformInterface (`self.platform_iface`)

All read methods renamed from `get_*` to `fetch_*`:

| Old Name | New Name |
|----------|----------|
| `get_ai(pin)` | `fetch_ai(pin)` |
| `get_di(pin)` | `fetch_di(pin)` |
| `get_do(pin)` | `fetch_do(pin)` |
| `get_ao(pin)` | `fetch_ao(pin)` |
| `get_input_voltage()` | `fetch_system_voltage()` |
| `get_system_power()` | `fetch_system_power()` |
| `get_temperature()` | `fetch_system_temperature()` |
| `get_location()` | `fetch_location()` |
| `get_shutdown_immunity()` | `fetch_immunity_seconds()` |
| `set_shutdown_immunity(secs)` | `set_immunity_seconds(secs)` |
| `get_io_table()` | `fetch_io_table()` |
| `get_events(...)` | `fetch_events(...)` |
| `get_di_events(...)` | `fetch_di_events(...)` |

Methods that kept the same name: `set_do(...)`, `set_ao(...)`, `schedule_do(...)`, `schedule_ao(...)`, `reboot()`, `shutdown()`, `schedule_startup(...)`, `schedule_shutdown(...)`, `sync_rtc()`.

New methods: `get_new_pulse_counter(...)`, `get_new_event_counter(...)`, `start_di_pulse_listener(...)`.

#### DeviceAgentInterface (`self.device_agent`)

| Old Name | New Name |
|----------|----------|
| `get_channel_aggregate(name)` | `fetch_channel_aggregate(name)` |
| `get_turn_token()` | `fetch_turn_token()` |
| `get_message_attachment(att)` | `fetch_message_attachment(att)` |
| `add_subscription(channel, callback)` | `add_event_callback(channel, callback, events)` |
| `publish_to_channel(channel, data)` | `update_channel_aggregate(channel, data)` |

**Important: `add_subscription` → `add_event_callback` callback signature change.**

The old `add_subscription` callback received `(channel_name: str, channel_values: dict)`.

The new `add_event_callback` callback receives a single event object. The callback must be `async` and accept one argument — an event (e.g., `AggregateUpdateEvent`). Access data via `event.aggregate.data` and channel name via the event payload.

```python
# Before (old)
self.device_agent.add_subscription("tag_values", self.on_values_update)

def on_values_update(self, channel_name, channel_values):
    ...

# After (new)
from pydoover.models import EventSubscription, AggregateUpdateEvent

self.device_agent.add_event_callback(
    "tag_values",
    self.on_values_update,
    EventSubscription.aggregate_update,
)

async def on_values_update(self, event: AggregateUpdateEvent):
    channel_name = "tag_values"  # or derive from event
    channel_values = event.aggregate.data
    ...
```

Methods that kept the same name: `create_message(...)`, `update_message(...)`, `update_channel_aggregate(...)`, `list_messages(...)`.

#### Application (`self`)

| Old Name | New Name |
|----------|----------|
| `set_tags_async({"key": val})` | `self.tags.<name>.set(val)` (preferred) or `set_tags({"key": val})` |

#### ModbusInterface (`self.modbus_iface`)

| Old Name | New Name |
|----------|----------|
| `get_bus_status(bus_id)` | `fetch_bus_status(bus_id)` |

Methods that kept the same name: `open_bus(...)`, `close_bus(...)`, `read_registers(...)`, `write_registers(...)`, `add_read_register_subscription(...)`.

#### Quick search commands

Run these in your app's `src/` directory to find any old method calls that need updating:

```bash
# Platform interface renames
grep -rn "\.get_ai\|\.get_di\|\.get_do\|\.get_ao" .
grep -rn "\.get_input_voltage\|\.get_system_power\|\.get_temperature\|\.get_location" .
grep -rn "\.get_shutdown_immunity\|\.set_shutdown_immunity\|\.get_io_table" .
grep -rn "\.get_events\|\.get_di_events" .

# Device agent renames
grep -rn "\.get_channel_aggregate\|\.get_turn_token\|\.get_message_attachment" .
grep -rn "\.add_subscription\|\.publish_to_channel" .

# Application renames
grep -rn "\.set_tags_async\|\.get_bus_status" .
```

## Conventions & Best Practices

### App Display Name

Don't add a config field for "app name" or "meter name". Use the built-in `self.app_display_name` property on the Application class. For dynamic titles (e.g. showing current state), use an `app_display_name` tag:

```python
# Tags
app_display_name = Tag("string", default="My App")

# Application main_loop
await self.tags.app_display_name.set(f"{self.app_display_name} ({status})")
```

### ApplicationPosition

Use `ApplicationPosition()` from `pydoover.config` instead of a custom `config.Integer("Position", ...)`:

```python
from pydoover.config import ApplicationPosition

class MyConfig(config.Schema):
    # ... other fields ...
    position = ApplicationPosition()
```

### Don't Duplicate UI Commands and Tags

If a value is set via a UI interaction (FloatInput, Select, Button, etc.), read it directly from the UI element. Don't create a corresponding tag to mirror the same data:

```python
# Good — read directly from UI element
threshold = self.ui.alert_counter.value
await self.ui.alert_counter.set(None)  # reset after use

# Bad — unnecessary tag duplication
await self.tags.alert_threshold.set(value)  # in handler
threshold = self.tags.alert_threshold.value  # in main_loop
```

Only use tags for state that isn't already held by a UI element.

### UI Element Mapping (Old → New)

| Old Element | New Element |
|-------------|-------------|
| `ui.Action("id", "Label")` | `ui.Button("Label")` |
| `ui.NumericParameter("id", "Label")` | `ui.FloatInput("Label")` |
| `ui.TextParameter("id", "Label")` | `ui.TextInput("Label")` |
| `ui.DateTimeParameter("id", "Label")` | `ui.DatetimeInput("Label")` |
| `ui.DateTimeVariable("id", "Label")` | `ui.Timestamp("Label", value=Tags.x)` |
| `ui.StateCommand("id", "Label", ...)` | `ui.Select("Label", options=[...])` |
| `ui.HiddenValue("id")` | Use a `Tag` instead |
| `ui.AlertStream("id", "Label")` | Use `self.create_message(channel, {...})` |
| `ui.Option("key", "Display")` | `ui.Option("Display")` |

Note: New elements use `display_name` as the first positional arg (not a separate `id`). The element name is auto-generated from the display name (snake_cased).

### UI Interaction Handlers

Use `@ui.handler` on the Application class to handle user interactions. The handler name matches the element's auto-generated name:

```python
# UI element "Alert Counter" → auto-name "alert_counter"
@ui.handler("alert_counter", parser=float)
async def on_alert(self, ctx, value: float):
    log.info(f"Alert set to {value}")
```

For elements where you only need to read the current value in `main_loop` (e.g. a Select for desired state), you don't need a handler — just read `self.ui.element.value`.

### Static UI Export

If the UI is fully static (no `setup()` override), add an export function and pyproject script:

```python
# app_ui.py
def export():
    from pathlib import Path
    MyUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "app_name"
    )
```

```toml
# pyproject.toml
[project.scripts]
export-ui = "my_app.app_ui:export"
```

If the UI has a `setup()` override (uses config values to set ranges, precision, hidden, etc.), it cannot be exported statically — omit the export function and script.

## Files Summary

| File | Action | Description |
|------|--------|-------------|
| `app_config.py` | **Modify** | Move elements from `__init__` to class-level. Subclass `config.Object` for nested objects. |
| `app_tags.py` | **Create** | New file declaring `Tags` subclass with `Tag` attributes. |
| `app_ui.py` | **Modify** | Subclass `ui.UI`, bind values to tags, use `setup()` for dynamic display names. |
| `application.py` | **Modify** | Add `config_cls`/`tags_cls`/`ui_cls`, remove `__init__`, use `self.tags.x.set()`. |
| `__init__.py` | **Modify** | Remove `config=` arg from `run_app()` call. |
| `sensor.py` / hardware code | **Modify** | Rename `get_*` → `fetch_*` for platform/device_agent/modbus interface calls. |
| `tests/test_imports.py` | **Modify** | Update assertions for new patterns. |
| `Dockerfile` | **Modify** | Add `apt-get install git` in builder stage before `uv sync`. |
| `.github/workflows/run-tests.yml` | **Modify** | Add git install step if using container image. |
| `pyproject.toml` | **No change** | Should already point to `pydoover @ git+...@doover-2`. |

## Verification

After migration, run these checks locally:

```bash
# Tests pass
uv run pytest tests -v

# Application imports cleanly
uv run python -c "from my_app.application import MyApp"

# Config export still works (if export-config script exists)
uv run export-config
```

### Remote device testing

Deploy the app to a remote device and check container logs to verify it runs correctly:

```bash
# Deploy to a remote device (builds and runs via Docker on the device)
doover app run <DEVICE_IP>

# SSH into the device to check container status
ssh doovit@<DEVICE_IP> "docker ps -a --format '{{.ID}} {{.Names}} {{.Status}}'"

# Check container logs (use the container ID from above)
ssh doovit@<DEVICE_IP> "docker logs --tail 50 <CONTAINER_ID>"

# Or follow logs in real-time
ssh doovit@<DEVICE_IP> "docker logs -f --tail 100 <CONTAINER_ID>"
```

Things to look for in the logs:
- **Startup errors**: `TypeError`, `AttributeError`, `ImportError` — indicates migration issues
- **DDA is available**: Confirms the Device Agent gRPC connection is working
- **Setting up internal app**: Confirms `_setup()` was reached
- **Application-specific logs**: e.g. "Started server on 0.0.0.0:8765" for foxglove

Common issues:
- **Old pydoover version**: If you see errors from old API methods, update the lock file with `uv lock --upgrade-package pydoover` and redeploy
- **Healthcheck port conflict**: If the old container is still bound to the port, stop it first: `ssh doovit@<DEVICE_IP> "docker stop <OLD_CONTAINER_ID>"`
