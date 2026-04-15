# Iteration 049 — free mode (v4, seventeenth targeted win, double hit)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Password reset — consume token + set new password

## Task (PHP 8.2 + MySQL 8, `password_resets` with `consumed_at DATETIME(6) NULL`)
`resetPassword` does: SELECT token → check expiry (lex compare of
`DATETIME(6)` strings) → check `consumed_at IS NULL` → BEGIN → UPDATE users
password → UPDATE password_resets SET consumed_at = NOW(6) WHERE id = :id
(UNCONDITIONAL on id) → COMMIT.

## Bugs planted (2)
- **B1** Token-replay race — SELECT checks `consumed_at IS NULL`, UPDATE is unconditional on id. Two concurrent replays both pass the gate, both enter own txn, both UPDATE user row. **TARGETED**
- **B2** Lexicographic comparison of `DATETIME(6)` strings — MySQL may return 19-char vs 26-char depending on insertion path; lex-compare reorders around second boundaries.

## Pre-edit simulation
Caught **0/2**. Existing TOCTOU reflex covers numeric counters (iter-7) and
read-then-write on real rows (iter-43), but neither covers **single-use
boolean resource consumption** where the fix is a conditional UPDATE with
rowCount gate. A purely structural audit sees "consumed_at check exists
+ wrapped in transaction + password hashed" and rubber-stamps it.

## Proposed edit (trimmed from subagent's +35 to +15)
New Cross-Layer sub-section **"Single-Use Resource Consumption
(token/coupon/one-time action replay)"** inserted before Auth Enforcement
Parity. Contains:

- Canonical SQL pattern:
  ```sql
  UPDATE t SET consumed_at = NOW(6)
   WHERE id = :id AND consumed_at IS NULL AND expires_at > NOW(6)
  ```
  + `rowCount() === 1` gate BEFORE any side effect
- Anti-pattern walkthrough: SELECT-gate → BEGIN → unconditional UPDATE
  side effect → unconditional UPDATE consumed_at — explains why wrapping
  in a transaction does NOT fix it (transactions serialize writes to
  same row, not reads)
- Audit reflex keyed on `consumed_at` / `used_at` / `redeemed_at` /
  `verified_at` / `processed_at` / `is_consumed` columns
- Concurrent-replay curl verification (`seq 1 20 | xargs -P20 -I{} curl ...`
  should show exactly 1 success + 19 `already_used`)
- **Timestamp sub-reflex**: expiry/window checks MUST be evaluated in SQL
  (`WHERE expires_at > NOW(6)`) or via typed `DateTimeImmutable`, never
  lex-compare of datetime strings

- `targeted_miss: "B1"` (B2 caught collaterally by timestamp sub-reflex)
- Framework tokens in new_string: **0** (all SQL + PHP stdlib)
- Line count delta: **+15** (subagent proposed +35; main loop dropped
  SELECT FOR UPDATE alternative explanation and the 2nd verification example)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +15 (closes two related bug classes in one reflex)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 0
post_caught:                2
delta:                      +2
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"Single-Use Resource Consumption section explicitly
names the SELECT-then-unconditional-UPDATE anti-pattern with `rowCount`
gate fix and timestamp sub-reflex; `consumed_at` trigger fires directly
on the candidate's columns."*

**Full 2/2 post-edit. Seventeenth v4 targeted win, delta +2.**

## Decision: **edit_verified**

## Progress after 49 iters
- Verified targeted wins: **17**
- Bugs closed cumulatively via v4 verify: **24**
- Benchmark passes: 4
- Regressions: 0

## Final JSON
```json
{"iter":49,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":866,"skill_md_delta":15,"pre_caught":0,"post_caught":2,"verify_delta":2,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_double_hit","spec_version":4}
```
