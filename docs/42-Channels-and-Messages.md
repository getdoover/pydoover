# Channels and Messages Reference

Detailed reference for the channel and message system in Doover.

## Channel Types

| Prefix | Type | Purpose |
|--------|------|---------|
| (none) | Data | General data channels |
| `#` | Processor | Cloud processor definitions |
| `!` | Task | Triggered task channels |

## Standard System Channels

| Channel | Purpose | Owner |
|---------|---------|-------|
| `ui_state` | UI element state | Application |
| `ui_cmds` | UI command values | Application |
| `deployment_config` | Configuration | Agent |
| `significantEvent` | Alert notifications | Application |
| `activity_logs` | Activity log entries | Application |

## Channel Object (Cloud API)

When using the Cloud API client:

```python
from pydoover.cloud.api import Client

client = Client(config_profile="default")

# Get channel by ID
channel = client.get_channel("channel-uuid")

# Get channel by name
channel = client.get_channel_named("my_channel", agent_id)
```

### Channel Properties

```python
channel.id          # UUID
channel.name        # Channel name
channel.agent_id    # Owning agent
```

### Channel Methods

```python
# Publish data
channel.publish(
    data={"key": "value"},
    save_log=True,           # Save to message log
    log_aggregate=False,     # Merge with aggregate
    override_aggregate=False,# Replace aggregate
    timestamp=None           # Custom timestamp
)

# Fetch messages
messages = channel.fetch_messages(limit=10)

# Fetch aggregate (merged state)
aggregate = channel.fetch_aggregate()
```

## Message Object

```python
message.id          # Message UUID
message.payload     # Message data (dict)
message.timestamp   # When published
```

## Publishing Messages

### From Device Application

```python
# Simple publish
self.publish_to_channel("sensor_data", {"temp": 25.5})

# With options
self.publish_to_channel(
    "sensor_data",
    {"temp": 25.5, "humidity": 60},
    record_log=True,      # Save to history
    max_age=3600          # Cache seconds
)

# Async
await self.publish_to_channel_async("sensor_data", {"temp": 25.5})
```

### From Cloud API

```python
# By channel ID
client.publish_to_channel(
    channel_id,
    data={"value": 100},
    save_log=True
)

# By channel name
client.publish_to_channel_name(
    agent_id,
    "my_channel",
    data={"value": 100}
)

# Via channel object
channel = client.get_channel_named("my_channel", agent_id)
channel.publish({"value": 100})
```

### From Cloud Processor

```python
def process(self):
    channel = self.fetch_channel_named("output")
    channel.publish({
        "processed": True,
        "timestamp": time.time()
    })
```

## Message Logging

### Log to History

```python
self.publish_to_channel(
    "sensor_data",
    {"temp": 25.5},
    record_log=True  # Saved to message history
)
```

### Don't Log (Transient State)

```python
self.publish_to_channel(
    "current_status",
    {"status": "processing"},
    record_log=False  # Only updates aggregate
)
```

## Aggregates

The aggregate is the merged state of all published messages.

### How Aggregates Work

```python
# Publish sequence:
channel.publish({"a": 1})
channel.publish({"b": 2})
channel.publish({"a": 3})

# Aggregate becomes:
{"a": 3, "b": 2}
```

### Getting Aggregates

```python
# Device application
aggregate = self.get_channel_aggregate("my_channel")

# Cloud API
channel = client.get_channel_named("my_channel", agent_id)
aggregate = channel.fetch_aggregate()
```

### Override Aggregate

Replace entire aggregate instead of merging:

```python
# Cloud API
channel.publish(
    {"new_state": True},
    override_aggregate=True
)
```

## Subscribing to Channels

### Device Application

```python
async def setup(self):
    self.subscribe_to_channel("external_data", self.on_data)

async def on_data(self, channel_name: str, data: dict):
    log.info(f"Received: {data}")
```

### Internal Mechanism

For persistent connections (Device Agent):

```python
# Low-level subscription
self.device_agent.add_subscription("channel_name", callback)
```

## Retrieving Messages

### Get Recent Messages

```python
# Cloud API
messages = client.get_channel_messages(channel_id, num_messages=10)

for msg in messages:
    print(f"{msg.timestamp}: {msg.payload}")
```

### Get Messages in Time Window

