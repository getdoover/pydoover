"""TagsManagerDocker keeps ``_tag_values`` as the cloud state with local writes
applied on top, so reads and change checks never copy the whole tag channel.
Local writes include flushed ones the device agent hasn't echoed back yet, so a
stale aggregate event can't revert them.
"""

import copy
import logging
import time
from types import SimpleNamespace as NS

import pytest

import pydoover.tags.manager as manager_module
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


def _event(data, request):
    # An AggregateUpdateEvent as the device agent sends it: the channel's
    # aggregate after a write, plus that write (``request_data``).
    return NS(aggregate=NS(data=data), request_data=NS(data=request))


class _FailingClient(_Client):
    async def update_channel_aggregate(self, channel_name, data, **kwargs):
        raise ConnectionError("device agent unavailable")


@pytest.fixture
def clock(monkeypatch):
    # Drive the manager's monotonic clock without touching the event loop's.
    now = [1000.0]
    monkeypatch.setattr(
        manager_module, "time", NS(monotonic=lambda: now[0], time=time.time)
    )
    return now


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
    async def test_update_with_in_flight_writes_does_not_copy_channel(
        self, deepcopy_calls
    ):
        manager = _manager(_big_channel())
        manager.subscribe_to_tag("tag_0", lambda k, v: None, app_key="app_1")
        await manager.set_tag("tag_1", -1.0, app_key="app_0", flush=True)

        for i in range(10):
            channel = _big_channel()
            channel["app_1"]["tag_0"] = float(i)
            await manager._on_tag_update(_event(channel, {"app_1": {"tag_0": i}}))

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


