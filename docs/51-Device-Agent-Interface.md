# Device Agent Interface

The Device Agent Interface provides cloud synchronization, channel communication, and configuration management for device applications.

## Overview

The Device Agent (DDA) is a service that:
- Synchronizes data with the Doover cloud
- Manages channel subscriptions
- Provides configuration injection
- Handles tag storage
- Manages device state

## Access

In your application:

```python
# Access the interface
self.device_agent  # DeviceAgentInterface instance

# Or via shorthand methods on Application
self.get_is_dda_available()
self.get_is_dda_online()
```

## Connection Status

### Check Availability

```python
# Is DDA service reachable?
if self.device_agent.get_is_dda_available():
    print("Device Agent is available")

# Convenience method
if self.get_is_dda_available():
    print("DDA available")
```

### Check Online Status

```python
# Is DDA connected to cloud?
if self.device_agent.get_is_dda_online():
    print("Connected to cloud")

# Convenience method
if self.get_is_dda_online():
    print("Online")
```

### Check Historical Connection

```python
# Has DDA ever been online this session?
if self.device_agent.get_has_dda_been_online():
    print("Has been connected")

# Convenience method
if self.get_has_dda_been_online():
    print("Has been online")
```

### Wait for Connection

```python
async def setup(self):
    # Wait for DDA to come online
    await self.device_agent.wait_for_online_async(timeout=30)
```

## Channel Operations

### Subscribe to Channel

```python
async def setup(self):
    # Add subscription
    self.device_agent.add_subscription(
        "channel_name",
        self.on_channel_update
    )

async def on_channel_update(self, channel_name: str, aggregate: dict):
    log.info(f"Channel {channel_name} updated: {aggregate}")
```

### Wait for Channel Sync

```python
async def setup(self):
    # Wait for specific channels to sync
    synced = await self.device_agent.wait_for_channels_sync_async(
        channel_names=["ui_state", "ui_cmds", "deployment_config"],
        timeout=10
    )

    if synced:
        print("All channels synchronized")
    else:
        print("Timeout waiting for sync")
```

### Publish to Channel

```python
# Synchronous
self.device_agent.publish_to_channel(
    "my_channel",
    {"data": "value"},
    record_log=True,
    max_age=3600
)

# Asynchronous
await self.device_agent.publish_to_channel_async(
    "my_channel",
    {"data": "value"},
    record_log=True,
    max_age=3600
)
```

### Get Channel Aggregate

```python
aggregate = self.device_agent.get_channel_aggregate("channel_name")
```

## Tag Operations

### Set Tag

```python
# Set tag for current app
self.device_agent.set_tag("my_tag", value)

# Set tag for another app
self.device_agent.set_tag("other_tag", value, app_key="other-app")

# Async
await self.device_agent.set_tag_async("my_tag", value)
```

### Get Tag

```python
# Get tag from current app
value = self.device_agent.get_tag("my_tag")
value = self.device_agent.get_tag("my_tag", default=0)

# Get tag from another app
value = self.device_agent.get_tag("tag", app_key="other-app")
```

### Subscribe to Tag

```python
self.device_agent.subscribe_to_tag(
    "tag_name",
    callback,
    app_key=None
)
```

## Global Tags

```python
# Set global tag
self.device_agent.set_global_tag("system_mode", "running")
await self.device_agent.set_global_tag_async("system_mode", "running")

# Get global tag
mode = self.device_agent.get_global_tag("system_mode")
```

## Configuration

### Get Agent ID

```python
agent_id = self.device_agent.agent_id
```

### Get Deployment Config

```python
# Full config
config = self.device_agent.deployment_config

# Specific app config
app_config = config.get("my_app_key", {})
```

## Shutdown

### Request Shutdown

```python
self.device_agent.request_shutdown()

# Async
await self.device_agent.request_shutdown_async()
```

### Shutdown Callbacks

```python
async def on_shutdown_at(self, dt: datetime):
    # Called when shutdown is scheduled
    pass

async def check_can_shutdown(self) -> bool:
    # Return True if safe to shutdown
    return True
```

## Connection URI

The Device Agent URI is configured via:

| Source | Value |
|--------|-------|
| Environment | `DDA_URI` |
| Command line | `--dda-uri` |
| Default | `localhost:50051` |

### Remote Development

```bash
# Connect to remote DDA
export DDA_URI=192.168.1.100:50051
python -m my_app

# Or use remote-dev (replaces localhost in all URIs)
python -m my_app --remote-dev 192.168.1.100
```

## gRPC Details

The interface uses gRPC for communication:

- **Port**: 50051 (default)
- **Protocol**: gRPC (HTTP/2)
- **Authentication**: Internal (no auth required within Docker network)

### Proto Services

```protobuf
service DeviceAgent {
    rpc GetStatus(Empty) returns (StatusResponse);
    rpc PublishToChannel(PublishRequest) returns (PublishResponse);
    rpc SubscribeToChannel(SubscribeRequest) returns (stream ChannelUpdate);
    rpc SetTag(TagRequest) returns (TagResponse);
    rpc GetTag(TagRequest) returns (TagResponse);
    // ... etc
}
```

## Error Handling

```python
try:
    await self.device_agent.publish_to_channel_async(
        "my_channel",
        {"data": "value"}
    )
except Exception as e:
    log.error(f"DDA publish failed: {e}")
```

## Application Integration

The `Application` class provides convenience methods that wrap the Device Agent:

```python
# These methods use self.device_agent internally:
self.set_tag("key", value)
self.get_tag("key")
self.set_global_tag("key", value)
self.get_global_tag("key")
self.subscribe_to_tag("key", callback)
self.publish_to_channel("name", data)
self.get_channel_aggregate("name")
self.request_shutdown()
```

## Complete Example

```python
from pydoover.docker import Application
import logging

log = logging.getLogger(__name__)

class DataSyncApp(Application):
    async def setup(self):
        # Wait for DDA to be fully online
        if not self.get_is_dda_available():
            log.error("DDA not available!")
            return

        # Wait for channels to sync
        synced = await self.device_agent.wait_for_channels_sync_async(
            channel_names=["ui_state", "ui_cmds"],
            timeout=30
        )

        if not synced:
            log.warning("Timeout waiting for channel sync")

        # Subscribe to external data
        self.device_agent.add_subscription(
            "external_commands",
            self.on_external_command
        )

        # Set initial tags
        self.set_tag("app_version", "1.0.0")
        self.set_tag("started_at", time.time())

        log.info(f"Connected to agent: {self.device_agent.agent_id}")

    async def main_loop(self):
        # Check connection status
        if not self.get_is_dda_online():
            log.warning("Lost cloud connection")
            return

        # Publish data
        await self.device_agent.publish_to_channel_async(
            "sensor_data",
            {
                "temperature": self.get_ai(0),
                "timestamp": time.time()
            },
            record_log=True
        )

    async def on_external_command(self, channel: str, aggregate: dict):
        command = aggregate.get("command")
        if command:
            log.info(f"Received command: {command}")
            await self.process_command(command)
```

---

> [!note] Persistent Connection
> The Device Agent Interface maintains a persistent gRPC connection with real-time subscriptions. This is different from the REST-based Cloud API which uses HTTP requests.

See Also:
- [[50-gRPC-Interfaces|gRPC Interfaces Overview]]
- [[52-Platform-Interface|Platform Interface]]
- [[12-Tags-and-Channels|Tags and Channels]]

#device-agent #grpc #cloud #pydoover
