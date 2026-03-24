# Tags and Channels

Tags and Channels are the primary communication mechanisms in Doover for sharing data between applications and with the cloud.

## Overview

| Feature | Tags | Channels |
|---------|------|----------|
| Purpose | Key-value state | Message queues |
| Data | Single values | Complex objects |
| History | Current value only | Message log |
| Scope | App-specific or global | Named queues |
| Use case | State sharing | Data streaming, events |

## Tags

Tags are key-value pairs for sharing state between applications.

### Setting Tags

```python
# Set a tag for the current application
self.set_tag("temperature", 25.5)
self.set_tag("status", "running")
self.set_tag("last_update", time.time())

# Set multiple tags atomically
self.set_tags({
    "temp1": 25.5,
    "temp2": 26.3,
    "temp3": 24.8
})

# Set a tag for another application
self.set_tag("external_value", 100, app_key="other-app")

# Async versions
await self.set_tag_async("temperature", 25.5)
await self.set_tags_async({"temp1": 25.5, "temp2": 26.3})
```

### Getting Tags

```python
# Get tag from current application
temp = self.get_tag("temperature")

# Get tag with default value
temp = self.get_tag("temperature", default=0.0)

# Get tag from another application
value = self.get_tag("pump_speed", app_key="pump-controller")

# Get all tags for current app
all_tags = self.get_all_tags()
```

### Global Tags

Global tags are shared across all applications on the agent:

```python
# Set a global tag
self.set_global_tag("system_mode", "auto")
self.set_global_tag("emergency_stop", False)

# Async version
await self.set_global_tag_async("system_mode", "auto")

# Get a global tag
mode = self.get_global_tag("system_mode")
mode = self.get_global_tag("system_mode", default="manual")
```

### Subscribing to Tags

React to tag changes from other applications:

```python
async def setup(self):
    # Subscribe to own app's tag
    self.subscribe_to_tag("external_trigger", self.on_trigger)

    # Subscribe to another app's tag
    self.subscribe_to_tag(
        "pump_status",
        self.on_pump_status,
        app_key="pump-controller"
    )

    # Subscribe to global tag
    self.subscribe_to_global_tag("system_mode", self.on_mode_change)

async def on_trigger(self, tag_key: str, new_value):
    log.info(f"Trigger received: {new_value}")

async def on_pump_status(self, tag_key: str, new_value):
    log.info(f"Pump status changed to: {new_value}")

async def on_mode_change(self, tag_key: str, new_value):
    log.info(f"System mode changed to: {new_value}")
```

### Tag Best Practices

1. **Use descriptive names**: `temperature_celsius` not `temp`
2. **Document tag contracts**: Other apps depend on your tags
3. **Set reasonable update rates**: Don't spam tag updates
4. **Use types consistently**: Always number or always string

## Channels

Channels are message queues for publishing and subscribing to data streams.

### Channel Types

| Prefix | Type | Purpose |
|--------|------|---------|
| (none) | Data | General data channels |
| `#` | Processor | Cloud processor channels |
| `!` | Task | Triggered task channels |

### Standard Channels

Common channels used by the framework:

| Channel | Purpose |
|---------|---------|
| `ui_state` | UI element state |
| `ui_cmds` | UI command values |
| `deployment_config` | Application configuration |
| `significantEvent` | Alert notifications |
| `activity_logs` | Activity log entries |

### Publishing to Channels

```python
# Basic publish
self.publish_to_channel("sensor_data", {
    "temperature": 25.5,
    "humidity": 60,
    "timestamp": time.time()
})

# With options
self.publish_to_channel(
    "sensor_data",
    {"temperature": 25.5},
    record_log=True,      # Save to message history
    max_age=3600          # Cache for 1 hour
)

# Async version
await self.publish_to_channel_async("sensor_data", {"value": 100})
```

### Subscribing to Channels

```python
async def setup(self):
    # Subscribe to channel
    self.subscribe_to_channel("external_data", self.on_data_received)

async def on_data_received(self, channel_name: str, data: dict):
    log.info(f"Received on {channel_name}: {data}")
    temperature = data.get("temperature")
    if temperature:
        self.process_temperature(temperature)
```

### Channel Aggregates

The aggregate is the merged state of all messages:

```python
# Get current aggregate (last known state)
aggregate = self.get_channel_aggregate("sensor_data")

# Aggregate merges all message payloads
# If messages were: {"a": 1}, {"b": 2}, {"a": 3}
# Aggregate is: {"a": 3, "b": 2}
```

