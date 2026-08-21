from __future__ import annotations

import os
import tempfile

import pytest

_tmp_dir = tempfile.mkdtemp(prefix="bug-hunt-test-db-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test.db"

from fastapi.testclient import TestClient  # noqa: E402

from api.app.db import Base, engine  # noqa: E402
from api.app.deps import get_execution_backend  # noqa: E402
from api.app.main import create_app  # noqa: E402
from sandbox.tests.fake_backend import FakeExecutionBackend  # noqa: E402


@pytest.fixture()
def fake_backend() -> FakeExecutionBackend:
    return FakeExecutionBackend()


@pytest.fixture()
def client(fake_backend: FakeExecutionBackend):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    app.dependency_overrides[get_execution_backend] = lambda: fake_backend

    with TestClient(app) as test_client:
        yield test_client
