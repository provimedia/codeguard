# Iteration 006 — free mode

**Agent**: general-purpose, model: opus
**Task title**: Refactor DiscountService->calculate() + wire Vue CheckoutSummary

## Task
Change `DiscountService->calculate()` signature from `(Cart)->float` to
`(Cart, ?string)->array`, add discount stacking fields, build `CheckoutController@summary`,
render in Vue. Plan references `PricingService.php` as "follow this pattern" source.
18k-row discounts table. 7 snippets incl. existing consumers `CartController` and
`AdminOrderEditController`.

## Bugs planted (11)
1. P1: accessor not in `$appends`
2. P1: field missing from `$fillable`
3. P2: `->get()` on 18k rows
4. P3: `?key=` URL leak
5. P3: API key exposed to client via Inertia prop
6. P4: `env()` outside config
7. P5: plan copies bugs from PricingService (source-audit required)
8. BUILD 1d: `CartController` still expects `float` return (dependency break)
9. N+1: DB call in row loop
10. Cross-Layer: dynamic Eloquent attribute not serialized
11. DB Integrity: missing index on `valid_until`

## Simulation outcome
**Caught (11/11)** — every bug hits a direct PLAN/BUILD reflex.

## Scoring
```
planted: 11, caught: 11, missed: 0
forbidden: 0
friction_notes: 2 (< 3, no penalty)
score = 11 - 0 - 0 - 0 = 11
baseline = 9 → ACCEPT (11 >= 9)
```

## Friction notes
1. BUILD Step 1d (Dependency Impact Analysis) and DEBUG Phase 1d (Cross-Page
   Dependency Trace) describe the same consumer-grep workflow twice with slightly
   different framing — reader has to mentally reconcile them.
2. P5 Pattern Source Quality Check forces an awkward "PASS (N/A)" when the plan
   has no "follow pattern of X" language.

## Proposed edit — ACCEPTED
**Rationale**: DEBUG Phase 1d re-describes the exact consumer-grep workflow
already fully specified in BUILD Step 1d. Replace the duplicated step-by-step
with a pointer back to Step 1d plus the two truly DEBUG-specific questions
(recency of consumer change + git log on the function itself). Removes ~10 lines
of near-duplicate instructions, makes the DEBUG-specific value visible, does NOT
touch any of the 4 known missed-bug-class gaps.

**Diff** (SKILL.md, DEBUG MODE Phase 1d section):
- Removed: explicit Step 1–4 enumeration + `grep -r "brokenFunction"` snippet
- Kept: reference to BUILD Step 1d for the mechanical workflow
- Kept: DEBUG-specific questions (consumer-recency + function-recency via git log)
- Kept: "DEPENDENCY BREAK" framing + STOP rule

**Effect**: ~10 lines removed, friction note #1 addressed, no functional
regression on simulation.

## Final JSON
```json
{"iter":6,"mode":"free","score":11,"baseline":9,"action":"edit","bugs_planted":11,"bugs_caught":11,"bugs_missed":0,"friction_notes":2,"token_cost":"medium"}
```
