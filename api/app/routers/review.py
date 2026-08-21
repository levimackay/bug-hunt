from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db

router = APIRouter(prefix="/investigations", tags=["review"])


@router.get("/{investigation_id}/review")
def get_review(investigation_id: int, db: Session = Depends(get_db)):
    investigation = db.get(models.Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="investigation not found")

    comments = (
        db.query(models.ReviewComment)
        .filter(models.ReviewComment.investigation_id == investigation.id)
        .order_by(models.ReviewComment.created_at)
        .all()
    )

    return {
        "comments": [
            {"id": c.id, "author": c.author, "body": c.body, "resolved": c.resolved}
            for c in comments
        ]
    }
