import pytest

from pydoover.tags import BoundTag, NotSet, Tag, Tags
from pydoover.tags.manager import KeyPath


class FakeTagsManager:
    _is_async = False

    def __init__(self, initial=None):
        self.values = initial or {}
        self.get_calls = []
        self.set_calls = []

    def get_tag(self, key, default=None, app_key=None):
        self.get_calls.append((key, default, app_key))
        return self.values.get(key, default)

    def set_tag(self, key, value, app_key=None):
        self.set_calls.append((key, value, app_key))
        self.values[key] = value


class AsyncFakeTagsManager(FakeTagsManager):
    _is_async = True

    async def set_tag_async(self, key, value, app_key=None):
        self.set_calls.append((key, value, app_key))
        self.values[key] = value


class MyAppTags(Tags):
    voltage = Tag("number")
    speed = Tag("number", default=0)
    enabled = Tag("boolean", default=False)


class TestTags:
    def test_class_attributes_are_templates(self):
        assert isinstance(MyAppTags.voltage, Tag)
        assert isinstance(MyAppTags.speed, Tag)

    def test_instance_access_returns_bound_proxy(self):
        tags = MyAppTags()

        assert isinstance(tags.voltage, BoundTag)
        assert tags.voltage.name == "voltage"
        assert tags.voltage.tag_type == "number"

    def test_get_uses_manager(self):
        manager = FakeTagsManager({"voltage": 12.7})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.voltage.get() == 12.7
        assert manager.get_calls == [("voltage", NotSet, None)]

    def test_get_returns_default_when_manager_has_no_value(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.speed.get() == 0
        assert tags.voltage.get() is NotSet

    def test_set_uses_manager(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        tags.voltage.set(13.1)

        assert manager.set_calls == [("voltage", 13.1, None)]
        assert manager.values["voltage"] == 13.1

    def test_assignment_still_sets_via_manager(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        tags.voltage = 10.5

        assert manager.values["voltage"] == 10.5

    def test_increment_and_decrement_use_manager(self):
        manager = FakeTagsManager({"voltage": 12.0})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.voltage.increment() == 13.0
        assert tags.voltage.decrement(0.5) == 12.5
        assert manager.values["voltage"] == 12.5

    def test_increment_non_numeric_tag_raises(self):
        manager = FakeTagsManager({"enabled": True})
        tags = MyAppTags()
        tags.register_manager(manager)

        with pytest.raises(TypeError):
            tags.enabled.increment()

    def test_to_dict_reads_all_declared_tags_from_manager(self):
        manager = FakeTagsManager({"voltage": 12.7})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.to_dict() == {"voltage": 12.7, "speed": 0, "enabled": False}

    def test_get_tag_returns_bound_tag(self):
        manager = FakeTagsManager({"voltage": 12.4})
        tags = MyAppTags()
        tags.register_manager(manager)

        voltage = tags.get_tag("voltage")
        assert isinstance(voltage, BoundTag)
        assert voltage.get() == 12.4

    def test_get_definition_returns_declared_tag_definition(self):
        tags = MyAppTags()

        voltage = tags.get_definition("voltage")
        assert isinstance(voltage, Tag)
        assert voltage.name is None
        assert voltage.tag_type == "number"

    def test_setting_without_manager_raises(self):
        tags = MyAppTags()

        with pytest.raises(RuntimeError):
            tags.voltage.set(1.0)

    def test_value_like_dunders(self):
        manager = FakeTagsManager({"voltage": 12.7, "enabled": True})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert str(tags.voltage) == "12.7"
        assert float(tags.voltage) == 12.7
        assert int(tags.speed) == 0
        assert bool(tags.enabled) is True
        assert tags.voltage > 10
        assert tags.voltage >= 12.7
        assert tags.voltage == 12.7

    def test_async_set_uses_async_manager_path(self):
        import asyncio

        manager = AsyncFakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        asyncio.run(tags.voltage.set(14.2))

        assert manager.values["voltage"] == 14.2
        assert manager.set_calls == [("voltage", 14.2, None)]

    def test_async_increment_uses_async_manager_path(self):
        import asyncio

        manager = AsyncFakeTagsManager({"voltage": 11.0})
        tags = MyAppTags()
        tags.register_manager(manager)

        new_value = asyncio.run(tags.voltage.increment(2.5))

        assert new_value == 13.5
        assert manager.values["voltage"] == 13.5


class TestKeyPath:
    def test_single_key_path(self):
        path = KeyPath("voltage")

        assert path.get() == ["voltage"]
        assert path.construct_dict(12.7) == {"voltage": 12.7}
        assert path.lookup_dict({"voltage": 12.7}) == 12.7

    def test_list_key_path(self):
        path = KeyPath(["metrics", "voltage"])

        assert path.get() == ["metrics", "voltage"]
        assert path.construct_dict(12.7) == {"metrics": {"voltage": 12.7}}
        assert path.lookup_dict({"metrics": {"voltage": 12.7}}) == 12.7

    def test_app_key_is_prepended(self):
        path = KeyPath("voltage", app_key="my_app")

        assert path.get() == ["my_app", "voltage"]
        assert path.construct_dict(12.7) == {"my_app": {"voltage": 12.7}}
        assert path.lookup_dict({"my_app": {"voltage": 12.7}}) == 12.7

    def test_lookup_missing_returns_none(self):
        path = KeyPath(["metrics", "voltage"])

        assert path.lookup_dict({"metrics": {}}) is None
        assert path.lookup_dict({"metrics": 1}) is None

    def test_in_dict(self):
        path = KeyPath(["metrics", "voltage"])

        assert path.in_dict({"metrics": {"voltage": 12.7}}) is True
        assert path.in_dict({"metrics": {}}) is False
        assert path.in_dict({"metrics": 1}) is False

    def test_invalid_path_raises(self):
        with pytest.raises(ValueError):
            KeyPath([])

        with pytest.raises(ValueError):
            KeyPath(["valid", ""])
            
    def test_equality(self):
        assert KeyPath("voltage") == ["voltage"]
        assert KeyPath(["metrics", "voltage"]) == ["metrics", "voltage"]
        assert KeyPath("voltage") == "voltage"
        assert not KeyPath(["metrics", "voltage"]) == "metrics.voltage"
        assert KeyPath("voltage") == KeyPath(["voltage"])
        assert KeyPath(["metrics", "voltage"]) == KeyPath(["metrics", "voltage"])
        
    def test_dict(self):
        tags_dict = {
            KeyPath("voltage"): 1,
            KeyPath(["metrics", "voltage"]): 2,
        }
        assert KeyPath("voltage") in tags_dict
        assert KeyPath(["metrics", "voltage"]) in tags_dict
        assert tags_dict[KeyPath("voltage")] == 1
        assert tags_dict[KeyPath(["metrics", "voltage"])] == 2
