# State Machine

PyDoover integrates with the `transitions` library to provide state machine functionality for managing complex application states.

## Overview

The state machine system provides:
- Declarative state definitions
- Transition rules with guards
- Enter/exit callbacks
- Async support
- Timeout-based transitions

## Basic Usage

```python
from pydoover.state import StateMachine

class MyStateMachine(StateMachine):
    states = ["idle", "running", "paused", "error"]

    transitions = [
        {"trigger": "start", "source": "idle", "dest": "running"},
        {"trigger": "pause", "source": "running", "dest": "paused"},
        {"trigger": "resume", "source": "paused", "dest": "running"},
        {"trigger": "stop", "source": ["running", "paused"], "dest": "idle"},
        {"trigger": "fail", "source": "*", "dest": "error"},
        {"trigger": "reset", "source": "error", "dest": "idle"}
    ]

    def __init__(self):
        super().__init__(
            states=self.states,
            transitions=self.transitions,
            initial="idle"
        )
```

## States

### Simple States

```python
states = ["idle", "running", "stopped"]
```

### States with Configuration

```python
states = [
    {"name": "idle", "on_enter": "on_enter_idle"},
    {"name": "running", "on_exit": "on_exit_running"},
    {"name": "error", "on_enter": "handle_error"}
]
```

## Transitions

### Basic Transition

```python
transitions = [
    {"trigger": "start", "source": "idle", "dest": "running"}
]
```

### Multiple Sources

```python
transitions = [
    {"trigger": "stop", "source": ["running", "paused"], "dest": "idle"}
]
```

### Wildcard Source

```python
transitions = [
    {"trigger": "emergency", "source": "*", "dest": "error"}
]
```

### Conditional Transitions

```python
transitions = [
    {
        "trigger": "start",
        "source": "idle",
        "dest": "running",
        "conditions": "can_start"
    }
]

def can_start(self):
    return self.system_ready
```

## Callbacks

### Enter/Exit Callbacks

```python
class MyStateMachine(StateMachine):
    async def on_enter_running(self):
        """Called when entering 'running' state."""
        log.info("Started running")
        self.app.set_do(0, True)

    async def on_exit_running(self):
        """Called when exiting 'running' state."""
        log.info("Stopped running")
        self.app.set_do(0, False)
```

## Triggering Transitions

```python
sm = MyStateMachine()

# Trigger transition
sm.start()  # idle -> running

# Or with trigger method
sm.trigger("start")

# Async trigger
await sm.start()
```

## Checking State

```python
# Current state
print(sm.state)  # "running"

# Check specific state
if sm.is_running():
    print("System is running")

# Check if transition is valid
if sm.may_start():
    sm.start()
```

## Integration with Application

```python
class MyApp(Application):
    async def setup(self):
        self.state_machine = AppStateMachine(self)

    @ui.callback("start_button")
    async def on_start(self, element, value):
        if self.state_machine.may_start():
            await self.state_machine.start()


class AppStateMachine(StateMachine):
    states = ["idle", "running", "error"]
    transitions = [
        {"trigger": "start", "source": "idle", "dest": "running"},
        {"trigger": "stop", "source": "running", "dest": "idle"},
        {"trigger": "fail", "source": "*", "dest": "error"}
    ]

    def __init__(self, app):
        super().__init__(
            states=self.states,
            transitions=self.transitions,
            initial="idle"
        )
        self.app = app

    async def on_enter_running(self):
        self.app.set_do(0, True)
        self.app.set_tag("state", "running")

    async def on_enter_error(self):
        self.app.set_do(0, False)
        await self.app.ui_manager.send_notification_async("System error!")
```

## Best Practices

1. **Keep states simple** - Each state should have a clear purpose
2. **Use callbacks** - React to state changes in callbacks
3. **Guard transitions** - Use conditions to prevent invalid transitions
4. **Update UI** - Reflect state changes in the UI
5. **Log transitions** - Log state changes for debugging

---

See Also:
- [[10-Application-Framework|Application Framework]]
- [[73-Example-Patterns|Common Patterns]]
- [[60-Utilities|Utilities Overview]]

#state-machine #transitions #control #pydoover
