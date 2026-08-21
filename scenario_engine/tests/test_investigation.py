from __future__ import annotations

from scenario_engine.investigation import is_visible_path, next_hint, visible_files
from scenario_engine.schema import Hint


def test_visible_files_excludes_hidden_tests():
    all_files = ["app/main.py", "tests/test_upload.py", "hidden_tests/test_upload_regression.py"]
    result = visible_files(all_files)
    assert result == ["app/main.py", "tests/test_upload.py"]


def test_is_visible_path():
    assert is_visible_path("app/main.py") is True
    assert is_visible_path("hidden_tests/test_upload_regression.py") is False


def test_next_hint_progresses_in_order():
    hints = [Hint(cost_xp=5, text="a"), Hint(cost_xp=10, text="b")]
    assert next_hint(hints, 0) == hints[0]
    assert next_hint(hints, 1) == hints[1]
    assert next_hint(hints, 2) is None
    assert next_hint(hints, -1) is None
