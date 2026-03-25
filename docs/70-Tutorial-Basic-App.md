# Tutorial: Creating a Basic Application

This tutorial walks through creating a complete Doover application from scratch, covering configuration, UI, and main loop logic.

## Goal

Create a temperature monitoring application that:
- Reads temperature from an analog input
- Displays the value in the UI with color ranges
- Allows setting a threshold via slider
- Triggers an alert when threshold is exceeded

## Step 1: Project Setup

### Create Project Structure

```bash
mkdir temp-monitor
cd temp-monitor
mkdir -p src/temp_monitor
touch src/temp_monitor/__init__.py
touch src/temp_monitor/application.py
touch src/temp_monitor/app_config.py
touch src/temp_monitor/app_ui.py
```

### Create pyproject.toml

```toml
[project]
name = "temp-monitor"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydoover>=0.4.13",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.scripts]
temp-monitor = "temp_monitor:main"
```

## Step 2: Configuration Schema

Create `src/temp_monitor/app_config.py`:

```python
from pydoover import config


class TempMonitorConfig(config.Schema):
    """Configuration schema for the Temperature Monitor application."""

    def __init__(self):
        # Input configuration
        self.analog_input = config.Integer(
            "Analog Input",
            default=0,
            minimum=0,
            maximum=7,
            description="Analog input channel for temperature sensor"
        )

        # Scaling configuration
        self.min_temp = config.Number(
            "Minimum Temperature",
            default=0.0,
            description="Temperature value at 0V (or 4mA)"
        )

        self.max_temp = config.Number(
            "Maximum Temperature",
            default=100.0,
            description="Temperature value at full scale"
        )

        # Alert configuration
        self.alert_enabled = config.Boolean(
            "Alerts Enabled",
            default=True,
            description="Enable high temperature alerts"
        )


def export():
    """Export schema to doover_config.json."""
    import pathlib
    cfg = TempMonitorConfig()
    cfg.export(pathlib.Path("doover_config.json"), "temp_monitor")


if __name__ == "__main__":
    export()
```

## Step 3: UI Elements

Create `src/temp_monitor/app_ui.py`:

```python
from pydoover import ui


def create_ui() -> list[ui.Element]:
    """Create all UI elements for the application."""
    return [
        # Temperature display
        ui.NumericVariable(
            name="temperature",
            display_name="Temperature",
            precision=1,
            ranges=[
                ui.Range("Cold", 0, 15, ui.Colour.blue),
                ui.Range("Normal", 15, 30, ui.Colour.green),
                ui.Range("Warm", 30, 40, ui.Colour.yellow),
                ui.Range("Hot", 40, 100, ui.Colour.red)
            ],
            default_zoom="1h"
        ),

        # Raw ADC value (for debugging)
        ui.NumericVariable(
            name="raw_value",
            display_name="Raw ADC",
            precision=0,
            hidden=True  # Hide from normal view
        ),

        # Status text
        ui.TextVariable(
            name="status",
            display_name="Status"
        ),

        # Threshold slider
        ui.Slider(
            name="threshold",
            display_name="Alert Threshold",
            min_val=0,
            max_val=100,
            step_size=1,
            default=35
        ),

        # Manual refresh button
        ui.Action(
            name="refresh",
            display_name="Refresh Now",
            colour=ui.Colour.blue,
            requires_confirm=False
        ),

        # Alert stream for notifications
        ui.AlertStream()
    ]


def update_ui(manager: ui.UIManager, temp: float, raw: int, status: str):
    """Update UI elements with new values."""
    temp_var = manager.get_element("temperature")
    if temp_var:
        temp_var.current_value = temp

    raw_var = manager.get_element("raw_value")
    if raw_var:
        raw_var.current_value = raw

    status_var = manager.get_element("status")
    if status_var:
        status_var.current_value = status
```

## Step 4: Application Logic

Create `src/temp_monitor/application.py`:

