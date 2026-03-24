# Utilities Overview

PyDoover includes various utility modules for common tasks in industrial applications.

## Available Utilities

| Module | Purpose |
|--------|---------|
| [[61-State-Machine]] | State machine integration |
| [[62-Reports]] | Report generation |
| `utils` | General utility functions |
| `alarm` | Alarm management |
| `kalman` | Kalman filtering |
| `pid` | PID controller |
| `diff` | Dict diff/merge operations |

## General Utilities

Located in `pydoover.utils`:

### Async Helpers

```python
from pydoover.utils import call_maybe_async, get_is_async, maybe_async

# Call function that may or may not be async
await call_maybe_async(func, arg1, arg2)

# Check if running in async context
is_async = get_is_async()

# Decorator for sync/async compatibility
@maybe_async()
def my_function():
    pass
```

### Dict Operations

```python
from pydoover.utils import find_object_with_key

# Find nested object by key
result = find_object_with_key(nested_dict, "target_key")
```

## Diff Utilities

Located in `pydoover.utils.diff`:

```python
from pydoover.utils.diff import dict_diff, dict_merge

# Get difference between dicts
diff = dict_diff(old_dict, new_dict)

# Merge dicts
merged = dict_merge(base_dict, update_dict)
```

## Alarm Utilities

For managing alarm states:

```python
from pydoover.utils.alarm import Alarm, AlarmState

alarm = Alarm(
    name="high_temperature",
    threshold=50.0,
    hysteresis=2.0,
    delay_seconds=5.0
)

# Update with current value
alarm.update(current_temp)

# Check state
if alarm.state == AlarmState.ACTIVE:
    send_notification()
```

## Kalman Filter

Simple Kalman filter implementation:

```python
from pydoover.utils.kalman import KalmanFilter

# Create filter
kf = KalmanFilter(
    process_variance=1e-4,
    measurement_variance=0.1
)

# Filter noisy readings
filtered_value = kf.update(noisy_reading)
```

## PID Controller

Basic PID controller:

```python
from pydoover.utils.pid import PIDController

pid = PIDController(
    kp=1.0,
    ki=0.1,
    kd=0.05,
    setpoint=50.0,
    output_min=0,
    output_max=100
)

# In control loop
output = pid.update(current_value, dt=0.1)
```

## Deprecation Utilities

For marking deprecated functions:

```python
from pydoover.utils.deprecator import deprecated

@deprecated("Use new_function instead")
def old_function():
    pass
```

---

See Also:
- [[61-State-Machine|State Machine]]
- [[62-Reports|Reports]]
- [[73-Example-Patterns|Common Patterns]]

#utilities #helpers #pydoover
