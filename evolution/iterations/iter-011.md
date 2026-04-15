# Iteration 011 — free mode (v3, optimization)

**Agent**: general-purpose, model: opus
**Target**: tighten iter-1's N+1 external HTTP bullet — drop `Http::pool()` Laravel token

## Change
SKILL.md `### N+1 Query Detection` section, bullet for external HTTP/RPC in loops:

```diff
-- External HTTP/RPC call inside a row loop — require a bulk endpoint, `Http::pool()`, or justify per-row cost against the row count
+- External HTTP/RPC call inside a row loop — require a bulk endpoint, a parallel-request primitive (concurrent fan-out), or justify per-row cost against the row count
```

## Metrics
```
BEFORE: 1 framework token (`Http::pool()`)
AFTER:  0 framework tokens
Line count: 734 → 734 (flat — principle preserved, cruft removed)
```

## Principle preserved
Auditor reviewing `foreach ($rows as $r) { httpClient->get(...) }` still gets
three fix paths: bulk endpoint, parallel-request primitive, or per-row cost
justification. Wording is now stack-agnostic — applies to Guzzle pools, Go
goroutines, Node Promise.all, Python asyncio.gather, Java CompletableFuture,
anything.

## Gate check (v3)
- edit != null ✓
- old_string unique ✓ (Grep count = 1)
- framework-token scan on new_string: **0 hits** ✓
- line count delta: 0 (flat, acceptable)
- post-edit structure: frontmatter + PLAN MODE marker present ✓

## Final JSON
```json
{"iter":11,"mode":"free","score":0,"baseline":11,"action":"edit","skill_md_lines":734,"skill_md_delta":0,"framework_tokens_in_edit":0,"edit_kind":"generalization_tightening"}
```
