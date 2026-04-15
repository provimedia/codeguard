# Iteration 038 — free mode (v4, tightening)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure tightening)

## Target
Cross-Layer Data Contracts "Producer → Consumer mismatches" section had 5
bullets with heavy framework-specific examples (`Eloquent accessor`,
`$appends`, `paginate()->toArray()`, `Vue receives key: undefined`, `Vue
calls router.post()`, `MAMP subdir`, `flash`, `->with('success', ...)`)
plus a redundant trailing "Derived-property exposure check" paragraph
that said the same thing as one of the bullets.

## Change
16 lines → 11 lines. Kept:
- The "Producer → Consumer mismatches" framing
- 3 generalized bullets: (1) key rename, (2) computed-property not opted
  into serializer, (3) hardcoded path bypassing base-URL helper in
  subdirectory/reverse-proxy installs
- The 3-step "How to check" instruction
- The #1-source-of-silent-bugs takeaway

Dropped:
- Service→Controller renaming example (repetitive with bullet 1)
- Flash/→with example (Laravel-specific)
- Eloquent accessor bullet (duplicated by bullet 2 + the Derived-property
  paragraph, which itself is now dropped and merged into bullet 2)
- Vue/MAMP/router.post subdirectory example (kept the lesson, dropped
  framework-specific detail)
- Redundant trailing "Derived-property exposure check" paragraph

## Framework tokens removed
`Eloquent`, `$appends`, `paginate()`, `Vue` (×3), `router.post`, `MAMP`,
`->with('success', ...)`, `data-page`, `href="/undefined"`, `flash`,
`@property` — **~11 framework tokens stripped**.

## Metrics
```
BEFORE: 820 lines
AFTER:  815 lines
Delta:  -5 lines, ~11 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-5** (target met) ✓
- structure intact ✓

## Verify: SKIPPED
Pure tightening. The 3 planted-bug patterns remain covered by the 3
generalized bullets, and the data-dumping reflex is reinforced by
iter-34's v4 Box A generalization. iter-40 benchmark will confirm no
regression on fixture-01 (which targets exactly this reflex).

## Trend
```
iter  lines  delta  action             verify_delta
35    811    +27    edit_verified      +1  session lifecycle
36    799    -12    edit_generalize    —
37    820    +21    edit_verified      +3  backfill (triple hit)
38    815    -5     edit_generalize    —
4-iter net: +31 lines, 2 verify wins (4 bugs)
```

## Final JSON
```json
{"iter":38,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":815,"skill_md_delta":-5,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":11,"edit_kind":"tightening","spec_version":4}
```
