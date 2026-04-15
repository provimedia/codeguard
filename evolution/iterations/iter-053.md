# Iteration 053 — free mode (v4, tightening with stale-fact fix)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure dedup)

## Target
Intro paragraph between the `# Code Guardian` header and `## Mode Selection`:

```
One skill. Two modes. Zero exceptions.

Born from real bug data: across six development phases, 5 bugs slipped past
audits that "looked correct". Every iteration of this skill is a tightening of
the verification reflex — never assert, always verify against command output.
```

## Two problems
1. **Stale claim**: "Two modes" is now wrong — the skill has THREE modes
   (PLAN MODE + BUILD MODE + DEBUG MODE). Iterations accumulated since the
   intro was written and the fact went stale.
2. **Non-actionable narrative**: the "Born from real bug data..." paragraph
   is backstory, not a reflex. VNA and zero-exceptions are restated verbatim
   in the Rules section ("No exception. No 'it's just a small change'") and
   in the v4 callout that anchors the entire Audit phase.

## Change
Header jumps straight to Mode Selection. 9 lines → 3 lines.

## Metrics
```
BEFORE: 878 lines
AFTER:  872 lines
Delta:  -6 lines
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-6** ✓
- structure intact ✓

## Verify: SKIPPED
Pure deletion of narrative. VNA and zero-exceptions are reinforced in
the Rules section (line ~863 "No exception. No 'it's just a small change'")
and in the v4 callout that anchors the Audit phase. iter-60 benchmark
re-run of fixture-03 will confirm no regression.

## Trend
```
iter  lines  delta  action            verify
48    851    -4     edit_generalize    —
49    866    +15    edit_verified      +2  single-use resource
50    866    0      benchmark_pass     —   halfway fixture-02 4/4
51    862    -4     edit_generalize    —   Interface Boundary collapse
52    878    +16    edit_verified      +1  open redirect
53    872    -6     edit_generalize    —   intro dropped + stale mode count fixed
6-iter net: +17 lines, 2 verify wins (3 bugs closed), stale fact cleaned
```

## Final JSON
```json
{"iter":53,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":872,"skill_md_delta":-6,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":0,"edit_kind":"dedup_stale_fact","spec_version":4}
```
