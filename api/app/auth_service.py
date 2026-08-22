from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy.orm import Session as DbSession

from api.app import models

MIN_PASSWORD_LENGTH = 8
MAX_USERNAME_LENGTH = 64
SESSION_TTL = timedelta(days=7)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Verified against on a login for a username that doesn't exist, so a miss costs
# the same bcrypt work as a wrong password and the two can't be told apart by timing.
_DUMMY_HASH = _pwd_context.hash("bug-hunt-nonexistent-user")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def _as_utc(value: datetime) -> datetime:
    # Timestamps are written as UTC but come back naive from SQLite, which has no
    # timezone-aware storage; re-attach UTC before comparing against an aware now().
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def get_user_by_username(db: DbSession, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate(db: DbSession, username: str, password: str) -> models.User | None:
    user = get_user_by_username(db, username)
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: DbSession, user: models.User) -> models.Session:
    session = models.Session(
        token=secrets.token_urlsafe(32),
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + SESSION_TTL,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def resolve_session(db: DbSession, token: str) -> models.User | None:
    session = db.get(models.Session, token)
    if session is None:
        return None

    if _as_utc(session.expires_at) <= datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None

    return db.get(models.User, session.user_id)


def revoke_session(db: DbSession, token: str) -> None:
    session = db.get(models.Session, token)
    if session is not None:
        db.delete(session)
        db.commit()
