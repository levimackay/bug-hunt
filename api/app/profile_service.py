from __future__ import annotations

import json

from sqlalchemy.orm import Session

from api.app import models
from scenario_engine.progression import distribute_skill_xp

PROFILE_ID = 1


def get_or_create_profile(db: Session) -> models.PlayerProfile:
    profile = db.get(models.PlayerProfile, PROFILE_ID)
    if profile is None:
        profile = models.PlayerProfile(id=PROFILE_ID, total_xp=0, skill_xp="{}")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def award_xp(db: Session, xp_awarded: int, skills: list[str]) -> models.PlayerProfile:
    profile = get_or_create_profile(db)
    skill_xp: dict[str, int] = json.loads(profile.skill_xp)

    profile.total_xp += xp_awarded
    for skill, share in distribute_skill_xp(xp_awarded, skills).items():
        skill_xp[skill] = skill_xp.get(skill, 0) + share
    profile.skill_xp = json.dumps(skill_xp)

    db.commit()
    db.refresh(profile)
    return profile
