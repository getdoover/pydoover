from pydoover.tags import NotSet, Tag, Tags


class FakeTagsManager:
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


class MyAppTags(Tags):
    voltage = Tag("number")
    speed = Tag("number", default=0)


class TestTags:
    def test_class_attributes_are_templates(self):
        assert isinstance(MyAppTags.voltage, Tag)
        assert isinstance(MyAppTags.speed, Tag)

    def test_get_uses_manager(self):
        manager = FakeTagsManager({"voltage": 12.7})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.voltage == 12.7
        assert manager.get_calls == [("voltage", NotSet, None)]

    def test_get_returns_default_when_manager_has_no_value(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.speed == 0
        assert tags.voltage is NotSet

    def test_set_uses_manager(self):
        manager = FakeTagsManager()
        tags = MyAppTags()
        tags.register_manager(manager)

        tags.voltage = 13.1

        assert manager.set_calls == [("voltage", 13.1, None)]
        assert manager.values["voltage"] == 13.1

    def test_to_dict_reads_all_declared_tags_from_manager(self):
        manager = FakeTagsManager({"voltage": 12.7})
        tags = MyAppTags()
        tags.register_manager(manager)

        assert tags.to_dict() == {"voltage": 12.7, "speed": 0}

    def test_get_tag_returns_declared_tag_definition(self):
        tags = MyAppTags()

        voltage = tags.get_tag("voltage")
        assert isinstance(voltage, Tag)
        assert voltage.name is None
        assert voltage.tag_type == "number"

    def test_setting_without_manager_raises(self):
        tags = MyAppTags()

        try:
            tags.voltage = 1.0
        except RuntimeError as exc:
            assert "registered" in str(exc)
        else:
            raise AssertionError("Expected RuntimeError when manager is missing")
