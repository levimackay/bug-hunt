from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Scenario(Base):
    """Mirrors scenario.yaml metadata. Loaded at startup, read-only at runtime."""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[str] = mapped_column(String(32))
    language: Mapped[str] = mapped_column(String(32))
    entry_service: Mapped[str] = mapped_column(String(128))
    visible_test_command: Mapped[str] = mapped_column(String(255))
    ticket_reporter: Mapped[str] = mapped_column(String(128))
    ticket_body: Mapped[str] = mapped_column(Text)
    # Everything else from the YAML that doesn't need its own column (slack
    # thread, hints, review_criteria, root_cause, learning_objectives) as JSON text.
    metadata_json: Mapped[str] = mapped_column(Text)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Session(Base):
    """Server-side bearer session. Deleting the row revokes the token."""

    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    scenario_id: Mapped[str] = mapped_column(String(128), ForeignKey("scenarios.id"))
    status: Mapped[str] = mapped_column(String(32), default="investigating")
    sandbox_workspace_id: Mapped[str] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    events: Mapped[list["InvestigationEvent"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[int] = mapped_column(Integer, ForeignKey("investigations.id"))
    type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text, default="{}")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    investigation: Mapped["Investigation"] = relationship(back_populates="events")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[int] = mapped_column(Integer, ForeignKey("investigations.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    diff: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[int] = mapped_column(Integer, ForeignKey("investigations.id"))
    author: Mapped[str] = mapped_column(String(128))
    body: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class PlayerProfile(Base):
    """Progression state, one row per user."""

    __tablename__ = "player_profiles"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    skill_xp: Mapped[str] = mapped_column(Text, default="{}")
