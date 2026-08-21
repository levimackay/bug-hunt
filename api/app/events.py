from __future__ import annotations

import json

from sqlalchemy.orm import Session

from api.app.models import InvestigationEvent


def log_event(db: Session, investigation_id: int, event_type: str, payload: dict) -> None:
    event = InvestigationEvent(
        investigation_id=investigation_id,
        type=event_type,
        payload=json.dumps(payload),
    )
    db.add(event)
    db.commit()
