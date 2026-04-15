# Iteration 028 — free mode (v4, heavy dedup)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure dedup)

## Target
The **"Eloquent Accessor Trap"** sub-section under Cross-Layer Data Contracts
(lines 594-608). The subagent identified that this Laravel-specific 15-line
example + code block was **triple-covered**:
1. A bullet in "Producer → Consumer mismatches" higher in the same section
2. A "Real bug this prevents" callout at lines 346-351
3. This explicit sub-section

Pure duplication plus heavy Laravel/Vue token density.

## Change
Replaced the 15-line sub-section with a 2-line generalized "Derived-property
exposure check":

```
**Derived-property exposure check:** any time a serializer (toArray/toJSON/marshal)
walks a model whose consumer reads a property that is COMPUTED (accessor, virtual
attribute, getter, lazy/@property field), verify the serializer opts-in to
computed output — otherwise the property is silently absent from the payload
and the consumer reads undefined.
```

## Framework tokens removed
`Eloquent`, `getLocalPathAttribute`, `$appends`, `paginate()`, `Vue`,
`->toArray()`, `->map()`, `->get()` — **~7-8 framework tokens stripped**.

## Preserved
The actual reflex ("computed properties are absent from serialized output
unless opted-in") is kept in the 2-line generalized version. Upper bullet
and "Real bug this prevents" callout at 346-351 remain as the other two
coverage points.

## Metrics
```
BEFORE: 794 lines
AFTER:  780 lines
Delta:  -14 lines, ~7 framework tokens removed
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-14** (strongest single-edit shrink so far) ✓
- structure intact ✓

## Verify: SKIPPED
Pure deletion/generalization. The concept is preserved by the generalized
line plus the two other mentions of the same reflex elsewhere in the skill.
iter-30 benchmark will re-run fixture-02 to confirm no regression.

## Trend
```
iter  lines  delta  action
25    787    +15    edit_verified      +1  auth parity
26    782    -5     edit_generalize    —   v4 recap dedup
27    794    +12    edit_verified      +2  NULL aggr + LEFT JOIN
28    780    -14    edit_generalize    —   eloquent accessor triple-dup
4-iter net: +8 lines (much better than the +27 trend we had at iter-23)
```

## Final JSON
```json
{"iter":28,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":780,"skill_md_delta":-14,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":7,"edit_kind":"heavy_dedup","spec_version":4}
```
