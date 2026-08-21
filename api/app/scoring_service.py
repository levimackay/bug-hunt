from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from api.app import models
from scenario_engine.scoring import Score, compute_score

if TYPE_CHECKING:
    from scenario_engine.schema import Scenario


def compute_investigation_score(
    db: Session, investigation: models.Investigation, scenario: "Scenario"
) -> Score | None:
    if investigation.status != "resolved":
        return None

    pr = (
        db.query(models.PullRequest)
        .filter(models.PullRequest.investigation_id == investigation.id)
        .order_by(models.PullRequest.created_at.desc())
        .first()
    )
    diff = pr.diff if pr is not None else ""

    events = (
        db.query(models.InvestigationEvent)
        .filter(models.InvestigationEvent.investigation_id == investigation.id)
        .order_by(models.InvestigationEvent.timestamp, models.InvestigationEvent.id)
        .all()
    )
    event_dicts = [{"type": e.type, "payload": json.loads(e.payload)} for e in events]

    comments = (
        db.query(models.ReviewComment)
        .filter(models.ReviewComment.investigation_id == investigation.id)
        .all()
    )
    comment_dicts = [{"resolved": c.resolved} for c in comments]

    return compute_score(
        hidden_test_passed=investigation.status == "resolved",
        diff=diff,
        expected_fix_paths=scenario.scoring.expected_fix_paths,
        hidden_tests_path=scenario.hidden_tests,
        events=event_dicts,
        review_comments=comment_dicts,
        code_quality_checks=scenario.scoring.code_quality_checks,
    )
