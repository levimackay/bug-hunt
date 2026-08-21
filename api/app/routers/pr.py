from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_execution_backend
from api.app.events import log_event
from api.app.profile_service import award_xp
from api.app.scenario_registry import get_scenario
from api.app.scoring_service import compute_investigation_score
from scenario_engine.evaluation import run_hidden_tests
from scenario_engine.investigation import visible_files
from scenario_engine.review import generate_review_comments
from sandbox.base import ExecutionBackend

router = APIRouter(prefix="/investigations", tags=["pr"])


class SubmitRequest(BaseModel):
    pr_title: str
    pr_description: str


def _get_investigation(db: Session, investigation_id: int) -> models.Investigation:
    investigation = db.get(models.Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="investigation not found")
    return investigation


@router.post("/{investigation_id}/submit")
def submit_investigation(
    investigation_id: int,
    body: SubmitRequest,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = _get_investigation(db, investigation_id)
    scenario = get_scenario(investigation.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")

    investigation.status = "submitted"
    db.commit()

    diff_result = backend.run_command(investigation.sandbox_workspace_id, ["git", "diff"])

    pr = models.PullRequest(
        investigation_id=investigation.id,
        title=body.pr_title,
        description=body.pr_description,
        diff=diff_result.stdout,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)

    hidden_result = run_hidden_tests(backend, investigation.sandbox_workspace_id, scenario)

    comments = generate_review_comments(scenario, hidden_result, body.pr_description)
    for comment in comments:
        db.add(
            models.ReviewComment(
                investigation_id=investigation.id,
                author=comment["author"],
                body=comment["body"],
                resolved=comment["resolved"],
            )
        )

    if hidden_result.passed:
        investigation.status = "resolved"
        investigation.resolved_at = datetime.now(timezone.utc)
    else:
        investigation.status = "in_review"

    db.commit()

    log_event(
        db,
        investigation.id,
        "command_run",
        {
            "action": "submit",
            "hidden_tests_passed": hidden_result.passed,
            "exit_code": hidden_result.exit_code,
        },
    )

    if investigation.status == "resolved":
        score = compute_investigation_score(db, investigation, scenario)
        if score is not None:
            award_xp(db, score.overall, scenario.skills)

    return {"pr_id": pr.id, "passed": hidden_result.passed, "status": investigation.status}


@router.get("/{investigation_id}/pr")
def get_pr(
    investigation_id: int,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = _get_investigation(db, investigation_id)

    pr = (
        db.query(models.PullRequest)
        .filter(models.PullRequest.investigation_id == investigation.id)
        .order_by(models.PullRequest.created_at.desc())
        .first()
    )
    if pr is None:
        raise HTTPException(status_code=404, detail="no pull request submitted yet")

    all_files = backend.list_files(investigation.sandbox_workspace_id)
    files = visible_files(all_files)

    return {
        "pr_id": pr.id,
        "title": pr.title,
        "description": pr.description,
        "diff": pr.diff,
        "files": files,
    }
