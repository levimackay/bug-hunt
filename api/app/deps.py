from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.app import models
from api.app.auth_service import resolve_session
from api.app.db import get_db

if TYPE_CHECKING:
    from sandbox.base import ExecutionBackend

SCENARIOS_ROOT = Path(__file__).resolve().parents[2] / "scenarios"

_backend: "ExecutionBackend | None" = None

bearer_scheme = HTTPBearer(auto_error=False)


def get_execution_backend() -> "ExecutionBackend":
    """Production dependency: always E2B. Never overridden except in tests.

    Tests replace this via app.dependency_overrides[get_execution_backend],
    which is the only place FakeExecutionBackend is allowed to appear -- this
    function itself never imports or constructs it.
    """
    global _backend
    if _backend is None:
        from sandbox.e2b_backend import E2BExecutionBackend

        _backend = E2BExecutionBackend()
    return _backend


def _unauthenticated(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise _unauthenticated("not authenticated")

    user = resolve_session(db, credentials.credentials)
    if user is None:
        raise _unauthenticated("invalid or expired token")

    return user


def get_owned_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.Investigation:
    """Resolve an investigation belonging to the caller.

    Another user's investigation is reported as 404 rather than 403 so the
    response doesn't confirm that the id exists.
    """
    investigation = (
        db.query(models.Investigation)
        .filter(
            models.Investigation.id == investigation_id,
            models.Investigation.user_id == user.id,
        )
        .first()
    )
    if investigation is None:
        raise HTTPException(status_code=404, detail="investigation not found")
    return investigation
