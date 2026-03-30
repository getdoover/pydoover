"""Live integration tests for MessageIterator pagination.

Run with:
    uv run pytest tests/test_iterators_live.py -v
"""

from datetime import datetime, timedelta, timezone

import pytest

from pydoover.api import DataClient
from pydoover.api.auth._config import ConfigManager


pytestmark = pytest.mark.live

DATA_PROFILE = "staging"
AGENT_ID = 160548444522423041
ORG_ID = 160537971806708483
CHANNEL = "ui_state"

skip_no_profile = pytest.mark.skipif(
    ConfigManager().get(DATA_PROFILE) is None,
    reason=f"Doover auth profile {DATA_PROFILE!r} is required",
)


def _make_client() -> DataClient:
    return DataClient(profile=DATA_PROFILE, organisation_id=ORG_ID)


def _check_ordering(msgs):
    """Assert messages are in descending ID order with no duplicates."""
    ids = [m.id if hasattr(m, "id") else m for m in msgs]
    assert len(ids) == len(set(ids)), (
        f"duplicate IDs found: {len(ids) - len(set(ids))} duplicates"
    )
    assert all(ids[i] > ids[i + 1] for i in range(len(ids) - 1)), (
        "messages are not sorted in descending order"
    )


@skip_no_profile
class TestMessageIterator:
    """Tests that iter_messages paginates correctly across page sizes."""

    def _time_range(self):
        now = datetime.now(timezone.utc)
        return now - timedelta(days=7), now

    def test_iter_collect(self):
        """iter_messages(...).collect() returns ordered, deduplicated results."""
        after, before = self._time_range()
        with _make_client() as client:
            msgs = client.iter_messages(
                AGENT_ID, CHANNEL, after=after, before=before, page_size=10
            ).collect()
            assert isinstance(msgs, list)
            if msgs:
                _check_ordering(msgs)

    def test_iter_for_loop(self):
        """Iterating via for-loop yields ordered, deduplicated results."""
        after, before = self._time_range()
        with _make_client() as client:
            ids = []
            for msg in client.iter_messages(
                AGENT_ID, CHANNEL, after=after, before=before, page_size=7
            ):
                ids.append(msg.id)
            if ids:
                assert len(ids) == len(set(ids)), "duplicate IDs from for-loop"

    def test_collect_matches_for_loop(self):
        """collect() and for-loop yield the same set of message IDs."""
        after, before = self._time_range()
        with _make_client() as client:
            collected = client.iter_messages(
                AGENT_ID, CHANNEL, after=after, before=before, page_size=5
            ).collect()
            looped = list(
                client.iter_messages(
                    AGENT_ID, CHANNEL, after=after, before=before, page_size=5
                )
            )
            assert {m.id for m in collected} == {m.id for m in looped}

    def test_page_sizes_return_same_ids(self):
        """Different page sizes should all return the same set of IDs."""
        after, before = self._time_range()
        with _make_client() as client:
            id_sets = {}
            for ps in [5, 10, 25]:
                msgs = client.iter_messages(
                    AGENT_ID, CHANNEL, after=after, before=before, page_size=ps
                ).collect()
                id_sets[ps] = {m.id for m in msgs}

            sizes = [len(s) for s in id_sets.values()]
            counts = {ps: len(s) for ps, s in id_sets.items()}
            assert len(set(sizes)) == 1, f"different counts per page size: {counts}"
