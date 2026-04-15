# Iteration 043 — free mode (v4, fourteenth targeted win, double hit)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: `transfer_funds` — read-then-write 2 wallets inside txn, no FOR UPDATE

## Task (self-contained, PHP 8.2 + MySQL 8 InnoDB REPEATABLE READ)
`transfer_funds(PDO, fromId, toId, amount)` called from HTTP handler AND
from nightly CLI that forks with `pcntl_fork`. Reads both wallets via
`SELECT ... WHERE id IN (?, ?)` inside `beginTransaction/commit`, checks
overdraft, UPDATEs both, inserts ledger rows.

## Bugs planted (2)
- **B1** Bare SELECT inside BEGIN/COMMIT is a REPEATABLE READ consistent snapshot — concurrent callers both see the same starting balance, both compute `newFrom = old - amount`, both UPDATE → lost update + overdraft check defeated. **TARGETED**
- **B2** Even after adding FOR UPDATE, lock order matches call order (from, to) → `transfer(A,B)` + `transfer(B,A)` deadlock.

## Pre-edit simulation
Caught **0/2**. Existing "SELECT FOR UPDATE without transaction" note
(iter-22) covered the OPPOSITE direction (missing transaction around a
FOR UPDATE) but not the inverse (transaction around a non-locking SELECT).
Counter TOCTOU reflex applies to single counters, not to multi-row
read-then-write inside explicit transactions. No lock-ordering guidance.

## Proposed edit — extend Concurrency/TOCTOU section with 2 paragraphs
After the existing "FOR UPDATE without transaction = no-op" note:

1. **"The inverse: a transaction without FOR UPDATE does NOT lock the rows
   it reads"** — names REPEATABLE READ consistent snapshot read, lost
   update, both fixes (FOR UPDATE or single atomic conditional UPDATE with
   `rowCount` check), audit reflex for every `beginTransaction` in the
   diff, verification via two-connection race script.
2. **"Lock ordering for multi-row locks"** — names `transfer(A,B)` +
   `transfer(B,A)` deadlock, `ORDER BY id ASC` fix, verification via race
   with swapped args confirming no `ERROR 1213 Deadlock found`.

- `targeted_miss: "B1"` (B2 caught as collateral)
- Framework tokens in new_string: **0** (`BEGIN`, `COMMIT`, `FOR UPDATE`, `SELECT`, `UPDATE`, `rowCount()`, `REPEATABLE READ`, `ERROR 1213`, `beginTransaction`, `pcntl_fork` — all SQL/PHP stdlib)
- Line count delta: **+4** (efficient — inline paragraphs inside existing sub-section)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +4 (closes TWO bugs in 4 lines) ✓
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

**Verify notes**: *"Lines 691/693 explicitly name REPEATABLE READ snapshot
read lost-update and `transfer(A,B)/transfer(B,A)` deadlock with `ORDER BY
id` fix."*

**Full 2/2 post-edit. Fourteenth v4 targeted win, delta +2.**

## Decision: **edit_verified**

## Progress after 43 iters
- Verified targeted wins: **14**
- Bugs closed cumulatively: **19** (counter + 4 v4 double/triple hits)
- Benchmark passes: 4
- Regressions: 0
- SKILL.md: 715 → 840 (+125 net across 43 iters, 14 verified wins + ~110 framework tokens stripped)

## Final JSON
```json
{"iter":43,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":840,"skill_md_delta":4,"pre_caught":0,"post_caught":2,"verify_delta":2,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_double_hit","spec_version":4}
```
