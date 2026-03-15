"""Paginating iterators for message listing."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ._base import _to_snowflake
from ..models import Message

if TYPE_CHECKING:
    from ._async import AsyncDataClient
    from ._sync import DataClient

DEFAULT_PAGE_SIZE = 50


class AsyncMessageIterator:
    """Async iterator that paginates through channel messages.

    Usage::

        async for message in client.iter_messages(agent_id, channel_name):
            ...

        # Or load all into memory:
        messages = await client.iter_messages(agent_id, channel_name).collect()
    """

    def __init__(
        self,
        client: AsyncDataClient,
        agent_id: int,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        self._client = client
        self._agent_id = agent_id
        self._channel_name = channel_name
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
            self._agent_id,
            self._channel_name,
            before=self._before,
            after=self._after,
            limit=self._page_size,
            field_names=self._field_names,
            organisation_id=self._organisation_id,
        )
        if not page or len(page) < self._page_size:
            self._exhausted = True
        if page:
            self._after = page[-1].id
            self._buffer = page

    async def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        results = []
        async for message in self:
            results.append(message)
        return results


class MessageIterator:
    """Sync iterator that paginates through channel messages.

    Usage::

        for message in client.iter_messages(agent_id, channel_name):
            ...

        # Or load all into memory:
        messages = client.iter_messages(agent_id, channel_name).collect()
    """

    def __init__(
        self,
        client: DataClient,
        agent_id: int,
        channel_name: str,
        before: int | datetime | None = None,
        after: int | datetime | None = None,
        field_names: list[str] | None = None,
        organisation_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        self._client = client
        self._agent_id = agent_id
        self._channel_name = channel_name
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
            self._agent_id,
            self._channel_name,
            before=self._before,
            after=self._after,
            limit=self._page_size,
            field_names=self._field_names,
            organisation_id=self._organisation_id,
        )
        if not page or len(page) < self._page_size:
            self._exhausted = True
        if page:
            self._after = page[-1].id
            self._buffer = page

    def collect(self) -> list[Message]:
        """Consume the iterator and return all messages as a list."""
        return list(self)
