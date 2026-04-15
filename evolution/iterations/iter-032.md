# Iteration 032 — free mode (v4, ninth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Implicit type/collation coercion defeating indexes in JOINs

## Task (self-contained, MySQL 8)
E-commerce reporting endpoint. `customers.external_id` = `utf8mb4_unicode_ci`;
`orders.external_ref` = `utf8_general_ci` (legacy table after partial utf8mb4
migration). 48M-row `orders` table. JOIN on `c.external_id = o.external_ref`.
Plus a stray `WHERE id = '{$orderId}'` string-interpolated.

## Bugs planted (2)
- **B1** Collation mismatch on JOIN — both columns indexed individually but MySQL implicit `CONVERT(... USING ...)` wraps one side, `idx_external_ref` becomes unusable, full-scan of 48M rows. Schema-reader audit misses it. **TARGETED**
- **B2** `WHERE id = '{$orderId}'` — SQL injection + string/int coercion

## Pre-edit simulation
- **B1** missed: no reflex for implicit coercion (type or collation). Composite Index Column-Order covers leading-column rule but not coercion. Schema audit ticks "both columns indexed" and moves on.
- **B2** caught: Security layer 3e catches raw SQL interpolation.

## Proposed edit (trimmed from subagent's +35 to +25)
New Cross-Layer sub-section **"Implicit Coercion Defeating Indexes
(type & collation mismatch)"** inserted between Composite Index
Column-Order and Deep-Offset Pagination.

- **Principle**: indexed column + implicit `CONVERT`/`CAST` wrapping = index unusable (not sargable). Schema-reading audit ticks the box; `EXPLAIN` shows `type: ALL`.
- **Distinct from column-order**: the index IS the leading key_part and there's no range-before-equality problem — coercion alone kills the seek.
- **Three sources**: (1) type mismatch (`WHERE bigint_col = '42'`), (2) collation mismatch on JOIN (common after partial utf8mb4 migration), (3) charset mismatch on literal/connection.
- **Audit reflex**: 2 questions — bound type matches column? JOIN string columns share charset AND collation?
- **Verification**: `EXPLAIN` + `SELECT ... FROM information_schema.COLUMNS WHERE ... IN ((t1,col),(t2,col))` — both rows must match on `CHARACTER_SET_NAME` AND `COLLATION_NAME`.

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all standard SQL + INFORMATION_SCHEMA; `CONVERT`, `CAST`, `EXPLAIN`, `CHARACTER_SET_NAME`, `COLLATION_NAME` are MySQL standard)
- Line count delta: **+25** (subagent proposed +35; main loop dropped the failure-signature paragraph with specific row numbers and the multi-pathway fix paragraph)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +25 (heavy but new general bug category, close neighbor of Composite Index Column-Order)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 1 (B2 via Security layer)
post_caught:                2
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New Implicit Coercion section with JOIN collation reflex
and `information_schema` verification catches B1; Security layer still
catches B2 SQLi."*

**Full 2/2 post-edit. Ninth v4 targeted win.**

## Decision: **edit_verified**

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
29    800    +20    edit_verified      +1            composite-index-order ✓
30    800    0      benchmark_pass     —             fixture-03 3/3
31    784    -16    edit_generalize    —             layout-link tightened
32    809    +25    edit_verified      +1            collation-coercion ✓
```

## Progress after 32 iters
- Verified wins: **9**
- Bugs closed cumulatively via v4 verify: **11**
- Benchmark passes: 3 (iter 10/20/30)
- Regressions: 0

## Final JSON
```json
{"iter":32,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":809,"skill_md_delta":25,"pre_caught":1,"post_caught":2,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
