# Application Lifecycle

This document provides detailed information about the lifecycle of a Doover application, from initialization through shutdown.

## Lifecycle Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LIFECYCLE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INITIALIZATION                                               │
│     ┌─────────────┐                                             │
│     │ __init__()  │  Config injected, interfaces created        │
│     └──────┬──────┘                                             │
│            │                                                     │
│            ▼                                                     │
│  2. CONNECTION                                                   │
│     ┌─────────────────────────────────────────────┐             │
│     │ Connect to Device Agent (gRPC)              │             │
│     │ Wait for deployment_config channel sync     │             │
│     │ Inject configuration values                 │             │
│     └──────────────────┬──────────────────────────┘             │
│                        │                                         │
│                        ▼                                         │
│  3. SETUP                                                        │
│     ┌─────────────┐                                             │
│     │  setup()    │  Initialize UI, state, subscriptions        │
│     └──────┬──────┘                                             │
│            │                                                     │
│            ▼                                                     │
│  4. MAIN LOOP (repeats)                                         │
│     ┌─────────────┐                                             │
│     │ main_loop() │  Read sensors, update UI, process data      │
│     └──────┬──────┘                                             │
│            │                                                     │
│            │ (every loop_target_period seconds)                  │
│            │                                                     │
│            ▼                                                     │
│  5. SHUTDOWN (when requested)                                    │
│     ┌──────────────────────────────────────────┐                │
│     │ on_shutdown_at() → check_can_shutdown()  │                │
│     │ close() → cleanup resources              │                │
│     └──────────────────────────────────────────┘                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Initialization

### Constructor (`__init__`)

The constructor is called with configuration and optional overrides:

```python
def __init__(
    self,
    config: Schema = None,
    name: str = None,
    app_key: str = None,
    loop_target_period: float = 1.0,
    test_mode: bool = False,
    **kwargs
):
    super().__init__(**kwargs)
    self.config = config
    self.name = name or self.__class__.__name__
    self.app_key = app_key  # Set from env if None
    self.loop_target_period = loop_target_period
```

**What happens:**
- Configuration schema is attached (but not yet populated)
- gRPC interface stubs are created
- UIManager is initialized
- Internal state is set up

**Do NOT:**
- Access `self.config.*.value` (not yet populated)
- Make gRPC calls (not yet connected)
- Access hardware I/O

## Phase 2: Connection

After initialization, the application connects to platform services.

### Device Agent Connection

```python
# Internal - happens automatically
async def _connect_to_dda(self):
    await self.device_agent.connect()
    await self.device_agent.wait_for_channels_sync_async(
        channel_names=["deployment_config", "ui_state", "ui_cmds"],
        timeout=30
    )
```

### Configuration Injection

Once `deployment_config` is received:

```python
# Internal - happens automatically
def _inject_config(self, deployment_config: dict):
    app_config = deployment_config.get(self.app_key, {})
    self.config._inject_deployment_config(app_config)
```

After this, `self.config.*.value` is accessible.

### Ready State

The application becomes "ready" after:
1. Device Agent connection established
2. Channels synchronized
3. Configuration injected

```python
# Check ready state
if self.is_ready:
    print("Application is ready")

# Wait for ready (in async context)
await self.wait_until_ready()
```

## Phase 3: Setup

The `setup()` method is called once after the application is ready.

### Purpose

- Initialize UI elements
- Set up channel subscriptions
- Initialize state machines
- Start background tasks
- Set initial tag values

### Implementation

```python
async def setup(self):
    """Called once after configuration is loaded."""
    # Set up UI
    self.set_ui([
        ui.NumericVariable("temperature", "Temperature"),
        ui.Action("refresh", "Refresh")
    ])

    # Subscribe to channels
    self.subscribe_to_channel("external_data", self.on_external_data)

    # Subscribe to tags from other apps
    self.subscribe_to_tag("pump_status", self.on_pump_status, app_key="pump_app")

    # Initialize state
    self.state_machine = AppStateMachine(self)

    # Set initial tags
    self.set_tag("app_initialized", True)
    self.set_tag("version", "1.0.0")

    log.info("Setup complete")
```

### Sync vs Async

`setup()` can be synchronous or asynchronous:

```python
# Synchronous
def setup(self):
    self.set_ui([...])

# Asynchronous (preferred for I/O operations)
async def setup(self):
    await self.load_cached_state()
    self.set_ui([...])
```

## Phase 4: Main Loop

The `main_loop()` method is called repeatedly at `loop_target_period` intervals.

### Timing

```python
class MyApp(Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loop_target_period = 1.0  # Default: 1 second

    async def main_loop(self):
        # Called every 1 second
        pass
```

### Typical Operations

