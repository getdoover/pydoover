# Tutorial: Modbus Communication

This tutorial covers integrating Modbus devices with your Doover application.

## Goal

Create an application that:
- Reads Modbus registers from a device
- Decodes various data types
- Writes setpoints to the device
- Displays data in the UI
- Handles communication errors

## Step 1: Configuration

Create `app_config.py`:

```python
from pydoover import config

class ModbusAppConfig(config.Schema):
    def __init__(self):
        # Modbus settings
        self.slave_id = config.Integer(
            "Modbus Slave ID",
            default=1,
            minimum=1,
            maximum=247,
            description="Modbus device address"
        )

        self.bus_id = config.String(
            "Bus ID",
            default="default",
            description="Modbus bus identifier"
        )

        # Register addresses (device-specific)
        self.temp_register = config.Integer(
            "Temperature Register",
            default=0,
            description="Holding register for temperature"
        )

        self.setpoint_register = config.Integer(
            "Setpoint Register",
            default=100,
            description="Holding register for setpoint"
        )

        # Scaling
        self.temp_scale = config.Number(
            "Temperature Scale",
            default=0.1,
            description="Multiply register value by this"
        )
```

## Step 2: Modbus Data Helpers

Create `modbus_helpers.py`:

```python
import struct
from typing import List, Tuple

def to_signed16(value: int) -> int:
    """Convert unsigned 16-bit to signed."""
    if value >= 0x8000:
        return value - 0x10000
    return value

def to_unsigned16(value: int) -> int:
    """Convert signed to unsigned 16-bit."""
    if value < 0:
        return value + 0x10000
    return value

def to_uint32(high: int, low: int) -> int:
    """Combine two 16-bit registers to unsigned 32-bit."""
    return (high << 16) | low

def to_int32(high: int, low: int) -> int:
    """Combine two 16-bit registers to signed 32-bit."""
    value = (high << 16) | low
    if value >= 0x80000000:
        return value - 0x100000000
    return value

def from_uint32(value: int) -> Tuple[int, int]:
    """Split 32-bit to two 16-bit registers (high, low)."""
    return (value >> 16) & 0xFFFF, value & 0xFFFF

def to_float32(high: int, low: int) -> float:
    """Combine two 16-bit registers to 32-bit float."""
    packed = struct.pack('>HH', high, low)
    return struct.unpack('>f', packed)[0]

def from_float32(value: float) -> Tuple[int, int]:
    """Split float to two 16-bit registers."""
    packed = struct.pack('>f', value)
    high, low = struct.unpack('>HH', packed)
    return high, low

def scale_value(raw: int, scale: float, offset: float = 0) -> float:
    """Scale a raw register value."""
    return (raw * scale) + offset

def unscale_value(value: float, scale: float, offset: float = 0) -> int:
    """Unscale a value back to register."""
    return int((value - offset) / scale)
```

## Step 3: UI Definition

Create `app_ui.py`:

```python
from pydoover import ui

def create_ui() -> list[ui.Element]:
    return [
        # Status
        ui.TextVariable("comm_status", "Communication"),

        # Readings
        ui.Submodule(
            "readings", "Device Readings",
            children=[
                ui.NumericVariable(
                    "temperature",
                    "Temperature (°C)",
                    precision=1,
                    ranges=[
                        ui.Range("Low", -20, 10, ui.Colour.blue),
                        ui.Range("Normal", 10, 40, ui.Colour.green),
                        ui.Range("High", 40, 100, ui.Colour.red)
                    ]
                ),
                ui.NumericVariable("raw_temp", "Raw Value", precision=0),
                ui.NumericVariable("setpoint", "Current Setpoint", precision=1)
            ]
        ),

        # Controls
        ui.Submodule(
            "controls", "Controls",
            children=[
                ui.Slider(
                    "new_setpoint",
                    "Temperature Setpoint",
                    min_val=0,
                    max_val=100,
                    step_size=1,
                    default=25
                ),
                ui.Action(
                    "write_setpoint",
                    "Write Setpoint",
                    colour=ui.Colour.blue,
                    requires_confirm=True
                ),
                ui.Action(
                    "read_now",
                    "Read Now",
                    colour=ui.Colour.green,
                    requires_confirm=False
                )
            ]
        ),

        # Diagnostics (collapsed)
        ui.Submodule(
            "diagnostics", "Diagnostics",
            is_collapsed=True,
            children=[
                ui.NumericVariable("read_count", "Read Count"),
                ui.NumericVariable("error_count", "Error Count"),
                ui.TextVariable("last_error", "Last Error")
            ]
        ),

        ui.AlertStream()
    ]
```

## Step 4: Application

Create `application.py`:

