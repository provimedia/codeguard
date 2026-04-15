# Iteration 024 — free mode (v4, heavy dedup)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure deletion/dedup, no simulation task)

## Target
The "### v5 Plan-Time Rules" section at the tail of SKILL.md contained 9
bullets. 7 of those paraphrased P1-P6 section content already present ~80
lines above in PLAN MODE. Pure duplication + framework-token accumulation.

## Change
Collapsed the section from 9 bullets → 2. Kept:
- **PLAN MODE is not optional when a spec/plan exists** (meta-rule, not a duplicate)
- **Fix prescriptions themselves need review** (meta-rule)

Removed 7 duplicated bullets:
- Cross-Layer `$fillable` / `Inertia::render` restatement (P1)
- `->get()` OOM hazard restatement (P2)
- `->lazy($n)` overrides `->limit($n)` Laravel gotcha restatement (P2)
- API keys in URLs restatement (P3)
- `env()` outside config restatement (P4)
- Pattern-copying restatement (P5)
- `git add -p` hunk-staging restatement (P6)

## Framework tokens removed in this single edit
`$fillable`, `Inertia::render`, `->get()`, `->lazy($n)`, `->limit($n)`,
`->cursor()`, `->lazy(500)`, `cursor()`, `config('services.x.key')`,
`config/services.php`, `env()`, `config:cache`, `Laravel`, `ExistingFile.php`,
`git add <file>`, `git add -p` — **~16 framework tokens stripped** in one
edit while removing duplication.

## Metrics
```
BEFORE: 779 lines
AFTER:  772 lines
Delta:  -7 lines, ~16 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string (meta-rules only) ✓
- line-count: **-7** (shrink ≥5 target met) ✓
- structure intact ✓

## Verify: SKIPPED
Pure deletion — the removed content was restatement of P1-P6 which remains
intact in PLAN MODE above. No simulation task. iter-30 benchmark will
re-verify fixture-02 and iter-40 fixture-03 to catch any accidental loss.

## Trend
```
iter  lines  delta  action             verify
22    762    +2     edit_verified      +1 (FOR UPDATE)
23    779    +17    edit_verified      +2 (deep offset + page cap)
24    772    -7     edit_generalize    — (v5 rules section dedup)
```

## Final JSON
```json
{"iter":24,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":772,"skill_md_delta":-7,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"edit_kind":"heavy_dedup","spec_version":4}
```
