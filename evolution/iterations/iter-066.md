# Iteration 066 — free mode (v4, 25th targeted win, triple hit +3)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: PHP comments JSON endpoint — charset drift corrupts response

## Task
PHP `recent-comments.php` endpoint. `new PDO('mysql:host=...;dbname=...')`
without `charset=utf8mb4`. `Content-Type: application/json` without
charset. `echo json_encode($rows)` unchecked. Production server default
`character_set_results = latin1`. Emoji comments produce literal
response body `"false"`.

## Bugs planted (3)
- **B1** PDO DSN missing `charset=utf8mb4` — server transcodes utf8mb4 to latin1 on delivery, emoji bytes become invalid UTF-8, `json_encode` returns `false`. **TARGETED**
- **B2** `Content-Type: application/json` missing `charset=utf-8`
- **B3** `json_encode` return value unchecked

## Pre-edit simulation
Caught **0/3**. Implicit Coercion (iter-32) covered charset mismatch as
an INDEX-usability problem, not as read-path DATA corruption. The two
failure modes look nothing alike, so the index reflex does not trip on
the data-corruption case. No reflex covered response Content-Type
charset parameter or unchecked `json_encode`.

## Proposed edit (trimmed from subagent's +50 to +16)
New Cross-Layer sub-section **"Client-Connection Charset Drift (READ-path
data corruption, not index cost)"** inserted after Implicit Coercion
Defeating Indexes. Explicitly distinguishes itself from that reflex and
targets the data-integrity failure mode.

- **Three silent failure modes**:
  1. `json_encode` returns `false` with `JSON_ERROR_UTF8` — echoes literal `"false"`
  2. Silent data loss on round-trip (read as `?`, write stores `?`)
  3. Index lookups by string value miss rows (emoji-bind → `?` → zero matches)
- **4-question audit reflex**:
  1. Client charset named in DSN/connect options? (SET NAMES is belt-and-braces, not a substitute — runs after handshake)
  2. Named charset matches column storage charset? (use the existing `information_schema.COLUMNS` verification)
  3. Response `Content-Type` carries `charset=utf-8`?
  4. Serializer return value checked? (`json_encode` returning `false` without a log entry = `HTTP 200 body="false"` in production)
- **Verification**: `SHOW SESSION VARIABLES LIKE 'character_set_%'` (all 3 must be utf8mb4) + `curl -sD -` with an emoji row

- `targeted_miss: "B1"` (B2 + B3 caught as collaterals)
- Framework tokens in new_string: **0** (pure PDO/MySQL/HTTP standard)
- Subagent originally proposed +50 lines with verbose intro + "Failure signature" paragraph + full HEX verification; main loop trimmed to +16
- Line count delta: **+16**

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +16 (new general bug class, 3 failure modes closed in one reflex)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 0
post_caught:                3
delta:                      +3  ← triple hit
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New Client-Connection Charset Drift sub-section
Q1/Q3/Q4 map 1:1 to B1/B2/B3; DSN grep, Content-Type header check, and
json_encode return check each fire on the diff."*

**Full 3/3 post-edit. Twenty-fifth v4 targeted win with triple delta.**

## Decision: **edit_verified**

## Progress after 66 iters
- Verified targeted wins: **25**
- Bugs closed cumulatively via v4 verify: **34**
- Benchmark passes: 6
- Regressions: 0
- **Triple-hit iterations**: 4 (iter-37 backfill-shape, iter-45 log-hygiene,
  iter-56 header-injection, iter-66 charset-drift)

## Final JSON
```json
{"iter":66,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":909,"skill_md_delta":16,"pre_caught":0,"post_caught":3,"verify_delta":3,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_triple_hit","spec_version":4}
```
