# Platform Interface

The Platform Interface provides access to hardware I/O including digital inputs/outputs and analog inputs/outputs.

## Overview

The Platform Interface handles:
- Digital Input (DI) reading
- Digital Output (DO) control
- Analog Input (AI) reading
- Analog Output (AO) control
- PWM output (where supported)
- Scheduled output operations

## Access

In your application:

```python
# Access the interface
self.platform_iface  # PlatformInterface instance

# Or use convenience methods
self.get_di(0)
self.set_do(0, True)
```

## Digital Inputs (DI)

Read digital input states.

### Read Single DI

```python
# Read digital input 0
value = self.platform_iface.get_di(0)  # Returns bool

# Convenience method
value = self.get_di(0)

# Async
value = await self.platform_iface.get_di_async(0)
```

### Read Multiple DIs

```python
# Read all DIs
values = self.platform_iface.get_all_di()  # Returns list[bool]

# Read range
for i in range(8):
    state = self.get_di(i)
    print(f"DI{i}: {state}")
```

## Digital Outputs (DO)

Control digital outputs.

### Read DO State

```python
# Read current DO state
state = self.platform_iface.get_do(0)  # Returns bool

# Convenience method
state = self.get_do(0)
```

### Set DO State

```python
# Set digital output high
self.platform_iface.set_do(0, True)

# Set digital output low
self.platform_iface.set_do(0, False)

# Convenience methods
self.set_do(0, True)
self.set_do(0, False)

# Async
await self.platform_iface.set_do_async(0, True)
```

### Schedule DO Change

```python
# Set DO low after 5 seconds
self.platform_iface.schedule_do(0, False, 5.0)

# Convenience method
self.schedule_do(0, False, 5.0)

# Async
await self.platform_iface.schedule_do_async(0, False, 5.0)
```

## Analog Inputs (AI)

Read analog input values.

### Read Single AI

```python
# Read analog input 0
value = self.platform_iface.get_ai(0)  # Returns int (typically 0-4095)

# Convenience method
value = self.get_ai(0)

# Async
value = await self.platform_iface.get_ai_async(0)
```

### Read Multiple AIs

```python
# Read all AIs
values = self.platform_iface.get_all_ai()  # Returns list[int]

# Read range
for i in range(4):
    reading = self.get_ai(i)
    print(f"AI{i}: {reading}")
```

### Scaling AI Values

```python
def scale_ai(self, channel: int, min_val: float, max_val: float) -> float:
    """Scale 12-bit ADC (0-4095) to engineering units."""
    raw = self.get_ai(channel)
    return min_val + (raw / 4095.0) * (max_val - min_val)

# Usage
temperature = self.scale_ai(0, -20.0, 100.0)  # °C
pressure = self.scale_ai(1, 0.0, 100.0)  # PSI
```

## Analog Outputs (AO)

Control analog outputs.

### Read AO State

```python
# Read current AO state
value = self.platform_iface.get_ao(0)  # Returns int

# Convenience method
value = self.get_ao(0)
```

### Set AO Value

```python
# Set analog output (typically 0-4095 for 12-bit DAC)
self.platform_iface.set_ao(0, 2048)  # 50% output

# Convenience method
self.set_ao(0, 2048)

# Async
await self.platform_iface.set_ao_async(0, 2048)
```

### Schedule AO Change

```python
# Set AO to 0 after 5 seconds
self.platform_iface.schedule_ao(0, 0, 5.0)

# Convenience method
self.schedule_ao(0, 0, 5.0)

# Async
await self.platform_iface.schedule_ao_async(0, 0, 5.0)
```

### Scaling AO Values

```python
def set_ao_scaled(self, channel: int, value: float, min_val: float, max_val: float):
    """Set AO from engineering units to 12-bit DAC."""
    scaled = int((value - min_val) / (max_val - min_val) * 4095)
    scaled = max(0, min(4095, scaled))  # Clamp
    self.set_ao(channel, scaled)

# Usage
self.set_ao_scaled(0, 50.0, 0.0, 100.0)  # 50% = 2047
```

## Connection URI

The Platform Interface URI is configured via:

| Source | Value |
|--------|-------|
| Environment | `PLT_URI` |
| Command line | `--plt-uri` |
| Default | `localhost:50053` |

### Remote Development

