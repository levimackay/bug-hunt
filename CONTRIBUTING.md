# Contributing

## Adding a new scenario

Scenarios are the most likely contribution. Each one lives in its own
directory under `scenarios/` and needs four things: a manifest, a real git
repo (shipped as a bundle), a hidden regression test, and a scoring block.

### 1. Build the fixture repo

Write a small, realistic service (FastAPI app is the existing convention,
but nothing in the loader requires it) with a real bug in it, then give it a
real git history — this is not simulated. The existing scenarios follow the
same shape:

1. An initial commit with a correct implementation and passing visible tests.
2. A "refactor" or "add feature" commit that introduces the actual
   regression as a side effect, without flagging it in a comment. Subtle,
   not artificial — the kind of thing that passes review because the
   existing tests don't happen to exercise the broken path.
3. At least one unrelated, plausible-looking recent commit as a red
   herring — something a user might suspect first ("we touched the image
   pipeline recently") but isn't the cause.

Build the repo in a scratch directory, `git init` it, make the commits, then
pack it as a bundle:

```bash
git bundle create repo.bundle --all
```

Put `repo.bundle` in the scenario directory (`scenarios/<id>/repo.bundle`).
Do **not** commit a `repo/` directory directly — a nested `.git` inside this
project's own repo would be recorded as an embedded/gitlink entry rather
than tracked file contents. `scenario_engine/loader.py` clones `repo.bundle`
into `repo/` on demand the first time the scenario is loaded (see
`_ensure_repo_materialized`); `scenarios/*/repo/` is already gitignored for
this reason. Delete your local `repo/` clone before committing if the loader
already materialized it during testing.

### 2. Write the hidden regression test

Add `scenarios/<id>/hidden_tests/test_<name>_regression.py` — a pytest file
that fails against the buggy commit and passes once the real fix is applied.
This file is never included in the investigation's visible file tree; it's
the thing that actually proves the fix at submit time. Keep the visible
tests (in the fixture repo's own `tests/`) passing on both sides of the
regression — they shouldn't accidentally catch the bug, or there's nothing
to investigate.

### 3. Write `scenario.yaml`

Full schema (see `bug-1842-profile-upload/scenario.yaml` or
`bug-1794-search-incorrect/scenario.yaml` for complete examples):

```yaml
id: bug-XXXX-short-slug
title: "User-facing bug title"
company: Nexus
severity: Low | Medium | High
difficulty: intern | junior | engineer | senior | staff
language: python
skills: [skill-tag-one, skill-tag-two]
learning_objectives:
  - What investigating this teaches, as a sentence

ticket:
  reporter: "Customer Support"
  body: |
    The bug report as the user will read it. A symptom, not a diagnosis.
  slack_thread:
    - author: "Name (Role)"
      body: "A supporting detail or a nudge, not the answer."

repo_path: repo/
entry_service: some-service-name
visible_test_command: "pytest tests/"

root_cause: >
  The ground-truth explanation, used to build the postmortem. Name the
  specific commit if useful.

hidden_tests: hidden_tests/test_name_regression.py

hints:
  - cost_xp: 5
    text: "A cheap, general nudge (e.g. narrow down when it started)."
  - cost_xp: 20
    text: "An expensive, near-answer hint."

review_criteria:
  - must_fix_the_specific_thing: true
  - must_add_regression_test: true
  - explanation_required: [what_was_broken, why, what_changed, how_verified]

scoring:
  expected_fix_paths: [app/the_file_that_should_change.py]
  code_quality_checks: [must_fix_the_specific_thing, must_add_regression_test]
```

Notes:

- `hints` should escalate from a general nudge toward something close to
  the answer — this is what the investigation-process score is weighed
  against (see `scenario_engine/scoring.py: score_investigation`).
- `review_criteria` entries are arbitrary named boolean checks — they're
  not a fixed enum, so name them for what actually matters in this
  scenario's fix.
- `scoring.expected_fix_paths` should be the file(s) the canonical fix
  touches — this is used as a proxy for "did the user find the root cause"
  (`score_root_cause`), so keep it tight; padding it with unrelated files
  makes that axis too easy to pass by accident.
- `scoring.code_quality_checks` should be the subset of `review_criteria`
  keys that specifically reflect code quality, as opposed to correctness
  (already covered by the hidden test's pass/fail).
- If you're modeling something that looks like a concurrency bug, keep it
  deterministic — no threads, no async, no real timing. It must reproduce
  identically on every test run. `bug-1831-duplicate-notifications` is the
  existing example of this (a type-mismatch idempotency bug, not a race).

### 4. Verify it end to end

```bash
.venv/bin/python -m pytest -q
```

The scenario loader (`scenario_engine/tests/test_loader.py`) and evaluation
tests will pick up a new scenario directory automatically if it's placed
under `scenarios/` and has a valid `scenario.yaml`. Add scenario-specific
assertions if the new scenario introduces a new shape the existing tests
don't already cover.

## Running tests

```bash
.venv/bin/python -m pytest -q
```

Test layout mirrors the source layout: `api/tests/`, `scenario_engine/tests/`,
`sandbox/tests/` (configured via `testpaths` in `pyproject.toml`). Backend
API tests use FastAPI's `TestClient`; sandbox tests run against
`sandbox/tests/fake_backend.py`, an in-memory stand-in for
`ExecutionBackend` — never point tests (or any non-test code path) at a real
E2B sandbox implicitly.

## Code style

Observed conventions in the existing code — follow them rather than
introducing a new style:

- `from __future__ import annotations` at the top of every module.
- Dataclasses (usually `frozen=True`) for plain data shapes, not
  dictionaries passed around loosely.
- No comments that restate what the code already says. Comments exist only
  to explain a non-obvious constraint or a decision someone would otherwise
  redo wrong (see `scenario_engine/loader.py`'s note on why `repo/` is
  gitignored and materialized from a bundle, or `sandbox/e2b_backend.py`'s
  note on `shlex.join` vs the allowlist).
- Subprocess and sandbox commands are always an argv list, never a shell
  string and never `shell=True`. If an underlying SDK only accepts a shell
  string (see `E2BExecutionBackend`), build it with `shlex.join()` on the
  argv list rather than any form of string interpolation.
- `scenario_engine/` has no FastAPI (or any web-framework) imports. Keep
  business logic there testable in isolation; the `api/` layer should stay
  thin glue over it plus persistence.
- Keep the command allowlist (`sandbox/base.py: ALLOWED_COMMANDS`) and its
  enforcement at the router layer (`api/app/routers/exec.py`) in sync if
  you ever need to add a command — enforce it in both places, not just one.
