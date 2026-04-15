# Iteration 007 — free mode (v2 spec — first iter under new gate)

**Agent**: general-purpose, model: opus
**Task title**: Promo code validation cache on /checkout

## Task
Laravel 11 + Vue 3 shop. New `PromoCacheService` uses `Cache::remember('active_promo_codes', 600, …)`.
`CheckoutController@validatePromo` reads cache, decrements `uses_left`.
`AdminPromoController@update/destroy` mutate `promo_codes`. Scheduled
`ExpirePromoCodesJob` flips `active=false`. Queued `SendPromoRedeemedEmailJob`
sends mail + increments counter.

## Bugs planted (4) — all targeting known gaps
1. **TOCTOU** on `uses_left` decrement (iter-4 gap)
2. **Cache staleness**: admin update/destroy never `Cache::forget`  (iter-4 gap)
3. **Cache staleness**: scheduled ExpirePromoCodesJob leaves cache dirty
4. **Queue idempotency**: `SendPromoRedeemedEmailJob` non-idempotent on retry (iter-5 gap)

## Simulation — 0/4 caught
Current SKILL.md (pre-edit) had:
- Zero mentions of `Cache::remember`, `Cache::forget`, cache invalidation, cache tags
- Zero mentions of `lockForUpdate`, transaction, concurrent, TOCTOU, race
- No reflex for at-least-once job semantics

## Scoring (diagnostic only under v2)
```
planted: 4, caught: 0, missed: 4
forbidden: 0, friction: 3
score = 0 - 2*4 - 0 - 1 = -9  (subagent reported 15 — math slip; corrected here)
```

## Proposed edit — ACCEPTED (structural gate, v2)
Insert three new Cross-Layer sub-sections BEFORE `## Self-Tuning`:

### 1. Cache Invalidation Coverage
- Every `Cache::remember($key, ...)` is a promise that every mutation path
  calls `Cache::forget($key)` or `Cache::tags([...])->flush()`
- Verification command: grep for Cache::remember → find model → grep all
  mutation paths → confirm forget-adjacent
- Also covers scheduled jobs and queue workers that mutate on a different
  process than the request cycle

### 2. Concurrency / TOCTOU on Counters and Quotas
- Check-then-act on counters (`uses_left`, `stock`, `seats_remaining`, `credits`)
  is always a race unless atomic SQL or `lockForUpdate()` inside transaction
- Cache-then-decrement is ALWAYS wrong — cached value is stale relative to
  concurrent requests
- Code example: WRONG (read-then-decrement) vs RIGHT (atomic conditional
  decrement, check affected rows)

### 3. Queue Job Idempotency (at-least-once by contract)
- Laravel queues = at-least-once; worker crash between side-effect and ack → replay
- Every `ShouldQueue` job that mutates external state needs a dedup key
  checked-and-set in one transaction OR must be provably pure
- `Mail::to(...)->send()` without guard = duplicate email on every retry
- Audit reflex: name the idempotency key or justify purity

## Impact
**3 of 4 documented gaps closed in one edit** (TOCTOU, cache staleness, queue idempotency).
Only path-traversal (iter-5 finding) remains un-addressed. ~55 lines added to
SKILL.md, all in Cross-Layer Checks section (tightest structural fit). Grep-based
verification commands follow existing VERIFICATION-NOT-ASSERTION discipline.

## Final JSON
```json
{"iter":7,"mode":"free","score":-9,"baseline":11,"action":"edit","bugs_planted":4,"bugs_caught":0,"bugs_missed":4,"friction_notes":3,"token_cost":"medium","edit_closes_gaps":["TOCTOU","cache_invalidation","queue_idempotency"]}
```
