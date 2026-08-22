from __future__ import annotations

import json

from sqlalchemy.orm import Session

from api.app import models
from scenario_engine.progression import distribute_skill_xp


def get_or_create_profile(db: Session, user_id: int) -> models.PlayerProfile:
    profile = db.get(models.PlayerProfile, user_id)
    if profile is None:
        profile = models.PlayerProfile(user_id=user_id, total_xp=0, skill_xp="{}")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def award_xp(
    db: Session, user_id: int, xp_awarded: int, skills: list[str]
) -> models.PlayerProfile:
    profile = get_or_create_profile(db, user_id)
    skill_xp: dict[str, int] = json.loads(profile.skill_xp)

    profile.total_xp += xp_awarded
    for skill, share in distribute_skill_xp(xp_awarded, skills).items():
        skill_xp[skill] = skill_xp.get(skill, 0) + share
    profile.skill_xp = json.dumps(skill_xp)

    db.commit()
    db.refresh(profile)
    return profile
