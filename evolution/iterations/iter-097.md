# Iteration 097 — free mode (v4, 45th targeted win, zero-cost inline, DOUBLE delta +2)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Random Featured Post + related widgets + rediscover email

## Task
PHP + MySQL content site. `posts` ~4M rows. `FeaturedWidget::pickOne`,
`RelatedPostsWidget::forPost`, `RediscoverEmailJob::handle` all use
`ORDER BY RAND()` on filtered sets. `HomeController::index` does
`LEFT JOIN post_views GROUP BY` on full table per request.

## Bugs planted (3)
- **B1** `FeaturedWidget` `ORDER BY RAND()` over 120k featured rows — filesort every homepage hit. **TARGETED**
- **B2** `RediscoverEmailJob` `ORDER BY RAND()` over millions of evergreen rows, per user, nightly.
- **B3** `HomeController::index` full-table LEFT JOIN COUNT GROUP BY per request.

## Pre-edit simulation
Caught **1/3** (B3 via P2 aggregate trap). Missed B1 and B2 — Efficiency
line listed loops-to-query, sequential awaits, SELECT-in-loop, missing
pagination, but never named `ORDER BY RAND()` as the canonical
full-scan-sort anti-pattern.

## Proposed edit (inline, 0 line delta, double delta)
Extended the Efficiency bullet inline with an ORDER BY RAND() reflex:

**"`ORDER BY RAND()` over any filtered set larger than a few hundred
rows — MySQL assigns RAND() per row then filesorts the WHOLE filtered
set to return LIMIT k, so cost is O(filtered rows) regardless of LIMIT
and indexes on the WHERE are irrelevant to the sort; fix by sampling on
an indexed id (`WHERE id >= FLOOR(RAND()*max_id) ... LIMIT k`),
precomputing a shuffled pool, or picking k random ids first and then
fetching by PK."**

- Topically correct ✓ (Efficiency already owns pagination and SELECT-in-loop anti-patterns)
- `targeted_miss: "B1"`
- Framework tokens: **0**
- Line count delta: **0** (inline extension within existing bullet)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("Loops replaceable by single query" matched once) ✓
- generality: 0 framework tokens ✓
- line-count: **0** (zero-cost inline) ✓
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 1
post_caught:                3
delta:                      +2   ← double delta
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"Efficiency bullet now names ORDER BY RAND()
explicitly with O(filtered rows) cost model; grep for the literal string
hits B1/B2 directly, HomeController aggregate scan caught via P2+Efficiency."*

**Forty-fifth v4 targeted win. Seventeenth zero-cost inline win. DOUBLE
delta (+2) — one reflex closed two bugs in the same diff.**

## Decision: **edit_verified**

## Progress after 97 iters
- Verified targeted wins: **45**
- Bugs closed cumulatively via v4 verify: **55**
- Benchmark passes: 9
- Regressions: 0
- Zero-cost inline wins: **17**
- Double-delta wins: iter-66, 37, 45, 85, 97 (many)
- Deferred gaps closed: 8-for-8
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":97,"mode":"free","score":55,"baseline":68,"action":"edit_verified","skill_md_lines":902,"skill_md_delta":0,"pre_caught":1,"post_caught":3,"verify_delta":2,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_double_delta","spec_version":4}
```