```python
import logging
from datetime import datetime

from pydoover.docker import Application
from pydoover import ui

from .app_config import ModbusAppConfig
from .app_ui import create_ui
from .modbus_helpers import to_signed16, scale_value, unscale_value

log = logging.getLogger(__name__)

class ModbusApp(Application):
    config: ModbusAppConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.read_count = 0
        self.error_count = 0
        self.last_error = None

    async def setup(self):
        self.set_ui(create_ui())

        # Set up subscription for continuous polling
        self.add_new_modbus_read_subscription(
            address=self.config.temp_register.value,
            count=5,  # Read 5 registers starting at temp_register
            register_type="holding",
            callback=self.on_register_update,
            poll_secs=1.0,
            modbus_id=self.config.slave_id.value,
            bus_id=self.config.bus_id.value
        )

        log.info(f"Monitoring Modbus device {self.config.slave_id.value}")
        self.update_status("Connected")

    async def main_loop(self):
        # Update diagnostic counters
        self.ui_manager.update_variable("read_count", self.read_count)
        self.ui_manager.update_variable("error_count", self.error_count)

        if self.last_error:
            self.ui_manager.get_element("last_error").current_value = self.last_error
        else:
            self.ui_manager.get_element("last_error").current_value = "None"

    async def on_register_update(
        self,
        bus_id: str,
        modbus_id: int,
        address: int,
        values: list[int]
    ):
        """Called when subscribed registers are read."""
        self.read_count += 1

        try:
            # Parse temperature (register 0, signed, scaled by 0.1)
            raw_temp = values[0]
            signed_temp = to_signed16(raw_temp)
            temperature = scale_value(signed_temp, self.config.temp_scale.value)

            # Parse setpoint (assume register offset from temp)
            setpoint_offset = self.config.setpoint_register.value - address
            if 0 <= setpoint_offset < len(values):
                raw_setpoint = values[setpoint_offset]
                setpoint = scale_value(raw_setpoint, self.config.temp_scale.value)
            else:
                setpoint = None

            # Update UI
            self.ui_manager.update_variable("temperature", temperature)
            self.ui_manager.update_variable("raw_temp", raw_temp)
            if setpoint is not None:
                self.ui_manager.update_variable("setpoint", setpoint)

            # Update tags
            self.set_tags({
                "temperature": temperature,
                "raw_temperature": raw_temp
            })

            self.update_status("OK")
            self.last_error = None

        except Exception as e:
            self.handle_error(f"Parse error: {e}")

    def update_status(self, status: str):
        """Update communication status display."""
        self.ui_manager.get_element("comm_status").current_value = status

        if status == "OK":
            self.set_ui_status_icon("ok")
        elif status == "Error":
            self.set_ui_status_icon("error")
        else:
            self.set_ui_status_icon("warning")

    def handle_error(self, error: str):
        """Handle communication error."""
        self.error_count += 1
        self.last_error = error
        self.update_status("Error")
        log.error(f"Modbus error: {error}")

    # UI Callbacks

    @ui.callback("write_setpoint")
    async def on_write_setpoint(self, element, value):
        """Write new setpoint to device."""
        new_setpoint = self.get_command("new_setpoint")
        if new_setpoint is None:
            return

        # Scale to register value
        raw_value = unscale_value(new_setpoint, self.config.temp_scale.value)

        try:
            await self.modbus_iface.write_registers_async(
                bus_id=self.config.bus_id.value,
                modbus_id=self.config.slave_id.value,
                start_address=self.config.setpoint_register.value,
                values=[raw_value],
                register_type="holding"
            )

            log.info(f"Wrote setpoint {new_setpoint} (raw: {raw_value})")
            await self.ui_manager.send_notification_async(
                f"Setpoint updated to {new_setpoint}°C"
            )

        except Exception as e:
            self.handle_error(f"Write failed: {e}")
            await self.ui_manager.send_notification_async(
                f"Failed to write setpoint: {e}"
            )

    @ui.callback("read_now")
    async def on_read_now(self, element, value):
        """Force an immediate read."""
        try:
            values = await self.modbus_iface.read_registers_async(
                bus_id=self.config.bus_id.value,
                modbus_id=self.config.slave_id.value,
                start_address=self.config.temp_register.value,
                num_registers=5,
                register_type="holding"
            )

            await self.on_register_update(
                self.config.bus_id.value,
                self.config.slave_id.value,
                self.config.temp_register.value,
                values
            )

        except Exception as e:
            self.handle_error(f"Read failed: {e}")
```

## Step 5: Entry Point

```python
# __init__.py
from pydoover.docker import run_app
from .application import ModbusApp
from .app_config import ModbusAppConfig

def main():
    run_app(ModbusApp(config=ModbusAppConfig()))

if __name__ == "__main__":
    main()
```

## Advanced Topics

### Multiple Devices

```python
class MultiDeviceApp(Application):
    async def setup(self):
        # Subscribe to multiple devices
        for device_id in [1, 2, 3]:
            self.add_new_modbus_read_subscription(
                address=0,
                count=10,
                register_type="holding",
                callback=self.on_device_update,
                poll_secs=1.0,
                modbus_id=device_id
            )

    async def on_device_update(self, bus_id, modbus_id, address, values):
        # Process based on device ID
        log.info(f"Device {modbus_id}: {values}")
```

### Register Mapping

```python
class RegisterMap:
    """Define device register layout."""
    TEMPERATURE = 0
    HUMIDITY = 1
    PRESSURE = 2
    STATUS = 10
    SETPOINT = 100
    CONTROL = 101

# Usage
values = await self.read_modbus_registers(
    address=RegisterMap.TEMPERATURE,
    count=3,
    ...
)
temp = values[0]
humidity = values[1]
pressure = values[2]
```

### Retry with Backoff

```python
async def read_with_retry(self, address, count, max_retries=3):
    delay = 0.5
    for attempt in range(max_retries):
        try:
            return await self.modbus_iface.read_registers_async(
                bus_id=self.config.bus_id.value,
                modbus_id=self.config.slave_id.value,
                start_address=address,
                num_registers=count,
                register_type="holding"
            )
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            log.warning(f"Retry {attempt+1}: {e}")
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff
```

---

See Also:
- [[53-Modbus-Interface|Modbus Interface Reference]]
- [[50-gRPC-Interfaces|gRPC Interfaces]]
- [[70-Tutorial-Basic-App|Basic App Tutorial]]

#tutorial #modbus #industrial #pydoover
