from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _latest_status(db: Session, scenario_id: str) -> str:
    investigation = (
        db.query(models.Investigation)
        .filter(models.Investigation.scenario_id == scenario_id)
        .order_by(models.Investigation.started_at.desc())
        .first()
    )
    return investigation.status if investigation is not None else "not_started"


@router.get("")
def list_tickets(db: Session = Depends(get_db)):
    scenarios = db.query(models.Scenario).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "severity": s.severity,
            "difficulty": s.difficulty,
            "status": _latest_status(db, s.id),
        }
        for s in scenarios
    ]


@router.get("/{scenario_id}")
def get_ticket(scenario_id: str, db: Session = Depends(get_db)):
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
        "status": _latest_status(db, scenario.id),
    }
