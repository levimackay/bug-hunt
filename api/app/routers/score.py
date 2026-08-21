from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.scenario_registry import get_scenario
from api.app.scoring_service import compute_investigation_score

router = APIRouter(prefix="/investigations", tags=["score"])


@router.get("/{investigation_id}/score")
def get_score(investigation_id: int, db: Session = Depends(get_db)):
    investigation = db.get(models.Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="investigation not found")

    scenario = get_scenario(investigation.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")

    score = compute_investigation_score(db, investigation, scenario)
    if score is None:
        raise HTTPException(status_code=404, detail="investigation not yet resolved")

    return score.as_dict()
