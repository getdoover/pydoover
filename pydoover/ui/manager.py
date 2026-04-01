import inspect
import logging
import re
from typing import Callable, Generic, TypeVar

from pydoover.models import (
    EventSubscription,
    AggregateUpdateEvent,
    MessageCreateEvent,
    MessageUpdateEvent,
)
from pydoover.rpc import RPCManager, RPCContext
from pydoover.ui import Interaction

UI_CMDS_CHANNEL = "ui_cmds"

log = logging.getLogger(__name__)


def handler(
    interaction: Interaction | str | re.Pattern,
    parser: Callable = None,
    auto_update: bool = True,
):
    """Decorator to mark an async method as an RPC handler.

    Parameters
    ----------
    interaction : str
        The RPC method name this handler responds to. Can be an interaction or regex pattern.
    """

    def decorator(func: Callable) -> Callable:
        func._is_rpc_handler = False
        func._is_ui_rpc_handler = True

        if isinstance(interaction, Interaction):
            func._rpc_method = interaction.name
        else:
            func._rpc_method = interaction

        func._rpc_channel = UI_CMDS_CHANNEL
        func._rpc_parser = parser
        func._ui_auto_update = auto_update
        return func

    return decorator


InteractionT = TypeVar("InteractionT", bound=Interaction)


class InteractionContext(RPCContext, Generic[InteractionT]):
    element: InteractionT
    interaction: InteractionT

    def __init__(
        self, method, message, interaction: InteractionT, _update_fn, _handler
    ):
        super().__init__(method, message, _update_fn, _handler)
        # dunno what to name this
        self.element = self.interaction = interaction
        self.auto_update = self._handler._ui_auto_update

    async def set_value(self, value, max_age: float = None, log_update: bool = True):
        return await self.element.set(value, max_age, log_update)


class UICommandsManager(RPCManager):
    def __init__(self, app):
        super().__init__(app)
        self.app_key = self.api.app_key

        self.values = {}
        self._interactions = {}

    def _set_interactions(self, interactions: dict[str, Interaction]):
        self._interactions = interactions
        for interaction in interactions.values():
            # this is the real reason we need a setter
            interaction._manager = self

    def subscribe(self, channel_name: str) -> None:
        super().subscribe(channel_name)

        if self.is_processor:
            return

        self.api.add_event_callback(
            channel_name,
            self._on_aggregate_update,
            EventSubscription.aggregate_update,
        )

    async def _on_aggregate_update(self, event: AggregateUpdateEvent):
        try:
            self.values = event.aggregate.data[self.app_key]
        except KeyError:
            self.values = {}

    async def set_value(self, key, value, log_update: bool = True):
        if self.is_processor:
            kwargs = {"allow_invoking_channel": True}
        else:
            kwargs = {}

        await self.api.update_channel_aggregate(
            UI_CMDS_CHANNEL, {self.app_key: {key: value}}, **kwargs
        )
        if log_update:
            await self.api.create_message(
                UI_CMDS_CHANNEL,
                {"type": "log", "app_key": self.app_key, "key": key, "value": value},
                **kwargs,
            )

    def get_value(self, key):
        return self.values[key]

    def _get_handler(self, channel_name, method):
        try:
            return super()._get_handler(channel_name, method)
        except KeyError:
            elem = self._interactions[method]
            return None, elem.handler

    def _build_context(
        self, method, event: MessageCreateEvent | MessageUpdateEvent, _handler: Callable
    ):
        return InteractionContext(
            method,
            event.message,
            self._interactions[method],
            self.api.update_message,
            _handler,
        )

    def check_handler(self, func: Callable):
        return inspect.ismethod(func) and getattr(func, "_is_ui_rpc_handler", False)

    async def on_success(self, ctx: InteractionContext, payload):
        if ctx.auto_update:
            log.debug(f"Auto-updating {ctx.element} with {payload}")
            await ctx.set_value(payload)
