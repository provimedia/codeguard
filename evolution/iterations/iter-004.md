# Iteration 004 — free mode

**Agent**: general-purpose, model: opus
**Task title**: Live inventory badge on Shop listing + admin stock bump

## Task
Laravel 11 + Vue 3 feature: live "In Stock / Low / Out of Stock" badge per product
on `/shop`, via new `WarehouseService` against 240k-row `warehouse_stocks` table.
`/api/stock-snapshot` endpoint polled every 30s. Cached `trending` list. Admin
`bump()` action for manual stock updates.

## Bugs planted (6)
A. **P2/N+1** — `ShopController::index` loops paginator calling `getStockFor()` per row
B. **Frontend reactivity** — `const { data: rows } = props.products` destructures reactive state
C. **TOCTOU race** — `bumpStock` reads then writes non-atomically
D. **Cache staleness** — `Cache::remember('trending_products', 3600)` never invalidated on product mutations
E. **Missing DB index** on `warehouse_stocks.product_id`
F. **Missing auth** on admin `bump()` route

## Simulation outcome
- **Caught (4)**: A, B, E, F — all textbook hits
- **Missed (2)**:
  - **C (TOCTOU race)**: SKILL.md Logic-layer checklist lists edge cases (null, 0, off-by-one) but has NO prompt for atomicity / check-then-act / race conditions. Security layer also omits it.
  - **D (Cache invalidation)**: SKILL.md has NO cache-invalidation reflex anywhere. `Cache::remember` TTL + related-model mutation is a whole bug family without a trigger.

## Scoring
```
planted: 6, caught: 4, missed: 2
forbidden: 0
friction_notes: 3 → penalty 1
score = 4 - 2*2 - 2*0 - 1 = -1
baseline = 9 → REJECT (-1 < 9)
```

## Gate decision: **NOOP**
Score -1 well below baseline 9. Subagent correctly returned `proposed_edit: null`
per spec: "If you can't score 9+, or if no clear improvement exists, return
`proposed_edit: null`. Do not force an edit to game the gate."

## ⚠ SIGNAL — meta-observation
Two real, concrete gaps identified but cannot land an edit under the current
scoring model. This is the gate working as designed (drift protection), but also
reveals a scoring-model weakness: baseline_score is absolute, so a task with more
planted bugs penalizes even honest simulations. Future run-iteration.md revision
should consider percentage-based scoring (catch_rate) or relative-delta scoring.

## Friction notes (for future iterations to address with a high-score task)
1. **No atomicity / TOCTOU / race-condition prompt** in Logic layer or Cross-Layer Checks
2. **No cache invalidation reflex** — `Cache::remember` staleness on related-model mutations has no checklist entry
3. **PLAN MODE P1–P6 not explicitly re-invoked in BUILD MODE Pre-Flight** when coding from a spec without a separate plan-review step

## Final JSON
```json
{"iter":4,"mode":"free","score":-1,"baseline":9,"action":"noop","bugs_planted":6,"bugs_caught":4,"bugs_missed":2,"friction_notes":3,"token_cost":"medium","proposed_edit":null}
```
