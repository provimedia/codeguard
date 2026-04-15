# Iteration 013 — free mode (**first iter under v4** — post-edit verify)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Monthly billing rollover cron (tenants + PayGate)

## Task (self-contained, PHP/MySQL substrate, framework-agnostic)
Monthly billing cron iterates tenants, computes usage overage, charges via
PayGate, emails invoice, resets counter. Follows `BillingRollover.php` pattern.
250k-row tenants table. Supervisor-retried cron. Full code snippets for
BillingRollover, PayGate, InvoiceController included.

## Bugs planted (8) — structured with bug_ids
- **B1** Money as FLOAT (`usage_this_month`, `rate_per_unit`, `balance_due`) — TARGETED
- **B2** `date('Y-m-d')` server TZ vs tenant `billing_tz` — off-by-one billing
- **B3** `fetchAll()` on unbounded 250k-row table — OOM
- **B4** PayGate::charge() in per-row loop (no bulk/parallel)
- **B5** TOCTOU reset of `usage_this_month` vs concurrent writers
- **B6** Retry-eligible cron without idempotency key → double-charge/double-email
- **B7** `?api_key=` in URL
- **B8** Raw SQL interpolation of `$amount`/`$today`

## Pre-edit simulation (attack subagent)
Caught 6/8 (B3 P2, B4 N+1 HTTP, B5 TOCTOU, B6 queue idempotency, B7 P3, B8
security). Missed: **B1** (money-as-float) and B2 (timezone).

## Proposed edit
Extend the `**DB Integrity**` bullet in audit layer 3d with one clause:

```diff
-**DB Integrity** — Fields match live schema? FKs correct? Missing indexes on queried columns? N+1 patterns? ORM attributes match real columns?
+**DB Integrity** — Fields match live schema? FKs correct? Missing indexes on queried columns? N+1 patterns? ORM attributes match real columns? Money/currency stored as integer minor units (cents) or DECIMAL(p,s), NEVER FLOAT/DOUBLE — float rounding silently corrupts totals across aggregation, and `a*b` in float arithmetic is not associative.
```

- `targeted_miss: "B1"`
- Framework tokens in new_string: 0
- Line count delta: 0 (same line, extended)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count guard: 0 delta ✓
- structure intact ✓

## **v4 — POST-EDIT VERIFY** (dispatched after apply, before commit)

The verify subagent re-simulated the same task with the new SKILL.md and
INDEPENDENT honest grading:

```
pre_caught:                   6
post_caught:                  7
delta:                        +1
targeted_miss:                B1
targeted_miss_now_caught:     TRUE ✓
forbidden_phrases_count:      0
```

**Verify notes** (from the second subagent): *"Edit added explicit
money-as-FLOAT clause to 3d DB Integrity; schema introspection in Pre-Flight
1b surfaces the FLOAT columns so the new clause fires and catches B1."*

B2 (timezone) remains missed — the edit didn't target it. No regression.

## Decision: **edit_verified** (targeted win)

The edit actually closed the gap it claimed, mechanically confirmed by an
independent simulation. This is the strongest signal v4 can produce.

- action = `"edit_verified"`
- consecutive_noops: 0 → 0
- baseline_score = max(11, score) — diagnostic only

## ⚠ Remaining gap — B2 (timezone boundary)
Candidate for a future iteration: add a timezone-boundary reflex. Would be a
new 1-bullet reflex ("date/time comparisons must use the correct timezone
and be robust to DST; cron fired on server TZ mishandles per-entity TZ
boundaries").

## Final JSON
```json
{"iter":13,"mode":"free","score":68,"baseline":11,"action":"edit_verified","skill_md_lines":726,"skill_md_delta":0,"pre_caught":6,"post_caught":7,"verify_delta":1,"verify_target_hit":true,"edit_kind":"bug_fix_targeted","spec_version":4}
```
