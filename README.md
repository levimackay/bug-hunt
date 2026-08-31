# Bug Hunt

Bug Hunt is a debugging-practice simulator. You get a realistic bug ticket for
a fictional company ("Nexus"), investigate a real miniature codebase in a
browser-based IDE, fix the actual bug, submit a simulated pull request, get
reviewed by a scripted senior-engineer persona, and read a post-incident
report with a deterministic engineering score and XP/skill progression.

## Why

Most debugging exercises are toy puzzles: a single function with an obvious
off-by-one, no history, no ambiguity. Real debugging looks nothing like that —
you're handed a vague symptom, a codebase you didn't write, and a git history
full of both the actual regression and unrelated red herrings. Bug Hunt tries
to practice that skill directly:

- The bug report is a support ticket and a Slack thread, not a spec.
- The codebase is a real, small git repository with real commit history —
  the regression is an actual commit, and at least one other recent commit
  is a plausible-looking distraction that isn't the cause.
- You investigate with real tools: `git log`, `git diff`, `pytest`, `grep`,
  in a real sandboxed shell, not a mocked-up terminal.
- There's a hidden regression test you never see that decides whether your
  fix actually works, the same way a CI suite would.
- Scoring is a deterministic formula over what you actually did (files
  touched, hints used, whether you checked history before submitting), not a
  vibes-based LLM judgment call.

## Features

- **Real git history per scenario** — each scenario ships a `repo.bundle`
  that's cloned into a real `.git` repository at scenario-load time. The
  regression is a real commit; `git log`/`git diff` return real, structured
  output for it.
