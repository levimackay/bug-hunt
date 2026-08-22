# Scenario Batch 2 — five more scenarios (target: 8 total)

Builds on `docs/BUILD_SPEC.md` and `docs/SCORING_AND_SCENARIOS_SPEC.md`. Read
both first — they're the living architecture and schema contracts. Each
scenario below is built by an independent agent working in its own git
worktree; there is zero file overlap between them or with existing scenarios,
so don't worry about collisions, just follow the existing three scenarios
(`scenarios/bug-1842-profile-upload/`, `scenarios/bug-1794-search-incorrect/`,
`scenarios/bug-1831-duplicate-notifications/`) as your structural and quality
reference.

## Shared requirements for every scenario in this batch

- Company is "Nexus." Pick a plausible small FastAPI service name per bug.
- Real git history: correct implementation → a refactor/feature commit that
  introduces the real, subtle regression (no comment flagging it, ever) → one
  unrelated recent commit as a red herring that touches nearby code but isn't
  the cause.
- `repo.bundle` packaging (not a committed nested `.git`) — mirror exactly
  what `scenario_engine/loader.py`'s `_ensure_repo_materialized` expects; look
  at an existing scenario's `repo.bundle` to confirm the mechanism.
- Visible tests that pass at every commit in the history (including the buggy
  one) — the regression must NOT be caught by the visible suite.
- A hidden test in `hidden_tests/` that fails against the buggy commit and
  passes once the real fix is applied.
- `scenario.yaml` matching the full schema used by the existing three files
  exactly (id, title, company, severity, difficulty, language, skills,
  learning_objectives, ticket with slack_thread, repo_path, entry_service,
  visible_test_command, root_cause, hidden_tests, hints — 4, ascending
  cost_xp — review_criteria as a list of single-key dicts (any check names
  you want, the schema is fully generic now — see `scenario_engine/schema.py`'s
  `ReviewCriteria.checks`), and a `scoring` block with `expected_fix_paths`
  and `code_quality_checks`).
- Verify with real pytest at each commit (materialize the repo via a plain
  `git clone`/worktree at each SHA, or reuse the loader) — don't just assert
  it should work, run it and paste the actual pass/fail output in your report.
- No comments flagging the bug. No AI attribution anywhere.
- Deterministic only — no threads, no real async timing races, even for the
  "async behavior" scenario below. It must reproduce identically every run.

## Scenario 4 — "Guest checkout crashes on the order summary" (intern / beginner, None handling)

Service: `checkout-service`. Endpoint computes an order total, applying a
loyalty discount when the customer has a membership tier.

History:
1. Correct: computes subtotal + tax; no loyalty discount logic yet, all
   customers (including guests, who have no account) work fine.
2. "Add loyalty discount to order summary" — adds discount logic that reads
   `customer.membership_tier.discount_pct` directly. For guest checkouts
   (`customer` has no membership, i.e. `membership_tier` is `None`), this
   raises an `AttributeError` and the endpoint 500s instead of just skipping
   the discount. Real, subtle: looks like ordinary attribute access, no
   obviously wrong logic if you don't think about the guest case.
3. Red herring: an unrelated "add order summary logging" commit.

Ticket: Customer Support reports "checkout crashes for some customers with a
500 error, seems random." Slack thread: one engineer guesses it's a payment
gateway timeout (wrong lead) before someone connects it to the recent loyalty
discount commit.

Root cause: missing None-check on `customer.membership_tier` before reading
its discount, which only guest customers (no account) hit.

## Scenario 5 — "Order history page 2 shows duplicate orders" (junior, pagination / off-by-one — must be a genuinely different code shape than the existing search off-by-one, not a copy)

Service: `orders-service`. `GET /orders?page=N&page_size=K` endpoint slices an
in-memory/list-backed order history.

History:
1. Correct: `start = (page - 1) * page_size`, `end = start + page_size`,
   slices `orders[start:end]`.
2. "Simplify order pagination math" — a refactor that changes the offset
   calculation to `start = page * page_size` (drops the `-1`), while keeping
   `end = start + page_size`. Page 1 now skips the first `page_size` orders
   entirely, and later pages show overlapping/shifted results relative to
   what a customer expects when clicking "next." Frame the customer-visible
   symptom as "page 2 shows some orders I already saw on page 1" (an overlap,
   not a crash) — pick concrete page_size/order-count numbers in your test
   fixtures that make this reproduce clearly and assert on the exact expected
   vs actual order IDs.
3. Red herring: an unrelated "add order status filter" commit.

