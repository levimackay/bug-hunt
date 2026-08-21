from __future__ import annotations

XP_PER_LEVEL = 500
XP_FOR_FULL_MASTERY = 200


def distribute_skill_xp(xp_awarded: int, skills: list[str]) -> dict[str, int]:
    if not skills:
        return {}
    share = xp_awarded // len(skills)
    return {skill: share for skill in skills}


def compute_level(total_xp: int) -> int:
    return total_xp // XP_PER_LEVEL + 1


def compute_mastery_pct(skill_xp: int) -> int:
    return min(100, skill_xp * 100 // XP_FOR_FULL_MASTERY)