```python
from datetime import datetime, timedelta

end = datetime.now()
start = end - timedelta(hours=24)

messages = client.get_channel_messages_in_window(
    channel_id,
    start,
    end
)
```

### Get Single Message

```python
message = client.get_message(channel_id, message_id)
```

## Creating Channels

### Cloud API

```python
# Data channel
channel = client.create_channel("my_data", agent_id)

# Processor channel (prefix #)
processor = client.create_processor("data_processor", agent_id)

# Task channel (prefix !)
task = client.create_task("my_task", agent_id, processor_id)
```

## Task Subscriptions

Tasks can subscribe to channels to receive triggers:

```python
# Subscribe task to channel
client.subscribe_to_channel(channel_id, task_id)

# Unsubscribe
client.unsubscribe_from_channel(channel_id, task_id)
```

## Channel Patterns

### Data Logging

```python
async def main_loop(self):
    data = {
        "temperature": self.get_ai(0),
        "humidity": self.get_ai(1),
        "timestamp": time.time()
    }

    self.publish_to_channel(
        "sensor_log",
        data,
        record_log=True  # Keep history
    )
```

### State Synchronization

```python
async def main_loop(self):
    # Update state (no history needed)
    self.publish_to_channel(
        "current_state",
        {"status": "running", "progress": 75},
        record_log=False
    )
```

### Event Notification

```python
def on_alarm(self, alarm_type):
    self.publish_to_channel(
        "alarms",
        {
            "type": alarm_type,
            "timestamp": time.time(),
            "acknowledged": False
        },
        record_log=True
    )
```

### Inter-App Communication

```python
# App A publishes
self.publish_to_channel("app_a_output", {"command": "start"})

# App B subscribes
async def setup(self):
    self.subscribe_to_channel("app_a_output", self.on_command)

async def on_command(self, channel, data):
    if data.get("command") == "start":
        await self.start()
```

## Notifications

### Send Notification

```python
# Via UIManager
self.ui_manager.send_notification("High temperature detected!")

# Async
await self.ui_manager.send_notification_async("Process complete")

# With activity log
self.ui_manager.send_notification(
    "Configuration updated",
    record_activity=True
)
```

### Direct to significantEvent Channel

```python
self.ui_manager.publish_to_channel(
    "significantEvent",
    {"notification_msg": "Alert message here"},
    record_log=True,
    max_age=1
)
```

### Activity Logs

```python
await self.ui_manager.record_activity_async("User logged in")
```

## Max Age

The `max_age` parameter controls caching:

```python
self.publish_to_channel(
    "fast_update",
    data,
    max_age=1     # Publish immediately (1 second)
)

self.publish_to_channel(
    "slow_update",
    data,
    max_age=3600  # Cache for 1 hour
)

self.publish_to_channel(
    "force_immediate",
    data,
    max_age=-1    # Force immediate update
)
```

## Error Handling

```python
try:
    self.publish_to_channel("my_channel", data)
except Exception as e:
    log.error(f"Failed to publish: {e}")
```

## Complete Example

```python
from pydoover.docker import Application
import time

class DataPublisher(Application):
    async def setup(self):
        # Subscribe to incoming commands
        self.subscribe_to_channel("commands", self.on_command)

    async def main_loop(self):
        # Read sensor data
        temp = self.get_ai(0)
        humidity = self.get_ai(1)

        # Publish to data log (with history)
        self.publish_to_channel(
            "sensor_data",
            {
                "temperature": temp,
                "humidity": humidity,
                "timestamp": time.time()
            },
            record_log=True
        )

        # Update current state (no history)
        self.publish_to_channel(
            "current_readings",
            {"temp": temp, "humidity": humidity},
            record_log=False
        )

        # Check for alarm conditions
        if temp > 50:
            await self.ui_manager.send_notification_async(
                f"High temperature: {temp}°C"
            )

    async def on_command(self, channel: str, data: dict):
        cmd = data.get("command")
        log.info(f"Received command: {cmd}")

        if cmd == "reset":
            self.publish_to_channel(
                "command_response",
                {"status": "reset_complete", "timestamp": time.time()}
            )
```

---

See Also:
- [[12-Tags-and-Channels|Tags and Channels Overview]]
- [[40-Cloud-API|Cloud API]]
- [[41-Cloud-Processors|Cloud Processors]]

#channels #messages #communication #reference #pydoover
