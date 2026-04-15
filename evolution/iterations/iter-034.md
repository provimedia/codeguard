# Iteration 034 — free mode (v4, heavy tightening)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure dedup/generalization)

## Target
The "v4 VERIFICATION Box A — JSON Inspection over Code Reading" callout at
lines 326-351 (26 lines) contained:
- Laravel/Vue/Inertia intro prose (`Eloquent accessors`, `$appends`, `when()` props)
- A 12-line bash block with three framework-specific commands (Inertia
  `data-page=` scrape via curl + python; Playwright `page.locator` query;
  `php artisan tinker --execute=\App\Models\X::paginate(3)->toArray()`)
- A 4-line "Real bug this prevents" anecdote about `getLocalPathAttribute()`
  + `$appends` + Vue `defineProps` + 1,142 undefined article links

The reflex itself ("dump the actual serialized response, don't just read code")
is framework-agnostic. All the framework-specific scaffolding was decoration.

## Change
26 lines → 7 lines. Kept the generic reflex in a single concise paragraph
("dump the real serialized response the consumer will receive — HTTP fetch,
REPL, or a browser assertion that no rendered link contains `undefined`").
Dropped all framework-specific shell commands AND the war-story anecdote
(the same reflex is reinforced by the "Derived-property exposure check" at
Cross-Layer Data Contracts, iter-28).

## Framework tokens removed
`Eloquent`, `Vue`, `Inertia`, `$appends`, `when()`, `curl`, `python3`,
`Playwright`, `page.locator`, `tinker`, `php artisan`,
`\App\Models\X::paginate(3)->toArray()`, `data-page`, `defineProps`,
`getLocalPathAttribute`, `paginate()`, `->toArray()`, `/undefined` narrative
— **~17 framework tokens stripped** in one edit.

## Metrics
```
BEFORE: 803 lines
AFTER:  784 lines
Delta:  -19 lines, ~17 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-19** (new strongest single-tightening) ✓
- structure intact ✓

## Verify: SKIPPED
Pure deletion/generalization; reflex is reinforced elsewhere in the skill
(Cross-Layer Data Contracts derived-property exposure check from iter-28).
iter-40 benchmark will confirm no regression.

## Trend
```
iter  lines  delta  action             verify
29    800    +20    edit_verified      +1  composite index order
30    800    0      benchmark_pass     —   fixture-03 3/3
31    784    -16    edit_generalize    —   layout-link tightened
32    809    +25    edit_verified      +1  collation-coercion
33    803    -6     edit_generalize    —   hunt-replace anecdote
34    784    -19    edit_generalize    —   box A triple-dup removed
6-iter net: +4 lines (very balanced — 2 verify wins + 4 tightening iters)
```

## Progress after 34 iters
- Verified wins: 9
- Bugs closed cumulatively: 11
- Benchmark passes: 3
- Framework tokens cumulatively stripped: ~95+
- SKILL.md: 715 → 784 (+69 net despite 9 new coverage categories)

## Final JSON
```json
{"iter":34,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":784,"skill_md_delta":-19,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":17,"edit_kind":"heavy_tightening","spec_version":4}
```
