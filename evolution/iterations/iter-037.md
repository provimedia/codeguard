# Iteration 037 — free mode (v4, eleventh targeted win, strongest delta +3)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Backfill normalized_email on 10M-row users table

## Task (self-contained, PHP 8.2 + MySQL 8)
One-shot data migration: backfill `users.normalized_email` for ~10.2M legacy
rows, normalization requires PHP (dots-strip for gmail.com). Production
constraints: `innodb_log_file_size=512MB`, async replica with 30s SLA, hot
400 writes/sec table, runs under `nohup` at 03:00 UTC, must be resumable.

## Bugs planted (3)
- **B1** Single-statement `UPDATE SET ... WHERE IS NULL` on 10M rows → undo log blow-up, transaction aborts or table locks for minutes. **TARGETED**
- **B2** No resumability checkpoint — crash at row 7M → restart from 0 or re-processes finished rows
- **B3** No replication-lag throttle — tight loop of chunk UPDATEs pushes binlog faster than async replica can apply

## Pre-edit simulation
Caught **0/3**. Adjacent reflexes (P2 scale, deep-offset, queue idempotency,
TOCTOU, saga) don't cover "one-shot mutation command shape". Naïve audit
ticks "uses the index" and approves.

## Proposed edit (trimmed from subagent's +40 to +21)
New Cross-Layer sub-section **"Long-Running Data Backfill Shape (undo log,
resumability, replica lag)"** inserted before Input Size & Complexity Limits.

- **Principle**: one-shot mutation commands are about OPERATIONAL shape, distinct from P2 read-streaming, deep-offset query shape, or queue retry semantics.
- **Three failure modes**: single UPDATE → undo log; no resume → crash-replay wastes work; no throttle → silent replica lag
- **Three audit questions** on every long-running mutation command:
  1. Chunk size + commit per chunk? — single unbounded UPDATE → BLOCKED
  2. Resume key? — name the column + prove finished rows excluded
  3. Throttle? — name sleep-between-chunks + replication-lag check
- **Verification**: `SHOW PROCESSLIST` (many short UPDATEs, not one long), `SHOW ENGINE INNODB STATUS\G` (History list length not unbounded), `SHOW REPLICA STATUS\G` (Seconds_Behind_Master within SLA)

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all MySQL/Unix standard: `innodb_log_file_size`, `nohup`, `SHOW PROCESSLIST`, `Seconds_Behind_Master`)
- Subagent originally included `Artisan`, `php artisan`, `pt-online-schema-change`; main loop trimmed those plus the "Copy-paste trap" paragraph (redundant with iter-23 deep offset)
- Line count delta: **+21**

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +21 (heavy; new general bug category with 3 failure modes closed in one reflex)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 0
post_caught:                3
delta:                      +3    ← STRONGEST DELTA YET
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none — all 3 planted bugs caught)
forbidden_phrases_count:    0
```

**Verify notes**: *"New backfill-shape sub-section maps 1:1 to B1/B2/B3;
task constraints mirror the three audit questions verbatim."*

**Full 3/3 post-edit. Eleventh v4 targeted win. First triple-hit delta.**

## Decision: **edit_verified**

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
32    809    +25    edit_verified      +1            collation ✓
33    803    -6     edit_generalize    —
34    784    -19    edit_generalize    —
35    811    +27    edit_verified      +1            session lifecycle ✓
36    799    -12    edit_generalize    —
37    820    +21    edit_verified      +3            backfill shape ✓✓✓
6-iter net: +36 lines, 3 verify wins, 5 bugs closed
```

## Progress after 37 iters
- Verified targeted wins: **11**
- Bugs closed cumulatively via v4 verify: **15** (money, timezone, saga, FOR-UPDATE, deep-offset, page-cap, auth-parity, NULL-aggr, LEFT-JOIN, composite-index, collation, session-fixation, backfill-undo, backfill-resume, backfill-replica-lag)
- Benchmark passes: 3
- Regressions: 0

## Final JSON
```json
{"iter":37,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":820,"skill_md_delta":21,"pre_caught":0,"post_caught":3,"verify_delta":3,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_triple_hit","spec_version":4}
```
