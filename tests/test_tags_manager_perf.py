"""TagsManagerDocker keeps ``_tag_values`` as the cloud state with local writes
applied on top, so reads and change checks never copy the whole tag channel.
"""

import copy
import logging
from types import SimpleNamespace as NS

import pytest

from pydoover.tags import Delta, Tag, Tags
from pydoover.tags.manager import TagsManagerDocker


class _Client:
    def __init__(self):
        self.aggregate_updates = []

    async def update_channel_aggregate(self, channel_name, data, **kwargs):
        self.aggregate_updates.append((channel_name, data))


def _manager(tag_values=None):
    manager = TagsManagerDocker(client=_Client(), app_key="app")
    manager._tag_values = tag_values if tag_values is not None else {}
    return manager


def _big_channel():
    return {f"app_{a}": {f"tag_{t}": float(t) for t in range(80)} for a in range(12)}


def _update(data):
    return NS(aggregate=NS(data=data))


@pytest.fixture
def deepcopy_calls(monkeypatch):
    calls = []
    real_deepcopy = copy.deepcopy

    def counting_deepcopy(obj, *args, **kwargs):
        calls.append(obj)
        return real_deepcopy(obj, *args, **kwargs)

    monkeypatch.setattr(copy, "deepcopy", counting_deepcopy)
    return calls


class _PerfTags(Tags):
    voltage = Tag("number", log_on=Delta(amount=1))
    speed = Tag("number", default=0)


class _ReprCountingDict(dict):
    repr_calls = 0

    def __repr__(self):
        type(self).repr_calls += 1
        return super().__repr__()


class TestNoFullChannelCopy:
    @pytest.mark.asyncio
    async def test_bound_tag_get_and_set_do_not_deepcopy(self, deepcopy_calls):
        manager = _manager(_big_channel())
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
    async def test_update_does_not_copy_channel(self, deepcopy_calls):
        manager = _manager(_big_channel())
        manager.subscribe_to_tag("tag_0", lambda k, v: None, app_key="app_1")
        await manager.set_tag("tag_1", -1.0, app_key="app_0")

        for i in range(10):
            channel = _big_channel()
            channel["app_1"]["tag_0"] = float(i)
            await manager._on_tag_update(_update(channel))

        assert deepcopy_calls == []
        assert manager.get_tag("tag_1", app_key="app_0") == -1.0

    @pytest.mark.asyncio
    async def test_unchanged_set_does_not_format_channel(self, caplog):
        manager = _manager(_ReprCountingDict(_big_channel()))
        _ReprCountingDict.repr_calls = 0
        caplog.set_level(logging.DEBUG, logger="pydoover.tags.manager")

        await manager.set_tag("tag_1", 1.0, app_key="app_0")

        assert "Value did not change" in caplog.text
        assert _ReprCountingDict.repr_calls == 0


class TestCloudUpdates:
    @pytest.mark.asyncio
    async def test_update_keeps_unflushed_local_writes(self):
        manager = _manager({"app": {"a": 1}, "other": {"z": 0}})
        await manager.set_tag("a", 2, app_key="app")

        await manager._on_tag_update(_update({"app": {"a": 1}, "other": {"z": 5}}))

        assert manager.get_tag("a", app_key="app") == 2
        assert manager.get_tag("z", app_key="other") == 5
        assert manager._pending_tag_aggregate == {"app": {"a": 2}}

    @pytest.mark.asyncio
    async def test_subscription_fires_for_remote_change(self):
        manager = _manager({"other": {"z": 0}})
        seen = []
        manager.subscribe_to_tag("z", lambda k, v: seen.append(v), app_key="other")

        await manager._on_tag_update(_update({"other": {"z": 1}}))

        assert seen == [1]

    @pytest.mark.asyncio
    async def test_subscription_skips_locally_pending_key(self):
        manager = _manager({"app": {"a": 1}})
        seen = []
        manager.subscribe_to_tag("a", lambda k, v: seen.append(v), app_key="app")
        await manager.set_tag("a", 2, app_key="app")

        # The cloud hasn't seen our write yet, so still reports the old value.
        await manager._on_tag_update(_update({"app": {"a": 1}}))

        assert seen == []
        assert manager.get_tag("a", app_key="app") == 2


class TestWriteThrough:
    @pytest.mark.asyncio
    async def test_mutating_a_read_list_then_setting_it_is_a_change(self):
        manager = _manager({"app": {"l": [1]}})

        value = manager.get_tag("l", app_key="app")
        value.append(2)
        await manager.set_tag("l", value, app_key="app")

        assert manager._pending_tag_aggregate == {"app": {"l": [1, 2]}}

    @pytest.mark.asyncio
    async def test_cleared_tag_is_not_republished_after_flush(self):
        manager = _manager({"app": {"a": 1}})

        await manager.set_tag("a", None, app_key="app")
        await manager.flush_tags()
        await manager.set_tag("a", None, app_key="app")

        assert manager.client.aggregate_updates == [
            ("tag_values", {"app": {"a": None}})
        ]
        assert manager._tags_dirty is False

    @pytest.mark.asyncio
    async def test_flush_with_nested_none_over_leaf(self):
        # With a leaf in both stores, writing a dict over it leaves both
        # sharing the same dict; flushing must not apply the diff onto itself.
        manager = _manager({"app": {"n": 5}})
        await manager.set_tag("n", 6, app_key="app")

        await manager.set_tag("n", {"x": None, "y": 1}, app_key="app", flush=True)

        assert manager.get_tag("n", app_key="app") == {"x": None, "y": 1}
