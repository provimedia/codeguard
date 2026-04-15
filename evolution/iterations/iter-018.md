# Iteration 018 — free mode (v4, targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Checkout endpoint: reserve stock + Stripe charge + order insert + confirmation email

## Task (self-contained, PHP/MySQL substrate)
POST /api/checkout endpoint: foreach cart item → stock check → decrement →
Stripe PaymentIntent.create(confirm=true) → Order::create(status='paid') →
OrderConfirmationMail. UNIQUE(user_id, stripe_charge_id) on orders table.
Full controller implementation provided.

## Bugs planted (6)
- **B1** Saga without compensation — stock decrement → Stripe charge → `Order::create` in sequence, no atomic boundary, no rollback. If INSERT throws (unique-index conflict / lock timeout / disk full) AFTER Stripe captured, customer is charged with no order row and no refund. **TARGETED**.
- **B2** TOCTOU on stock check-then-decrement
- **B3** Money through PHP float (iter-13 rule)
- **B4** N+1: `Product::find` inside per-item loop
- **B5** `env('STRIPE_SECRET')` in controller body (P4)
- **B6** `$request->input('items')` no array length cap (iter-16 rule)

## Pre-edit simulation
Caught **5/6**: B2, B3, B4, B5, B6. Missed **B1** — skill had Queue
Idempotency (retries), TOCTOU (concurrency races), Return Type
Completeness (return types), but NO reflex for "ONE request with N
sequential side-effects and no compensation on partial failure".

## Proposed edit (trimmed by main loop from subagent's 40-line version)
New sub-section **"Multi-Step Side-Effect Atomicity (saga / compensation)"**
inserted between Queue/Task Idempotency and Input Size & Complexity Limits.

Contents (~16 lines):
- Definition: 2+ side-effects in one handler = saga; partial commit on throw
- Distinction from Queue Idempotency (same payload, retries) and TOCTOU (concurrency)
- Audit reflex: enumerate steps IN ORDER; for each transition answer "if step N+1 throws, what automatically undoes step N?"
- Three remediations: (1) single atomic boundary, (2) **external-last ordering**, (3) explicit compensation
- Concrete anti-pattern: `local decrement → external charge → INSERT order` — fix is INSERT with `status='pending'` FIRST, then charge, then UPDATE to `status='paid'`, email moves AFTER commit
- Verification: mark each step L/X, point at the L step that must come LAST

Subagent's original was 40 lines including a "silent failure mode" paragraph and a code-block walkthrough — main loop trimmed to ~16 lines for honest line-count budget.

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (UPDATE, INSERT, DELETE are vanilla SQL)
- Line count delta: **+16** (744 → 760)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +16 (heavy but justified — new critical bug category, trimmed from subagent's +40)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 5
post_caught:                6
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New Multi-Step Side-Effect Atomicity section names the
EXACT `decrement → charge → INSERT` anti-pattern; all 5 prior catches still
fire. L/X step mapping on this handler: step 1 decrement (L), step 2 charge
(X), step 3 INSERT (L), step 4 mail (X). Last step must be L not X — INSERT
with pending must come before charge → explicit BLOCK."*

**Full 6/6 post-edit.** Third v4 targeted win in a row.

## Decision: **edit_verified**

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
13    726    0      edit_verified      +1            B1 money ✓
14    738    +12    edit_verified      +1            B1 timezone ✓
15    736    -2     edit_generalize    —             —
16    755    +19    edit_generalize    —             —
17    744    -11    edit_generalize    —             —
18    760    +16    edit_verified      +1            B1 saga ✓
6-iter net: +34 lines, +3 verify wins, 0 regressions
```

## Final JSON
```json
{"iter":18,"mode":"free","score":0.83,"baseline":68,"action":"edit_verified","skill_md_lines":760,"skill_md_delta":16,"pre_caught":5,"post_caught":6,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_trimmed","spec_version":4}
```
