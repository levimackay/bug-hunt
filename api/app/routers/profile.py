from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_current_user
from api.app.profile_service import get_or_create_profile
from scenario_engine.progression import compute_level, compute_mastery_pct

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
def get_profile(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    profile = get_or_create_profile(db, user.id)
    skill_xp: dict[str, int] = json.loads(profile.skill_xp)

    return {
        "username": user.username,
        "total_xp": profile.total_xp,
        "level": compute_level(profile.total_xp),
        "skills": [
            {"name": name, "xp": xp, "mastery_pct": compute_mastery_pct(xp)}
            for name, xp in skill_xp.items()
        ],
    }
