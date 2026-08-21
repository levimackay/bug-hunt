# Bug Hunt — Walking Skeleton Build Spec

Milestone: one complete scenario playable end to end, single local user, no auth.
Company fiction: "Nexus". First scenario ships as a real git repo with real commit
history and real pytest suites — nothing simulated as fake strings.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, SQLite (models written so swapping
  to Postgres later is a connection-string change — no SQLite-only column types).
- Frontend: Vite + React + TypeScript + Tailwind CSS + Monaco Editor.
- Execution sandbox: E2B (Firecracker microVMs). Abstract behind an
  `ExecutionBackend` interface — see below. No Docker anywhere in this project.
- No auth in this milestone. One implicit local user, no login screen.

## Directory layout

```
bug-hunt/
  api/                  FastAPI app: routers, models, scenario engine glue
    app/
      main.py
      db.py
      models.py         SQLAlchemy models
      routers/
        tickets.py
        investigations.py
        exec.py
        git.py
        pr.py
        review.py
        hints.py
      scenario_loader.py
  scenario_engine/       Pure logic: scenario YAML parsing, investigation state,
                         hidden-test evaluation. No FastAPI imports here — the
                         API layer calls into this, so it's independently testable.
  sandbox/               ExecutionBackend interface + E2BExecutionBackend impl
  scenarios/
    bug-1842-profile-upload/
      scenario.yaml
      repo/             actual git repo, cloned into sandbox workspace per investigation
      hidden_tests/     pytest files NOT shown in the user's visible file tree
  frontend/              Vite React app
  docs/
    BUILD_SPEC.md        this file
```

## Scenario YAML schema

```yaml
id: bug-1842-profile-upload
title: "Profile image uploads are failing for some users"
company: Nexus
severity: Medium
difficulty: intern        # intern | junior | engineer | senior | staff
language: python
skills: [input-validation, defensive-programming, regression-testing]
learning_objectives:
  - Trace a bug report to a specific commit using git log/diff
  - Recognize a case-sensitivity defect in string validation
  - Write a regression test that would have caught it

ticket:
  reporter: "Customer Support"
  body: |
    Several users are reporting that their profile pictures disappear
    after uploading them. Can you investigate?
  slack_thread:
    - author: "Priya Nandakumar (Support)"
      body: "Getting a few reports of vanished profile photos, mostly iPhone users."
    - author: "Marcus Rivera (Staff Eng)"
      body: "We shipped a validation refactor on user-service last week, worth a look."

repo_path: repo/           # relative to scenario dir
entry_service: user-service
visible_test_command: "pytest tests/"

root_cause: >
  The upload validation added in commit 91c72aa checks file extensions with a
  case-sensitive comparison, so files like IMG_0421.JPG (uppercase, common from
  iOS exports) fail validation. The upload endpoint swallows the validation
  exception and returns 200, so the frontend reports success while the image
  is never persisted — it appears to "disappear."

hidden_tests: hidden_tests/test_upload_regression.py

hints:
  - cost_xp: 5
    text: "When did users first start reporting this? Check when it started, not just what's broken."
  - cost_xp: 10
    text: "Look at git log for the upload/validation path specifically, not the whole repo."
  - cost_xp: 15
    text: "Compare the validation function before and after the most recent refactor commit."
  - cost_xp: 20
    text: "The bug isn't in what gets rejected — it's in what happens after rejection."

review_criteria:
  - must_fix_case_sensitivity: true
  - must_add_regression_test: true
  - must_not_swallow_exception: true
  - explanation_required: [what_was_broken, why, what_changed, how_verified]
```

## Database models (api/app/models.py)

- `Scenario` — mirrors YAML metadata, loaded at startup from `scenarios/`, read-only at runtime.
- `Investigation` — id, scenario_id, status (`investigating|submitted|in_review|resolved`), sandbox_workspace_id, started_at, resolved_at.
- `InvestigationEvent` — id, investigation_id, type (`file_opened|command_run|hint_used|git_viewed`), payload (JSON text), timestamp. Logged from day one even though scoring lands in a later milestone.
- `PullRequest` — investigation_id, title, description, diff (text snapshot at submit time).
- `ReviewComment` — investigation_id, author (persona name), body, resolved (bool).

## API contract (FastAPI, base path /api)

