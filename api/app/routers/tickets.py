from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_current_user

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _latest_status(db: Session, scenario_id: str, user_id: int) -> str:
    investigation = (
        db.query(models.Investigation)
        .filter(
            models.Investigation.scenario_id == scenario_id,
            models.Investigation.user_id == user_id,
        )
        .order_by(models.Investigation.started_at.desc(), models.Investigation.id.desc())
        .first()
    )
    return investigation.status if investigation is not None else "not_started"


@router.get("")
def list_tickets(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    scenarios = db.query(models.Scenario).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "severity": s.severity,
            "difficulty": s.difficulty,
            "status": _latest_status(db, s.id, user.id),
        }
        for s in scenarios
    ]


@router.get("/{scenario_id}")
def get_ticket(
    scenario_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    scenario = db.get(models.Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="ticket not found")

    metadata = json.loads(scenario.metadata_json)

    return {
        "id": scenario.id,
        "title": scenario.title,
        "company": scenario.company,
        "severity": scenario.severity,
        "difficulty": scenario.difficulty,
        "ticket": {
            "reporter": scenario.ticket_reporter,
            "body": scenario.ticket_body,
            "slack_thread": metadata["slack_thread"],
        },
        "entry_service": scenario.entry_service,
        "status": _latest_status(db, scenario.id, user.id),
    }
