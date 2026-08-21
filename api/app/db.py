from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    # No SQLite-only column types are used anywhere in models.py, so this same
    # connection string shape works unchanged against Postgres later.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./bug_hunt.db")
engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
