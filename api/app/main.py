from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.app.db import Base, SessionLocal, engine
from api.app.deps import SCENARIOS_ROOT
from api.app.scenario_loader import sync_scenarios
from api.app.scenario_registry import load_registry
from api.app.routers import exec as exec_router
from api.app.routers import git, hints, investigations, pr, review, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    load_registry(SCENARIOS_ROOT)

    db = SessionLocal()
    try:
        sync_scenarios(db, SCENARIOS_ROOT)
    finally:
        db.close()

    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Bug Hunt API", lifespan=lifespan)

    app.include_router(tickets.router, prefix="/api")
    app.include_router(investigations.router, prefix="/api")
    app.include_router(exec_router.router, prefix="/api")
    app.include_router(git.router, prefix="/api")
    app.include_router(pr.router, prefix="/api")
    app.include_router(review.router, prefix="/api")
    app.include_router(hints.router, prefix="/api")

    return app


app = create_app()
