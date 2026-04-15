# Iteration 085 — free mode (v4, 36th targeted win, +2 lines)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Order fulfillment webhook + random featured + audit trail

## Task
PHP + MySQL shop. `OrderFulfillmentClient` POSTs to `/v1/shipments` via HTTP
client with auto-retry middleware on 5xx/timeout (non-idempotent endpoint,
no Idempotency-Key); `FeaturedProductsRepository::pickFeatured` uses
`ORDER BY RAND()` on 4M rows; `AuditTrailWriter::log` serializes `$_SERVER`
+ full row blobs; `OrderController::fulfill` is `GET` with raw int-concat
SQL and mutates state.

## Bugs planted (4)
- **B1** HTTP client retry middleware duplicates non-idempotent POST on 5xx/timeout; no `Idempotency-Key` header. **TARGETED**
- **B2** `ORDER BY RAND()` on 4M rows.
- **B3** `$_SERVER` + full row blobs in audit logger.
- **B4** GET route mutates state + raw int-concat SQL.

## Pre-edit simulation
Caught **3/4**. Missed **B1** — Queue/Task Idempotency reflex was scoped
to "enqueued job types" and worker retries. HTTP transport-layer retry
middleware is the same failure class on the egress path (at-least-once
delivery, connection reset after remote accept → duplicate commit) but
was not explicitly anchored. Literal readers checked queue workers, not
HTTP clients.

## Proposed edit (+2 lines, new paragraph in existing Queue/Task Idempotency section)
Added a follow-up paragraph to the existing Queue/Task Idempotency
reflex, keeping the same "at-least-once" anchor:

**"Same reflex for HTTP client retry middleware.** Any outbound client
configured to auto-retry on network error / 5xx / timeout is at-least-once
on the egress path: a connection reset AFTER the remote accepted the write
re-sends the same body on the next attempt and the remote executes it
twice. Non-idempotent verbs (POST / PATCH / non-conditional PUT / DELETE)
under such middleware MUST send a caller-generated `Idempotency-Key`
header (UUIDv4 or hash of `aggregate_id + operation_id`) that the remote
dedupes on, OR the retry policy MUST exclude non-idempotent verbs. A
`timeout` is NOT a failure signal — the remote may have committed and
only the response was lost; retrying on timeout without a dedup key is
indistinguishable from retrying on a confirmed error. Audit reflex: for
every HTTP client construction in the diff, name the retry policy AND
the verbs it applies to; any non-idempotent verb in the retry set without
an idempotency-key header → BLOCKED."

- Topically correct ✓ (same section, same at-least-once principle, just
  extended to egress path)
- `targeted_miss: "B1"`
- Framework tokens: **0** (POST/PATCH/PUT/DELETE/Idempotency-Key/UUIDv4
  are web standards)
- Line count delta: **+2** (new paragraph, no new section)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +2 (new reflex class, justifies growth)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 3
post_caught:                4
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New HTTP-client retry paragraph under Queue/Task
Idempotency anchors B1; B2 via Efficiency/P2 full-sort, B3 via Error-Path
Log Hygiene ($_SERVER + full row explicit), B4 via Verb Safety + Security
SQLi."*

**Thirty-sixth v4 targeted win. 4/4 clean sweep post-edit.**

## Decision: **edit_verified**

## Progress after 85 iters
- Verified targeted wins: **36**
- Bugs closed cumulatively via v4 verify: **45**
- Benchmark passes: 8
- Regressions: 0
- Noops: 2 (iter-75, iter-78)
- Zero-cost inline wins: 9
- Line count: 904 → 906 (+2, closing a distinct gap class)

## Final JSON
```json
{"iter":85,"mode":"free","score":7,"baseline":68,"action":"edit_verified","skill_md_lines":906,"skill_md_delta":2,"pre_caught":3,"post_caught":4,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_new_reflex_class","spec_version":4}
```
