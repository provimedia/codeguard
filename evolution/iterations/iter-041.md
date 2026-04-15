# Iteration 041 — free mode (v4, tightening)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure tightening)

## Target
**P4 "config:cache Safety"** section — heaviest remaining Laravel-specific
block in PLAN MODE. 18 lines with `env()`, `config('namespace.key')`,
`php artisan config:cache`, `config/services.php`, `GEMINI_API_KEY`, plus
a PHP code block showing FORBIDDEN/REQUIRED patterns.

## Change
Renamed **"P4. config:cache Safety"** → **"P4. Cached-Config Safety"**
(generalized from Laravel terminology to "runtimes that pre-compile config
at boot"). 18 lines → 8 lines. Kept the core reflex ("every plan that
introduces a new env var MUST route access through the project's config
layer, not a raw env read at the call site; verification: grep the
pseudocode for direct env reads outside config files").

## Framework tokens removed
`env()`, `config('namespace.key')`, `config()`, `php artisan config:cache`,
`config/services.php`, `GEMINI_API_KEY`, `$key`, `->` — **~7 framework
tokens stripped**.

## Metrics
```
BEFORE: 846 lines
AFTER:  836 lines
Delta:  -10 lines, ~7 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-10** (exceeds target) ✓
- structure intact ✓

## Verify: SKIPPED
Pure tightening. P4 reflex (env-vars must go through config layer, not
direct call-site reads) is preserved. Iter-50 benchmark will re-run
fixture-01 which targets this exact P4 reflex and will confirm no
regression.

## Trend
```
iter  lines  delta  action             verify
37    820    +21    edit_verified      +3  backfill (triple hit)
38    815    -5     edit_generalize    —
39    846    +31    edit_verified      +1  error-path cleanup
40    846    0      benchmark_pass     —   fixture-01 re-run 5/5
41    836    -10    edit_generalize    —   P4 cached-config generalized
5-iter net: +16 lines (moderate)
```

## Final JSON
```json
{"iter":41,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":836,"skill_md_delta":-10,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":7,"edit_kind":"tightening","spec_version":4}
```