```bash
# Connect to remote platform
export PLT_URI=192.168.1.100:50053
python -m my_app

# Or use remote-dev (replaces localhost in all URIs)
python -m my_app --remote-dev 192.168.1.100
```

## gRPC Details

- **Port**: 50053 (default)
- **Protocol**: gRPC (HTTP/2)

### Proto Services

```protobuf
service Platform {
    rpc GetDigitalInput(IoRequest) returns (DigitalValue);
    rpc SetDigitalOutput(DigitalSetRequest) returns (Empty);
    rpc GetAnalogInput(IoRequest) returns (AnalogValue);
    rpc SetAnalogOutput(AnalogSetRequest) returns (Empty);
    rpc ScheduleDigitalOutput(ScheduleRequest) returns (Empty);
    rpc ScheduleAnalogOutput(ScheduleRequest) returns (Empty);
}
```

## Simulator

For development without hardware:

```yaml
# docker-compose.yml
services:
  platform:
    image: doover/platform_simulator:latest
    ports:
      - "50053:50053"
```

The simulator provides:
- Configurable number of DI/DO/AI/AO
- Randomized AI values
- State tracking for DO/AO

## Error Handling

```python
try:
    value = self.get_di(0)
except Exception as e:
    log.error(f"Failed to read DI0: {e}")
    value = None
```

## Common Patterns

### Debounced Digital Input

```python
class MyApp(Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._di_states = {}
        self._di_stable_count = {}
        self._debounce_threshold = 3

    async def main_loop(self):
        for i in range(8):
            current = self.get_di(i)

            if current == self._di_states.get(i):
                self._di_stable_count[i] = self._di_stable_count.get(i, 0) + 1
            else:
                self._di_stable_count[i] = 0

            if self._di_stable_count[i] >= self._debounce_threshold:
                if self._di_states.get(i) != current:
                    self._di_states[i] = current
                    await self.on_di_change(i, current)

    async def on_di_change(self, channel: int, state: bool):
        log.info(f"DI{channel} changed to {state}")
```

### Pulse Output

```python
async def pulse_output(self, channel: int, duration: float = 0.5):
    """Pulse a digital output high then low."""
    self.set_do(channel, True)
    self.schedule_do(channel, False, duration)
```

### Analog Input Filtering

```python
class FilteredAI:
    def __init__(self, samples: int = 10):
        self._samples = samples
        self._buffer = []

    def add_sample(self, value: int) -> float:
        self._buffer.append(value)
        if len(self._buffer) > self._samples:
            self._buffer.pop(0)
        return sum(self._buffer) / len(self._buffer)

# Usage
filter = FilteredAI(samples=10)

async def main_loop(self):
    raw = self.get_ai(0)
    filtered = filter.add_sample(raw)
```

## Complete Example

```python
from pydoover.docker import Application
import logging

log = logging.getLogger(__name__)

class IoController(Application):
    async def setup(self):
        # Initialize outputs to known state
        for i in range(4):
            self.set_do(i, False)

        # Set analog outputs to midpoint
        for i in range(2):
            self.set_ao(i, 2048)

        log.info("I/O initialized")

    async def main_loop(self):
        # Read all digital inputs
        di_states = [self.get_di(i) for i in range(8)]

        # Read and scale analog inputs
        temperature = self.scale_ai(0, -20.0, 100.0)
        pressure = self.scale_ai(1, 0.0, 100.0)

        # Update UI
        self.ui_manager.update_variable("temperature", temperature)
        self.ui_manager.update_variable("pressure", pressure)

        # Control logic
        if temperature > 50:
            self.set_do(0, True)  # Turn on cooling
        elif temperature < 40:
            self.set_do(0, False)  # Turn off cooling

        # Report states
        self.set_tag("temperature", temperature)
        self.set_tag("pressure", pressure)
        self.set_tag("di_states", di_states)

    def scale_ai(self, channel: int, min_val: float, max_val: float) -> float:
        raw = self.get_ai(channel)
        return min_val + (raw / 4095.0) * (max_val - min_val)
```

---

See Also:
- [[50-gRPC-Interfaces|gRPC Interfaces Overview]]
- [[51-Device-Agent-Interface|Device Agent Interface]]
- [[53-Modbus-Interface|Modbus Interface]]

#platform #gpio #analog #digital #pydoover
