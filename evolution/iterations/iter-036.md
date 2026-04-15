# Iteration 036 — free mode (v4, tightening)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure tightening)

## Target
The **P1 Cross-Layer Trace** section at lines 53-89 was the densest
framework-token block still remaining in PLAN MODE: `$fillable` (×3),
`$hidden`, `$appends`, `Inertia` (×2), `Vue` (×2), `->only(`, `->toArray()`,
`v-if`, `Inertia::render`, `app/Http/Controllers`, plus a 7-step
Laravel/Vue-specific data flow diagram and a bash grep command with
framework paths.

## Change
37 lines → 25 lines. Kept:
- The core teaching ("model-layer allowlist does NOT guarantee client delivery; always grep the serializer, not the model")
- A 5-step data flow diagram (framework-agnostic: DB column → model allowlist → serializer → transport payload → client template)
- The plan-time verification instruction

Dropped:
- Laravel-specific data flow nodes (`$fillable`, `$hidden/$appends`, `Inertia/JSON payload`, `Vue prop`, `v-if/interpolation`)
- Bash grep command with Laravel paths
- Redundant "Lesson:" paragraph (merged into principle statement at top)

## Framework tokens removed
`$fillable` (×3), `$hidden`, `$appends`, `Inertia` (×2), `Vue` (×2), `->only(`,
`->toArray()`, `v-if`, `Inertia::render`, `app/Http/Controllers`,
`product.field_name` — **~13 framework tokens stripped**.

## Metrics
```
BEFORE: 811 lines
AFTER:  799 lines
Delta:  -12 lines, ~13 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-12** ✓
- structure intact ✓

## Verify: SKIPPED
Pure tightening/generalization. The reflex ("grep the serializer, not the
model") is preserved in the compressed version. iter-40 benchmark will
re-run fixture-01 to confirm no regression on the canonical cross-layer
scenario (fixture-01 targets exactly this reflex).

## Trend
```
iter  lines  delta  action             verify
33    803    -6     edit_generalize    —
34    784    -19    edit_generalize    —
35    811    +27    edit_verified      +1  session lifecycle
36    799    -12    edit_generalize    —
4-iter net: -10 (excellent balance)
```

## Final JSON
```json
{"iter":36,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":799,"skill_md_delta":-12,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":13,"edit_kind":"tightening","spec_version":4}
```
