from __future__ import annotations

SCENARIO_ID = "bug-1842-profile-upload"

FIXED_VALIDATION = '''ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif")


def is_allowed_extension(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


def validate_extension(filename: str) -> None:
    if not is_allowed_extension(filename):
        raise ValueError(f"Unsupported file type: {filename}")
'''

FIXED_MAIN = '''from fastapi import FastAPI, HTTPException, UploadFile, File

from app.storage import save_profile_photo
from app.thumbnails import generate_thumbnail
from app.validation import validate_extension

app = FastAPI()


@app.post("/upload")
async def upload_profile_photo(file: UploadFile = File(...)):
    try:
        validate_extension(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    contents = await file.read()
    save_profile_photo(file.filename, contents)
    generate_thumbnail(file.filename)
    return {"status": "upload received"}
'''


def _create_investigation(client) -> int:
    resp = client.post("/api/investigations", json={"scenario_id": SCENARIO_ID})
    assert resp.status_code == 200, resp.text
    return resp.json()["investigation_id"]


def test_list_tickets(client):
    resp = client.get("/api/tickets")
    assert resp.status_code == 200
    tickets = resp.json()
    assert any(t["id"] == SCENARIO_ID for t in tickets)
    assert all(t["status"] == "not_started" for t in tickets)


def test_ticket_detail(client):
    resp = client.get(f"/api/tickets/{SCENARIO_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticket"]["reporter"] == "Customer Support"
    assert len(body["ticket"]["slack_thread"]) == 2


def test_ticket_detail_unknown_scenario_404s(client):
    resp = client.get("/api/tickets/does-not-exist")
    assert resp.status_code == 404


def test_create_investigation_and_browse_files(client):
    investigation_id = _create_investigation(client)

    resp = client.get(f"/api/investigations/{investigation_id}/files")
    assert resp.status_code == 200
    files = resp.json()["files"]
    assert "app/main.py" in files
    assert not any(f.startswith("hidden_tests/") for f in files)

    resp = client.get(f"/api/investigations/{investigation_id}/files/app/main.py")
    assert resp.status_code == 200
    assert "upload" in resp.json()["content"]


def test_hidden_test_file_is_never_reachable(client):
    investigation_id = _create_investigation(client)

    resp = client.get(
        f"/api/investigations/{investigation_id}/files/hidden_tests/test_upload_regression.py"
    )
    assert resp.status_code == 404


def test_git_log_and_diff(client):
    investigation_id = _create_investigation(client)

    resp = client.get(f"/api/investigations/{investigation_id}/git/log")
    assert resp.status_code == 200
    commits = resp.json()["commits"]
    assert len(commits) == 3
    subjects = [c["subject"] for c in commits]
    assert "Add automatic thumbnail generation for profile photos" in subjects
    assert "Refactor upload validation for clarity" in subjects
    assert "Initial user-service implementation" in subjects

    refactor_commit = next(c for c in commits if c["subject"] == "Refactor upload validation for clarity")
    resp = client.get(f"/api/investigations/{investigation_id}/git/diff/{refactor_commit['sha']}")
    assert resp.status_code == 200
    assert ".lower()" in resp.json()["diff"]


def test_git_diff_rejects_malformed_sha(client):
    investigation_id = _create_investigation(client)

    resp = client.get(f"/api/investigations/{investigation_id}/git/diff/--upload-pack=x")
    assert resp.status_code == 400


def test_run_visible_tests(client):
    investigation_id = _create_investigation(client)

    resp = client.post(
        f"/api/investigations/{investigation_id}/exec",
        json={"argv": ["pytest", "tests/", "-q"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["exit_code"] == 0


def test_exec_rejects_disallowed_command(client):
    investigation_id = _create_investigation(client)

    resp = client.post(
        f"/api/investigations/{investigation_id}/exec",
        json={"argv": ["rm", "-rf", "/"]},
    )
    assert resp.status_code == 400


def test_hints_reveal_in_order(client):
    investigation_id = _create_investigation(client)

    resp = client.post(f"/api/investigations/{investigation_id}/hints/next")
    assert resp.status_code == 200
    first = resp.json()
    assert first["index"] == 0
    assert first["cost_xp"] == 5

    resp = client.post(f"/api/investigations/{investigation_id}/hints/next")
    second = resp.json()
    assert second["index"] == 1
    assert second["cost_xp"] == 10

    for _ in range(2):
        client.post(f"/api/investigations/{investigation_id}/hints/next")

    resp = client.post(f"/api/investigations/{investigation_id}/hints/next")
    assert resp.status_code == 404


def test_submit_without_fix_fails_hidden_tests(client):
    investigation_id = _create_investigation(client)

    resp = client.post(
        f"/api/investigations/{investigation_id}/submit",
        json={"pr_title": "no-op", "pr_description": "did not fix anything yet"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is False
    assert body["status"] == "in_review"

    review_resp = client.get(f"/api/investigations/{investigation_id}/review")
    assert review_resp.status_code == 200
    comments = review_resp.json()["comments"]
    assert len(comments) >= 1
    assert any(not c["resolved"] for c in comments)


def test_submit_with_fix_passes_hidden_tests(client):
    investigation_id = _create_investigation(client)

    resp = client.put(
        f"/api/investigations/{investigation_id}/files/app/validation.py",
        json={"content": FIXED_VALIDATION},
    )
    assert resp.status_code == 200

    resp = client.put(
        f"/api/investigations/{investigation_id}/files/app/main.py",
        json={"content": FIXED_MAIN},
    )
    assert resp.status_code == 200

    resp = client.post(
        f"/api/investigations/{investigation_id}/submit",
        json={
            "pr_title": "Fix case-sensitive extension validation",
            "pr_description": (
                "What was broken: uppercase file extensions like .JPG were rejected "
                "because validation compared case-sensitively, and the upload endpoint "
                "swallowed that failure and returned 200 anyway. Why: a refactor commit "
                "dropped the .lower() normalization. What changed: restored case-insensitive "
                "comparison and stopped catching the validation error silently. How verified: "
                "ran the visible test suite and manually uploaded an uppercase-extension file."
            ),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is True
    assert body["status"] == "resolved"

    pr_resp = client.get(f"/api/investigations/{investigation_id}/pr")
    assert pr_resp.status_code == 200
    pr_body = pr_resp.json()
    assert "validation.py" in pr_body["diff"] or "main.py" in pr_body["diff"]
    assert not any(f.startswith("hidden_tests/") for f in pr_body["files"])

    review_resp = client.get(f"/api/investigations/{investigation_id}/review")
    comments = review_resp.json()["comments"]
    assert any(c["resolved"] for c in comments)

    postmortem_resp = client.get(f"/api/investigations/{investigation_id}/postmortem")
    assert postmortem_resp.status_code == 200
    postmortem = postmortem_resp.json()
    assert "case-sensitive" in postmortem["root_cause"]


def test_submit_updates_ticket_status(client):
    investigation_id = _create_investigation(client)
    client.post(
        f"/api/investigations/{investigation_id}/submit",
        json={"pr_title": "no-op", "pr_description": "nothing"},
    )

    resp = client.get("/api/tickets")
    ticket = next(t for t in resp.json() if t["id"] == SCENARIO_ID)
    assert ticket["status"] == "in_review"
