from __future__ import annotations

from scenario_engine.progression import (
    XP_FOR_FULL_MASTERY,
    XP_PER_LEVEL,
    compute_level,
    compute_mastery_pct,
    distribute_skill_xp,
)


def test_distribute_skill_xp_splits_evenly():
    result = distribute_skill_xp(90, ["a", "b", "c"])
    assert result == {"a": 30, "b": 30, "c": 30}


def test_distribute_skill_xp_floors_uneven_split():
    result = distribute_skill_xp(10, ["a", "b", "c"])
    assert result == {"a": 3, "b": 3, "c": 3}


def test_distribute_skill_xp_empty_skills():
    assert distribute_skill_xp(100, []) == {}


def test_compute_level_starts_at_1():
    assert compute_level(0) == 1
    assert compute_level(XP_PER_LEVEL - 1) == 1
    assert compute_level(XP_PER_LEVEL) == 2
    assert compute_level(XP_PER_LEVEL * 3) == 4


def test_compute_mastery_pct_scales_to_full_mastery_constant():
    assert compute_mastery_pct(0) == 0
    assert compute_mastery_pct(XP_FOR_FULL_MASTERY // 2) == 50
    assert compute_mastery_pct(XP_FOR_FULL_MASTERY) == 100


def test_compute_mastery_pct_caps_at_100():
    assert compute_mastery_pct(XP_FOR_FULL_MASTERY * 5) == 100
