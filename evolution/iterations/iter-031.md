# Iteration 031 — free mode (v4, heavy tightening)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure tightening)

## Target
The "Layout-Link → Route Existence Check" callout (box C at lines 377-405)
was 29 lines of Laravel/Vue/Inertia-specific war-story narrative + shell
commands with framework-specific paths:
- `TopNav`, `Footer`, `AdminLayout`, `MobileTabBar`
- `<Link href>`, `<a href>`, `.vue` files
- `resources/js/Layouts/*.vue`, `resources/js/Components/{TopNav,MobileTabBar}.vue`
- `php artisan route:list`
- `Route::get('/matches')`, `/matches/{id}/annehmen`, `/matches/{id}/ablehnen`
- `Inertia` reference
- `node tests/e2e/link-click-test.mjs`

## Change
29 lines → 13 lines. Kept the core reflex (every internal href must resolve
to a registered route; structural key-match alone doesn't catch wrong-verb/
typo/moved routes; extract hrefs → list routes → diff). Dropped the war
story, the specific grep commands with framework paths, and the e2e test
script filename. Generalized to "headless browser walks every nav" wording.

## Framework tokens removed
`TopNav`, `Footer`, `AdminLayout`, `MobileTabBar`, `<Link href>`, `<a href>`,
`resources/js/Layouts`, `resources/js/Components`, `php artisan route:list`,
`Route::get('/matches')`, `/matches/{id}/annehmen`, `/matches/{id}/ablehnen`,
`Inertia`, `.vue`, `link-click-test.mjs` — **~15 framework tokens stripped**
in one edit.

## Metrics
```
BEFORE: 800 lines
AFTER:  784 lines
Delta:  -16 lines, ~15 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-16** (strongest single tightening yet, tied with iter-28's -14) ✓
- structure intact ✓

## Verify: SKIPPED
Pure tightening/generalization; the reflex ("layout-link → route existence")
is preserved by the 3-step verification procedure. iter-40 benchmark will
confirm no regression on the next fixture-01 run.

## Trend
```
iter  lines  delta  action
27    794    +12    edit_verified      +2  NULL aggr + LEFT JOIN
28    780    -14    edit_generalize    —   eloquent accessor triple-dup
29    800    +20    edit_verified      +1  composite index order
30    800    0      benchmark_pass     —   fixture-03 3/3
31    784    -16    edit_generalize    —   layout-link callout tightened
5-iter net: +2 lines (much better balance)
```

## Progress summary (iters 1-31)
```
Verified targeted wins:  8  (iters 13, 14, 18, 22, 23, 25, 27, 29)
Bugs closed via verify: 10  (money-FLOAT, timezone, saga, FOR-UPDATE-autocommit,
                              deep-offset + page-cap, auth-parity, NULL-aggr +
                              LEFT-JOIN, composite-index-order)
Benchmark passes:        3  (iters 10, 20, 30 — one per fixture)
Regressions:             0
Framework tokens stripped (cumulative): ~60+ across tightening iters
SKILL.md:                715 → 784 (+69 net across 31 iters, despite 8 new
                         general-purpose bug-class coverages)
```

## Final JSON
```json
{"iter":31,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":784,"skill_md_delta":-16,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":15,"edit_kind":"heavy_tightening","spec_version":4}
```