### Publishing with Logging

```python
# Always log (for historical data)
self.publish_to_channel(
    "temperature_log",
    {"value": temp, "timestamp": time.time()},
    record_log=True
)

# Don't log (for transient state)
self.publish_to_channel(
    "current_status",
    {"status": "running"},
    record_log=False
)
```

## UI Channels

The UI system uses special channels automatically:

### ui_state Channel

Published by your app to update UI element values:

```python
# Framework handles this, but internally:
# {
#     "state": {
#         "children": {
#             "your_app_key": {
#                 "temperature": {"currentValue": 25.5},
#                 "status": {"currentValue": "OK"}
#             }
#         }
#     }
# }
```

### ui_cmds Channel

Contains user interaction values:

```python
# Framework handles this, but aggregate looks like:
# {
#     "cmds": {
#         "your_app_key_mode": "auto",
#         "your_app_key_threshold": 50
#     }
# }
```

## Notifications

Send user-visible notifications:

```python
# Send notification (appears in UI alert banner)
self.ui_manager.send_notification("High temperature detected!")

# Async version
await self.ui_manager.send_notification_async("Pump started")

# With activity log
self.ui_manager.send_notification(
    "Configuration updated",
    record_activity=True
)
```

### Activity Logs

Record activities without notifications:

```python
await self.ui_manager.record_activity_async("Sensor calibration started")
```

## Communication Patterns

### State Sharing (Tags)

For simple state that other apps need to read:

```python
# Producer app
class SensorApp(Application):
    async def main_loop(self):
        temp = self.read_sensor()
        self.set_tag("temperature", temp)
        self.set_tag("sensor_healthy", True)
```

```python
# Consumer app
class DisplayApp(Application):
    async def setup(self):
        self.subscribe_to_tag("temperature", self.on_temp, app_key="sensor-app")

    async def main_loop(self):
        # Or poll directly
        temp = self.get_tag("temperature", app_key="sensor-app")
```

### Data Streaming (Channels)

For complex data or historical logging:

```python
# Producer app
class DataLogger(Application):
    async def main_loop(self):
        readings = self.collect_all_readings()
        self.publish_to_channel("readings", {
            "timestamp": time.time(),
            "readings": readings
        }, record_log=True)
```

```python
# Consumer app
class DataProcessor(Application):
    async def setup(self):
        self.subscribe_to_channel("readings", self.process_readings)

    async def process_readings(self, channel, data):
        for reading in data["readings"]:
            self.analyze(reading)
```

### Event Notification (Channels)

For events that trigger actions:

```python
# Event publisher
class AlarmApp(Application):
    async def check_alarms(self):
        if self.high_temp_detected():
            self.publish_to_channel("alarms", {
                "type": "high_temperature",
                "value": self.current_temp,
                "timestamp": time.time()
            })
```

```python
# Event handler
class ResponseApp(Application):
    async def setup(self):
        self.subscribe_to_channel("alarms", self.handle_alarm)

    async def handle_alarm(self, channel, data):
        if data["type"] == "high_temperature":
            self.activate_cooling()
```

### Request/Response Pattern

For inter-app commands:

```python
# Command sender
class ControlApp(Application):
    def request_pump_start(self):
        self.set_tag("pump_command", {
            "action": "start",
            "request_id": uuid.uuid4().hex,
            "timestamp": time.time()
        }, app_key="pump-controller")
```

```python
# Command handler
class PumpApp(Application):
    async def setup(self):
        self.subscribe_to_tag("pump_command", self.on_command)

    async def on_command(self, tag_key, command):
        if command["action"] == "start":
            self.start_pump()
            self.set_tag("pump_response", {
                "request_id": command["request_id"],
                "status": "started"
            })
```

## Cloud Processor Integration

Cloud processors can publish to channels:

```python
# In a ProcessorBase subclass
def process(self):
    # Fetch data
    channel = self.fetch_channel_named("sensor_data")
    messages = channel.fetch_messages(limit=100)

    # Process and publish result
    result_channel = self.fetch_channel_named("processed_data")
    result_channel.publish({
        "summary": self.calculate_summary(messages),
        "processed_at": time.time()
    })
```

---

See Also:
- [[10-Application-Framework|Application Framework]]
- [[40-Cloud-API|Cloud API]]
- [[42-Channels-and-Messages|Channels and Messages Reference]]

#tags #channels #communication #pydoover
