# Iteration 075 — free mode (v4, noop — deferred gap flagged)

**Attack agent**: general-purpose, model: opus
**Verify**: N/A (noop)
**Task title**: JSON schema drift + BIGINT ID precision loss in customer export API

## Task
PHP 8.2 + MySQL 8 customer export endpoint. `preferences` JSON column has
schema drift (v1 flat `notify: bool` vs v2 nested `notify.email/sms`) from an
incomplete migration. Customer IDs are `BIGINT UNSIGNED` with current max
`9,100,000,123,456,789` (>2^53). `ExportHandler` does
`(float) str_replace(',', '.', $raw)` for a locale-aware min_spend filter
while `Locale::parseNumber` already exists in the codebase unused.

## Bugs planted (3)
- **B1** JSON schema drift — v1 rows have `notify` as bool scalar; `$prefs['notify']['email'] ?? false` silently returns false for every v1-shape row.
- **B2** BIGINT ID > 2^53 cast to `(int)` and `json_encode`d — JS client loses precision on round-trip. **TARGETED (deferred)**
- **B3** Locale-dependent number parsing: `(float) str_replace(',', '.', '1.234,50')` → `1.234` silently. Existing `Locale::parseNumber` helper unused.

## Pre-edit simulation
Caught **2/3**. Missed **B2** (BIGINT JSON precision loss).
- B1 caught via P1 Cross-Layer Trace + live DB query revealing v1-shape rows.
- B3 caught via Existing Code Scan (1c) surfacing `Locale::parseNumber` +
  `php -r` reproduction of the str_replace bug.
- B2 slipped: Cross-Layer Data Contracts asks "does the key exist" and "is
  it non-null", not "does the numeric value round-trip losslessly in JSON".
  The Implicit Coercion reflex focuses on SQL-side index usability, not
  serializer-side precision.

## Proposed edit
**NULL** (subagent judgment).

Subagent rationale (verbatim): *"Line count is stable at 904, the SKILL
document passed 3 consecutive zero-cost iterations, and no obvious
tightening/dedup target emerged from a full re-read. The BIGINT-ID-over-2^53
JSON precision gap IS a real missing reflex, but adding it is content
expansion (10+ lines) and would need its own placement discussion — not a
minimal inline tightening. Preserving the streak and flagging the gap for a
targeted future iteration is the higher-value move than a forced cosmetic
edit."*

## Deferred gap for iter-76+
**BIGINT ID > 2^53 precision loss in JSON serialization.** Consumer-side
(JS / any language with 64-bit float-backed numbers) rounds to nearest
representable double. Fix idiom: emit IDs as strings in JSON, never
`json_encode((int)$row['id'])`. Candidate inline reflex extension site:
the Implicit Coercion or Return Type Completeness section.

## Decision: **noop**

- edit == null → noop gate ✓ (generality check N/A)
- structure intact ✓
- consecutive_noops: 0 → 1 (first noop since iter-8)

## Progress after 75 iters
- Verified targeted wins: 29
- Bugs closed cumulatively via v4 verify: 38
- Benchmark passes: 7
- Regressions: 0
- Noops: **1** (first since iter-8)
- Deferred gaps: B2 BIGINT JSON precision (→ iter-76 target)

## Final JSON
```json
{"iter":75,"mode":"free","score":0,"baseline":68,"action":"noop","skill_md_lines":904,"skill_md_delta":0,"pre_caught":2,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"edit_kind":"noop_deferred_gap","deferred_gap":"B2_bigint_json_precision","spec_version":4}
```
