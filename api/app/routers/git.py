from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.app import models
from api.app.db import get_db
from api.app.deps import get_execution_backend
from api.app.events import log_event
from sandbox.base import ExecutionBackend

router = APIRouter(prefix="/investigations", tags=["git"])

# Restrict shas to hex characters so a crafted "sha" can never be interpreted
# as a git flag (e.g. "--upload-pack=...") even though argv already blocks shell injection.
_SHA_RE = re.compile(r"^[0-9a-fA-F]{4,40}$")


def _get_investigation(db: Session, investigation_id: int) -> models.Investigation:
    investigation = db.get(models.Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="investigation not found")
    return investigation


@router.get("/{investigation_id}/git/log")
def git_log(
    investigation_id: int,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = _get_investigation(db, investigation_id)

    result = backend.run_command(
        investigation.sandbox_workspace_id,
        ["git", "log", "--pretty=format:%H\x1f%an\x1f%ad\x1f%s", "--date=iso-strict"],
    )

    commits = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        sha, author, date, subject = parts
        commits.append({"sha": sha, "short_sha": sha[:7], "author": author, "date": date, "subject": subject})

    log_event(db, investigation.id, "git_viewed", {"action": "log"})

    return {"commits": commits}


@router.get("/{investigation_id}/git/diff/{sha}")
def git_diff(
    investigation_id: int,
    sha: str,
    db: Session = Depends(get_db),
    backend: ExecutionBackend = Depends(get_execution_backend),
):
    investigation = _get_investigation(db, investigation_id)

    if not _SHA_RE.match(sha):
        raise HTTPException(status_code=400, detail="invalid commit sha")

    result = backend.run_command(investigation.sandbox_workspace_id, ["git", "show", sha])
    if result.exit_code != 0:
        raise HTTPException(status_code=404, detail="commit not found")

    log_event(db, investigation.id, "git_viewed", {"action": "diff", "sha": sha})

    return {"sha": sha, "diff": result.stdout}