```python
async def main_loop(self):
    # 1. Read sensor data
    raw_value = self.get_ai(0)
    temperature = self.scale_temperature(raw_value)

    # 2. Process data
    if temperature > self.config.threshold.value:
        self.handle_high_temp(temperature)

    # 3. Update UI
    self.ui_manager.update_variable("temperature", temperature)

    # 4. Update tags for other apps
    self.set_tag("current_temp", temperature)

    # 5. Handle UI communications (push changes to cloud)
    await self.ui_manager.handle_comms_async()
```

### Loop Timing Considerations

```python
async def main_loop(self):
    start = time.time()

    # Your logic here...

    elapsed = time.time() - start
    if elapsed > self.loop_target_period:
        log.warning(f"Loop took {elapsed:.2f}s, target is {self.loop_target_period}s")
```

### Skipping Iterations

The framework handles timing, but you can skip work:

```python
async def main_loop(self):
    # Only process every 10th iteration
    self._loop_count = getattr(self, '_loop_count', 0) + 1
    if self._loop_count % 10 != 0:
        return

    # Heavy processing here...
```

## Phase 5: Shutdown

Shutdown can be triggered by:
- System shutdown request
- Container stop signal
- Error conditions
- Manual request (`self.request_shutdown()`)

### Shutdown Notification

```python
async def on_shutdown_at(self, dt: datetime):
    """Called when shutdown is scheduled."""
    log.info(f"Shutdown scheduled for {dt}")

    # Calculate time remaining
    remaining = (dt - datetime.now()).total_seconds()
    log.info(f"Shutdown in {remaining:.0f} seconds")

    # Prepare for shutdown
    await self.save_current_state()
```

### Shutdown Permission

```python
async def check_can_shutdown(self) -> bool:
    """Return True if safe to shutdown."""
    # Check for critical operations
    if self.pump_running:
        log.warning("Cannot shutdown - pump is running")
        return False

    if self.data_transfer_in_progress:
        log.warning("Cannot shutdown - data transfer in progress")
        return False

    return True
```

### Cleanup

```python
async def close(self):
    """Called during shutdown for cleanup."""
    # Stop hardware
    self.set_do(0, False)  # Turn off pump
    self.set_do(1, False)  # Turn off heater

    # Save state
    await self.save_state_to_channel()

    # Close connections
    if hasattr(self, 'external_connection'):
        await self.external_connection.close()

    log.info("Cleanup complete")
```

### Requesting Shutdown

```python
# Request shutdown programmatically
self.request_shutdown()

# Or async version
await self.request_shutdown_async()
```

## Event Callbacks

### Channel Updates

```python
async def setup(self):
    self.subscribe_to_channel("sensor_data", self.on_sensor_data)

async def on_sensor_data(self, channel_name: str, data: dict):
    """Called when subscribed channel receives data."""
    log.info(f"Received data on {channel_name}: {data}")
```

### Tag Updates

```python
async def setup(self):
    self.subscribe_to_tag("external_signal", self.on_signal)

async def on_signal(self, tag_key: str, new_value):
    """Called when subscribed tag changes."""
    log.info(f"Tag {tag_key} changed to {new_value}")
```

### UI Command Updates

```python
@ui.callback("mode_selector")
async def on_mode_change(self, element, new_value):
    """Called when UI command changes."""
    log.info(f"Mode changed to {new_value}")
    self.current_mode = new_value
```

## Lifecycle Hooks Summary

| Hook | When Called | Purpose |
|------|-------------|---------|
| `__init__` | Object creation | Initialize attributes |
| `setup` | After ready | Set up UI, subscriptions |
| `main_loop` | Every period | Main processing logic |
| `on_shutdown_at` | Shutdown scheduled | Prepare for shutdown |
| `check_can_shutdown` | Before shutdown | Verify safe to stop |
| `close` | During shutdown | Cleanup resources |

## State Diagram

```
                    ┌──────────────┐
                    │   CREATED    │
                    └──────┬───────┘
                           │ connect()
                           ▼
                    ┌──────────────┐
                    │  CONNECTING  │
                    └──────┬───────┘
                           │ channels synced
                           ▼
                    ┌──────────────┐
                    │    READY     │◄────────────┐
                    └──────┬───────┘             │
                           │ setup()             │
                           ▼                     │
                    ┌──────────────┐             │
             ┌─────►│   RUNNING    │─────────────┘
             │      └──────┬───────┘  main_loop()
             │             │
             │             │ shutdown requested
             │             ▼
             │      ┌──────────────┐
             │      │  SHUTTING    │
             │      │    DOWN      │
             │      └──────┬───────┘
             │             │ close()
             │             ▼
             │      ┌──────────────┐
             └──────│   STOPPED    │
                    └──────────────┘
```

---

See Also:
- [[10-Application-Framework|Application Framework]]
- [[12-Tags-and-Channels|Tags and Channels]]
- [[61-State-Machine|State Machine]]

#lifecycle #application #pydoover
