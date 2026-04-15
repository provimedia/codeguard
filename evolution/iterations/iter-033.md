# Iteration 033 — free mode (v4, tightening)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure dedup)

## Target
The "Hunt-and-Replace" callout (box B) still contained a 5-line
framework-specific "Real bug this prevents" anecdote about a personality
test router.post() bug under MAMP subdir, plus a 2-line paragraph with
framework-specific examples (`/storage/`, `<a href>`, `Route::get`).

## Change
Compressed the 5-line anecdote + 2 lines of framework-specific examples to
one general sentence. The Hunt-and-Replace rule itself remains stated
clearly above this point.

## Framework tokens removed
`router.post()`, `persoenlichkeitstest`, `url()`, `/storage/`, `<a href>`,
`Vue`, `Route::get('/...')`, `MAMP subdir` — **~8 framework tokens stripped**.

## Metrics
```
BEFORE: 809 lines
AFTER:  803 lines
Delta:  -6 lines, ~8 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-6** ✓
- structure intact ✓

## Verify: SKIPPED
Pure deletion; Hunt-and-Replace rule remains stated elsewhere in the box.

## Trend
```
iter  lines  delta  action             verify
29    800    +20    edit_verified      +1  composite index order
30    800    0      benchmark_pass     —   fixture-03 3/3
31    784    -16    edit_generalize    —   layout-link tightened
32    809    +25    edit_verified      +1  collation-coercion
33    803    -6     edit_generalize    —   hunt-and-replace anecdote
5-iter net: +23 (still high — next iter should tighten more)
```

## Final JSON
```json
{"iter":33,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":803,"skill_md_delta":-6,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":8,"edit_kind":"tightening","spec_version":4}
```
