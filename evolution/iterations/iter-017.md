# Iteration 017 — free mode (v4, tightening — manual correction)

**Attack agent**: general-purpose, model: opus (proposed wrong target)
**Verify agent**: SKIPPED (pure tightening)
**Main loop**: manual correction — identified real target and applied directly

## Subagent error
The attack subagent proposed tightening the P2 "Real bug from this session"
anecdote at lines 115-117. But that anecdote is ALREADY tight (it was
compressed in a prior state I can't pinpoint — possibly was already like this
at start). The real Laravel-heavy P2 content was the **"Critical Laravel
gotcha"** paragraph + PHP code block at lines 102-113 (not the "Real bug"
block). Main loop caught this and applied a corrected edit directly.

## Corrected edit (applied by main loop, not subagent)

```diff
-**Critical Laravel gotcha:** `->lazy($size)` internally uses `forPage()` which
-**OVERRIDES** any user-supplied `->limit()`. If the plan needs both a `limit()`
-clause AND streaming, use `->cursor()`. `->lazy()` only works when there's no
-limit (or the limit is the chunk size itself).
-
-```php
-// BROKEN — limit(2) is silently ignored, processes ALL matching rows
-ShopProduct::whereNull('x')->limit(2)->lazy(500);
-
-// CORRECT — cursor() respects all preceding constraints in a single SQL query
-ShopProduct::whereNull('x')->limit(2)->cursor();
-```
-
-**Real bug:** a streaming iteration primitive silently overrode the caller's
-row limit, processing 150+ rows instead of 2. Verify actual rows processed,
-not the name of the primitive you picked.
+**Gotcha:** some streaming primitives silently override upstream row limits
+(internal pagination re-drives the query and ignores an earlier `LIMIT` / take).
+If the plan needs BOTH streaming AND a hard cap, either pick a primitive that
+respects both OR apply the cap server-side — and verify the actual row count
+processed, not the primitive name you picked.
```

Note: the "Real bug" 3-line tail was folded into the gotcha (redundant after
compression — both said the same thing).

## Metrics
```
BEFORE: 755 lines, ~8 framework tokens in this block
        (Laravel, ->lazy($size), forPage(), ->limit(), ->cursor(),
         ShopProduct::whereNull, limit(2), lazy(500), cursor())
AFTER:  744 lines, 0 framework tokens in this block
Delta:  -11 lines, -8 framework tokens
```

## Gate checks (v4)
- edit != null ✓
- old_string found exactly once ✓ (14 lines verbatim, unique)
- generality: 0 framework tokens ✓
- line-count: **-11** (negative = good) ✓
- structure intact ✓

## Verify: SKIPPED (pure tightening, no attack sim task)

## Trend
```
iter  lines  delta  action
13    726    0      edit_verified
14    738    +12    edit_verified
15    736    -2     edit_generalize
16    755    +19    edit_generalize
17    744    -11    edit_generalize
Last 5 net: +18 → much better than before's +29
```

## Final JSON
```json
{"iter":17,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":744,"skill_md_delta":-11,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"edit_kind":"tightening_manual_correction","spec_version":4}
```

## Note on subagent reliability
This is the first iter where the subagent proposed a wrong target (stale
mental model of the file state). Main loop caught it by verifying the
old_string didn't match and re-inspecting the section. Future iters should
continue to Grep/Read before trusting a proposed old_string's context.
