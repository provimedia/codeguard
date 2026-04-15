# Iteration 009 — free mode (v3, generalization/optimization)

**Agent**: general-purpose, model: opus
**Task title**: Generalize iter-7 sub-sections — strip Laravel, keep PHP/MySQL

## Goal
User directive mid-loop: "entferne die Laravel Sachen und optimiere lieber auf
generell, aber mit php und mysql". Iter-7's three Cross-Layer sub-sections
(Cache Invalidation / TOCTOU / Queue Idempotency) were principle-universal
but example-Laravel-heavy. Retrofit them.

## Approach
1. Subagent proposed a pure-prose framework-agnostic generalization (0 tokens,
   35 → 17 lines). Good principles, but no concrete substrate.
2. User's latest directive allows PHP/MySQL code — so I added one vanilla SQL
   example to the TOCTOU sub-section showing the WRONG read-then-write vs
   RIGHT atomic conditional UPDATE + rowCount() check.
3. Kept Cache Invalidation and Queue Idempotency as prose-only (the principles
   don't need code to be actionable).

## Changes
### Cache Invalidation Coverage
- Removed: Laravel `Cache::remember`, `Cache::forget`, `Cache::tags` references
- Removed: bash grep snippet targeting `app/` + `--include='*.php'` + `PromoCode::`
- Kept: the "every write path must invalidate" principle
- Kept: "name 0 unguarded mutation paths out loud before the check passes" reflex
- Kept: inverse-direction check (background processes must invalidate too)

### Concurrency / TOCTOU on Counters and Quotas
- Removed: `DB::transaction(fn() => Model::lockForUpdate()...)`, `PromoCode::`,
  `->decrement`, `Cache::remember` references
- Replaced: PHP Eloquent WRONG/RIGHT example with **vanilla SQL** WRONG/RIGHT:
  ```sql
  UPDATE promo SET uses_left = uses_left - 1 WHERE id = ? AND uses_left > 0;
  -- PHP then checks PDOStatement::rowCount(); 0 = race lost, reject.
  ```
- Kept: `check-then-act`, `lockForUpdate`, `CAS` phrases as universal concepts
- Kept: audit reflex

### Queue/Task Idempotency
- Removed: `Laravel queues`, `ShouldQueue`, `implements ShouldQueue`, `Mail::to`,
  `handle()` references
- Kept: at-least-once contract principle
- Kept: dedup key / UNIQUE index mechanism
- Kept: audit reflex

## Metrics
```
BEFORE (iter-7 + v3 retrospective baseline):
  lines (3 sub-sections):  35
  framework tokens:        ~17 (Cache::, ShouldQueue, Mail::to, PromoCode::, etc.)
  SKILL.md total lines:    745

AFTER (iter-9 generalized):
  lines (3 sub-sections):  24
  framework tokens:        0 (only: PDOStatement::rowCount, SQL, UNIQUE)
  SKILL.md total lines:    734

Δ: -11 lines in total, -17 framework tokens, same 3 principles preserved
```

## Scoring (diagnostic)
```
planted: 0 (optimization iter, not bug-hunting)
caught: 0
score: 0
```

## Gate check (v3)
- edit != null ✓
- old_string unique ✓ (verified via Grep)
- framework-token scan on new_string: 0 hits ✓
- post-edit structure: `name: code-guardian` present, `## PLAN MODE (v5` present ✓
- line-count trend: -11 (NEGATIVE = good under v3) ✓

**Action**: edit
**consecutive_noops**: 1 → 0

## Final JSON
```json
{"iter":9,"mode":"free","score":0,"baseline":11,"action":"edit","bugs_planted":0,"bugs_caught":0,"skill_md_lines":734,"skill_md_delta":-11,"framework_tokens_in_edit":0,"edit_kind":"generalization_tightening"}
```
