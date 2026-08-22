from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_owned_investigation

router = APIRouter(prefix="/investigations", tags=["review"])


@router.get("/{investigation_id}/review")
def get_review(
    investigation: models.Investigation = Depends(get_owned_investigation),
    db: Session = Depends(get_db),
):
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