Root cause: the offset calculation was changed from `(page - 1) * page_size`
to `page * page_size`, shifting every page's window by one page_size and
causing overlap/skip depending on which pages are compared.

## Scenario 6 — "Customers see stale prices after a price update" (engineer, caching)

Service: `catalog-service`. Product prices are cached in-memory (a simple
dict-based cache, no Redis needed) keyed by product id, with a
`GET /products/{id}` endpoint reading through the cache and an
`admin PUT /products/{id}/price` endpoint that updates the canonical price.

History:
1. Correct: `PUT` updates the canonical store AND invalidates
   (deletes/overwrites) that product's cache entry, so the next `GET`
   recomputes/refetches the fresh price.
2. "Add per-category price cache for faster catalog browsing" — introduces a
   second cache layer keyed by category (for a category-listing endpoint) and
   in doing so, refactors the invalidation call to only clear the per-product
   cache key built from a normalized/lowercased product id, while the read
   path's cache-key builder for a specific lookup case (e.g. an id containing
   a hyphen/mixed case, or an alias lookup) produces a different key that
   never gets invalidated — the real regression. Make it concrete and
   testable: pick an exact product id format whose cache key mismatches
   between the write path's invalidation and a specific read path, and assert
   that reading it after a price update still returns the old price pre-fix.
3. Red herring: an unrelated "add cache hit/miss metrics" commit.

Root cause: the invalidation path and a specific read path compute the cache
key for the same product differently, so an update invalidates a key nothing
ever reads, leaving the stale cached price in place indefinitely for that
product until process restart.

## Scenario 7 — "Order confirmation emails show the wrong item list" (engineer, async behavior — deterministic, not a real race)

Service: `notify-service` (a different, standalone service from
bug-1831-duplicate-notifications — don't reuse or import that one). An async
endpoint builds an order-confirmation email body: it fetches the order,
fetches the order's line items, and fetches the customer's shipping address,
then assembles a summary.

History:
1. Correct: each of the three async fetch functions is properly `await`-ed
   before assembling the summary; the summary always reflects the order
   passed in.
2. "Refactor email assembly for readability" — extracts the three fetches
   into a helper that kicks off the line-items fetch as a fire-and-forget
   task (`asyncio.create_task(...)` without ever awaiting or using its
   result) intending to "prefetch for a future optimization," but then the
   summary builder falls back to reading a shared/module-level
   `_last_fetched_items` variable that a different code path incidentally
   populated — so the email can end up describing a different order's items
   than the one actually being confirmed. This must be constructed so it
   reproduces deterministically in a test: e.g. call the endpoint for order A
   then order B in sequence within the same test and assert B's email
   correctly contains B's items, not leftover state from A, or vice versa —
   pick whichever concrete construction makes the bug 100% reproducible
   without relying on real scheduling/timing.
3. Red herring: an unrelated "add email delivery retry counter" commit.

Root cause: the refactor introduced a fire-and-forget async task alongside
reliance on shared mutable state instead of awaiting and using the fetched
result directly, so under certain call sequences the wrong order's line items
end up in the assembled email.

## Scenario 8 — "Expired discount codes are being accepted on bundle orders" (engineer, data validation / regression from a recent commit)

Service: `pricing-service`. A `POST /apply-discount` endpoint validates a
discount code (checks it exists, isn't expired, isn't already used up) before
applying it to an order.

History:
1. Correct: validation runs for every order regardless of type; only
   "standard" single-item orders exist at this point.
2. "Add bundle order support to pricing" — introduces a new `order.type ==
   "bundle"` code path for multi-item bundle orders, but the discount
   validation function's guard clause only runs its expiry/usage checks
   `if order.type == "standard"`, silently skipping all validation (code
   exists check, expiry check, usage-limit check) for the new "bundle" type
   — so an expired or already-maxed-out code is accepted without error on
   bundle orders. Real, subtle: the intent reads like "only standard orders
   need this check" but that's actually the regression, not a deliberate
   design choice, and it needs to apply to every order type.
3. Red herring: an unrelated "add bundle order shipping calculator" commit.

Root cause: the bundle-order feature commit scoped discount validation to
`order.type == "standard"` instead of running it for every order type,
letting invalid discount codes through unchecked on the new bundle path.

## What NOT to do

Don't touch anything outside your own new `scenarios/<your-id>/` directory.
Don't modify `scenario_engine/`, `api/`, or `frontend/` — the schema already
supports everything you need. Don't add auth-awareness to your scenario
content — a separate track is adding auth to the platform itself and your
scenario content doesn't need to know about it.
