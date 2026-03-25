# Cloud API

The pydoover Cloud API provides a REST client for interacting with the Doover cloud platform. It's primarily used for cloud processors, CLI tools, and server-side integrations.

## Overview

The Cloud API (`pydoover.cloud.api`) provides:
- Authentication and session management
- Agent and channel operations
- Message publishing and retrieval
- Application management
- Tunnel management

## Client Setup

### Basic Authentication

```python
from pydoover.cloud.api import Client

# Using username/password
client = Client(
    username="user@example.com",
    password="password",
    base_url="https://my.doover.com"
)

# Using token
client = Client(
    token="your-api-token",
    base_url="https://my.doover.com"
)

# Using config profile (from doover login)
client = Client(config_profile="default")
```

### Client Options

```python
client = Client(
    username=None,           # Username for login
    password=None,           # Password for login
    token=None,              # Pre-existing token
    token_expires=None,      # Token expiration datetime
    base_url="https://my.doover.dev",
    agent_id=None,           # Default agent ID
    verify=True,             # Verify SSL certificates
    login_callback=None,     # Called after login
    config_profile="default",# Config profile name
    debug=False              # Enable debug logging
)
```

## Agents

Agents represent devices or cloud processors.

### Get Agent

```python
# Get a specific agent
agent = client.get_agent("agent-uuid-here")

print(agent.id)
print(agent.name)
print(agent.status)
```

### List Agents

```python
# Get all accessible agents
agents = client.get_agent_list()

for agent in agents:
    print(f"{agent.name}: {agent.id}")
```

## Channels

Channels are message queues for communication.

### Get Channel

```python
# By channel ID
channel = client.get_channel("channel-uuid")

# By name and agent
channel = client.get_channel_named("ui_state", agent_id)
```

### Create Channel

```python
# Create a new channel
channel = client.create_channel("my_channel", agent_id)

# Create a processor channel (prefix with #)
processor = client.create_processor("data_processor", agent_id)

# Create a task channel (prefix with !)
task = client.create_task("my_task", agent_id, processor_id)
```

### Channel Properties

```python
channel = client.get_channel(channel_id)

print(channel.id)
print(channel.name)
print(channel.agent_id)
```

## Messages

### Publish Messages

```python
# Publish to channel by ID
client.publish_to_channel(
    channel_id,
    data={"temperature": 25.5},
    save_log=True,           # Save to message log
    log_aggregate=False,     # Merge with aggregate
    override_aggregate=False,# Replace aggregate entirely
    timestamp=None           # Custom timestamp
)

# Publish to channel by name
client.publish_to_channel_name(
    agent_id,
    "my_channel",
    data={"status": "running"},
    save_log=True
)
```

### Retrieve Messages

```python
# Get messages from channel
messages = client.get_channel_messages(channel_id, num_messages=10)

for msg in messages:
    print(f"{msg.timestamp}: {msg.payload}")

# Get messages in time window
from datetime import datetime, timedelta

end = datetime.now()
start = end - timedelta(hours=24)

messages = client.get_channel_messages_in_window(channel_id, start, end)

# Get single message
message = client.get_message(channel_id, message_id)
```

### Channel Aggregate

The aggregate is the merged state of all messages:

```python
# Get aggregate (via Channel object)
channel = client.get_channel_named("ui_state", agent_id)
aggregate = channel.fetch_aggregate()

# Aggregate is a dict of merged message payloads
print(aggregate)
```

## Subscriptions

### Subscribe Task to Channel

```python
# Subscribe a task to receive channel messages
client.subscribe_to_channel(channel_id, task_id)

# Unsubscribe
client.unsubscribe_from_channel(channel_id, task_id)
```

## Applications

Manage Doover applications:

```python
from pydoover.cloud.api import Application

# Get all applications
apps = client.get_applications()

# Get specific application
app = client.get_application("app-key")

# Create application
new_app = Application(
    key="my-new-app",
    name="My New App",
    app_type="docker",
    visibility="private"
)
app_key = client.create_application(new_app)

# Update application
client.update_application(app)
```

## Tunnels

Manage SSH tunnels to devices:

```python
# Get tunnels for agent
tunnels = client.get_tunnels(agent_id)

# Create tunnel
tunnel = client.create_tunnel(
    agent_id,
    name="SSH Access",
    local_port=22,
    tunnel_type="ssh"
)

# Activate/deactivate
client.activate_tunnel(tunnel_id)
client.deactivate_tunnel(tunnel_id)

# Delete tunnel
client.delete_tunnel(tunnel_id)
```

## Authentication

### Login Flow

```python
# Manual login
client.login()  # Uses username/password

# Token refresh (automatic on expiry)
token, expires_at, agent_id = client.fetch_token()
```

### Config Manager

The `ConfigManager` handles credential storage:

```python
from pydoover.cloud.api import ConfigManager

config_manager = ConfigManager("default")
config_manager.read()

# Access current profile
profile = config_manager.current
print(profile.username)
print(profile.token)
print(profile.agent_id)
```

## Exceptions

```python
from pydoover.cloud.api import NotFound, Forbidden, HTTPException

try:
    channel = client.get_channel("invalid-id")
except NotFound:
    print("Channel not found")
except Forbidden:
    print("Access denied")
except HTTPException as e:
    print(f"HTTP error: {e}")
```

## Channel Objects

### Channel

Basic data channel:

```python
channel = client.get_channel_named("sensor_data", agent_id)

# Publish
channel.publish({"temp": 25.5}, save_log=True)

# Get messages
messages = channel.fetch_messages(limit=10)

# Get aggregate
aggregate = channel.fetch_aggregate()
```

### Task

Task channel (prefix `!`):

```python
task = client.get_channel_named("!my_task", agent_id)

# Task-specific operations
task.subscribe_to(channel_id)  # Subscribe to another channel
```

### Processor

Processor channel (prefix `#`):

```python
processor = client.get_channel_named("#my_processor", agent_id)
```

## Complete Example

```python
from pydoover.cloud.api import Client
from datetime import datetime, timedelta

# Initialize client
client = Client(config_profile="default")

# Get agent
agent = client.get_agent(client.agent_id)
print(f"Connected to: {agent.name}")

# Get channel
ui_state = client.get_channel_named("ui_state", agent.id)

# Get current state
current_state = ui_state.fetch_aggregate()
print(f"Current state: {current_state}")

# Get historical data
messages = client.get_channel_messages_in_window(
    ui_state.id,
    datetime.now() - timedelta(hours=24),
    datetime.now()
)

print(f"Found {len(messages)} messages in last 24 hours")

# Publish update
client.publish_to_channel(
    ui_state.id,
    {"state": {"children": {"my_app": {"status": "updated"}}}},
    save_log=True
)
```

---

> [!note] Device Applications
> Device applications typically use `DeviceAgentInterface` instead of the REST `Client`. The Cloud API is primarily for cloud processors, CLI tools, and external integrations.

See Also:
- [[41-Cloud-Processors|Cloud Processors]]
- [[42-Channels-and-Messages|Channels and Messages]]
- [[51-Device-Agent-Interface|Device Agent Interface]]

#cloud #api #pydoover #rest
