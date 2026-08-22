from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_owned_investigation
from api.app.scenario_registry import get_scenario
from api.app.scoring_service import compute_investigation_score

router = APIRouter(prefix="/investigations", tags=["score"])


@router.get("/{investigation_id}/score")
def get_score(
    investigation: models.Investigation = Depends(get_owned_investigation),
    db: Session = Depends(get_db),
):
    scenario = get_scenario(investigation.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")

    score = compute_investigation_score(db, investigation, scenario)
    if score is None:
        raise HTTPException(status_code=404, detail="investigation not yet resolved")

    return score.as_dict()
