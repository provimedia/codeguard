# Iteration 026 — free mode (v4, dedup)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure deletion/dedup)

## Target
The "### v4 Verification Rules (born from real bugs that escaped the audit)"
section at the tail of SKILL.md had 6 bullets. Each duplicated content
already covered in depth earlier:
- "VERIFICATION beats ASSERTION" → Audit phase callout line 318
- "Dump the JSON" → box A lines 326-346 (with `Inertia`, `Playwright`, `paginate()->toArray()` framework tokens)
- "Hunt-and-replace" → box B lines 354-370
- "Layout-link → Route-existence" → box C lines 377-405 (with `TopNav`, `MobileTabBar`, `AdminLayout`, `<Link href>`)
- "Eloquent Accessors need `$appends`" → Cross-Layer Data Contracts lines 594-608 (with `Eloquent`, `$appends`, `getXxxAttribute`, `->map()`, `Vue`)
- "Forbidden Phrase List" → audit phrases lines 461-465

This is the same dedup pattern iter-24 applied to the adjacent "v5 Plan-Time
Rules" section (which also had 9 bullets → 2).

## Change
Collapsed 8 lines (heading + 6 recap bullets + blank) to 3 lines (heading + 1
pointer). The pointer explicitly names the 6 covered reflexes so grep still
finds them.

## Framework tokens removed
`Inertia`, `Playwright`, `Vue`, `Eloquent`, `TopNav`, `MobileTabBar`,
`AdminLayout`, `<Link href>`, `paginate()->toArray()`, `->map()`,
`getXxxAttribute`, `$appends` — **~12 framework tokens stripped** in one
deletion.

## Metrics
```
BEFORE: 787 lines
AFTER:  782 lines
Delta:  -5 lines, ~12 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-5** (target ≥5 met) ✓
- structure intact ✓

## Verify: SKIPPED (pure deletion — content remains in-depth above)

## Trend
```
iter  lines  delta  action
23    779    +17    edit_verified    +2  deep offset
24    772    -7     edit_generalize  —   v5 recap dedup
25    787    +15    edit_verified    +1  auth parity
26    782    -5     edit_generalize  —   v4 recap dedup
4-iter net: +20 lines, 3 verify wins, 2 dedup passes
```

## Pattern noted
After iter-24 (v5 recap dedup, -7) and iter-26 (v4 recap dedup, -5), the
two "rules recap" sections at the tail of SKILL.md have been consolidated
to pointers. Any future "v6/v7 Rules" section should use the same
non-duplication pattern from day one.

## Final JSON
```json
{"iter":26,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":782,"skill_md_delta":-5,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":12,"edit_kind":"dedup_recap","spec_version":4}
```
