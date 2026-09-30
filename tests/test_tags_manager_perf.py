"""TagsManagerDocker reads/writes must only touch the requested tag paths.

``get_tag`` / ``set_tags`` / ``flush_live_tags`` used to materialise the whole
device-wide tag channel (``apply_diff`` with a full ``copy.deepcopy``) on every
call. These tests pin the observable semantics of the cached-plus-pending view
and guard against the full-channel copy creeping back in.
"""

import copy
import logging
import random
import time

import pytest

from pydoover.tags import Delta, Tag, Tags
from pydoover.tags.manager import (
    KeyPath,
    TagsManagerDocker,
    _project_merged,
)
from pydoover.utils.diff import apply_diff, generate_diff


class _Client:
    def __init__(self):
        self.aggregate_updates = []
        self.oneshot_messages = []

    async def update_channel_aggregate(self, channel_name, data, **kwargs):
        self.aggregate_updates.append((channel_name, data))

    async def send_oneshot_message(self, channel_name, data, **kwargs):
        self.oneshot_messages.append((channel_name, data))


def _manager(tag_values=None, pending=None):
    manager = TagsManagerDocker(client=_Client(), app_key="app")
    manager._tag_values = tag_values if tag_values is not None else {}
    manager._pending_tag_aggregate = pending if pending is not None else {}
    return manager


def _big_channel():
    return {f"app_{a}": {f"tag_{t}": float(t) for t in range(80)} for a in range(12)}


class TestGetTagSemantics:
    def test_pending_none_returns_none_not_default(self):
        manager = _manager({"app": {"a": 1}}, {"app": {"a": None}})

        assert manager.get_tag("a", default="dflt", app_key="app") is None
        assert manager.get_tag("a", app_key="app", raise_key_error=True) is None

    def test_pending_none_for_uncached_key_exists(self):
        manager = _manager({}, {"app": {"a": None}})

        assert manager.get_tag("a", default="dflt", app_key="app") is None

    def test_cached_none_exists(self):
        manager = _manager({"app": {"a": None}})

        assert manager.get_tag("a", default="dflt", app_key="app") is None

    def test_missing_key_returns_default(self):
        manager = _manager({"app": {"a": 1}}, {"app": {"b": 2}})

        assert manager.get_tag("c", default="dflt", app_key="app") == "dflt"
        assert manager.get_tag("a", default="dflt", app_key="other") == "dflt"

    def test_pending_overrides_cached_leaf(self):
        manager = _manager({"app": {"a": 1, "b": 2}}, {"app": {"a": 10}})

        assert manager.get_tag("a", app_key="app") == 10
        assert manager.get_tag("b", app_key="app") == 2

    def test_subtree_read_returns_nested_merge(self):
        manager = _manager(
            {"app": {"a": 1, "nested": {"x": 1, "y": 2}}},
            {"app": {"b": 2, "nested": {"y": 20, "z": None}}},
        )

        assert manager.get_tag("app") == {
            "a": 1,
            "b": 2,
            "nested": {"x": 1, "y": 20, "z": None},
        }
        assert manager.get_tag(["app", "nested"]) == {"x": 1, "y": 20, "z": None}
        assert manager.get_tag("nested", app_key="app") == {
            "x": 1,
            "y": 20,
            "z": None,
        }

    def test_pending_non_dict_replaces_cached_dict(self):
        manager = _manager({"app": {"n": {"x": 1}}}, {"app": {"n": 5}})

        assert manager.get_tag("n", app_key="app") == 5
        # The cached child is hidden by the pending leaf.
        assert manager.get_tag(["n", "x"], default="dflt", app_key="app") == "dflt"
        with pytest.raises(KeyError):
            manager.get_tag(["n", "x"], app_key="app", raise_key_error=True)

    def test_pending_dict_replaces_cached_non_dict(self):
        manager = _manager({"app": {"n": 5}}, {"app": {"n": {"x": 1}}})

        assert manager.get_tag("n", app_key="app") == {"x": 1}
        assert manager.get_tag(["n", "x"], app_key="app") == 1

    def test_pending_dict_replaces_cached_none(self):
        manager = _manager({"app": {"n": None}}, {"app": {"n": {"x": 1}}})

        assert manager.get_tag("n", app_key="app") == {"x": 1}

    def test_descending_through_leaf_is_missing(self):
        manager = _manager({"app": {"a": 1}})

        assert manager.get_tag(["a", "b"], default="dflt", app_key="app") == "dflt"
        with pytest.raises(KeyError):
            manager.get_tag(["a", "b"], app_key="app", raise_key_error=True)

    def test_raise_key_error_on_missing(self):
        manager = _manager({"app": {"a": 1}})

        with pytest.raises(KeyError):
            manager.get_tag("missing", app_key="app", raise_key_error=True)

    def test_uninitialised_tag_values_reads_pending_only(self):
        # ``_on_tag_sync`` can store ``None`` for an empty channel.
        manager = _manager(None, {"app": {"a": 1}})
        manager._tag_values = None

        assert manager.get_tag("a", app_key="app") == 1
        assert manager.get_tag("b", default="dflt", app_key="app") == "dflt"

    def test_accepts_keypath(self):
        manager = _manager({"app": {"a": 1}})

        assert manager.get_tag(KeyPath("a", app_key="app")) == 1


