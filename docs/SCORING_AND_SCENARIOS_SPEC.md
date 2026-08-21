# Milestone 2 — Scoring, Progression, and Two More Scenarios

Builds on `docs/BUILD_SPEC.md` (already implemented and verified — read it
first for the existing architecture, don't redesign anything there). This
addendum covers three things built in parallel by separate agents:

1. A scoring engine (backend) evaluated on investigation resolution.
2. A single-profile progression system (XP, level, per-skill mastery).
3. Two new scenarios (content) proving the scenario engine generalizes.

## Scenario schema addition: `scoring` block

Every scenario.yaml (including the existing bug-1842) gets a new block:

```yaml
scoring:
  expected_fix_paths: [app/validation.py, app/main.py]
  code_quality_checks: [must_not_swallow_exception, must_add_regression_test]
```

`expected_fix_paths` — files the canonical fix touches, used as a proxy for
"did the user actually find the root cause vs. patch around it."
`code_quality_checks` — the subset of the scenario's existing `review_criteria`
keys that should count toward the code-quality score specifically (as opposed
to correctness, which is already covered by hidden-test pass/fail).

The backend-engineer building scoring should add this block to
`scenarios/bug-1842-profile-upload/scenario.yaml` using:
```yaml
scoring:
  expected_fix_paths: [app/validation.py, app/main.py]
  code_quality_checks: [must_not_swallow_exception, must_add_regression_test]
```

## Scoring formula (deterministic, computed at resolution time)

Inputs available: the InvestigationEvent log, the final PullRequest diff, the
hidden test result, and the ReviewComment set from the resolving submission.

- `fix` (0-100): 100 if the resolving submission's hidden test passed, else 0.
  (Only ever computed once `status == "resolved"`.)
- `root_cause` (0-100): `100 * (touched ∩ expected_fix_paths / len(expected_fix_paths))`
  where `touched` is the set of file paths appearing in the resolving PR's
  diff. Floor of 50 if the investigation resolved but overlap is somehow zero.
- `testing` (0-100): 50 base once resolved; +50 more if the diff also adds or
  modifies a test file that is NOT in `hidden_tests/` (i.e. the user wrote
  their own regression test, not just relied on the hidden one).
- `investigation` (0-100): starts at 100. Subtract each hint's `cost_xp` for
  every `hint_used` event (floor 0). Subtract an additional 15 if there is no
  `git_viewed` event before the first `command_run` event of type `submit`
  (i.e. they never looked at history before submitting).
- `code_quality` (0-100): `100 * (resolved review_criteria checks in
  code_quality_checks / len(code_quality_checks))`, read from the resolving
  submission's ReviewComment set (each check already maps 1:1 to a comment
  with a `resolved` boolean via `generate_review_comments`).
- `overall`: weighted average — root_cause 25%, fix 30%, testing 20%,
  investigation 15%, code_quality 10%. Round to nearest int.

This must live in `scenario_engine/scoring.py` (pure logic, testable without
FastAPI, same pattern as the rest of scenario_engine) and be exposed via:

- `GET /investigations/{id}/score` — returns
  `{root_cause, fix, testing, investigation, code_quality, overall}`, all ints
  0-100, or 404 if the investigation isn't yet resolved.
- The existing `GET /investigations/{id}/postmortem` response gains a `score`
  field with the same shape (still returns the rest of what it already
  returns — root_cause explanation, did_well, missed, hints_used, commands_run).

## Progression (single local profile, no auth)

