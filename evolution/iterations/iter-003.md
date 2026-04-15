# Iteration 003 — free mode

**Agent**: general-purpose, model: opus
**Task title**: GDPR Data Export — async job builds per-tenant ZIP, emails signed download link

## Task (invented)
Multi-tenant SaaS. Tenant-admin triggers queued `BuildGdprExport` job that aggregates
14 tables per `tenant_id`, writes ZIP, uploads to S3, emails a signed time-limited
download URL. Nightly `ReapGdprExports` deletes ZIPs > 48h old. Rate-limit: 1
export/tenant/24h.

## Bugs planted (9)
A. `?token=` in email download URL → leaks to logs/Referer/history
B. `env('GDPR_SIGNING_KEY')` in runtime helper → null after `config:cache`
C. `DB::table()->get()` across 14 tables up to 500k rows each → OOM
D. `GdprExport` model: no `$casts`/`$hidden`/`$appends` → `download_token` undefined in Vue
E. `ReapGdprExports` fires per-row `Storage::disk('s3')->delete()` in `foreach`
F. Migration has no index on `tenant_id` → full-scan on rate-limit query
G. Vue destructures `reactive(props)` → loses reactivity (P1 Frontend Reactivity Trap)
H. Rate-limit scope ambiguous: tenant-vs-user mismatch between comment and query
I. Raw `download_token` stored in DB (never marked used) — replay attack possible

## Simulation
Session (armed with iter-2 SKILL.md) caught all 9:
- B (P4), C (P2), E (N+1 external-in-loop — caught thanks to iter-1 edit)
- A (P3 — caught by analogy from iter-2's inbound extension)
- D (Accessor/serialization trap), F (DB integrity), G (Frontend Reactivity Traps section)
- H (Cross-layer contract between comment and SQL), I (security audit check 6)

## Scoring
```
planted: 9, caught: 9, missed: 0
forbidden: 0
friction_notes: 2 (< 3, no penalty)
token_cost: medium

score = 9 - 0 - 0 - 0 = 9
baseline = 7 → accept (9 >= 7)
```

## Friction notes
1. SKILL.md exceeds 10k-token Read default → cold-start agents must offset/limit-read
2. P5 Pattern Source reflex awkward to report as PASS when plan has no "follow pattern" reference

## Proposed edit — ACCEPTED
**Rationale**: Bug A (download/reset/magic-login token in URL) was caught only by
analogy from iter-2's inbound webhook extension. It's a distinct, high-value bug
class — password resets, GDPR exports, magic links — with its own set of requirements
(signed routes, SHA-256 hash at rest, one-time-use via `consumed_at`). Adding a
bullet under P3 closes the analogy gap without duplicating other guidance.

**Diff** (SKILL.md, extends P3 after iter-2's inbound-webhook bullet):
```diff
 - Why (inbound): `?api_key=` in a webhook URL leaks into Nginx/Apache access logs,
   reverse-proxy logs, browser history, and Referer headers on any redirect. Require
   `$request->header('X-...-Signature')` + constant-time compare, never `$request->query('api_key')`.
+- Why (user-facing download/reset tokens): same leakage surface applies to `?token=` in
+  emailed download/reset/magic-login links. Required: `URL::temporarySignedRoute()` (signature
+  travels in the URL but is bound to the route+expiry and verified server-side), store a SHA-256
+  HASH of the token in the DB (never the raw value), and enforce one-time use via a `consumed_at`
+  column checked+set in a single transaction.
```

## Final JSON
```json
{"iter":3,"mode":"free","score":9,"baseline":7,"action":"edit","bugs_planted":9,"bugs_caught":9,"bugs_missed":0,"friction_notes":2,"token_cost":"medium"}
```
