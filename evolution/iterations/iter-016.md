# Iteration 016 — free mode (v4, new-gap coverage)

**Attack agent**: general-purpose, model: opus
**Verify agent**: SKIPPED (exploratory generalization — no simulation task)
**Kind**: new general gap coverage

## New sub-section: **"Input Size & Complexity Limits (DoS budget)"**
Inserted in Cross-Layer Checks between Queue/Task Idempotency and
Timezone/Date-Boundary Sanity.

## Coverage
Names three dimensions (**bytes**, **cardinality**, **complexity**) that every
untrusted input needs explicit caps on, BEFORE code allocates memory/CPU
proportional to it. 7-row dimension table:

| Dimension | Vector | Cap |
|---|---|---|
| Raw bytes | JSON body / multipart upload / webhook | Web-server body limit + per-route override |
| Array length | Bulk-create / ID lists | `count($arr) <= N` before iteration |
| Nested depth | User JSON/YAML/XML | Explicit `$depth` on decode |
| Decompression ratio | gzip/zip upload | Stream-decode + max output bytes (zip bomb) |
| Regex input size | Server-side text validation | Length cap before regex; reject nested quantifiers (catastrophic backtracking) |
| Page size | `?per_page=` / `?limit=` | Server clamp to hard max; never trust client |
| Pixel area | Image upload / thumbnail | Reject `width*height > N` BEFORE decode (image bomb) |

**Two silent failure modes** documented:
1. **OOM at p99.9** — cap passes p50 tests, stack trace at p99.9 points at the
   allocator, not the missing cap
2. **CPU lock via catastrophic regex backtracking** — worker hangs for minutes,
   no error, no log, queue stops draining

**Verification contract**: for each new input-accepting endpoint, produce
command output showing behavior at 2x the documented cap — expect 413/422,
NOT 500/OOM/hang.

## Rationale
Input-size/DoS was a systemic bug class absent from the skill despite being
textbook. Same shape as adjacent existing reflexes (cache invalidation, TOCTOU,
queue idempotency, timezone) — a per-dimension reflex that names the cap out
loud with verified command output as the gate.

## Metrics
```
BEFORE: 736 lines, 0 DoS coverage
AFTER:  755 lines, 7-dimension DoS coverage table
Delta:  +19 lines
Framework tokens introduced: 0 (PHP stdlib + HTTP-status + generic)
```

## Trend over last 4 iters
```
iter  lines  delta
13    726    0      edit_verified    (money-as-FLOAT, +1 verify)
14    738    +12    edit_verified    (timezone boundary, +1 verify)
15    736    -2     edit_generalize  (P1 anecdote compressed)
16    755    +19    edit_generalize  (DoS budget new section)
Net:  +29 over 4 iters
```

Growing trend. Next iter should tighten to compensate — still 3 Laravel-flavored
"Real bug from this session" anecdotes left in PLAN MODE (P2, P5, P6). Each
compression yields ~-3 to -5 lines + -1 framework token.

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count guard: +19 (heavier than preferred — justified: new coverage category, not duplication; adjacent categories added ~12 for single concepts, this adds 7 vectors in one table)
- structure intact ✓

## Verify: SKIPPED
No attack simulation task (pure exploratory addition). Iter-20 benchmark is
the drift guard.

## Final JSON
```json
{"iter":16,"mode":"free","score":0,"baseline":68,"action":"edit_generalize","skill_md_lines":755,"skill_md_delta":19,"pre_caught":null,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"edit_kind":"new_coverage_category","spec_version":4}
```
