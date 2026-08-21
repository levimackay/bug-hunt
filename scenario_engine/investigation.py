from __future__ import annotations

from scenario_engine.schema import Hint

HIDDEN_TESTS_PREFIX = "hidden_tests/"


def is_visible_path(path: str) -> bool:
    return not path.startswith(HIDDEN_TESTS_PREFIX)


def visible_files(all_files: list[str]) -> list[str]:
    return [f for f in all_files if is_visible_path(f)]


def next_hint(hints: list[Hint], revealed_count: int) -> Hint | None:
    if revealed_count < 0 or revealed_count >= len(hints):
        return None
    return hints[revealed_count]
