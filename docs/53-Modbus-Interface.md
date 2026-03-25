# Modbus Interface

The Modbus Interface provides Modbus RTU and TCP communication for industrial device integration.

## Overview

The Modbus Interface supports:
- Modbus RTU (serial)
- Modbus TCP
- Multiple bus configurations
- Register subscriptions with polling
- Async operations

## Access

In your application:

```python
# Access the interface
self.modbus_iface  # ModbusInterface instance

# Or use convenience methods
self.read_modbus_registers(...)
self.write_modbus_registers(...)
```

## Register Types

| Type | Function Code | Access | Description |
|------|---------------|--------|-------------|
| `"holding"` | 3 (read), 6/16 (write) | Read/Write | 16-bit registers |
| `"input"` | 4 | Read-only | 16-bit input registers |
| `"coil"` | 1 (read), 5/15 (write) | Read/Write | Single bits |
| `"discrete"` | 2 | Read-only | Single bit inputs |

## Reading Registers

### Basic Read

```python
# Read 10 holding registers starting at address 0
values = self.modbus_iface.read_registers(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    num_registers=10,
    register_type="holding"
)
```

### Convenience Method

```python
values = self.read_modbus_registers(
    address=0,
    count=10,
    register_type="holding",
    modbus_id=1,
    bus_id="default"
)
```

### Async Read

```python
values = await self.modbus_iface.read_registers_async(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    num_registers=10,
    register_type="holding"
)
```

### Read Different Types

```python
# Holding registers
holding = self.read_modbus_registers(
    address=0, count=10, register_type="holding", modbus_id=1
)

# Input registers
inputs = self.read_modbus_registers(
    address=0, count=10, register_type="input", modbus_id=1
)

# Coils (bits)
coils = self.read_modbus_registers(
    address=0, count=8, register_type="coil", modbus_id=1
)

# Discrete inputs (bits)
discretes = self.read_modbus_registers(
    address=0, count=8, register_type="discrete", modbus_id=1
)
```

## Writing Registers

### Basic Write

```python
# Write values to holding registers
self.modbus_iface.write_registers(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    values=[100, 200, 300],
    register_type="holding"
)
```

### Convenience Method

```python
self.write_modbus_registers(
    address=0,
    values=[100, 200, 300],
    register_type="holding",
    modbus_id=1,
    bus_id="default"
)
```

### Async Write

```python
await self.modbus_iface.write_registers_async(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    values=[100, 200, 300],
    register_type="holding"
)
```

### Write Single vs Multiple

```python
# Single register (function code 6)
self.write_modbus_registers(address=0, values=[100], ...)

# Multiple registers (function code 16)
self.write_modbus_registers(address=0, values=[100, 200, 300], ...)

# Single coil (function code 5)
self.write_modbus_registers(address=0, values=[1], register_type="coil", ...)

# Multiple coils (function code 15)
self.write_modbus_registers(address=0, values=[1, 0, 1], register_type="coil", ...)
```

## Register Subscriptions

Automatically poll registers at intervals.

### Add Subscription

```python
self.modbus_iface.add_read_register_subscription(
    bus_id="default",
    modbus_id=1,
    start_address=0,
    num_registers=10,
    register_type="holding",
    poll_secs=1.0,
    callback=self.on_modbus_update
)
```

### Convenience Method

```python
self.add_new_modbus_read_subscription(
    address=0,
    count=10,
    register_type="holding",
    callback=self.on_modbus_update,
    poll_secs=1.0,
    modbus_id=1,
    bus_id="default"
)
```

### Callback Signature

```python
async def on_modbus_update(
    self,
    bus_id: str,
    modbus_id: int,
    address: int,
    values: list[int]
):
    log.info(f"Modbus update from {bus_id}/{modbus_id}@{address}: {values}")
```

## Configuration

### Modbus Configuration Class

```python
from pydoover.docker.modbus import ModbusConfig

class MyConfig(config.Schema):
    def __init__(self):
        self.modbus = ModbusConfig()

        # Or custom settings
        self.slave_id = config.Integer("Modbus Slave ID", default=1)
        self.baud_rate = config.Integer("Baud Rate", default=9600)
```

### Bus Configuration

Bus configurations are set in the Doover platform or via environment.

## Connection URI

| Source | Value |
|--------|-------|
| Environment | `MODBUS_URI` |
| Command line | `--modbus-uri` |
| Default | `localhost:50054` |

### Remote Development

```bash
export MODBUS_URI=192.168.1.100:50054
python -m my_app

# Or
python -m my_app --remote-dev 192.168.1.100
```

