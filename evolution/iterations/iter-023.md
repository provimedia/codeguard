# Iteration 023 — free mode (v4, targeted win +2)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Admin activity feed — paginated list of user actions

## Task (self-contained, PHP 8.2 + PDO + MySQL 8)
Internal admin tool `ops-console`, 84M-row `user_events` audit log (+250k/day,
7-year retention). Existing `forUser()` endpoint uses `LIMIT ? OFFSET ?` and
is fast because `WHERE user_id = ?` narrows via `idx_user_created` to ~10k
rows. Task: add `global_()` firehose method "following the same pattern",
over ALL rows, using `idx_created`. Ops team scrolls deep during incidents.

## Bugs planted (2)
- **B1** Deep OFFSET pagination on 84M rows without narrowing predicate. `LIMIT 50 OFFSET ?` = O(N+M) → page 1000 = 50,050 index rows; page 100k = 5M. Copy-paste from `forUser()` drops the `WHERE user_id=?` that made the source safe. **TARGETED**
- **B2** Unbounded `page` parameter — `?page=999999999` forces MySQL to walk full index, one-request DoS.

## Pre-edit simulation
Caught **0/2**. Existing reflexes:
- Efficiency asks "Missing pagination on large sets?" — pagination IS present, check passes (false negative)
- P2 aggregate trap (iter-21) names SUM/COUNT/AVG/MAX/MIN but not LIMIT/OFFSET
- Input Size table names `?per_page=`/`?limit=` but not `?page=`
- P5 Pattern Source Quality only runs in PLAN MODE, not BUILD MODE
- Forbidden phrase "follows the existing pattern" is listed BUT skill has no reflex to catch the *pattern-copy-blindness* for LIMIT/OFFSET specifically

Most likely outcome: auditor reads the code, notes the shape matches `forUser()`, approves. The trap.

## Proposed edit (trimmed from subagent's ~40 lines to ~20)
New sub-section **"Deep-Offset Pagination (LIMIT/OFFSET at depth)"** inserted
under N+1 Query Detection:

- States `LIMIT N OFFSET M` is O(N+M) with concrete row-count math
- Three mandatory audit questions:
  1. **What narrows the scan BEFORE the OFFSET?** Name the WHERE predicate and prove index coverage.
  2. **Is the filtered set bounded?** If unbounded → OFFSET is NOT acceptable, use keyset: `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT N`.
  3. **Is the `page` parameter capped?** `?page=999999999` is a one-request DoS.
- `EXPLAIN`-based verification: `rows` column must NOT scale with OFFSET
- **Copy-paste trap**: "Follow the existing pagination pattern" is safe ONLY if the new call site keeps the source's narrowing predicate

- `targeted_miss: "B1"` (B2 caught as collateral via question 3)
- Framework tokens in new_string: **0** — SQL keywords (LIMIT, OFFSET, WHERE, EXPLAIN, ORDER BY) are SQL standard, not framework
- Line count delta: **+17** (trimmed from subagent's +40)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓ (iter-23 subagent actually suggested `->paginate()`/`->forPage()` tokens in its version; main loop's trim dropped them)
- line-count: +17 (heavy but 0 framework tokens AND closes two bugs in one reflex)
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

**Verify notes**: *"Deep-Offset Pagination section triggers directly on
LIMIT/OFFSET; Q1 catches dropped WHERE (B1), Q3 catches uncapped page (B2);
copy-paste trap callout names the exact scenario."*

**Full 2/2 post-edit. Delta +2 — strongest single-edit gain yet.**

## Decision: **edit_verified**

Fifth v4 targeted win.

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
13    726    0      edit_verified      +1            money-FLOAT ✓
14    738    +12    edit_verified      +1            timezone ✓
18    760    +16    edit_verified      +1            saga ✓
22    762    +2     edit_verified      +1            FOR-UPDATE-autocommit ✓
23    779    +17    edit_verified      +2            deep-offset + page-cap ✓✓
5 targeted wins, 6 bugs closed cumulatively via verify, 0 regressions
```

## Final JSON
```json
{"iter":23,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":779,"skill_md_delta":17,"pre_caught":0,"post_caught":2,"verify_delta":2,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_double_hit","spec_version":4}
```
