from __future__ import annotations

from datetime import datetime, timedelta, timezone

from api.app import models
from api.app.db import SessionLocal
from api.tests.conftest import TEST_USERNAME
from api.tests.test_lifecycle import (
    FIXED_MAIN,
    FIXED_VALIDATION,
    SCENARIO_ID,
    _create_investigation,
)

PROTECTED_ENDPOINTS = [
    ("get", "/api/tickets"),
    ("get", f"/api/tickets/{SCENARIO_ID}"),
    ("get", "/api/profile"),
    ("get", "/api/auth/me"),
]


def test_register_returns_token_and_username(anon_client):
    resp = anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "correct-horse"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["username"] == "ada"
    assert body["token"]

    me = anon_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert me.status_code == 200
    assert me.json() == {"username": "ada"}


def test_register_never_stores_the_raw_password(anon_client):
    anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "correct-horse"}
    )

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "ada").one()
        assert user.password_hash != "correct-horse"
        assert user.password_hash.startswith("$2")
    finally:
        db.close()


def test_register_rejects_duplicate_username(anon_client):
    first = anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "correct-horse"}
    )
    assert first.status_code == 200

    second = anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "another-password"}
    )
    assert second.status_code == 400
    assert "taken" in second.json()["detail"]


def test_register_rejects_short_password(anon_client):
    resp = anon_client.post("/api/auth/register", json={"username": "ada", "password": "short"})
    assert resp.status_code == 400
    assert "8 characters" in resp.json()["detail"]


def test_register_rejects_blank_username(anon_client):
    resp = anon_client.post("/api/auth/register", json={"username": "   ", "password": "correct-horse"})
    assert resp.status_code == 400


def test_login_succeeds_with_correct_credentials(anon_client):
    anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "correct-horse"}
    )

    resp = anon_client.post(
        "/api/auth/login", json={"username": "ada", "password": "correct-horse"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "ada"
    assert resp.json()["token"]


def test_login_fails_with_wrong_password(anon_client):
    anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "correct-horse"}
    )

    resp = anon_client.post("/api/auth/login", json={"username": "ada", "password": "wrong-password"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid username or password"


def test_login_failure_does_not_reveal_whether_username_exists(anon_client):
    anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "correct-horse"}
    )

    wrong_password = anon_client.post(
        "/api/auth/login", json={"username": "ada", "password": "wrong-password"}
    )
    unknown_user = anon_client.post(
        "/api/auth/login", json={"username": "nobody", "password": "wrong-password"}
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_logout_revokes_the_token(client):
    token = client.headers["Authorization"].removeprefix("Bearer ")

    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200

    db = SessionLocal()
    try:
        assert db.get(models.Session, token) is None
    finally:
        db.close()

    assert client.get("/api/auth/me").status_code == 401


def test_logging_out_one_session_leaves_the_other_valid(anon_client):
    first = anon_client.post(
        "/api/auth/register", json={"username": "ada", "password": "correct-horse"}
    ).json()["token"]
    second = anon_client.post(
        "/api/auth/login", json={"username": "ada", "password": "correct-horse"}
    ).json()["token"]

    anon_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {first}"})

    assert (
        anon_client.get("/api/auth/me", headers={"Authorization": f"Bearer {first}"}).status_code
        == 401
    )
    assert (
        anon_client.get("/api/auth/me", headers={"Authorization": f"Bearer {second}"}).status_code
        == 200
    )


def test_protected_endpoints_reject_missing_token(anon_client):
    for method, path in PROTECTED_ENDPOINTS:
        resp = getattr(anon_client, method)(path)
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}"


def test_protected_endpoints_reject_invalid_token(anon_client):
    headers = {"Authorization": "Bearer not-a-real-token"}
    for method, path in PROTECTED_ENDPOINTS:
        resp = getattr(anon_client, method)(path, headers=headers)
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}"


def test_creating_an_investigation_requires_a_token(anon_client):
    resp = anon_client.post("/api/investigations", json={"scenario_id": SCENARIO_ID})
    assert resp.status_code == 401


def test_expired_token_is_rejected_and_discarded(client):
    token = client.headers["Authorization"].removeprefix("Bearer ")

    db = SessionLocal()
    try:
        session = db.get(models.Session, token)
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    assert client.get("/api/auth/me").status_code == 401

    db = SessionLocal()
    try:
        assert db.get(models.Session, token) is None
    finally:
        db.close()


def test_user_cannot_access_another_users_investigation(client, other_client):
    investigation_id = _create_investigation(client)

    for path in (
        f"/api/investigations/{investigation_id}/files",
        f"/api/investigations/{investigation_id}/files/app/main.py",
        f"/api/investigations/{investigation_id}/git/log",
        f"/api/investigations/{investigation_id}/review",
        f"/api/investigations/{investigation_id}/score",
        f"/api/investigations/{investigation_id}/pr",
        f"/api/investigations/{investigation_id}/postmortem",
    ):
        resp = other_client.get(path)
        assert resp.status_code == 404, f"GET {path} returned {resp.status_code}"

    resp = other_client.post(
        f"/api/investigations/{investigation_id}/exec", json={"argv": ["ls"]}
    )
    assert resp.status_code == 404

    resp = other_client.put(
        f"/api/investigations/{investigation_id}/files/app/main.py",
        json={"content": "# owned"},
    )
    assert resp.status_code == 404

    resp = other_client.post(
        f"/api/investigations/{investigation_id}/submit",
        json={"pr_title": "hijack", "pr_description": "not mine"},
    )
    assert resp.status_code == 404

    resp = other_client.post(f"/api/investigations/{investigation_id}/hints/next")
    assert resp.status_code == 404

    # The owner is unaffected by any of the above.
    assert client.get(f"/api/investigations/{investigation_id}/files").status_code == 200


def test_ticket_status_is_scoped_to_the_current_user(client, other_client):
    investigation_id = _create_investigation(client)
    client.post(
        f"/api/investigations/{investigation_id}/submit",
        json={"pr_title": "no-op", "pr_description": "nothing"},
    )

    owner_ticket = next(
        t for t in client.get("/api/tickets").json() if t["id"] == SCENARIO_ID
    )
    other_ticket = next(
        t for t in other_client.get("/api/tickets").json() if t["id"] == SCENARIO_ID
    )

    assert owner_ticket["status"] == "in_review"
    assert other_ticket["status"] == "not_started"
    assert other_client.get(f"/api/tickets/{SCENARIO_ID}").json()["status"] == "not_started"


def test_profile_is_scoped_to_the_current_user(client, other_client):
    investigation_id = _create_investigation(client)
    client.put(
        f"/api/investigations/{investigation_id}/files/app/validation.py",
        json={"content": FIXED_VALIDATION},
    )
    client.put(
        f"/api/investigations/{investigation_id}/files/app/main.py",
        json={"content": FIXED_MAIN},
    )
    client.post(
        f"/api/investigations/{investigation_id}/submit",
        json={"pr_title": "fix", "pr_description": "what was broken, why, what changed, how verified"},
    )

    assert client.get("/api/profile").json()["total_xp"] > 0
    assert other_client.get("/api/profile").json()["total_xp"] == 0
    assert other_client.get("/api/profile").json()["username"] == "otheruser"
    assert client.get("/api/profile").json()["username"] == TEST_USERNAME