class TestStaleEcho:
    """A flushed write must survive aggregate events that predate it.

    The device agent sends every aggregate event — including the echo of each
    of our own writes — down one ordered stream, but an event already queued
    before our write reached the agent still carries the old value. Found in
    the field: a DCS result went OK -> PENDING -> OK, a stale aggregate (OK)
    landed after PENDING was flushed, so the final OK looked unchanged and was
    never sent; the channel stayed PENDING.
    """

    @staticmethod
    def _sent(manager):
        return [data for _, data in manager.client.aggregate_updates]

    @pytest.mark.asyncio
    async def test_value_returning_to_earlier_survives_stale_event(self):
        manager = _manager({"app": {"result": 0, "other": 0}})
        await manager.set_tag("result", 2, app_key="app", flush=True)
        await manager._on_tag_update(
            _event({"app": {"result": 2}}, {"app": {"result": 2}})
        )
        await manager.set_tag("result", 1, app_key="app", flush=True)

        # Queued before the agent applied result=1: another writer's update.
        await manager._on_tag_update(
            _event({"app": {"result": 2, "other": 5}}, {"app": {"other": 5}})
        )
        await manager.set_tag("result", 2, app_key="app", flush=True)

        # The final write must go out, or the channel is left on 1.
        assert self._sent(manager) == [
            {"app": {"result": 2}},
            {"app": {"result": 1}},
            {"app": {"result": 2}},
        ]
        assert manager.get_tag("other", app_key="app") == 5

        # The echoes of 1 and 2 arrive in order; the value ends on 2.
        await manager._on_tag_update(
            _event({"app": {"result": 1, "other": 5}}, {"app": {"result": 1}})
        )
        assert manager.get_tag("result", app_key="app") == 2
        await manager._on_tag_update(
            _event({"app": {"result": 2, "other": 5}}, {"app": {"result": 2}})
        )
        assert manager.get_tag("result", app_key="app") == 2
        assert manager._in_flight == {}

    @pytest.mark.asyncio
    async def test_late_echo_of_earlier_write_does_not_confirm_later_one(self):
        # A -> B -> A with every echo late: the echo of the first A holds the
        # value we last sent but predates B, so it must not end the tracking.
        manager = _manager({"app": {"result": 0}})
        await manager.set_tag("result", 2, app_key="app", flush=True)
        await manager.set_tag("result", 1, app_key="app", flush=True)
        await manager.set_tag("result", 2, app_key="app", flush=True)

        await manager._on_tag_update(
            _event({"app": {"result": 2}}, {"app": {"result": 2}})
        )
        await manager._on_tag_update(
            _event({"app": {"result": 1}}, {"app": {"result": 1}})
        )
        assert manager.get_tag("result", app_key="app") == 2

        # Still B in the cache would drop this; it must be sent.
        await manager.set_tag("result", 1, app_key="app", flush=True)
        assert self._sent(manager)[-1] == {"app": {"result": 1}}

    @pytest.mark.asyncio
    async def test_stale_event_without_request_data_is_overridden(self):
        manager = _manager({"app": {"result": 2}})
        await manager.set_tag("result", 1, app_key="app", flush=True)

        await manager._on_tag_sync(_update({"app": {"result": 2}}))
        assert manager.get_tag("result", app_key="app") == 1

        await manager.set_tag("result", 2, app_key="app", flush=True)
        assert self._sent(manager)[-1] == {"app": {"result": 2}}

    @pytest.mark.asyncio
    async def test_unflushed_write_still_wins_over_in_flight(self):
        manager = _manager({"app": {"result": 0}})
        await manager.set_tag("result", 1, app_key="app", flush=True)
        await manager.set_tag("result", 2, app_key="app")

        await manager._on_tag_update(_event({"app": {"result": 0}}, {"app": {"x": 1}}))

        assert manager.get_tag("result", app_key="app") == 2
        assert manager._pending_tag_aggregate == {"app": {"result": 2}}

    @pytest.mark.asyncio
    async def test_echo_confirms_and_later_change_is_adopted(self):
        manager = _manager({"app": {"result": 0}})
        await manager.set_tag("result", 1, app_key="app", flush=True)
        assert set(manager._in_flight) == {("app", "result")}

        await manager._on_tag_update(
            _event({"app": {"result": 1}}, {"app": {"result": 1}})
        )
        assert manager._in_flight == {}

        # Another writer changes it straight after: adopted, no timeout needed.
        await manager._on_tag_update(
            _event({"app": {"result": 7}}, {"app": {"result": 7}})
        )
        assert manager.get_tag("result", app_key="app") == 7

    @pytest.mark.asyncio
    async def test_each_send_needs_its_own_echo(self):
        manager = _manager({"app": {"result": 0}})
        await manager.set_tag("result", 1, app_key="app", flush=True)
        await manager.set_tag("result", 2, app_key="app", flush=True)

        await manager._on_tag_update(
            _event({"app": {"result": 1}}, {"app": {"result": 1}})
        )
        assert manager.get_tag("result", app_key="app") == 2
        assert manager._in_flight[("app", "result")].unconfirmed == 1

        await manager._on_tag_update(
            _event({"app": {"result": 2}}, {"app": {"result": 2}})
        )
        assert manager._in_flight == {}

    @pytest.mark.asyncio
    async def test_aggregate_holding_the_value_confirms_without_request_data(self):
        manager = _manager({"app": {"result": 0}})
        await manager.set_tag("result", 1, app_key="app", flush=True)

        await manager._on_tag_sync(_update({"app": {"result": 1}}))

        assert manager._in_flight == {}

    @pytest.mark.asyncio
    async def test_external_change_is_adopted_after_timeout(self, clock):
        manager = _manager({"app": {"result": 0}})
        await manager.set_tag("result", 1, app_key="app", flush=True)
        # Our echo is lost; another writer's value arrives in events that
        # don't carry a write to this tag.
        clock[0] += manager.in_flight_timeout - 0.5
        await manager._on_tag_update(_event({"app": {"result": 9}}, {"app": {"x": 1}}))
        assert manager.get_tag("result", app_key="app") == 1

        clock[0] += 1.0
        await manager._on_tag_update(_event({"app": {"result": 9}}, {"app": {"x": 2}}))
        assert manager.get_tag("result", app_key="app") == 9
        assert manager._in_flight == {}

    @pytest.mark.asyncio
    async def test_timeout_runs_from_latest_send(self, clock):
        manager = _manager({"app": {"result": 0}})
        await manager.set_tag("result", 1, app_key="app", flush=True)
        clock[0] += manager.in_flight_timeout - 1
        await manager.set_tag("result", 2, app_key="app", flush=True)
        clock[0] += 2

        await manager._on_tag_sync(_update({"app": {"result": 0}}))

        assert manager.get_tag("result", app_key="app") == 2

    @pytest.mark.asyncio
    async def test_configurable_timeout(self, clock):
        manager = TagsManagerDocker(client=_Client(), in_flight_timeout=1.0)
        manager._tag_values = {"app": {"result": 0}}
        await manager.set_tag("result", 1, app_key="app", flush=True)

        clock[0] += 1.5
        await manager._on_tag_sync(_update({"app": {"result": 0}}))

        assert manager.get_tag("result", app_key="app") == 0

    @pytest.mark.asyncio
    async def test_no_subscription_callback_for_in_flight_key(self):
        manager = _manager({"app": {"result": 2}, "other": {"z": 0}})
        seen = []
        manager.subscribe_to_tag("result", lambda k, v: seen.append(v), app_key="app")
        others = []
        manager.subscribe_to_tag("z", lambda k, v: others.append(v), app_key="other")
        await manager.set_tag("result", 1, app_key="app", flush=True)

        # Stale for our key, genuinely new for another.
        await manager._on_tag_update(
            _event({"app": {"result": 2}, "other": {"z": 4}}, {"other": {"z": 4}})
        )
        # Our own echo.
        await manager._on_tag_update(
            _event({"app": {"result": 1}, "other": {"z": 4}}, {"app": {"result": 1}})
        )
        assert seen == []
        assert others == [4]

        # Once confirmed, a real change by someone else does notify.
        await manager._on_tag_update(
            _event({"app": {"result": 3}, "other": {"z": 4}}, {"app": {"result": 3}})
        )
        assert seen == [3]

    @pytest.mark.asyncio
    async def test_nested_path_with_app_key(self):
        manager = _manager({"app": {"dcs": {"result": 2, "error": 0}}})
        seen = []
        manager.subscribe_to_tag(
            ["dcs", "result"], lambda k, v: seen.append(v), app_key="app"
        )
        await manager.set_tag(["dcs", "result"], 1, app_key="app", flush=True)
        assert set(manager._in_flight) == {("app", "dcs", "result")}

        await manager._on_tag_update(
            _event(
                {"app": {"dcs": {"result": 2, "error": 3}}},
                {"app": {"dcs": {"error": 3}}},
            )
        )
        assert manager.get_tag(["dcs", "result"], app_key="app") == 1
        assert manager.get_tag(["dcs", "error"], app_key="app") == 3
        assert seen == []

        await manager.set_tag(["dcs", "result"], 2, app_key="app", flush=True)
        assert self._sent(manager)[-1] == {"app": {"dcs": {"result": 2}}}

    @pytest.mark.asyncio
    async def test_in_flight_path_is_restored_when_stale_event_lacks_parent(self):
        manager = _manager({})
        await manager.set_tag("result", 1, app_key="app", flush=True)

        await manager._on_tag_update(_event({"other": {"z": 1}}, {"other": {"z": 1}}))

        assert manager.get_tag("result", app_key="app") == 1
        assert manager.get_tag("z", app_key="other") == 1

    @pytest.mark.asyncio
    async def test_delete_survives_stale_event(self):
        manager = _manager({"app": {"result": 2}})
        await manager.set_tag("result", None, app_key="app", flush=True)

        await manager._on_tag_update(_event({"app": {"result": 2}}, {"app": {"x": 1}}))
        assert manager.get_tag("result", app_key="app") is None

        # Deleting again is still a no-op; restoring the old value is sent.
        await manager.set_tag("result", None, app_key="app", flush=True)
        await manager.set_tag("result", 2, app_key="app", flush=True)
        assert self._sent(manager) == [
            {"app": {"result": None}},
            {"app": {"result": 2}},
        ]

    @pytest.mark.asyncio
    async def test_delete_is_confirmed_by_its_echo(self):
        manager = _manager({"app": {"result": 2}})
        await manager.set_tag("result", None, app_key="app", flush=True)

        # The agent drops a None key from the aggregate.
        await manager._on_tag_update(_event({"app": {}}, {"app": {"result": None}}))

        assert manager._in_flight == {}
        assert manager.get_tag("result", app_key="app") is None

    @pytest.mark.asyncio
    async def test_delete_is_confirmed_by_missing_key_without_request_data(self):
        manager = _manager({"app": {"result": 2}})
        await manager.set_tag("result", None, app_key="app", flush=True)

        await manager._on_tag_sync(_update({"app": {}}))

        assert manager._in_flight == {}

    @pytest.mark.asyncio
    async def test_failed_send_is_not_held_in_flight(self):
        manager = TagsManagerDocker(client=_FailingClient(), app_key="app")
        manager._tag_values = {"app": {"result": 2}}

        with pytest.raises(ConnectionError):
            await manager.set_tag("result", 1, app_key="app", flush=True)

        assert manager._in_flight == {}
        await manager._on_tag_update(_event({"app": {"result": 2}}, {"app": {"x": 1}}))
        assert manager.get_tag("result", app_key="app") == 2

    @pytest.mark.asyncio
    async def test_flush_tags_tracks_buffered_writes(self):
        manager = _manager({"app": {"a": 0, "b": 0}})
        await manager.set_tag("a", 1, app_key="app")
        await manager.set_tag("b", 1, app_key="app")
        assert manager._in_flight == {}

        await manager.flush_tags()

        assert set(manager._in_flight) == {("app", "a"), ("app", "b")}
        await manager._on_tag_update(
            _event({"app": {"a": 0, "b": 0}}, {"app": {"c": 1}})
        )
        assert manager.get_tag("a", app_key="app") == 1
        assert manager.get_tag("b", app_key="app") == 1
