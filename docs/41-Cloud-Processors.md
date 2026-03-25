# Cloud Processors

Cloud Processors are serverless functions that run in the Doover cloud in response to channel messages. They're useful for aggregation, notifications, and operations that don't require a device.

## Overview

Processors are:
- **Event-driven**: Triggered by channel messages
- **Serverless**: Run in the Doover cloud infrastructure
- **Stateless**: Each invocation is independent
- **Time-limited**: Designed for quick operations

## Basic Structure

```python
import logging
from pydoover.cloud.processor import ProcessorBase

class MyProcessor(ProcessorBase):
    def setup(self):
        """Called before processing. Optional."""
        pass

    def process(self):
        """Main processing logic. Required."""
        logging.info("Processing message...")

        # Access the triggering message
        if self.message:
            data = self.message.payload
            logging.info(f"Received: {data}")

        # Perform operations
        self.do_something()

    def close(self):
        """Called after processing. Optional."""
        pass
```

## ProcessorBase Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `agent_id` | `str` | Agent that owns this processor |
| `app_key` | `str` | Application key (usually "app") |
| `access_token` | `str` | Temporary API token |
| `log_channel_id` | `str` | Channel for processor logs |
| `task_id` | `str` | Task channel that triggered this |
| `api` | `Client` | API client for cloud operations |
| `ui_manager` | `UIManager` | UI manager (optional use) |
| `message` | `Message` | Triggering message (may be None) |
| `deployment_config` | `dict` | Agent deployment configuration |
| `package_config` | `dict` | Processor-specific configuration |

## API Client

The `self.api` client is pre-authenticated:

```python
def process(self):
    # Get a channel
    channel = self.api.get_channel_named("sensor_data", self.agent_id)

    # Fetch messages
    messages = channel.fetch_messages(limit=10)

    # Publish data
    channel.publish({"processed": True})
```

## Accessing Channels

### By Name

```python
def process(self):
    # Fetch channel owned by current agent
    channel = self.fetch_channel_named("my_channel")

    # Or use API directly
    channel = self.api.get_channel_named("my_channel", self.agent_id)
```

### By ID

```python
def process(self):
    channel = self.fetch_channel("channel-uuid-here")
```

## Configuration

### Deployment Config

Configuration for the agent:

```python
def process(self):
    # Get all deployment config
    config = self.get_agent_config()

    # Get specific key
    api_key = self.get_agent_config("external_api_key")
```

### Package Config

Processor-specific configuration (from task channel):

```python
def process(self):
    threshold = self.package_config.get("threshold", 100)
```

## The Triggering Message

When a processor is triggered by a channel message:

```python
def process(self):
    if self.message:
        # Message payload
        data = self.message.payload

        # Message metadata
        timestamp = self.message.timestamp
        msg_id = self.message.id
```

## Logging

Logs are automatically captured and published:

```python
import logging

def process(self):
    logging.info("Starting processing")
    logging.debug("Debug info")
    logging.warning("Warning message")
    logging.error("Error occurred")
```

Logs are sent to `self.log_channel_id` when processing completes.

## UI Manager

Processors can update UI state:

```python
from pydoover import ui

def setup(self):
    self.ui_manager.set_children([
        ui.TextVariable("status", "Status")
    ])

def process(self):
    self.ui_manager.update_variable("status", "Processed")
    self.ui_manager.push()
```

## Complete Example

```python
import logging
from pydoover.cloud.processor import ProcessorBase

log = logging.getLogger(__name__)

class DataAggregator(ProcessorBase):
    """Aggregates sensor data and publishes daily summaries."""

    def setup(self):
        self.threshold = self.package_config.get("threshold", 100)

    def process(self):
        log.info(f"Processing data for agent {self.agent_id}")

        # Get sensor channel
        sensor_channel = self.fetch_channel_named("sensor_data")
        messages = sensor_channel.fetch_messages(limit=100)

        if not messages:
            log.info("No messages to process")
            return

        # Aggregate data
        values = [m.payload.get("value", 0) for m in messages]
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)

        log.info(f"Aggregated {len(values)} readings: avg={avg_value:.2f}")

        # Publish summary
        summary_channel = self.fetch_channel_named("daily_summary")
        summary_channel.publish({
            "average": avg_value,
            "maximum": max_value,
            "minimum": min_value,
            "count": len(values),
            "above_threshold": sum(1 for v in values if v > self.threshold)
        })

        # Check for alerts
        if max_value > self.threshold * 2:
            alert_channel = self.fetch_channel_named("significantEvent")
            alert_channel.publish({
                "notification_msg": f"High reading detected: {max_value}"
            })

    def close(self):
        log.info("Processing complete")


# For local testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    processor = DataAggregator(
        agent_id="test-agent-id",
        access_token="test-token",
        api_endpoint="https://my.doover.com",
        package_config={"threshold": 100},
        msg_obj=None,
        task_id="test-task",
        log_channel="test-log",
        agent_settings={"deployment_config": {}}
    )
    processor.execute()
```

## Deployment

### doover_config.json

```json
{
    "my_processor": {
        "display_name": "Data Aggregator",
        "processor_type": "python",
        "entry_point": "my_processor.target:DataAggregator"
    }
}
```

### Task Setup

Tasks trigger processors on channel updates:

```json
{
    "tasks": [
        {
            "name": "hourly_aggregation",
            "processor": "data_aggregator",
            "trigger": "schedule",
            "schedule": "0 * * * *"
        },
        {
            "name": "on_sensor_update",
            "processor": "data_aggregator",
            "trigger": "channel",
            "channel": "sensor_data"
        }
    ]
}
```

## Best Practices

1. **Keep it fast** - Processors should complete quickly
2. **Handle missing data** - `self.message` may be None
3. **Use logging** - Logs are captured automatically
4. **Idempotency** - Design for re-runs on failure
5. **Error handling** - Catch exceptions to allow cleanup

## Limitations

- Processors are stateless between invocations
- Execution time is limited
- Memory and CPU resources are constrained
- No persistent file system access

---

> [!warning] Unsure About Deployment
> The exact deployment process for processors may vary. Consult the Doover documentation or `doover-cli` for current deployment procedures.

See Also:
- [[40-Cloud-API|Cloud API]]
- [[42-Channels-and-Messages|Channels and Messages]]

#processor #cloud #serverless #pydoover
