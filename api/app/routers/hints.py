from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_owned_investigation
from api.app.events import log_event
from api.app.scenario_registry import get_scenario
from scenario_engine.investigation import next_hint

router = APIRouter(prefix="/investigations", tags=["hints"])


@router.post("/{investigation_id}/hints/next")
def reveal_next_hint(
    investigation: models.Investigation = Depends(get_owned_investigation),
    db: Session = Depends(get_db),
):
    scenario = get_scenario(investigation.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")

    revealed_count = (
        db.query(models.InvestigationEvent)
        .filter(
            models.InvestigationEvent.investigation_id == investigation.id,
            models.InvestigationEvent.type == "hint_used",
        )
        .count()
    )

    hint = next_hint(scenario.hints, revealed_count)
    if hint is None:
        raise HTTPException(status_code=404, detail="no more hints")

    log_event(db, investigation.id, "hint_used", {"index": revealed_count, "cost_xp": hint.cost_xp})

    return {"index": revealed_count, "cost_xp": hint.cost_xp, "text": hint.text}
