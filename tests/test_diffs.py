from pydoover.utils import apply_diff, generate_diff


class TestApplyDiff:
    def test_apply_diff_basic(self):
        x1 = {"a": 1, "b": 2, "c": 3}
        diff = {"c": 4}
        assert apply_diff(x1, diff) == {"a": 1, "b": 2, "c": 4}

    def test_apply_diff_remove(self):
        x1 = {"a": 1, "b": 2, "c": 3}
        diff = {"c": None}
        assert apply_diff(x1, diff) == {"a": 1, "b": 2}

    def test_apply_diff_nested(self):
        x1 = {"a": 1, "b": 2, "c": {"d": 3}}
        diff = {"c": {"d": 4}}
        assert apply_diff(x1, diff) == {"a": 1, "b": 2, "c": {"d": 4}}

    def test_apply_diff_nested_remove(self):
        x1 = {"a": 1, "b": 2, "c": {"d": 3}}
        diff = {"c": {"d": None}}
        assert apply_diff(x1, diff) == {"a": 1, "b": 2, "c": {}}

        x1 = {"a": 1, "b": 2, "c": {"d": 3, "e": 4}}
        diff = {"b": 3, "c": {"d": None}}
        assert apply_diff(x1, diff) == {"a": 1, "b": 3, "c": {"e": 4}}

    def test_apply_new_dict_old_string(self):
        x1 = "a"
        diff = {"a": 1}
        assert apply_diff(x1, diff) == {"a": 1}

    def test_apply_new_string_old_dict(self):
        x1 = {"a": 1}
        diff = "a"
        assert apply_diff(x1, diff) == "a"

    def test_apply_diff_nested_remove_no_delete(self):
        x1 = {"a": 1, "b": 2, "c": {"d": 3}}
        diff = {"c": {"d": None}}
        assert apply_diff(x1, diff, do_delete=False) == {
            "a": 1,
            "b": 2,
            "c": {"d": None},
        }

        x1 = {"a": 1, "b": 2, "c": {"d": 3, "e": 4}}
        diff = {"b": 3, "c": {"d": None}}
        assert apply_diff(x1, diff, do_delete=False) == {
            "a": 1,
            "b": 3,
            "c": {"e": 4, "d": None},
        }


class TestGenerateDiff:
    def test_generate_basic(self):
        x1 = {"a": 1, "b": 2, "c": 3}
        x2 = {"a": 1, "b": 2, "c": 4}
        assert generate_diff(x1, x2) == {"c": 4}

    def test_generate_remove(self):
        x1 = {"a": 1, "b": 2, "c": 3}
        x2 = {"a": 1, "b": 2}
        assert generate_diff(x1, x2) == {"c": None}

    def test_generate_nested(self):
        x1 = {"a": 1, "b": 2, "c": {"d": 3}}
        x2 = {"a": 1, "b": 2, "c": {"d": 4}}
        assert generate_diff(x1, x2) == {"c": {"d": 4}}

    def test_generate_nested_remove(self):
        x1 = {"a": 1, "b": 2, "c": {"d": 3}}
        x2 = {"a": 1, "b": 2, "c": {}}
        assert generate_diff(x1, x2) == {"c": {"d": None}}

        x1 = {"a": 1, "b": 2, "c": {"d": 3, "e": 4}}
        x2 = {"a": 1, "b": 2, "c": {"e": 4}}
        assert generate_diff(x1, x2) == {"c": {"d": None}}

    def test_generate_nested_same(self):
        x1 = {"a": 1, "b": 2, "c": {"d": 3}}
        x2 = {"a": 1, "b": 2, "c": {"d": 3}}
        assert generate_diff(x1, x2) == {}

    def test_generate_old_string_new_dict(self):
        x1 = "a"
        x2 = {"a": 1}
        assert generate_diff(x1, x2) == {"a": 1}

    def test_generate_new_string_old_dict(self):
        x1 = {"a": 1}
        x2 = "a"
        assert generate_diff(x1, x2) == "a"
