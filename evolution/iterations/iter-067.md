# Iteration 067 — free mode (v4, tightening)

**Attack agent**: general-purpose, model: opus
**Verify**: SKIPPED (pure dedup)

## Target
P6 had two paragraphs ("Why plan-time, not audit-time" + "Lesson") that
duplicated each other — both explained the dispatch-lock-in and the
`git add <path>` sweep-in consequence.

## Change
9 lines → 1 paragraph (merged). Preserved: dispatch lock-in timing,
sweep-in mechanic, `git add -p` fix, history rewriting cost,
"fix the briefing template" principle.

## Metrics
```
BEFORE: 909 lines
AFTER:  901 lines
Delta:  -8 lines
```

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens in new_string ✓
- line-count: **-8** ✓
- structure intact ✓

## Final JSON
```json
{"iter":67,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":901,"skill_md_delta":-8,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"framework_tokens_removed_in_edit":0,"edit_kind":"dedup","spec_version":4}
```
