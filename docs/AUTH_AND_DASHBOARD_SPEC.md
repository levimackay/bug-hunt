# Milestone — Real Auth and a Connected Dashboard

Builds on `docs/BUILD_SPEC.md` and `docs/SCORING_AND_SCENARIOS_SPEC.md`. This
is a breaking schema change (there are no real users yet — this is a
pre-1.0 dev-only project, so a clean break is fine; don't build a migration
path from the single implicit profile). Two agents build this together on the
same branch: one backend, one frontend, against the contract below.

## Why now

The product has been single-local-user with an implicit profile. Real auth
turns that into a real multi-user product and unblocks the "connected"
engineering-workspace feel the original product brief asks for (a dashboard
that greets you by name, shows your open investigations, your level/XP,
recommended next ticket).

## Backend: auth

- `User` model in `api/app/models.py`: `id`, `username` (unique, indexed),
  `password_hash`, `created_at`.
- Password hashing: use `passlib`'s bcrypt handler (add to `pyproject.toml`
  dependencies) — never store or log a raw password.
- Token: a simple signed session token, not full OAuth. Use `itsdangerous` or
  Python's `hmac`/`secrets` to issue an opaque bearer token stored in a new
  `Session` table (`token`, `user_id`, `created_at`, `expires_at` — 7 day
  expiry is fine) rather than a stateless JWT, since revocation (logout) needs
  to actually work and this project has no need for cross-service token
  verification. Pick whichever of these two you're most confident implementing
  correctly and securely; document the choice in your report.
- Endpoints (new router `api/app/routers/auth.py`):
  - `POST /auth/register` `{username, password}` → creates the user (400 if
    username taken, with a clear detail message; require a minimum password
    length, e.g. 8 chars, 400 if violated), creates a session, returns
    `{token, username}`.
  - `POST /auth/login` `{username, password}` → verifies password, creates a
    new session, returns `{token, username}`. 401 on bad credentials (don't
    leak whether the username exists vs. the password was wrong — same
    generic error either way).
  - `POST /auth/logout` (requires auth) → deletes the current session's token
    server-side.
  - `GET /auth/me` (requires auth) → `{username}`.
- A `get_current_user` FastAPI dependency (in `api/app/deps.py` alongside the
  existing `get_execution_backend`) that reads the `Authorization: Bearer
  <token>` header, looks up the session, checks expiry, and returns the
  `User` row, raising 401 if missing/invalid/expired.
- Every existing endpoint under `/investigations`, `/tickets`, `/profile`
  needs `Depends(get_current_user)` added and needs to actually scope data to
  that user:
  - `Investigation` gains a `user_id` column (nullable is NOT acceptable —
    every investigation belongs to a user going forward). All investigation
    queries/creates must filter/set by the current user's id. A user must
    never be able to read or act on another user's investigation (404, not
    403, on cross-user access — don't leak existence).
  - `PlayerProfile` changes from a single fixed `id=1` row to one row per
    user (`user_id` as the primary/unique key instead of a hardcoded id).
    `GET /profile` returns the current user's profile.
  - `GET /tickets` can stay global (scenario metadata isn't user-specific),
    but each ticket's `status` field must reflect *this user's*
    latest-investigation status for that scenario, not any user's.
- Update every existing test that creates an investigation or checks
  `/profile` to first register+login a test user and pass the bearer token —
  don't leave the old tests broken. Add new auth-specific tests: register,
  duplicate username rejected, login success/failure, protected endpoint
  rejects missing/invalid/expired token, one user cannot access another
  user's investigation.
- `FakeExecutionBackend`/sandbox behavior is unaffected by this change —
  don't touch `sandbox/`.

## Frontend: auth UI

- `POST`-based login and register forms/pages (`/login`, `/register`),
  consistent with the app's existing dark IBM Plex visual language — don't
  introduce a different look for these two pages.
- An auth context/hook storing the bearer token (localStorage is fine for
  this project's threat model — no payment/PII data involved) and exposing
  `login`, `register`, `logout`, and the current username to the rest of the
  app.
- A route guard: every existing route except `/login` and `/register`
  redirects to `/login` if there's no valid token. On 401 from any API call
  (token expired/invalid), clear the stored token and redirect to `/login`
  rather than showing a broken page.
- Update every API call in `frontend/src/api/*.ts` to attach the
  `Authorization: Bearer <token>` header (a shared fetch wrapper change in
  `frontend/src/api/http.ts` is the right place — don't repeat this in every
  call site).
- `TopBar` gains the current username and a logout action, alongside the
  existing level/XP chip.

## Frontend: connected dashboard (replaces the current bare ticket-list Dashboard page)

Redesign `frontend/src/pages/Dashboard.tsx` into a real engineering homepage,
in the spirit of (not a literal copy of) this shape from the product brief:

```text
GOOD MORNING, {USERNAME}
NEXUS ENGINEERING

Open Investigations          Recommended next
──────────────────           ─────────────────
BUG-XXXX  ...                 (first ticket this user hasn't resolved yet)
BUG-XXXX  ...

Your progress
─────────────
Level N · N,NNN XP
(reuse whatever the /profile skills breakdown already renders on the Profile
page — a compact version here, full detail stays on /profile)
```

Concretely: fetch `/tickets` and `/profile` on this page, group tickets by
this user's per-ticket status (investigating / in_review / resolved /
not_started), show open investigations prominently, surface one "recommended
next" ticket (simplest reasonable heuristic: the lowest-difficulty
not-yet-resolved ticket), and a compact level/XP/top-skill summary linking to
the full `/profile` page. Keep it dense and dark, consistent with the
existing visual language — this is the home screen of a dev tool, not a
marketing page. Time-of-day greeting ("Good morning"/"Good afternoon"/"Good
evening") based on the browser's local clock is a nice touch but not
required if it complicates things.

## What NOT to do

No password reset flow, no email verification, no OAuth/social login, no
role/permission system beyond "every user sees only their own investigations"
— all explicitly out of scope for this pass. Don't touch `scenarios/` — five
new scenarios are being authored in parallel by other agents and don't need
any auth-awareness.