```python
import logging
from datetime import datetime

from pydoover.docker import Application
from pydoover import ui

from .app_config import TempMonitorConfig
from .app_ui import create_ui, update_ui

log = logging.getLogger(__name__)


class TempMonitorApp(Application):
    """Temperature monitoring application."""

    config: TempMonitorConfig  # Type hint for IDE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_alert_time = None
        self._alert_cooldown = 60  # seconds between alerts

    async def setup(self):
        """Initialize the application."""
        log.info("Setting up Temperature Monitor")

        # Set up UI
        self.set_ui(create_ui())

        # Set initial status
        self.set_tag("app_ready", True)

        log.info(f"Monitoring AI{self.config.analog_input.value}")
        log.info(f"Range: {self.config.min_temp.value} - {self.config.max_temp.value}")

    async def main_loop(self):
        """Main processing loop - runs every loop_target_period seconds."""
        # Read raw ADC value
        raw_value = self.get_ai(self.config.analog_input.value)

        # Scale to temperature
        temperature = self._scale_temperature(raw_value)

        # Determine status
        threshold = self.get_command("threshold") or 35
        if temperature > threshold:
            status = "HIGH"
            self.set_ui_status_icon("warning")
            self._check_alert(temperature, threshold)
        else:
            status = "OK"
            self.set_ui_status_icon("ok")

        # Update UI
        update_ui(self.ui_manager, temperature, raw_value, status)

        # Update tags for other apps
        self.set_tag("temperature", temperature)
        self.set_tag("status", status)

        log.debug(f"Temp: {temperature:.1f}C (raw: {raw_value})")

    def _scale_temperature(self, raw_value: int) -> float:
        """Scale raw ADC value to temperature."""
        # Assuming 12-bit ADC (0-4095)
        min_temp = self.config.min_temp.value
        max_temp = self.config.max_temp.value

        ratio = raw_value / 4095.0
        temperature = min_temp + (ratio * (max_temp - min_temp))

        return round(temperature, 1)

    def _check_alert(self, temperature: float, threshold: float):
        """Check if we should send an alert."""
        if not self.config.alert_enabled.value:
            return

        now = datetime.now()
        if self._last_alert_time:
            elapsed = (now - self._last_alert_time).total_seconds()
            if elapsed < self._alert_cooldown:
                return  # Still in cooldown

        # Send alert
        self._last_alert_time = now
        self.ui_manager.send_notification(
            f"High temperature alert: {temperature:.1f}C (threshold: {threshold}C)"
        )
        log.warning(f"Alert sent: {temperature:.1f}C > {threshold}C")

    # UI Callbacks

    @ui.callback("refresh")
    async def on_refresh(self, element, new_value):
        """Handle refresh button press."""
        log.info("Manual refresh requested")
        # The next main_loop iteration will update values

    @ui.callback("threshold")
    async def on_threshold_change(self, element, new_value):
        """Handle threshold slider change."""
        log.info(f"Threshold changed to {new_value}")
        self.set_tag("alert_threshold", new_value)
```

## Step 5: Entry Point

Create `src/temp_monitor/__init__.py`:

```python
from pydoover.docker import run_app

from .application import TempMonitorApp
from .app_config import TempMonitorConfig


def main():
    """Application entry point."""
    run_app(TempMonitorApp(config=TempMonitorConfig()))


if __name__ == "__main__":
    main()
```

## Step 6: Docker Setup

Create `Dockerfile`:

```dockerfile
FROM doover/device_base:latest

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN uv sync --no-dev

ENTRYPOINT ["uv", "run", "temp-monitor"]
```

Create `simulators/docker-compose.yml`:

```yaml
version: '3.8'

services:
  device_agent:
    image: doover/device_agent:latest
    environment:
      - AGENT_ID=${AGENT_ID:-test-agent}
    ports:
      - "50051:50051"

  platform:
    image: doover/platform_simulator:latest
    ports:
      - "50053:50053"

  temp_monitor:
    build:
      context: ..
      dockerfile: Dockerfile
    environment:
      - APP_KEY=temp_monitor
      - DDA_URI=device_agent:50051
      - PLT_URI=platform:50053
      - DEBUG=1
    depends_on:
      - device_agent
      - platform
```

## Step 7: Export Configuration

```bash
# Generate doover_config.json
cd src/temp_monitor
python app_config.py
```

This creates `doover_config.json` with your schema.

## Step 8: Run the Application

```bash
# Navigate to simulators directory
cd simulators

# Run with docker compose
docker compose up --build
```

## Testing

### Manual Testing

1. Open the Doover web interface
2. Navigate to your agent
3. Find the Temperature Monitor app
4. Observe temperature readings
5. Adjust the threshold slider
6. Verify alerts trigger correctly

### Unit Testing

Create `tests/test_application.py`:

```python
import pytest
import asyncio
from temp_monitor.application import TempMonitorApp
from temp_monitor.app_config import TempMonitorConfig


@pytest.fixture
def app():
    return TempMonitorApp(
        config=TempMonitorConfig(),
        test_mode=True
    )


@pytest.mark.asyncio
async def test_scale_temperature(app):
    # Test scaling at different points
    assert app._scale_temperature(0) == 0.0
    assert app._scale_temperature(4095) == 100.0
    assert app._scale_temperature(2048) == pytest.approx(50.0, rel=0.1)


@pytest.mark.asyncio
async def test_setup(app):
    # Run setup
    await app.setup()
    assert app.is_ready
```

Run tests:
```bash
pytest tests/
```

## Next Steps

- Add data logging to a channel
- Create a Multiplot for historical data
- Add multiple sensor support
- Implement a state machine for different modes

---

See Also:
- [[10-Application-Framework|Application Framework]]
- [[20-Configuration-System|Configuration System]]
- [[30-UI-System-Overview|UI System]]
- [[73-Example-Patterns|Common Patterns]]

#tutorial #example #pydoover #getting-started
