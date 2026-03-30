"""Paginating iterators for message listing."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ._base import _to_snowflake
from ...models import Message

if TYPE_CHECKING:
    from ._async import AsyncDataClient
    from ._sync import DataClient

DEFAULT_PAGE_SIZE = 50

# 2 days in milliseconds, shifted into snowflake space (millis << 22).
_TWO_DAYS_SNOWFLAKE = 2 * 24 * 60 * 60 * 1000 << 22


class AsyncMessageIterator:
    """Async iterator that paginates through channel messages.

    Usage::

        async for message in client.iter_messages("my_channel", agent_id=123):
            ...

        # Or load all into memory:
        messages = await client.iter_messages("my_channel", agent_id=123).collect()
    """

    def __init__(
        self,
        client: AsyncDataClient,
        channel_name: str,
        *,
        agent_id: int | None = None,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        self._client = client
        self._channel_name = channel_name
        self._agent_id = agent_id
        self._before = _to_snowflake(before)
        self._after = _to_snowflake(after)
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []
        self._exhausted = False

    def __aiter__(self):
        return self

    async def __anext__(self) -> Message:
        if not self._buffer:
            if self._exhausted:
                raise StopAsyncIteration
            await self._fetch_page()
            if not self._buffer:
                raise StopAsyncIteration
        return self._buffer.pop(0)

    async def _fetch_page(self):
        page = await self._client.list_messages(
            self._channel_name,
            before=self._before,
            after=self._after,
            limit=self._page_size,
            field_names=self._field_names,
            agent_id=self._agent_id,
            organisation_id=self._organisation_id,
        )
        if not page or len(page) < self._page_size:
            self._exhausted = True
        if page:
            # API returns descending order when both before/after are set.
            # Paginate backwards: move `before` to the oldest in this page.
            # I'm not 100% sure on this, it needs a fix in doover-data with default sort options
            # and then this may work a bit better.
            if self._before is not None:
                page = [m for m in page if m.id < self._before]
            if page:
                self._before = page[-1].id
                self._buffer = page

    async def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        results = []
        async for message in self:
            results.append(message)
        return results


class AsyncMultiAgentMessageIterator:
    """Async iterator that paginates through multi-agent channel messages.

    The multi-agent endpoint requires ``before`` and ``after`` to be at most
    2 days apart.  This iterator automatically splits wider ranges into
    consecutive 2-day windows so callers don't need to worry about it.

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
        self._before = _to_snowflake(before)
        self._after = _to_snowflake(after)
        self._agent_message_limit = agent_message_limit
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []
        self._exhausted = False
        # Current window upper bound — capped to _before or after + 2 days.
        self._window_before = self._next_window_before(self._after)

    def _next_window_before(self, after: int | None) -> int | None:
        """Return the ``before`` for the current window (at most 2 days from *after*)."""
        if after is None or self._before is None:
            return self._before
        window_end = after + _TWO_DAYS_SNOWFLAKE
        return min(window_end, self._before)

    def __aiter__(self):
        return self

    async def __anext__(self) -> Message:
        if not self._buffer:
            if self._exhausted:
                raise StopAsyncIteration
            await self._fetch_page()
            if not self._buffer:
                raise StopAsyncIteration
        return self._buffer.pop(0)

    def _advance_window(self) -> bool:
        """Move to the next 2-day window. Return True if a new window is available."""
        if self._window_before is not None and self._window_before < self._before:
            self._after = self._window_before
            self._window_before = self._next_window_before(self._after)
            return True
        return False

    async def _fetch_page(self):
        while True:
            batch = await self._client.fetch_multi_agent_messages(
                self._channel_name,
                self._agent_ids,
                before=self._window_before,
                after=self._after,
                limit=self._page_size,
                agent_message_limit=self._agent_message_limit,
                field_names=self._field_names,
                organisation_id=self._organisation_id,
            )
            results = batch.results
            if results and self._after is not None:
                results = [m for m in results if m.id > self._after]
            if results:
                self._after = results[-1].id
                self._buffer = results
                if len(batch.results) >= self._page_size:
                    return
            # Current window exhausted — try the next one.
            if not self._advance_window():
                self._exhausted = True
                return

    async def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        results = []
        async for message in self:
            results.append(message)
        return results


class MessageIterator:
    """Sync iterator that paginates through channel messages.

    Usage::

        for message in client.iter_messages("my_channel", agent_id=123):
            ...

        # Or load all into memory:
        messages = client.iter_messages("my_channel", agent_id=123).collect()
    """

    def __init__(
        self,
        client: DataClient,
        channel_name: str,
        *,
        agent_id: int | None = None,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        self._client = client
        self._channel_name = channel_name
        self._agent_id = agent_id
        self._before = _to_snowflake(before)
        self._after = _to_snowflake(after)
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []
        self._exhausted = False

    def __iter__(self):
        return self

    def __next__(self) -> Message:
        if not self._buffer:
            if self._exhausted:
                raise StopIteration
            self._fetch_page()
            if not self._buffer:
                raise StopIteration
        return self._buffer.pop(0)

    def _fetch_page(self):
        page = self._client.list_messages(
            self._channel_name,
            before=self._before,
            after=self._after,
            limit=self._page_size,
            field_names=self._field_names,
            agent_id=self._agent_id,
            organisation_id=self._organisation_id,
        )
        if not page or len(page) < self._page_size:
            self._exhausted = True
        if page:
            # API returns descending order when both before/after are set.
            # Paginate backwards: move `before` to the oldest in this page.
            if self._before is not None:
                page = [m for m in page if m.id < self._before]
            if page:
                self._before = page[-1].id
                self._buffer = page

    def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        return list(self)


class MultiAgentMessageIterator:
    """Sync iterator that paginates through multi-agent channel messages.

    The multi-agent endpoint requires ``before`` and ``after`` to be at most
    2 days apart.  This iterator automatically splits wider ranges into
    consecutive 2-day windows so callers don't need to worry about it.

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
        self._before = _to_snowflake(before)
        self._after = _to_snowflake(after)
        self._agent_message_limit = agent_message_limit
        self._field_names = field_names
        self._organisation_id = organisation_id
        self._page_size = page_size
        self._buffer: list[Message] = []
        self._exhausted = False
        self._window_before = self._next_window_before(self._after)

    def _next_window_before(self, after: int | None) -> int | None:
        if after is None or self._before is None:
            return self._before
        window_end = after + _TWO_DAYS_SNOWFLAKE
        return min(window_end, self._before)

    def __iter__(self):
        return self

    def __next__(self) -> Message:
        if not self._buffer:
            if self._exhausted:
                raise StopIteration
            self._fetch_page()
            if not self._buffer:
                raise StopIteration
        return self._buffer.pop(0)

    def _advance_window(self) -> bool:
        if self._window_before is not None and self._window_before < self._before:
            self._after = self._window_before
            self._window_before = self._next_window_before(self._after)
            return True
        return False

    def _fetch_page(self):
        while True:
            batch = self._client.fetch_multi_agent_messages(
                self._channel_name,
                self._agent_ids,
                before=self._window_before,
                after=self._after,
                limit=self._page_size,
                agent_message_limit=self._agent_message_limit,
                field_names=self._field_names,
                organisation_id=self._organisation_id,
            )
            results = batch.results
            if results and self._after is not None:
                results = [m for m in results if m.id > self._after]
            if results:
                self._after = results[-1].id
                self._buffer = results
                if len(batch.results) >= self._page_size:
                    return
            if not self._advance_window():
                self._exhausted = True
                return

    def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        return list(self)
