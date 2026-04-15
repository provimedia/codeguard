# Iteration 025 — free mode (v4, sixth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Auth enforcement asymmetry — service called from web route + CLI + queue + admin

## Task (self-contained, PHP/Laravel substrate)
`MessageService::sendFromUser` enforced at web edge via `MessagePolicy`
(checks `is_verified && !is_banned && credits >= 1`). PR adds 3 new entry
points: `BroadcastCommand` (CLI), `BroadcastJob` (queue worker), and admin
route only checking `is_admin`. All three reuse the same service, bypassing
the policy.

## Bugs planted (4)
- **B1** Auth enforcement asymmetry — 4 entry points, 4 different auth gates for the same service. **TARGETED**
- **B2** Saga/compensation — CLI foreach has no per-recipient resume; iter 3 throwing leaves iters 1-2 committed + emailed
- **B3** Queue idempotency — `BroadcastJob` has no dedup key, at-least-once retry double-charges + double-emails
- **B4** TOCTOU — `credits < 1` check then `decrement` is non-atomic

## Pre-edit simulation
Caught **3/4**: B2, B3, B4 via saga/queue-idempotency/TOCTOU reflexes. Missed
**B1** — skill Security layer had generic "Missing auth checks?" bullet but
no reflex to audit auth parity across multiple entry points reaching the
same service.

## Proposed edit (trimmed from subagent's +35 to +15)
New Cross-Layer sub-section **"Auth Enforcement Parity Across Entry Points"**
inserted before Frontend Reactivity Traps:

- Principle: when a service method is invoked from 2+ entry points (web route,
  CLI command, queue/background worker, scheduled task, admin panel, internal
  API, webhook), the auth gate must be equivalent at every entry point OR live
  INSIDE the service.
- Why edge-auth breaks: middleware doesn't run for background workers or CLI
  invocations.
- Audit reflex: for every service method touched, run consumer grep (BUILD
  Step 1d), for each caller answer (1) what auth check guards this entry
  point, (2) is it equivalent to every other entry point's check, (3) if
  different, does the difference match documented intent.
- Fix: push authz INTO the service. Edge-auth becomes defense-in-depth.
- Silent failure: web UI + policy tests green, banned user still triggers
  action via weekly CLI job or queue worker.

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (generic "middleware/policy/gate",
  "admin flag", "service method")
- Line count delta: **+15** (subagent proposed +35; main loop trimmed by
  dropping Laravel/Rails/Django mention, grep command with framework paths,
  and the "Real bug shape this prevents" narrative — content was essentially
  the task itself)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +15 (heavy but new coverage category; subagent original was +35)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 3
post_caught:                4
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New Auth Enforcement Parity section triggers cleanly on
multi-entry-point sendFromUser; B2/B3/B4 still fire via saga/queue-idempotency/
TOCTOU sections."*

**Full 4/4 post-edit. Sixth v4 targeted win.**

## Decision: **edit_verified**

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
13    726    0      edit_verified      +1            money-FLOAT ✓
14    738    +12    edit_verified      +1            timezone ✓
18    760    +16    edit_verified      +1            saga ✓
22    762    +2     edit_verified      +1            FOR-UPDATE-autocommit ✓
23    779    +17    edit_verified      +2            deep offset + page cap ✓✓
25    787    +15    edit_verified      +1            auth parity ✓
6 targeted wins, 7 bugs closed via verify, 0 regressions
```

## Final JSON
```json
{"iter":25,"mode":"free","score":6,"baseline":68,"action":"edit_verified","skill_md_lines":787,"skill_md_delta":15,"pre_caught":3,"post_caught":4,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
