"""Paginating iterators for message listing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from ._base import _to_snowflake
from ...models import Message

if TYPE_CHECKING:
    from ._async import AsyncDataClient
    from ._sync import DataClient

DEFAULT_PAGE_SIZE = 50

# 2 days in milliseconds, shifted into snowflake space (millis << 22).
_TWO_DAYS_SNOWFLAKE = 2 * 24 * 60 * 60 * 1000 << 22

Order = Literal["asc", "desc"]

_OUT_OF_ORDER = (
    "messages came back out of order; the server may predate the `order` parameter"
)


class _ChannelPager:
    """Feeds the server's ``next`` back as ``after`` (asc) or ``before`` (desc)."""

    def __init__(self, before, after, order: Order | None):
        self.before = _to_snowflake(before)
        self.after = _to_snowflake(after)
        # The server's default: `after` alone reads forward, else newest first.
        if order is None:
            order = "asc" if self.before is None and self.after is not None else "desc"
        self.order: Order = order
        self.exhausted = False

    def advance(self, page: list[Message], next_id: int | None) -> None:
        ids = [m.id for m in page]
        if ids != sorted(ids, reverse=self.order == "desc"):
            raise RuntimeError(_OUT_OF_ORDER)
        if next_id is None:
            self.exhausted = True
        elif self.order == "asc":
            self.after = next_id
        else:
            self.before = next_id


class _WindowPager:
    """Walks back from ``before`` (default now) to ``after`` in 2-day windows,
    following the server's ``next`` within each."""

    def __init__(self, before, after):
        self.start = _to_snowflake(after)
        self.cursor = _to_snowflake(before) or _to_snowflake(datetime.now(UTC))
        self.window_after = self._floor(self.cursor)
        self.exhausted = False

    def _floor(self, before: int) -> int:
        floor = before - _TWO_DAYS_SNOWFLAKE
        return floor if self.start is None else max(floor, self.start)

    def advance(self, next_id: int | None) -> None:
        if next_id is not None:
            if next_id >= self.cursor:
                raise RuntimeError(_OUT_OF_ORDER)
            self.cursor = next_id
        elif self.start is None or self.window_after <= self.start:
            self.exhausted = True
        else:
            # Bounds are exclusive: +1 so a message on the boundary isn't skipped.
            self.cursor = self.window_after + 1
            self.window_after = self._floor(self.cursor)


class AsyncMessageIterator:
    """Async iterator that paginates through channel messages.

    Usage::

        async for message in client.iter_messages(123, "my_channel"):
            ...

        # Or load all into memory:
        messages = await client.iter_messages(123, "my_channel").collect()
    """

    def __init__(
        self,
        client: AsyncDataClient,
        agent_id: int,
        channel_name: str,
        *,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        order: Order | None = None,
    ):
        self._client = client
        self._channel_name = channel_name
        self._agent_id = agent_id
        self._pager = _ChannelPager(before, after, order)
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []

    def __aiter__(self):
        return self

    async def __anext__(self) -> Message:
        while not self._buffer and not self._pager.exhausted:
            page = await self._client.fetch_messages_page(
                agent_id=self._agent_id,
                channel_name=self._channel_name,
                before=self._pager.before,
                after=self._pager.after,
                limit=self._page_size,
                field_names=self._field_names,
                order=self._pager.order,
                organisation_id=self._organisation_id,
            )
            self._buffer = list(page.results)
            self._pager.advance(page.results, page.next)
        if not self._buffer:
            raise StopAsyncIteration
        return self._buffer.pop(0)

    async def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        results = []
        async for message in self:
            results.append(message)
        return results


