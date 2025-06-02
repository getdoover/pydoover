# fixme: make this an optional package
try:
    from transitions.extensions.asyncio import AsyncTimeout, AsyncMachine
    from transitions.extensions.states import add_state_features
except ImportError:
    print(
        "Transitions module not found. State machine functionality will not be available."
    )
    StateMachine = None
else:

    @add_state_features(AsyncTimeout)
    class StateMachine(AsyncMachine):
        """Async state machine with timeout support."""