A `PlayerProfile` row (id fixed at 1, created on first access if absent):
`total_xp` (int), and a `skill_xp` JSON text column mapping skill name →
accumulated xp (skills come from each scenario's `skills` list in its YAML).

On resolution of any investigation: `xp_awarded = overall_score` (the same
number as the score's `overall` field — no separate currency, keeps this
honest and simple for MVP). Add `xp_awarded` to `total_xp`. For each skill tag
in that scenario's `skills` list, add `xp_awarded // len(skills)` to that
skill's accumulated xp in `skill_xp`.

Level: `level = total_xp // 500 + 1` (documented constant, easy to retune
later). Mastery per skill for display: `min(100, skill_xp[name] * 100 // 200)`
— i.e. 200 accumulated xp in a skill reads as 100% mastery. Document these
two constants (`XP_PER_LEVEL = 500`, `XP_FOR_FULL_MASTERY = 200`) as named
constants, not magic numbers, so they're easy to retune later.

Endpoint: `GET /profile` — `{total_xp, level, skills: [{name, xp, mastery_pct}]}`,
where `skills` includes every skill ever touched across played scenarios
(nothing to show before any investigation resolves — empty list is fine).

## Scenario 2 — BUG-1794, "Search results incorrect" (Easy / junior)

Company: Nexus. Service: `search-service`, a small FastAPI app exposing
`GET /search?q=...` over an in-memory product catalog (a plain Python list of
dicts is fine — no real DB needed for this scenario).

Ticket:
```yaml
ticket:
  reporter: "Customer Support"
  body: |
    Customers say searching for a product sometimes returns the wrong items
    or misses obvious matches. One customer searched "cable" and got zero
    results even though we definitely sell cables.
  slack_thread:
    - author: "Devon Okafor (Support)"
      body: "A few reports the search box is 'broken' — mostly single-word queries."
    - author: "Sarah Chen (Senior Eng)"
      body: "We tweaked the ranking/filter logic last sprint, might be related."
```

Real git history, oldest to newest:
1. `Initial search-service implementation` — naive substring search over
   product name + description, case-insensitive, correct.
2. `Add relevance ranking to search results` — introduces a scoring function
   to rank matches by relevance and, while doing so, changes the match
   filter from "substring anywhere in name or description" to an **off-by-one
   slice** that drops the last character of the query when comparing (e.g.
   `query[:-1]` used somewhere it shouldn't be, framed as "trimming trailing
   whitespace" but actually implemented wrong) — the real, subtle regression.
   Short queries or queries ending in a character that happens not to appear
   earlier in the product text now miss real matches. Don't comment-flag it.
3. `Add search analytics logging` — unrelated recent commit (red herring):
   adds a logging call around search requests, tempting to blame for "why did
   this get worse recently" but not the actual cause.

Root cause for scenario.yaml: the ranking-commit's query-normalization step
drops the last character of the search query before matching, so short or
specific queries silently under-match.

Hidden test: searches for a real product using a short/edge-case query that
the off-by-one drops, asserts the expected product IS in the results
(fails pre-fix, passes post-fix). Visible tests cover a couple of normal
multi-character searches that still pass on both sides of the regression.

difficulty: junior. skills: [debugging, string-manipulation, regression-testing].
scoring.expected_fix_paths: the file containing the ranking/filter function.
scoring.code_quality_checks: whatever review_criteria you define for this
scenario (e.g. `must_fix_query_normalization`, `must_add_regression_test`).

## Scenario 3 — BUG-1831, "Duplicate notifications" (intermediate / engineer)

Company: Nexus. Service: `notifications-service`, a small FastAPI app with a
`POST /notify` endpoint that sends a notification for an event (model it as
appending to an in-memory/SQLite "sent_notifications" list — no real email/push
needed, just record that a send happened).

Ticket:
```yaml
ticket:
  reporter: "Customer Support"
  body: |
    Users are getting the same notification two or three times for a single
    event — e.g. one order confirmation shows up 2-3 times in a row.
  slack_thread:
    - author: "Priya Nandakumar (Support)"
      body: "Seems tied to retries — happens more when the network is flaky client-side."
    - author: "Marcus Rivera (Staff Eng)"
      body: "Client does retry POST /notify on timeout. Should be idempotent but maybe isn't."
  # deliberately echoes the spec's own worked review example about retries —
  # keep the review comment for this scenario in that spirit.
```

Real git history, oldest to newest:
1. `Initial notifications-service implementation` — correct idempotent
   behavior: accepts an `event_id`, checks whether a notification for that
   `event_id` was already sent before sending again.
2. `Refactor notification sending for clarity` — extracts the "already sent"
   check into its own function during a readability pass, but the refactor
   checks the wrong collection / checks it before the id is normalized (e.g.
   the event_id is compared as a raw string in one place and as an int
   elsewhere, so the idempotency check never actually matches on retry) — the
   real regression, subtle, no comment flagging it.
3. `Add notification delivery metrics` — unrelated recent commit (red herring):
   adds counters/logging around delivery, tempting to blame but isn't the cause.

Root cause for scenario.yaml: the idempotency check compares `event_id` as
two different types (string vs int) depending on code path, so a retried
request with the same event_id is never recognized as a duplicate and gets
sent again.

Hidden test: calls `POST /notify` twice with the same `event_id` (simulating
a client retry) and asserts exactly one notification was recorded (fails
pre-fix — duplicate gets recorded — passes post-fix). Visible tests cover a
single successful notify call and don't catch the duplicate-on-retry case.

difficulty: engineer. skills: [state-management, debugging, api-design,
regression-testing]. This is explicitly a deterministic bug (a type-mismatch
in an idempotency check), not a true concurrency/race condition — per
BUILD_SPEC's own scope notes, race conditions are an "advanced foundation"
tier the platform doesn't support yet. Don't implement this with threads,
async, or real timing — it must reproduce the same way every single time a
test runs it.

## What's explicitly out of scope this round

Auth, the public GitHub repo, the Jira/Slack/GitHub-style chrome beyond what
already exists, streaks (no session/day tracking without accounts yet), and
any scenario beyond these three. Landing/marketing page also not this round.
