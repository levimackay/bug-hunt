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

TEST_USERNAME = "testuser"
TEST_PASSWORD = "hunter2-hunter2"


def register_and_login(test_client: TestClient, username: str, password: str) -> str:
    resp = test_client.post(
        "/api/auth/register", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text

    resp = test_client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


@pytest.fixture()
def fake_backend() -> FakeExecutionBackend:
    return FakeExecutionBackend()


@pytest.fixture()
def anon_client(fake_backend: FakeExecutionBackend):
    """App client with no credentials attached."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()
    app.dependency_overrides[get_execution_backend] = lambda: fake_backend

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def client(anon_client: TestClient):
    """Client authenticated as a freshly registered user."""
    token = register_and_login(anon_client, TEST_USERNAME, TEST_PASSWORD)
    anon_client.headers["Authorization"] = f"Bearer {token}"
    return anon_client


@pytest.fixture()
def other_client(client: TestClient):
    """A second authenticated user against the same already-started app."""
    second = TestClient(client.app)
    token = register_and_login(second, "otheruser", TEST_PASSWORD)
    second.headers["Authorization"] = f"Bearer {token}"
    return second
