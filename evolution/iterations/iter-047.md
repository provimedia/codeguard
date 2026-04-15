# Iteration 047 — free mode (v4, sixteenth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Profile update — silent VARCHAR truncation under non-strict sql_mode

## Task (PHP/PDO/MySQL, MAMP non-strict)
`updateProfile` binds `display_name` (VARCHAR(50), no cap) and `bio`
(VARCHAR(500), frontend JS-caps at 2000). `sql_mode=''`. Both inputs
silently truncate.

## Bugs planted (1)
- **B1** Silent VARCHAR truncation under non-strict sql_mode. Server returns success, `rowCount()==1`, stored value is cut. **TARGETED**

## Pre-edit simulation
Caught **0/1**. Input Size table had 7 dimensions (raw bytes, array
length, nested depth, decompression ratio, regex input size, page size,
pixel area) but **no "string length" row**. DB Integrity named
money-as-FLOAT and counter overflow but not string-width vs input length.

## Proposed edit
Added one new row to the Input Size & Complexity Limits table (after
Pixel area):

```
| String length | Any text field persisted to a sized column
                  (VARCHAR(N), CHAR(N), TINYTEXT) |
  PHP-side mb_strlen($s) <= N BEFORE the INSERT/UPDATE. Under non-strict
  sql_mode MySQL SILENTLY truncates oversize strings — statement returns
  success, rowCount()==1, stored value is cut. Verify: SELECT @@sql_mode
  AND information_schema.COLUMNS.CHARACTER_MAXIMUM_LENGTH. Under utf8mb4,
  CHARACTER_MAXIMUM_LENGTH is in characters but a 4-byte emoji still
  counts as 1 — use mb_strlen with the right encoding. |
```

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all SQL standard + PHP stdlib `mb_strlen`)
- Line count delta: **+1** (single new table row)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +1 (near-zero-cost coverage) ✓
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 0
post_caught:                1
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New String length row in Input Size table explicitly
names VARCHAR + non-strict sql_mode silent truncation and mandates
`mb_strlen` cap; both `display_name(50)` and `bio(500)` fire."*

**Full 1/1 post-edit. Sixteenth v4 targeted win.**

## Decision: **edit_verified**

## Progress after 47 iters
- Verified targeted wins: **16**
- Bugs closed cumulatively via v4 verify: **22**
- Benchmark passes: 4
- Regressions: 0

## Final JSON
```json
{"iter":47,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":855,"skill_md_delta":1,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_near_zero_cost","spec_version":4}
```
