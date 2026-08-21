from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_execution_backend
from api.app.events import log_event
from sandbox.base import ALLOWED_COMMANDS, ExecutionBackend

router = APIRouter(prefix="/investigations", tags=["exec"])


class ExecRequest(BaseModel):
    argv: list[str]


@router.post("/{investigation_id}/exec")
def run_exec(
    investigation_id: int,
    body: ExecRequest,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = db.get(models.Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="investigation not found")

    # Allowlist enforced here, before anything reaches the sandbox, and again
    # defensively inside the backend implementation itself.
    if not body.argv or body.argv[0] not in ALLOWED_COMMANDS:
        rejected = body.argv[0] if body.argv else ""
        raise HTTPException(status_code=400, detail=f"command not allowed: {rejected}")

    result = backend.run_command(investigation.sandbox_workspace_id, body.argv)

    log_event(
        db,
        investigation.id,
        "command_run",
        {"argv": body.argv, "exit_code": result.exit_code},
    )

    return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}
