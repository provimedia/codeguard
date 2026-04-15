# Iteration 021 — free mode (v4, clarity fix from iter-20 benchmark)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (clarity extension, no simulation task)

## Motivation
Iter-20 benchmark noted Bug 4 (unbounded `Order::sum('total')`) was borderline
under current P2 framing — P2 was oriented around row-iteration primitives
(get/cursor/lazy/lazyById) and silent on pure aggregate queries at scale.

## Change
P2 Scale Verification section gains a 6-line **"Aggregate trap"** paragraph
inserted after the existing Gotcha (streaming-primitive-overrides-limit) block:

```
**Aggregate trap:** SUM / COUNT / AVG / MAX / MIN look O(1) but scan rows.
Three failure modes on large tables:
(1) no WHERE narrowing — aggregate walks full history every call;
(2) filtered column has no covering index — even narrow WHERE still full-scans;
(3) computed live per request where a denormalized counter or materialized
    rollup would eliminate the query entirely.
Verify with EXPLAIN: index is used AND the row estimate is bounded.
```

## Preserved
- Existing P2 row-count table (< 1k / 1k-100k / 100k+) untouched
- Streaming-primitive gotcha untouched
- Section header "### P2. Scale Verification" untouched

## Metrics
```
BEFORE: 753 lines, P2 silent on aggregates
AFTER:  760 lines, P2 covers 3 aggregate failure modes
Delta:  +7 lines, 0 framework tokens
```

Framework tokens in new_string: SUM / COUNT / AVG / MAX / MIN / WHERE / EXPLAIN
are pure SQL (not framework). "Covering index", "denormalized counter",
"materialized rollup" are DB-generic.

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓ (verified via Grep count = 1)
- generality: 0 framework tokens ✓
- line-count: +7 (acceptable, targets a benchmark-flagged gap)
- structure intact ✓

## Verify: SKIPPED (clarity extension, no simulation task)
iter-30 benchmark will re-run fixture-02 and see whether Bug 4 is now caught
cleanly (pre: borderline, post: expected direct hit via new aggregate paragraph).

## Trend
```
iter  lines  delta  action             verify
18    760    +16    edit_verified      +1 (saga)
19    753    -7     edit_generalize    —
20    753    0      benchmark_pass     4/4 fixture-02
21    760    +7     edit_generalize    — (aggregate ext.)
```

## Final JSON
```json
{"iter":21,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":760,"skill_md_delta":7,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"edit_kind":"clarity_extension_from_benchmark","spec_version":4}
```
