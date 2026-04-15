# Iteration 015 — free mode (v4, pure tightening)

**Attack agent**: general-purpose, model: opus
**Verify agent**: SKIPPED (no simulation task — pure generalization edit)
**Kind**: tightening / generalization

## Rationale
Last two iters added content (+12 net for iter-14). Spec v3 "optimization bias"
calls for tightening edits to keep line-count trend honest. Target: PLAN MODE
P1 "Real bug from this session" anecdote — 6 lines including the framework
token `Vue`.

## Change
P1 section, "Real bug from this session" anecdote:

```diff
-**Real bug from this session:** Plan said "ShopController needs no change because
-description_helpful is in $fillable". `ShopController@show` actually built an
-explicit `['id' => ..., 'name' => ..., ...]` array. Without the controller fix,
-Vue would receive `product.description_helpful === undefined` and the v-if would
-never fire → dead feature in production. Caught by implementer's pre-commit
-audit, not by the plan.
+**Lesson:** A model-layer allowlist (e.g. mass-assignment fillable) does NOT
+guarantee client delivery — if the controller serializes via an explicit key
+whitelist, any field absent from that whitelist is dropped silently and the
+client-side conditional never fires. Always grep the controller, not the model.
```

## Preserved
- Core teaching: model-layer allowlist ≠ client delivery
- Controller-whitelist trap
- Audit reflex: grep the controller, not the model

## Removed
- `Vue` framework token (1)
- `ShopController@show` / `description_helpful` session-specific narrative
- `v-if` framework-specific phrasing

## Metrics
```
BEFORE: 738 lines, anecdote framework tokens: 1 (Vue)
AFTER:  736 lines, anecdote framework tokens: 0
Delta:  -2 lines, -1 framework token
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-2** (negative = good under v3) ✓
- structure intact ✓

## Verify: SKIPPED
Pure tightening edit with no attack simulation task. Nothing to re-run. The
iter-20 benchmark (fixture-01 again) will detect any regression if the
compression dropped something important. Action under v4: `edit_generalize`.

## Scope note
P2/P5/P6 anecdotes left intact for future iterations. ONE compression per iter
to keep diffs small and trackable.

## Final JSON
```json
{"iter":15,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":736,"skill_md_delta":-2,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"edit_kind":"tightening","spec_version":4}
```