class TestReadsDoNotMutateOrAlias:
    def test_subtree_read_cannot_mutate_manager_state(self):
        tag_values = {"app": {"a": 1, "nested": {"x": [1, 2]}}}
        pending = {"app": {"b": 2, "nested": {"y": {"deep": 1}}}}
        manager = _manager(tag_values, pending)
        before = (copy.deepcopy(tag_values), copy.deepcopy(pending))

        subtree = manager.get_tag("app")
        subtree["a"] = "mutated"
        subtree["new"] = "mutated"
        subtree["nested"]["x"].append(3)
        subtree["nested"]["y"]["deep"] = "mutated"
        cached_only = manager.get_tag(["app", "nested", "x"])
        cached_only.append(4)

        assert (manager._tag_values, manager._pending_tag_aggregate) == before
        assert manager.get_tag("app") == {
            "a": 1,
            "b": 2,
            "nested": {"x": [1, 2], "y": {"deep": 1}},
        }

    def test_pending_dict_over_cached_leaf_is_not_aliased(self):
        manager = _manager({"app": {"n": 5}}, {"app": {"n": {"x": 1}}})

        value = manager.get_tag("n", app_key="app")
        value["x"] = "mutated"

        assert manager._pending_tag_aggregate == {"app": {"n": {"x": 1}}}

    @pytest.mark.parametrize("cached", [5, None])
    def test_nested_pending_dict_over_cached_leaf_is_not_aliased(self, cached):
        manager = _manager(
            {"app": {"cfg": {"mode": cached}}}, {"app": {"cfg": {"mode": {"x": 1}}}}
        )

        value = manager.get_tag("cfg", app_key="app")
        value["mode"]["x"] = "mutated"

        assert manager._pending_tag_aggregate == {"app": {"cfg": {"mode": {"x": 1}}}}

    def test_pending_list_is_not_aliased(self):
        manager = _manager({"app": {}}, {"app": {"l": [1, {"x": 1}]}})

        value = manager.get_tag("l", app_key="app")
        value.append(2)
        value[1]["x"] = "mutated"

        assert manager._pending_tag_aggregate == {"app": {"l": [1, {"x": 1}]}}

    @pytest.mark.asyncio
    async def test_reads_and_unchanged_sets_leave_stores_untouched(self):
        tag_values = {"app": {"a": 1, "nested": {"x": 1}}, "other": {"z": 0}}
        pending = {"app": {"b": None}}
        manager = _manager(tag_values, pending)
        before = (copy.deepcopy(tag_values), copy.deepcopy(pending))

        manager.get_tag("a", app_key="app")
        manager.get_tag("missing", app_key="app")
        manager.get_tag("app")
        await manager.set_tags({"app": {"a": 1, "nested": {"x": 1}, "b": None}})

        assert (manager._tag_values, manager._pending_tag_aggregate) == before
        assert manager._tags_dirty is False


