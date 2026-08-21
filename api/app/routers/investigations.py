from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_execution_backend
from api.app.events import log_event
from api.app.scenario_registry import get_scenario
from scenario_engine.investigation import is_visible_path, visible_files
from scenario_engine.postmortem import build_postmortem
from scenario_engine.evaluation import HiddenTestResult
from sandbox.base import ExecutionBackend

router = APIRouter(prefix="/investigations", tags=["investigations"])


class CreateInvestigationRequest(BaseModel):
    scenario_id: str


class WriteFileRequest(BaseModel):
    content: str


def _get_investigation(db: Session, investigation_id: int) -> models.Investigation:
    investigation = db.get(models.Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="investigation not found")
    return investigation


@router.post("")
def create_investigation(
    body: CreateInvestigationRequest,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    scenario = get_scenario(body.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")

    workspace_id = backend.create_workspace(str(scenario.repo_dir))

    investigation = models.Investigation(
        scenario_id=scenario.id,
        status="investigating",
        sandbox_workspace_id=workspace_id,
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    log_event(db, investigation.id, "command_run", {"action": "create_investigation"})

    return {
        "investigation_id": investigation.id,
        "scenario_id": scenario.id,
        "status": investigation.status,
    }


@router.get("/{investigation_id}/files")
def list_files(
    investigation_id: int,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = _get_investigation(db, investigation_id)
    all_files = backend.list_files(investigation.sandbox_workspace_id)
    files = visible_files(all_files)

    log_event(db, investigation.id, "file_opened", {"action": "list_files"})

    return {"files": files}


@router.get("/{investigation_id}/files/{path:path}")
def read_file(
    investigation_id: int,
    path: str,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = _get_investigation(db, investigation_id)
    if not is_visible_path(path):
        raise HTTPException(status_code=404, detail="file not found")

    try:
        content = backend.read_file(investigation.sandbox_workspace_id, path)
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=404, detail="file not found") from exc

    log_event(db, investigation.id, "file_opened", {"path": path})

    return {"path": path, "content": content}


@router.put("/{investigation_id}/files/{path:path}")
def write_file(
    investigation_id: int,
    path: str,
    body: WriteFileRequest,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = _get_investigation(db, investigation_id)
    if not is_visible_path(path):
        raise HTTPException(status_code=400, detail="cannot write to that path")

    backend.write_file(investigation.sandbox_workspace_id, path, body.content)

    log_event(db, investigation.id, "command_run", {"action": "write_file", "path": path})

    return {"path": path, "status": "written"}


@router.get("/{investigation_id}/postmortem")
def get_postmortem(investigation_id: int, db: Session = Depends(get_db)):
    investigation = _get_investigation(db, investigation_id)
    scenario = get_scenario(investigation.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")

    events = (
        db.query(models.InvestigationEvent)
        .filter(models.InvestigationEvent.investigation_id == investigation.id)
        .order_by(models.InvestigationEvent.timestamp)
        .all()
    )
    event_dicts = [{"type": e.type, "payload": e.payload} for e in events]

    hidden_result = None
    has_pr = (
        db.query(models.PullRequest)
        .filter(models.PullRequest.investigation_id == investigation.id)
        .first()
    )
    if has_pr is not None:
        hidden_result = HiddenTestResult(
            passed=investigation.status == "resolved",
            stdout="",
            stderr="",
            exit_code=0 if investigation.status == "resolved" else 1,
        )

    return build_postmortem(scenario, event_dicts, hidden_result)
