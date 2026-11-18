"""Message iterators against fakes of the data API's paging rules."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from pydoover.api.data._iterators import (
    AsyncMessageIterator,
    AsyncMultiAgentMessageIterator,
    MessageIterator,
    MultiAgentMessageIterator,
)
from pydoover.models import Message
from pydoover.models.data import BatchMessageResponse
from pydoover.utils.snowflake import generate_snowflake_id_at

NOW = datetime.now(UTC)


def _msg(when, agent=1):
    return Message(
        generate_snowflake_id_at(when),
        agent,
        {"agent_id": str(agent), "name": "c"},
        {},
        [],
    )


def _between(messages, before, after):
    return sorted(
        (
            m
            for m in messages
            if (before is None or m.id < before) and (after is None or m.id > after)
        ),
        key=lambda m: m.id,
    )


class Channel:
    """Paginated single-agent list; `honour_order=False` acts like a server from
    before `order`, which is always newest first."""

    def __init__(self, messages, honour_order=True):
        self.messages, self.honour_order = messages, honour_order

    def fetch_messages_page(self, *, before, after, limit, order, **_):
        page = _between(
            self.messages, before or generate_snowflake_id_at(datetime.now(UTC)), after
        )
        if order == "desc" or not self.honour_order:
            page.reverse()
        page = page[:limit]
        return BatchMessageResponse(
            page, len(page), page[-1].id if len(page) == limit else None
        )

    async def afetch_messages_page(self, **kw):
        return Channel.fetch_messages_page(self, **kw)


class Fleet:
    """Multi-agent endpoint: newest first, each agent capped per page, `next`
    the highest of the capped agents' oldest ids."""

    def __init__(self, messages, per_agent):
        self.messages, self.per_agent = messages, per_agent

    def fetch_multi_agent_messages(self, channel, agent_ids, *, before, after, **_):
        out, marks = [], []
        for agent in agent_ids:
            mine = [
                m
                for m in _between(self.messages, before, after)
                if m.author_id == agent
            ]
            mine = mine[::-1][: self.per_agent]
            out += mine
            if len(mine) == self.per_agent:
                marks.append(mine[-1].id)
        mark = max(marks, default=None)
        out = sorted(
            (m for m in out if mark is None or m.id >= mark),
            key=lambda m: m.id,
            reverse=True,
        )
        return BatchMessageResponse(out, len(out), mark)

    async def afetch_multi_agent_messages(self, *a, **kw):
        return Fleet.fetch_multi_agent_messages(self, *a, **kw)


def _collect(iterator_cls, client, *args, asynchronous, **kw):
    if asynchronous:
        # The async iterators call the same method names, so alias the async fakes in.
        client.fetch_messages_page = getattr(client, "afetch_messages_page", None)
        client.fetch_multi_agent_messages = getattr(
            client, "afetch_multi_agent_messages", None
        )
        return [m.id for m in asyncio.run(iterator_cls(client, *args, **kw).collect())]
    return [m.id for m in iterator_cls(client, *args, **kw).collect()]


# Every 15 minutes for 3 days: several pages at the default page size of 50.
HISTORY = [_msg(NOW - timedelta(minutes=15 * i)) for i in range(288, 0, -1)]
IDS = [m.id for m in HISTORY]


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "kw, expected",
    [
        ({"after": IDS[9]}, IDS[10:]),
        ({"after": IDS[9], "before": IDS[200]}, IDS[199:9:-1]),
        ({"after": IDS[9], "before": IDS[200], "order": "asc"}, IDS[10:200]),
    ],
    ids=["after-alone-forward", "both-bounds-back", "asc-range"],
)
def test_reads_each_message_once(asynchronous, kw, expected):
    cls = AsyncMessageIterator if asynchronous else MessageIterator
    assert (
        _collect(cls, Channel(HISTORY), 1, "c", asynchronous=asynchronous, **kw)
        == expected
    )


def test_a_server_ignoring_order_raises():
    with pytest.raises(RuntimeError, match="order"):
        MessageIterator(
            Channel(HISTORY, honour_order=False), 1, "c", after=IDS[0]
        ).collect()


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_multi_agent_reads_every_window_once(asynchronous):
    # Two agents, hourly, across 5 days: three 2-day windows, several pages each.
    fleet = [
        _msg(NOW - timedelta(hours=h, minutes=a), a)
        for a in (1, 2)
        for h in range(1, 120)
    ]
    cls = AsyncMultiAgentMessageIterator if asynchronous else MultiAgentMessageIterator
    got = _collect(
        cls,
        Fleet(fleet, 7),
        "c",
        [1, 2],
        asynchronous=asynchronous,
        after=NOW - timedelta(days=5),
    )
    assert got == sorted((m.id for m in fleet), reverse=True)
