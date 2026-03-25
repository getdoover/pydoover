# gRPC Interfaces Overview

Doover device applications communicate with platform services via gRPC interfaces. These provide access to cloud synchronization, hardware I/O, and industrial protocols.

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Docker Container                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Your Application                       │  │
│  │      (extends pydoover.docker.Application)               │  │
│  └─────────────┬────────────────┬────────────────┬──────────┘  │
│                │                │                │              │
│                ▼                ▼                ▼              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │ DeviceAgent     │ │ Platform        │ │ Modbus          │  │
│  │ Interface       │ │ Interface       │ │ Interface       │  │
│  │ (port 50051)    │ │ (port 50053)    │ │ (port 50054)    │  │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘  │
└───────────┼────────────────────┼────────────────────┼──────────┘
            │ gRPC               │ gRPC               │ gRPC
            ▼                    ▼                    ▼
┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
│   Device Agent     │ │  Platform Service  │ │  Modbus Bridge     │
│   Service          │ │  (HW I/O)          │ │  Service           │
└────────────────────┘ └────────────────────┘ └────────────────────┘
```

## Interface Summary

| Interface | Default Port | Purpose |
|-----------|--------------|---------|
| Device Agent | 50051 | Cloud sync, channels, configuration |
| Platform | 50053 | Digital/Analog I/O, PWM |
| Modbus | 50054 | Modbus RTU/TCP communication |

## Device Agent Interface

The Device Agent Interface handles cloud communication.

### Access

```python
# In your Application class
self.device_agent  # DeviceAgentInterface instance
```

### Key Operations

```python
# Check availability
if self.device_agent.get_is_dda_available():
    print("Device Agent is available")

# Check cloud connection
if self.device_agent.get_is_dda_online():
    print("Connected to cloud")

# Publish to channel
self.device_agent.publish_to_channel(
    "my_channel",
    {"data": "value"},
    record_log=True,
    max_age=3600  # seconds
)

# Async version
await self.device_agent.publish_to_channel_async(...)

# Subscribe to channel
self.device_agent.add_subscription("my_channel", self.on_channel_update)

# Get channel aggregate
aggregate = self.device_agent.get_channel_aggregate("my_channel")

# Wait for channels to sync
await self.device_agent.wait_for_channels_sync_async(
    channel_names=["ui_state", "ui_cmds"],
    timeout=10
)
```

See [[51-Device-Agent-Interface]] for details.

## Platform Interface

The Platform Interface provides hardware I/O operations.

### Access

```python
# In your Application class
self.platform_iface  # PlatformInterface instance
```

### Digital I/O

```python
# Read digital input (returns bool)
value = self.platform_iface.get_di(0)
value = self.get_di(0)  # Convenience method

# Read digital output state
value = self.platform_iface.get_do(0)

# Set digital output
self.platform_iface.set_do(0, True)
self.set_do(0, True)  # Convenience method

# Schedule digital output (delayed)
self.platform_iface.schedule_do(0, False, 5.0)  # Set low after 5s
```

### Analog I/O

```python
# Read analog input (typically 0-4095)
value = self.platform_iface.get_ai(0)
value = self.get_ai(0)  # Convenience method

# Read analog output state
value = self.platform_iface.get_ao(0)

# Set analog output
self.platform_iface.set_ao(0, 2048)
self.set_ao(0, 2048)  # Convenience method

# Schedule analog output (delayed)
self.platform_iface.schedule_ao(0, 0, 5.0)  # Set to 0 after 5s
```

See [[52-Platform-Interface]] for details.

## Modbus Interface

The Modbus Interface provides Modbus RTU/TCP communication.

### Access

```python
# In your Application class
self.modbus_iface  # ModbusInterface instance
```

### Register Types

| Type | Description |
|------|-------------|
| `"holding"` | Holding registers (read/write) |
| `"input"` | Input registers (read-only) |
| `"coil"` | Coils (read/write bits) |
| `"discrete"` | Discrete inputs (read-only bits) |

### Read Registers

```python
# Synchronous
values = self.modbus_iface.read_registers(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    num_registers=10,
    register_type="holding"
)

# Convenience method
values = self.read_modbus_registers(
    address=0,
    count=10,
    register_type="holding",
    modbus_id=1,
    bus_id="default"
)

# Async
values = await self.modbus_iface.read_registers_async(...)
```

### Write Registers

```python
# Synchronous
self.modbus_iface.write_registers(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    values=[100, 200, 300],
    register_type="holding"
)

# Convenience method
self.write_modbus_registers(
    address=0,
    values=[100, 200, 300],
    register_type="holding",
    modbus_id=1
)

# Async
await self.modbus_iface.write_registers_async(...)
```

### Subscriptions

```python
# Subscribe to register changes
self.modbus_iface.add_read_register_subscription(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    num_registers=10,
    register_type="holding",
    poll_secs=1.0,
    callback=self.on_modbus_update
)

# Convenience method
self.add_new_modbus_read_subscription(
    address=0,
    count=10,
    register_type="holding",
    callback=self.on_modbus_update,
    poll_secs=1.0,
    modbus_id=1,
    bus_id="default"
)

async def on_modbus_update(self, bus_id, modbus_id, address, values):
    print(f"Modbus update: {values}")
```

See [[53-Modbus-Interface]] for details.

## URI Configuration

Interface URIs are configured via environment variables or command line:

| Interface | Env Var | Default |
|-----------|---------|---------|
| Device Agent | `DDA_URI` | `localhost:50051` |
| Platform | `PLT_URI` | `localhost:50053` |
| Modbus | `MODBUS_URI` | `localhost:50054` |

### Remote Development

Connect to a remote device:

```bash
# Via command line
python -m my_app --remote-dev 192.168.1.100

# Via environment
export REMOTE_DEV=192.168.1.100
```

This replaces `localhost` with the specified address in all URIs.

## Async vs Sync

All interfaces support both synchronous and asynchronous operation:

```python
# Synchronous (blocking)
value = self.get_di(0)

# Asynchronous (non-blocking)
value = await self.platform_iface.get_di_async(0)

# The Application class handles this automatically based on
# whether your setup()/main_loop() are async or not
```

## Error Handling

```python
try:
    values = self.read_modbus_registers(
        address=0, count=10,
        register_type="holding",
        modbus_id=1
    )
except Exception as e:
    logging.error(f"Modbus read failed: {e}")
    values = None
```

## Testing Without Hardware

For development without hardware, use simulators:

```yaml
# docker-compose.yml
services:
  platform:
    image: doover/platform_simulator:latest
    ports:
      - "50053:50053"

  modbus:
    image: doover/modbus_simulator:latest
    ports:
      - "50054:50054"
```

---

See Also:
- [[51-Device-Agent-Interface|Device Agent Interface]]
- [[52-Platform-Interface|Platform Interface]]
- [[53-Modbus-Interface|Modbus Interface]]
- [[10-Application-Framework|Application Framework]]

#grpc #interfaces #hardware #pydoover