class AsyncMultiAgentMessageIterator:
    """Async iterator that paginates through multi-agent channel messages,
    newest first.

    The multi-agent endpoint requires ``before`` and ``after`` to be at most
    2 days apart, so this walks wider ranges back in 2-day windows. Without
    ``after`` it covers the 2 days before ``before`` (default now).

    Usage::

        async for message in client.iter_multi_agent_messages("my_channel", agent_ids=[1, 2]):
            ...

        # Or load all into memory:
        messages = await client.iter_multi_agent_messages("my_channel", agent_ids=[1, 2]).collect()
    """

    def __init__(
        self,
        client: AsyncDataClient,
        channel_name: str,
        agent_ids: list[int],
        *,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        agent_message_limit: int | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        self._client = client
        self._channel_name = channel_name
        self._agent_ids = agent_ids
        self._pager = _WindowPager(before, after)
        self._agent_message_limit = agent_message_limit
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []

    def __aiter__(self):
        return self

    async def __anext__(self) -> Message:
        while not self._buffer and not self._pager.exhausted:
            batch = await self._client.fetch_multi_agent_messages(
                self._channel_name,
                self._agent_ids,
                before=self._pager.cursor,
                after=self._pager.window_after,
                limit=self._page_size,
                agent_message_limit=self._agent_message_limit,
                field_names=self._field_names,
                organisation_id=self._organisation_id,
            )
            self._buffer = list(batch.results)
            self._pager.advance(batch.next)
        if not self._buffer:
            raise StopAsyncIteration
        return self._buffer.pop(0)

    async def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        results = []
        async for message in self:
            results.append(message)
        return results


class MessageIterator:
    """Sync iterator that paginates through channel messages.

    Usage::

        for message in client.iter_messages(123, "my_channel"):
            ...

        # Or load all into memory:
        messages = client.iter_messages(123, "my_channel").collect()
    """

    def __init__(
        self,
        client: DataClient,
        agent_id: int,
        channel_name: str,
        *,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        order: Order | None = None,
    ):
        self._client = client
        self._channel_name = channel_name
        self._agent_id = agent_id
        self._pager = _ChannelPager(before, after, order)
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []

    def __iter__(self):
        return self

    def __next__(self) -> Message:
        while not self._buffer and not self._pager.exhausted:
            page = self._client.fetch_messages_page(
                agent_id=self._agent_id,
                channel_name=self._channel_name,
                before=self._pager.before,
                after=self._pager.after,
                limit=self._page_size,
                field_names=self._field_names,
                order=self._pager.order,
                organisation_id=self._organisation_id,
            )
            self._buffer = list(page.results)
            self._pager.advance(page.results, page.next)
        if not self._buffer:
            raise StopIteration
        return self._buffer.pop(0)

    def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        return list(self)


class MultiAgentMessageIterator:
    """Sync iterator that paginates through multi-agent channel messages,
    newest first.

    The multi-agent endpoint requires ``before`` and ``after`` to be at most
    2 days apart, so this walks wider ranges back in 2-day windows. Without
    ``after`` it covers the 2 days before ``before`` (default now).

    Usage::

        for message in client.iter_multi_agent_messages("my_channel", agent_ids=[1, 2]):
            ...

        # Or load all into memory:
        messages = client.iter_multi_agent_messages("my_channel", agent_ids=[1, 2]).collect()
    """

    def __init__(
        self,
        client: DataClient,
        channel_name: str,
        agent_ids: list[int],
        *,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        agent_message_limit: int | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        self._client = client
        self._channel_name = channel_name
        self._agent_ids = agent_ids
        self._pager = _WindowPager(before, after)
        self._agent_message_limit = agent_message_limit
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []

    def __iter__(self):
        return self

    def __next__(self) -> Message:
        while not self._buffer and not self._pager.exhausted:
            batch = self._client.fetch_multi_agent_messages(
                self._channel_name,
                self._agent_ids,
                before=self._pager.cursor,
                after=self._pager.window_after,
                limit=self._page_size,
                agent_message_limit=self._agent_message_limit,
                field_names=self._field_names,
                organisation_id=self._organisation_id,
            )
            self._buffer = list(batch.results)
            self._pager.advance(batch.next)
        if not self._buffer:
            raise StopIteration
        return self._buffer.pop(0)

    def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        return list(self)
