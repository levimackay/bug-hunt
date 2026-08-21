from __future__ import annotations

from api.tests.test_lifecycle import FIXED_MAIN, FIXED_VALIDATION, SCENARIO_ID, _create_investigation


def _submit_fix(client, investigation_id: int, *, view_git_first: bool = True):
    if view_git_first:
        client.get(f"/api/investigations/{investigation_id}/git/log")

    client.put(
        f"/api/investigations/{investigation_id}/files/app/validation.py",
        json={"content": FIXED_VALIDATION},
    )
    client.put(
        f"/api/investigations/{investigation_id}/files/app/main.py",
        json={"content": FIXED_MAIN},
    )

    return client.post(
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


def test_score_404s_before_resolution(client):
    investigation_id = _create_investigation(client)

    resp = client.get(f"/api/investigations/{investigation_id}/score")
    assert resp.status_code == 404


def test_score_available_after_resolution(client):
    investigation_id = _create_investigation(client)
    submit_resp = _submit_fix(client, investigation_id)
    assert submit_resp.json()["status"] == "resolved"

    resp = client.get(f"/api/investigations/{investigation_id}/score")
    assert resp.status_code == 200
    score = resp.json()

    for key in ("root_cause", "fix", "testing", "investigation", "code_quality", "overall"):
        assert key in score
        assert 0 <= score[key] <= 100

    assert score["fix"] == 100
    assert score["root_cause"] == 100  # both expected_fix_paths touched


def test_score_penalizes_missing_git_log_before_submit(client):
    investigation_id = _create_investigation(client)
    _submit_fix(client, investigation_id, view_git_first=False)

    resp = client.get(f"/api/investigations/{investigation_id}/score")
    assert resp.status_code == 200
    assert resp.json()["investigation"] == 85


def test_postmortem_includes_score_field(client):
    investigation_id = _create_investigation(client)
    _submit_fix(client, investigation_id)

    resp = client.get(f"/api/investigations/{investigation_id}/postmortem")
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] is not None
    assert body["score"]["overall"] > 0


def test_postmortem_score_is_null_before_resolution(client):
    investigation_id = _create_investigation(client)

    resp = client.get(f"/api/investigations/{investigation_id}/postmortem")
    assert resp.status_code == 200
    assert resp.json()["score"] is None


def test_profile_starts_empty(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_xp"] == 0
    assert body["level"] == 1
    assert body["skills"] == []


def test_profile_updates_after_resolution(client):
    investigation_id = _create_investigation(client)
    _submit_fix(client, investigation_id)

    score_resp = client.get(f"/api/investigations/{investigation_id}/score")
    overall = score_resp.json()["overall"]

    resp = client.get("/api/profile")
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_xp"] == overall
    assert body["level"] == overall // 500 + 1

    skills_by_name = {s["name"]: s for s in body["skills"]}
    assert set(skills_by_name) == {"input-validation", "defensive-programming", "regression-testing"}

    expected_share = overall // 3
    for skill in skills_by_name.values():
        assert skill["xp"] == expected_share
        assert skill["mastery_pct"] == min(100, expected_share * 100 // 200)


def test_profile_accumulates_across_multiple_resolutions(client):
    first_id = _create_investigation(client)
    _submit_fix(client, first_id)
    first_overall = client.get(f"/api/investigations/{first_id}/score").json()["overall"]

    second_id = _create_investigation(client)
    _submit_fix(client, second_id)
    second_overall = client.get(f"/api/investigations/{second_id}/score").json()["overall"]

    resp = client.get("/api/profile")
    body = resp.json()
    assert body["total_xp"] == first_overall + second_overall


def test_unresolved_submission_does_not_award_xp(client):
    investigation_id = _create_investigation(client)
    client.post(
        f"/api/investigations/{investigation_id}/submit",
        json={"pr_title": "no-op", "pr_description": "did not fix anything yet"},
    )

    resp = client.get("/api/profile")
    assert resp.json()["total_xp"] == 0