class TestSetTagsSemantics:
    @pytest.mark.asyncio
    async def test_set_none_over_value_produces_pending_none(self):
        manager = _manager({"app": {"a": 12.0}})

        await manager.set_tag("a", None, app_key="app")

        assert manager._pending_tag_aggregate == {"app": {"a": None}}
        assert manager._tags_dirty is True
        assert manager.get_tag("a", default="dflt", app_key="app") is None

    @pytest.mark.asyncio
    async def test_set_none_for_absent_key_produces_pending_none(self):
        manager = _manager({"app": {}})

        await manager.set_tag("a", None, app_key="app")

        assert manager._pending_tag_aggregate == {"app": {"a": None}}

    @pytest.mark.asyncio
    async def test_set_none_twice_is_unchanged(self):
        manager = _manager({"app": {"a": None}})

        await manager.set_tag("a", None, app_key="app")

        assert manager._pending_tag_aggregate == {}
        assert manager._tags_dirty is False

    @pytest.mark.asyncio
    async def test_unchanged_nested_value_produces_no_pending_change(self):
        manager = _manager({"app": {"n": {"x": 1, "y": {"z": 2}}, "other": 3}})

        await manager.set_tag("n", {"x": 1, "y": {"z": 2}}, app_key="app")
        await manager.set_tag("n", {"y": {"z": 2}}, app_key="app")

        assert manager._pending_tag_aggregate == {}
        assert manager._tags_dirty is False

    @pytest.mark.asyncio
    async def test_unchanged_against_pending_value_is_skipped(self):
        manager = _manager({"app": {"a": 1}}, {"app": {"a": 2}})

        await manager.set_tag("a", 2, app_key="app")
        assert manager._pending_tag_log == {}

        await manager.set_tag("a", 1, app_key="app")
        assert manager._pending_tag_aggregate == {"app": {"a": 1}}

    @pytest.mark.asyncio
    async def test_changed_nested_value_is_published(self):
        manager = _manager({"app": {"n": {"x": 1, "y": 2}}})

        await manager.set_tag("n", {"x": 1, "y": 3}, app_key="app")

        assert manager._pending_tag_aggregate == {"app": {"n": {"x": 1, "y": 3}}}
        assert manager.get_tag("n", app_key="app") == {"x": 1, "y": 3}

    @pytest.mark.asyncio
    async def test_dict_over_cached_leaf_is_a_change(self):
        manager = _manager({"app": {"n": 5}})

        await manager.set_tag("n", {"x": 1}, app_key="app")

        assert manager._pending_tag_aggregate == {"app": {"n": {"x": 1}}}

    @pytest.mark.asyncio
    async def test_leaf_over_cached_dict_is_a_change(self):
        manager = _manager({"app": {"n": {"x": 1}}})

        await manager.set_tag("n", 5, app_key="app")

        assert manager._pending_tag_aggregate == {"app": {"n": 5}}


def _random_value(rng, depth):
    roll = rng.random()
    if depth > 0 and roll < 0.35:
        return _random_tree(rng, depth - 1)
    if roll < 0.5:
        return None
    if roll < 0.6:
        return [rng.randint(0, 2)]
    return rng.randint(0, 2)


def _random_tree(rng, depth):
    return {
        rng.choice("abcd"): _random_value(rng, depth) for _ in range(rng.randint(0, 4))
    }


def _random_path(rng):
    return [rng.choice("abcd") for _ in range(rng.randint(1, 4))]


class TestEquivalenceWithFullMerge:
    """Compare against the previous implementation: a full ``apply_diff`` merge."""

    def test_get_tag_matches_full_merge(self):
        rng = random.Random(1234)
        sentinel = object()
        for _ in range(3000):
            tag_values = _random_tree(rng, 3)
            pending = _random_tree(rng, 3)
            manager = _manager(tag_values, pending)
            full = apply_diff(tag_values, pending, do_delete=False)
            key_path = KeyPath(_random_path(rng))

            if key_path.in_dict(full):
                expected = key_path.lookup_dict(full)
            else:
                expected = sentinel

            assert manager.get_tag(key_path, default=sentinel) == expected

    def test_set_tags_diff_matches_full_merge(self):
        rng = random.Random(4321)
        for _ in range(3000):
            tag_values = _random_tree(rng, 3)
            pending = _random_tree(rng, 3)
            tags = _random_tree(rng, 3)
            full = apply_diff(tag_values, pending, do_delete=False)

            expected = generate_diff(full, tags, do_delete=False)
            projected = _project_merged(tag_values, pending, tags)
            assert generate_diff(projected, tags, do_delete=False) == expected