- **Real sandboxed code execution** — commands run inside an
  [E2B](https://e2b.dev) Firecracker microVM, not on the host. See
  [Security model](#security-model) below.
- **Real hidden regression tests** — a pytest file that proves the fix,
  never shown in the investigation's visible file tree, run only at submit
  time.
- **Deterministic scoring** — a fixed formula over five axes (root cause,
  fix, testing, investigation process, code quality), not model judgment.
  See `docs/SCORING_AND_SCENARIOS_SPEC.md` for the exact formula.
- **XP / skill progression** — each account's profile accumulates XP per
  resolved investigation and per-skill mastery (e.g. `debugging`,
  `input-validation`) tagged on each scenario.
- **Accounts** — username/password registration and login, sessions backed
  by a hashed token, and investigations, PRs and profile XP all scoped to
  the signed-in user.

## Architecture

```
bug-hunt/
  api/                  FastAPI app: routers, models, scenario engine glue
    app/
      main.py           app factory, router registration, startup sync
      db.py             SQLAlchemy engine/session (DATABASE_URL env var)
      models.py         SQLAlchemy models (Investigation, PullRequest, etc.)
      scenario_loader.py   syncs scenarios/ into the DB at startup
      scenario_registry.py in-memory registry of loaded Scenario objects
      scoring_service.py   wires scenario_engine scoring into the API
      profile_service.py   wires scenario_engine progression into the API
      auth_service.py      password hashing, session tokens
      deps.py              auth dependency, per-user investigation lookup
      routers/
        auth.py          register, login, logout, /auth/me
        tickets.py      GET /tickets, /tickets/{id}
        investigations.py  create investigation, file tree, file read/write
        exec.py          POST /investigations/{id}/exec (allowlisted commands)
        git.py           git log / git diff for the investigation's workspace
        pr.py            submit endpoint, PR view
        review.py        scripted review comments
        hints.py         hint reveal
        score.py         GET /investigations/{id}/score
        profile.py       GET /profile
    tests/
  scenario_engine/       Pure logic, no FastAPI imports — independently
                         testable and reused by the API layer.
    schema.py            Scenario/Ticket/Hint/Scoring dataclasses
    loader.py            parses scenario.yaml, materializes repo/ from repo.bundle
    investigation.py     investigation state helpers
    evaluation.py        hidden-test evaluation
    review.py            scripted review-comment generation
    scoring.py           the scoring formula
    progression.py       XP / level / skill mastery
    postmortem.py        post-incident report assembly
    tests/
  sandbox/               ExecutionBackend interface + implementations
    base.py              Protocol, ExecResult, command allowlist
    e2b_backend.py        the only production backend (needs E2B_API_KEY)
    tests/
      fake_backend.py     in-memory backend, test-only, never used in prod config
  scenarios/
    bug-1794-search-incorrect/
    bug-1831-duplicate-notifications/
    bug-1842-profile-upload/
    bug-1877-orders-pagination/
    bug-1901-guest-checkout-crash/
    bug-1912-catalog-stale-price/
    bug-1923-confirmation-wrong-items/
    bug-1938-discount-bundle-bypass/
      scenario.yaml
      repo.bundle         real git history, cloned into repo/ on demand
      repo/               materialized clone (gitignored, not committed)
      hidden_tests/        pytest file(s) never exposed to the user
  frontend/               Vite + React + TypeScript + Tailwind + Monaco
    src/
      api/                typed fetch wrappers, one per resource
      pages/
      components/
      hooks/
  docs/
    BUILD_SPEC.md         core architecture spec (walking skeleton milestone)
    SCORING_AND_SCENARIOS_SPEC.md   scoring formula, progression, scenario schema
```

The scenario engine has no FastAPI imports so it can be unit-tested and
reasoned about independently of the web layer; the API layer is a thin glue
on top of it plus persistence.

## Getting started

### Backend

Requires Python 3.12+ (developed and tested against 3.14).

```bash
uv venv --python 3.14
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy the environment template and fill in real values as needed:

```bash
cp .env.example .env
```

Run the API:

```bash
uvicorn api.app.main:app --reload --port 8000
```

This creates `bug_hunt.db` (SQLite) on first run and syncs `scenarios/` into
it. Register an account through the frontend (or `POST /auth/register`) to
get a session token; investigations, PRs and XP are scoped to that account.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000` (see
`frontend/vite.config.ts`), so run the backend first.

### Running tests

```bash
.venv/bin/python -m pytest -q
```

Covers `api/tests/`, `scenario_engine/tests/`, and `sandbox/tests/`.

## How scenarios are structured

Each directory under `scenarios/` is a self-contained scenario: a
`scenario.yaml` manifest, a `repo.bundle` (a real git repository packed as a
single file so it can live inside this project's own git history without
being recorded as a nested/embedded repo), and a `hidden_tests/` directory.

At load time (`scenario_engine/loader.py`), if `repo/` doesn't already exist
as a real git checkout, it's cloned from `repo.bundle` on demand — this is
why `scenarios/*/repo/` is gitignored: it's a derived artifact, not source.

The manifest schema (see `docs/BUILD_SPEC.md` and
`docs/SCORING_AND_SCENARIOS_SPEC.md` for the full annotated version) covers:

- ticket metadata (`title`, `severity`, `difficulty`, `skills`,
  `learning_objectives`) and the ticket content itself (`reporter`, `body`,
  a `slack_thread` of messages)
- `repo_path`, `entry_service`, `visible_test_command`
- `root_cause` — the ground-truth explanation used to build the postmortem
- `hidden_tests` — path to the regression test that proves the fix
- `hints` — an ordered list of `{cost_xp, text}`, each hint costing XP when
  revealed
- `review_criteria` — named boolean checks (e.g. `must_not_swallow_exception`)
  plus `explanation_required` fields the submitted PR description must cover
- `scoring.expected_fix_paths` and `scoring.code_quality_checks` — used by
  the scoring formula to judge whether the fix touched the right files and
  which review criteria count toward the code-quality axis

Eight scenarios exist today, each shipping a real, deliberately unrelated
extra commit as a red herring:

- `bug-1842-profile-upload` (intern) — a case-sensitivity validation bug.
- `bug-1794-search-incorrect` (junior) — an off-by-one in a hand-rolled
  substring scan.
- `bug-1831-duplicate-notifications` (engineer) — a type-mismatch
  idempotency check.
- `bug-1877-orders-pagination` (junior) — a dropped `-1` in a pagination
  refactor that shifts every page's slice window forward by one page.
- `bug-1901-guest-checkout-crash` (intern) — a loyalty-discount lookup
  that assumes every order has a customer, so guest checkout 500s.
- `bug-1912-catalog-stale-price` (engineer) — a price-cache invalidation
  key that's lowercased while the read path's key is uppercased, so
  SKU-format ids never get their stale price cleared.
- `bug-1923-confirmation-wrong-items` (engineer) — a fire-and-forget async
  task read from a shared buffer before it's run, so confirmation emails
  carry the previous order's line items.
- `bug-1938-discount-bundle-bypass` (engineer) — an early-return guard
  added for bundle orders that skips discount-code validation entirely.

## Security model

Code execution never happens on the host. Every `pytest`/`python`/`git`/etc.
command a user runs is executed inside an isolated E2B Firecracker microVM via
`sandbox/e2b_backend.py`. Specifically:

- **Command allowlist** — only `pytest`, `python`, `git`, `ls`, `cat`,
  `grep`, `find`, `diff` are permitted. This is enforced twice: once at the
  API router (`api/app/routers/exec.py`, rejected with a 400 before it
  reaches the sandbox) and once again inside the sandbox backend itself
  (`sandbox/base.py`), so a caller that bypasses the router still can't
  reach an arbitrary command.
- **Argv only, never a shell string** — commands are always passed as an
  argv list. The E2B SDK's underlying `Commands.run()` takes a single
  shell-parsed string, so the backend builds that string with `shlex.join()`
  (each token individually quoted) rather than any string interpolation —
  no argument can inject additional shell syntax.
- **No host filesystem or secrets access from investigation code** — the
  sandbox is a fresh microVM per investigation seeded only with the
  scenario's repo contents.

This requires a real `E2B_API_KEY` to actually run investigations end to
end. **As of this writing the project is not wired to a live E2B key** —
without one, `E2BExecutionBackend` fails loudly at startup (per design: it
never silently falls back to running code unsandboxed on the host). The test
suite exercises the API and scenario logic against an in-memory
`FakeExecutionBackend` (`sandbox/tests/fake_backend.py`) instead, which is
test-only and never reachable from production configuration.

See `SECURITY.md` for how to report a vulnerability.

## Current scope and status

This is a working prototype, not a finished product:

- 8 scenarios exist (listed above).
- Username/password authentication with hashed session tokens; no password
  reset or email verification flow yet.
- No live E2B key wired up in this repo; sandbox execution is implemented
  and tested against a fake backend but not yet exercised against a real
  microVM outside development.
- Single-player, local SQLite by default (`DATABASE_URL` can point at
  Postgres instead — models avoid SQLite-only column types by design).

## Roadmap

Pulled directly from the "out of scope" notes in `docs/BUILD_SPEC.md` and
`docs/SCORING_AND_SCENARIOS_SPEC.md` — this is what's genuinely still
missing, not a marketing wishlist:

- More scenarios — toward a target range of 8-12, including harder
  difficulty tiers (`senior`, `staff`)
- Richer Jira/Slack/GitHub-style connected chrome beyond the current minimal
  ticket and PR/review views
- Session/day tracking (e.g. streaks)
- A public landing/marketing page
- True concurrency/race-condition scenarios — deliberately out of scope for
  now; existing "concurrency-flavored" bugs (e.g.
  `bug-1831-duplicate-notifications`) are implemented as deterministic
  logic bugs, not real threads/async/timing, so they reproduce identically
  on every run

## License

MIT — see `LICENSE`.
