from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.app import models
from api.app.auth_service import (
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    authenticate,
    create_session,
    get_user_by_username,
    hash_password,
    revoke_session,
)
from api.app.db import get_db
from api.app.deps import bearer_scheme, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class CredentialsRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(body: CredentialsRequest, db: Session = Depends(get_db)):
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="username is required")
    if len(username) > MAX_USERNAME_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"username must be at most {MAX_USERNAME_LENGTH} characters",
        )
    if len(body.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"password must be at least {MIN_PASSWORD_LENGTH} characters",
        )
    if get_user_by_username(db, username) is not None:
        raise HTTPException(status_code=400, detail="username already taken")

    user = models.User(username=username, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="username already taken") from exc
    db.refresh(user)

    session = create_session(db, user)
    return {"token": session.token, "username": user.username}


@router.post("/login")
def login(body: CredentialsRequest, db: Session = Depends(get_db)):
    user = authenticate(db, body.username.strip(), body.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session = create_session(db, user)
    return {"token": session.token, "username": user.username}


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    revoke_session(db, credentials.credentials)
    return {"status": "logged out"}


@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return {"username": user.username}
