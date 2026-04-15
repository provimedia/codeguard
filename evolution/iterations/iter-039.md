# Iteration 039 — free mode (v4, twelfth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: CSV bulk importer — add negative-price validator

## Task (self-contained, PHP 8.2 + PDO + MySQL)
`VendorCsvImporter::import()` does `fopen → beginTransaction → loop
insert → commit → fclose`. Task: add `throw InvalidArgumentException` on
`price < 0`. Caller catches `Throwable` and continues.

## Bugs planted (2)
- **B1** New throw leaves PDO transaction open — PHP doesn't auto-rollback; connection returns to pool with stale TX. (Partially covered pre-edit by saga reflex.)
- **B2** `fclose($fh)` only reached on happy path — every throw leaks the file descriptor. (Not covered pre-edit — no finally-block reflex.) **TARGETED**

## Pre-edit simulation
Caught **1/2**. B1 via saga/compensation reflex (iter-18). B2 missed —
no "finally-block discipline" or "resource leak on throw" category.
Read-only audits miss this because the happy-path `fclose` looks present
on line N.

## Proposed edit (trimmed from subagent's +50 to +31)
New Cross-Layer sub-section **"Error-Path Resource Cleanup (finally-block
discipline)"** inserted before Long-Running Data Backfill Shape.

- **Principle**: distinct from saga (multi-step UNDO ordering) — this
  reflex covers SINGLE resources whose lifetime must span every exit path
  of a function. A release call on the happy path AFTER the work leaks
  the resource on every non-happy exit.
- **Why PDO transactions are the most dangerous case**: PHP does NOT
  auto-rollback on exception. Connection returns to pool/long-running
  worker with open TX. Next unrelated query runs inside stale TX.
- **6-row resource table**: PDO transaction, file handle, advisory lock,
  temp file/dir, process/pipe, keep-alive connection
- **Audit reflex**: draw the function's exit graph (happy + early return +
  every throw reachable from acquire — INCLUDING throws inside library
  calls). For EACH exit: "Is release reached?" Only safe answer on all
  exits simultaneously is `try { ... } finally { release(); }`.
- **Canonical PDO-transaction fix** with `inTransaction()` guard (to avoid
  masking the original exception when DDL implicitly committed).

- `targeted_miss: "B2"`
- Framework tokens in new_string: **0** (all PHP stdlib: `$pdo->beginTransaction`, `rollBack`, `commit`, `inTransaction`, `fopen`, `fclose`, `tmpfile`, `flock`, `proc_open`, `GET_LOCK`, `RELEASE_LOCK`)
- Subagent originally included `Swoole`, `Octane`, `RoadRunner` framework refs + a copy-paste trap paragraph + lsof verification; main loop trimmed those.
- Line count delta: **+31** (heavy; new general bug category with comprehensive resource table + canonical fix)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +31 (heaviest but justified; 6 distinct leak-on-throw failure modes closed in one reflex)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 1
post_caught:                2
delta:                      +1
targeted_miss:              B2
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New Error-Path Resource Cleanup section explicitly
tables fopen→fclose and mandates exit-graph walk; B2 fh leak is now caught
alongside B1 PDO-tx leak (also reinforced by canonical try/catch/rollBack
example)."*

**Full 2/2 post-edit. Twelfth v4 targeted win.**

## Decision: **edit_verified**

## Progress after 39 iters
- Verified targeted wins: **12** (iters 13, 14, 18, 22, 23, 25, 27, 29, 32, 35, 37, 39)
- Bugs closed cumulatively via v4 verify: **16** (money, timezone, saga, FOR-UPDATE, deep-offset, page-cap, auth-parity, NULL-aggr, LEFT-JOIN, composite-index, collation, session-fixation, backfill-undo, backfill-resume, backfill-replica-lag, file-handle-leak)
- Benchmark passes: 3
- Regressions: 0

## Final JSON
```json
{"iter":39,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":846,"skill_md_delta":31,"pre_caught":1,"post_caught":2,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