class _ReprCountingDict(dict):
    repr_calls = 0

    def __repr__(self):
        type(self).repr_calls += 1
        return super().__repr__()


class _PerfTags(Tags):
    voltage = Tag("number", log_on=Delta(amount=1))
    speed = Tag("number", default=0)


class TestNoFullChannelCopy:
    @pytest.fixture
    def deepcopy_calls(self, monkeypatch):
        calls = []
        real_deepcopy = copy.deepcopy

        def counting_deepcopy(obj, *args, **kwargs):
            calls.append(obj)
            return real_deepcopy(obj, *args, **kwargs)

        monkeypatch.setattr(copy, "deepcopy", counting_deepcopy)
        return calls

    @pytest.mark.asyncio
    async def test_scalar_get_and_set_do_not_deepcopy(self, deepcopy_calls):
        manager = _manager(_big_channel(), {"app_0": {"tag_1": 99.0}})

        for i in range(50):
            manager.get_tag(f"tag_{i}", app_key="app_0")
            await manager.set_tag(f"tag_{i}", float(i + 1000), app_key="app_0")
            await manager.set_tag(f"tag_{i}", float(i + 1000), app_key="app_0")

        assert deepcopy_calls == []

    @pytest.mark.asyncio
    async def test_subtree_read_copies_only_that_subtree(self, deepcopy_calls):
        channel = _big_channel()
        manager = _manager(channel, {"app_1": {"tag_0": -1.0}})

        subtree = manager.get_tag("app_0")

        assert subtree == channel["app_0"]
        assert all(obj is not channel for obj in deepcopy_calls)
        for app_key, app_tags in channel.items():
            if app_key != "app_0":
                assert all(obj is not app_tags for obj in deepcopy_calls)

    @pytest.mark.asyncio
    async def test_flush_live_tags_does_not_copy_channel(self, deepcopy_calls):
        manager = _manager(_big_channel(), {"app_0": {"tag_1": 99.0}})
        now_ms = int(time.time() * 1000)
        manager.ui_sub_aggregate = {
            "live_tag_open": {
                "u1": {"ts": now_ms, "tags": ["app_0.tag_1", "app_3.tag_2"]}
            }
        }
        manager.set_live_tags(
            [("app_0", "tag_1"), ("app_3", "tag_2"), ("app_4", "tag_0")]
        )

        assert await manager.flush_live_tags() is True

        assert manager.client.oneshot_messages[-1][1] == {
            "app_0": {"tag_1": 99.0},
            "app_3": {"tag_2": 2.0},
        }
        assert deepcopy_calls == []

    @pytest.mark.asyncio
    async def test_bound_tag_get_and_set_do_not_deepcopy(self, deepcopy_calls):
        manager = _manager(_big_channel(), {"app_0": {"tag_1": 99.0}})
        tags = _PerfTags("app_0", manager, None)

        assert tags.speed.get() == 0
        for i in range(20):
            await tags.voltage.set(float(i))
            await tags.voltage.set(float(i))
            await tags.speed.set(i, log=True)
            assert tags.voltage.get() == float(i)
            assert tags.speed.get() == i

        assert manager._pending_immediate_log["app_0"] == {"voltage": 19.0, "speed": 19}
        assert deepcopy_calls == []

    @pytest.mark.asyncio
    async def test_unchanged_set_does_not_format_channel(self, caplog):
        channel = _ReprCountingDict(_big_channel())
        manager = _manager(channel)
        _ReprCountingDict.repr_calls = 0
        caplog.set_level(logging.DEBUG, logger="pydoover.tags.manager")

        await manager.set_tag("tag_1", 1.0, app_key="app_0")

        assert "Value did not change" in caplog.text
        assert _ReprCountingDict.repr_calls == 0