## Data Conversion

### 16-bit to Signed Integer

```python
def to_signed16(value: int) -> int:
    if value >= 0x8000:
        return value - 0x10000
    return value

# Usage
raw = self.read_modbus_registers(address=0, count=1, ...)[0]
signed = to_signed16(raw)
```

### 32-bit from Two Registers

```python
def to_uint32(high: int, low: int) -> int:
    return (high << 16) | low

def to_int32(high: int, low: int) -> int:
    value = (high << 16) | low
    if value >= 0x80000000:
        return value - 0x100000000
    return value

# Usage
regs = self.read_modbus_registers(address=0, count=2, ...)
value = to_uint32(regs[0], regs[1])
```

### Float from Two Registers

```python
import struct

def to_float32(high: int, low: int) -> float:
    packed = struct.pack('>HH', high, low)
    return struct.unpack('>f', packed)[0]

# Usage
regs = self.read_modbus_registers(address=0, count=2, ...)
value = to_float32(regs[0], regs[1])
```

### Scaling

```python
def scale_register(value: int, min_val: float, max_val: float) -> float:
    """Scale 16-bit unsigned to engineering units."""
    return min_val + (value / 65535.0) * (max_val - min_val)

# Usage
raw = self.read_modbus_registers(address=0, count=1, ...)[0]
temp = scale_register(raw, -40.0, 125.0)
```

## Error Handling

```python
try:
    values = await self.modbus_iface.read_registers_async(
        bus_id="default",
        modbus_id=1,
        start_address=0,
        num_registers=10,
        register_type="holding"
    )
except Exception as e:
    log.error(f"Modbus read failed: {e}")
    values = None
```

### Retry Logic

```python
async def read_with_retry(self, address: int, count: int, retries: int = 3):
    for attempt in range(retries):
        try:
            return await self.modbus_iface.read_registers_async(
                bus_id="default",
                modbus_id=self.config.slave_id.value,
                start_address=address,
                num_registers=count,
                register_type="holding"
            )
        except Exception as e:
            if attempt == retries - 1:
                raise
            log.warning(f"Retry {attempt + 1}/{retries}: {e}")
            await asyncio.sleep(0.5)
```

## Simulator

For development without hardware:

```yaml
# docker-compose.yml
services:
  modbus:
    image: doover/modbus_simulator:latest
    ports:
      - "50054:50054"
```

## Complete Example

```python
import struct
from pydoover.docker import Application
from pydoover import config
import logging

log = logging.getLogger(__name__)

class ModbusDevice(Application):
    async def setup(self):
        # Subscribe to register updates
        self.add_new_modbus_read_subscription(
            address=0,
            count=20,
            register_type="holding",
            callback=self.on_registers,
            poll_secs=1.0,
            modbus_id=self.config.slave_id.value
        )

        log.info(f"Monitoring Modbus device {self.config.slave_id.value}")

    async def main_loop(self):
        # Manual read (alternative to subscription)
        try:
            regs = await self.modbus_iface.read_registers_async(
                bus_id="default",
                modbus_id=self.config.slave_id.value,
                start_address=0,
                num_registers=10,
                register_type="holding"
            )

            # Process data
            temperature = self.to_signed16(regs[0]) / 10.0
            pressure = regs[1] / 100.0
            status = regs[2]

            # Update UI
            self.ui_manager.update_variable("temperature", temperature)
            self.ui_manager.update_variable("pressure", pressure)

            # Update tags
            self.set_tags({
                "temperature": temperature,
                "pressure": pressure,
                "status": status
            })

        except Exception as e:
            log.error(f"Read failed: {e}")
            self.ui_manager.update_variable("status", "COMM ERROR")

    async def on_registers(self, bus_id, modbus_id, address, values):
        log.debug(f"Register update @{address}: {values}")

    async def write_setpoint(self, value: float):
        """Write temperature setpoint."""
        scaled = int(value * 10)  # Scale for device
        await self.modbus_iface.write_registers_async(
            bus_id="default",
            modbus_id=self.config.slave_id.value,
            start_address=100,  # Setpoint register
            values=[scaled],
            register_type="holding"
        )

    @staticmethod
    def to_signed16(value: int) -> int:
        if value >= 0x8000:
            return value - 0x10000
        return value
```

---

See Also:
- [[50-gRPC-Interfaces|gRPC Interfaces Overview]]
- [[52-Platform-Interface|Platform Interface]]
- [[72-Tutorial-Modbus|Modbus Tutorial]]

#modbus #industrial #serial #tcp #pydoover
