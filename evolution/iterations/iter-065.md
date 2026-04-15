# Iteration 065 — free mode (v4, 24th targeted win, zero-cost)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Bulk-lookup endpoint — IN(...) list plan pathology at HTTP cap

## Task
PHP/Laravel `bulkLookup` validates `ids` array capped at 5000 and binds each
element via placeholder into `WHERE id IN (?,?,...)` on a 40M-row table.
`id` is PK. Per-element binding (not SQLi).

## Bugs planted (1)
- **B1** 5000-element IN(...) crosses MySQL `eq_range_index_dive_limit` (default 200) → planner bails from range to ALL/index scan even though `id` IS the PK leading column. Each distinct arity = new prepared-statement plan-cache entry. **TARGETED**

## Pre-edit simulation
Caught **0/1**. The Input Size table row "Array length" stopped at HTTP-layer
iteration cap (`count($arr) <= N`). Composite Index Column-Order passed
because `id` is the leading PK. Implicit Coercion passed (ints bound as
ints). No reflex connected HTTP-cap to SQL-plan sanity.

## Proposed edit (zero-cost inline extension)
Extended the existing Array length row in the Input Size & Complexity Limits
table IN-PLACE with an "SQL follow-up" clause:

- Names `eq_range_index_dive_limit` (MySQL default 200) as the pathology
  threshold
- Names plan-cache arity explosion (each distinct arity = new plan entry)
- Requires EXPLAIN at the CAP value (not at 3 elements) showing
  `type: range` + `rows ≈ list size`
- Fix: chunk IN list into fixed-size batches (≤500) OR temp/VALUES join

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (pure MySQL planner vocabulary)
- **Line count delta: 0** (inline extension of existing table row — zero-cost)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: **0** (zero-cost new coverage) ✓
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

**Verify notes**: *"Array length row's SQL follow-up clause
(eq_range_index_dive_limit, plan-cache arity, EXPLAIN-at-CAP,
chunk-or-VALUES) fires directly on 5000-element IN against 40M-row PK;
fix prescription matches ground truth."*

**Full 1/1 post-edit. Twenty-fourth v4 targeted win, zero line cost.**

## Decision: **edit_verified**

## Progress after 65 iters
- Verified targeted wins: **24**
- Bugs closed cumulatively via v4 verify: **31**
- Benchmark passes: 6
- Regressions: 0

## Final JSON
```json
{"iter":65,"mode":"free","score":1,"baseline":68,"action":"edit_verified","skill_md_lines":893,"skill_md_delta":0,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost","spec_version":4}
```
