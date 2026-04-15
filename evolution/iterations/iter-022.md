# Iteration 022 — free mode (v4, targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Inventory reservation handler with `SELECT FOR UPDATE` (no txn)

## Task (self-contained, PHP/PDO/MySQL)
Flash-sale inventory reservation endpoint. PDO direct (no ORM). Handler
does `SELECT ... FOR UPDATE`, then `UPDATE stock = stock - ?`, then
`INSERT reservations`. No outer `beginTransaction()`. Team added `FOR UPDATE`
last week expecting it to fix the oversell race; bug persists.

## Bugs planted (3)
- **B1** `SELECT ... FOR UPDATE` without transaction — under PDO/MySQL autocommit default, each statement is its own txn; the row lock is released the instant SELECT finishes, BEFORE the UPDATE runs. Developer believes they have a lock. **TARGETED**
- **B2** Saga: 2 writes (UPDATE stock, INSERT reservation) with no atomic boundary and no compensation on INSERT failure (phantom hold)
- **B3** TOCTOU — even with a working lock, atomic conditional `UPDATE stock = stock - ? WHERE id = ? AND stock >= ?` + rowCount check eliminates the race without needing a lock

## Pre-edit simulation
Caught **2/3**: B2 (saga), B3 (TOCTOU conditional-UPDATE alternative).
Missed **B1** — skill had TOCTOU guidance and the saga reflex (iter-18), but
no explicit check for "FOR UPDATE outside a transaction = lock is a no-op".
Reviewer sees `FOR UPDATE` and reads it as a valid lock without verifying
the txn boundary.

## Proposed edit
Append one paragraph to the Concurrency/TOCTOU section directly after the
existing audit reflex:

```
**SELECT ... FOR UPDATE without a transaction is a no-op.** Under autocommit
(PDO MySQL default and most driver defaults), each statement is its own
transaction — the row lock acquired by FOR UPDATE is released the instant
the SELECT finishes, BEFORE the follow-up UPDATE runs. The code READS as
locked-then-updated but executes as unlocked. Verification: grep every
FOR UPDATE in the diff and prove a BEGIN/START TRANSACTION opens before it
AND a COMMIT closes after the UPDATE. Missing either → the lock is decorative.
Same failure applies to advisory locks (GET_LOCK) released at session end
when the connection is returned to a pool mid-request.
```

- `targeted_miss: "B1"`
- Framework tokens: 0 (PDO is PHP stdlib; BEGIN/COMMIT/FOR UPDATE/GET_LOCK are SQL; "autocommit" is SQL standard)
- Line count delta: **+2** (appended inline under existing audit reflex line)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +2 (cheap) ✓
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 2
post_caught:                3
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New paragraph explicitly names FOR-UPDATE-without-txn
as a no-op under autocommit, triggering B1 catch alongside retained B2
(saga) and B3 (conditional UPDATE) reflexes."*

**Full 3/3 post-edit.** Fourth v4 targeted win.

## Decision: **edit_verified**

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
13    726    0      edit_verified      +1            money-FLOAT ✓
14    738    +12    edit_verified      +1            timezone ✓
18    760    +16    edit_verified      +1            saga ✓
22    762    +2     edit_verified      +1            FOR-UPDATE-autocommit ✓
4 targeted v4 wins, 0 regressions
```

## Final JSON
```json
{"iter":22,"mode":"free","score":2,"baseline":68,"action":"edit_verified","skill_md_lines":762,"skill_md_delta":2,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