- `GET /tickets` — list scenarios as tickets (id, title, severity, difficulty, status for this user)
- `GET /tickets/{scenario_id}` — ticket detail: bug report body, slack thread, related repo name
- `POST /investigations` `{scenario_id}` — creates Investigation, calls ExecutionBackend.create_workspace(scenario repo), clones scenario's `repo/` into it, returns investigation_id
- `GET /investigations/{id}/files` — file tree of the workspace (hidden_tests/ never included)
- `GET /investigations/{id}/files/{path}` — file content
- `PUT /investigations/{id}/files/{path}` — write file content into workspace
- `POST /investigations/{id}/exec` `{argv: string[]}` — run an allowlisted command in the sandbox (allowlist: pytest, python, git, ls, cat, grep, find, diff — reject anything else with 400 before it reaches the sandbox); returns stdout/stderr/exit_code
- `GET /investigations/{id}/git/log` — real `git log` parsed to structured commits
- `GET /investigations/{id}/git/diff/{sha}` — real `git show <sha>` diff
- `POST /investigations/{id}/submit` `{pr_title, pr_description}` — runs hidden tests against workspace inside sandbox, creates PullRequest with a real diff (workspace vs scenario base), triggers review, returns pass/fail + PR id
- `GET /investigations/{id}/pr` — PR view: title, description, diff, file list
- `GET /investigations/{id}/review` — review comments for this investigation
- `POST /investigations/{id}/hints/next` — reveals next hint, logs an InvestigationEvent
- `GET /investigations/{id}/postmortem` — root cause explanation + what the user did well/missed, built from InvestigationEvent log vs scenario metadata

Every mutating endpoint logs an InvestigationEvent — this is what later milestones (scoring, post-incident "you missed") will read.

## Execution sandbox interface (sandbox/)

```python
class ExecutionBackend(Protocol):
    def create_workspace(self, scenario_repo_path: str) -> str: ...  # returns workspace_id
    def run_command(self, workspace_id: str, argv: list[str], timeout_s: int = 20) -> ExecResult: ...
    def read_file(self, workspace_id: str, path: str) -> str: ...
    def write_file(self, workspace_id: str, path: str, content: str) -> None: ...
    def list_files(self, workspace_id: str) -> list[str]: ...
    def destroy(self, workspace_id: str) -> None: ...
```

`E2BExecutionBackend` is the only production implementation — it requires an
`E2B_API_KEY` env var. If it's absent, the backend must fail loudly at startup
with a clear message ("set E2B_API_KEY to run investigations"), never silently
fall back to running code unsandboxed on the host. A `FakeExecutionBackend`
(in-memory, same interface) exists only under `tests/` for unit-testing the API
layer without needing real sandbox credentials or network access — it must
never be reachable from production config.

Command allowlist enforcement happens twice: once at the API router (reject
before touching the sandbox) and once conceptually inside the sandbox command
construction (never pass a user-supplied string to a shell — always argv list,
never `shell=True`).

## First scenario content (scenarios/bug-1842-profile-upload/)

A small real FastAPI service, `user-service`, handling profile photo uploads.

Git history (oldest to newest):
1. `Initial user-service implementation` — upload endpoint, storage module, basic tests, all passing, extension check is case-insensitive (`.lower()` used correctly).
2. `Refactor upload validation for clarity` — extracts validation into its own function/module for readability, but drops the `.lower()` normalization during the extraction (the actual regression — subtle, not a comment-flagged bug). Existing tests still pass because none of them use an uppercase extension.
3. `Add automatic thumbnail generation for profile photos` — unrelated recent feature commit (red herring: touches image processing code, tempting to blame, isn't the cause).

The upload endpoint currently catches the validation's rejection and returns
HTTP 200 with a generic "upload received" body instead of a 4xx — this is why
the frontend/user perceives success while the file never persists. Fixing
requires two things: (1) restore case-insensitive extension comparison, (2)
stop swallowing the validation failure — return a proper error response.

Visible tests (`tests/test_upload.py`): cover happy path with lowercase
extensions and a couple of rejection cases (wrong file type entirely) — pass
before and after the fix, don't catch the regression.

Hidden test (`hidden_tests/test_upload_regression.py`): uploads a file named
with an uppercase extension (e.g. `IMG_0421.JPG`) and asserts both that the
response is non-success AND (after fix) that the file is actually persisted
when a valid-but-uppercase extension is used. This is the file that proves the
fix; it is never shown in the investigation's file tree.

## What's explicitly out of scope this milestone

No auth/login, no Jira/Slack/GitHub-style chrome beyond a minimal ticket view
and PR/review view, no XP/leveling UI, no scenario #2+. Those come after this
skeleton is proven end to end.
