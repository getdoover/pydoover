# Getting Started with PyDoover

This guide walks you through creating your first Doover application using the `pydoover` package.

## Prerequisites

- Python 3.11 or higher
- `uv` package manager (recommended) or `pip`
- Docker (for running applications locally)
- Doover CLI (`doover-cli`)

## Installation

```bash
# Install pydoover with uv
uv add pydoover

# Or with pip
pip install -U pydoover

# For gRPC support (required for device applications)
pip install -U pydoover[grpc]
```

## Creating Your First Application

### Option 1: Using the Doover CLI (Recommended)

```bash
# Create a new application from the template
doover app create my-first-app

# Navigate to the app directory
cd my-first-app

# Run the application locally
doover app run
```

### Option 2: Manual Setup

Create a basic application structure:

```
my-app/
├── src/my_app/
│   ├── __init__.py
│   ├── application.py
│   └── app_config.py
├── pyproject.toml
└── doover_config.json
```

## Basic Application Structure

### 1. Configuration Schema (`app_config.py`)

```python
from pydoover import config

class MyAppConfig(config.Schema):
    def __init__(self):
        self.sample_setting = config.Integer(
            "Sample Setting",
            default=10,
            minimum=0,
            maximum=100,
            description="A sample configuration value"
        )

        self.enabled = config.Boolean(
            "Feature Enabled",
            default=True,
            description="Enable or disable the feature"
        )
```

### 2. Application Class (`application.py`)

```python
from pydoover.docker import Application, run_app
from .app_config import MyAppConfig

class MyApplication(Application):
    config: MyAppConfig  # Type hint for IDE support

    def setup(self):
        """Called once when the application starts."""
        print(f"Starting with setting: {self.config.sample_setting.value}")

        # Set up UI elements
        self.set_ui_elements([
            # Your UI elements here
        ])

    def main_loop(self):
        """Called repeatedly at loop_target_period intervals."""
        if self.config.enabled.value:
            # Your main logic here
            pass

# Entry point
def main():
    run_app(MyApplication(config=MyAppConfig()))
```

### 3. Entry Point (`__init__.py`)

```python
from .application import main

if __name__ == "__main__":
    main()
```

## Running Your Application

### Local Development with Docker Compose

Create a `simulators/docker-compose.yml`:

```yaml
version: '3.8'
services:
  device_agent:
    image: doover/device_agent:latest
    environment:
      - AGENT_ID=${AGENT_ID}
    ports:
      - "50051:50051"

  my_app:
    build: ..
    environment:
      - APP_KEY=my_app
      - DDA_URI=device_agent:50051
    depends_on:
      - device_agent
```

Run with:
```bash
docker compose up --build
```

### Using Doover CLI

```bash
doover app run
```

## Key Concepts

### Application Lifecycle

1. **Initialization**: `__init__` is called with config
2. **Setup**: `setup()` runs once after connection to device agent
3. **Main Loop**: `main_loop()` runs repeatedly every `loop_target_period` seconds
4. **Shutdown**: `close()` is called when application exits

### Communication Channels

- **Tags**: Key-value pairs for sharing state between apps
- **Channels**: Message queues for publishing/subscribing to data
- **UI State**: Synchronized state for the user interface

### Interfaces

| Interface | Purpose | Port |
|-----------|---------|------|
| Device Agent | Cloud sync, channels | 50051 |
| Platform | Digital/Analog I/O | 50053 |
| Modbus | Modbus RTU/TCP | 50054 |

## Next Steps

- [[10-Application-Framework|Deep dive into the Application Framework]]
- [[20-Configuration-System|Learn about Configuration Schemas]]
- [[30-UI-System-Overview|Build User Interfaces]]
- [[70-Tutorial-Basic-App|Complete Tutorial: Building a Full App]]

## Common Issues

### "DDA not available" Error
The Device Agent isn't running or is unreachable. Check:
- Docker compose is running
- `DDA_URI` environment variable is correct
- Network connectivity between containers

### "Config not found" Error
The deployment config hasn't been received. Ensure:
- Agent is connected to cloud
- App key matches configuration

---

#getting-started #tutorial #pydoover
