# Iteration 002 — free mode

**Agent**: general-purpose, model: opus
**Task title**: Refund-Eligibility Webhook + Sync for B2B Invoicing SaaS

## Task (invented by red team)
Laravel 11 + Vue 3 + MySQL. Add `refund_eligible`, `refund_checked_at`,
`refund_reason` to `invoices`, plus a computed `refund_badge_class` accessor,
an Inertia dashboard, a 240k-row sync command against `PayVault` (one HTTP call
per invoice), AND a POST `/webhooks/payvault/refund` endpoint authed via
`?api_key=`. Spec says "follow SyncDisputeStatus.php pattern".

## Ground truth — bugs planted (8)
1. **P1** Cross-layer: dashboard controller whitelists fields, forgets `refund_badge_class`
2. **Accessor-Trap**: `getRefundBadgeClassAttribute()` without `$appends`
3. **P2 Scale**: 240k invoices processed sequentially in sync command
4. **N+1 external HTTP**: one `Http::get` per invoice in the loop (no bulk endpoint, no `Http::pool()`)
5. **P3 outbound**: sync command passes API key in URL query
6. **P4**: `env('PAYVAULT_KEY')` in the command (not `config()`)
7. **P5**: "follow SyncDisputeStatus.php" — source pattern not audited
8. **P3 inbound webhook**: `/webhooks/payvault/refund?api_key=xxx` — key in URL of INBOUND webhook

## Simulation
The simulated session (armed with current SKILL.md) caught all 8 bugs:
- P1, P2, P4, P5, Accessor-Trap → textbook hits from existing PLAN MODE
- N+1 external HTTP → caught thanks to iter-1's N+1 extension ✓ (the previous
  iteration's fix already paid off)
- P3 outbound → direct hit
- P3 inbound webhook → **caught only by analogy** because P3 section is phrased
  outbound-only ("Every plan that introduces an **external** API call")

## Scoring
```
bugs_planted:        8
bugs_caught:         8
bugs_missed:         0
forbidden_phrases:   0
friction_notes:      3
token_cost:          medium

score = 8 - 0 - 0 - 1 = 7
baseline: 3 → accept (7 >= 3)
```

## Friction notes
1. P3 Secrets Hygiene is outbound-only framed — inbound webhook auth only caught
   by analogical reasoning, not direct pattern match
2. Overlap between P2 scale and Cross-Layer N+1 section when the loop body is an
   external HTTP call (both sections fire with similar guidance)
3. BUILD MODE audit section repeats dependency-impact concepts already covered
   in PLAN MODE P1

## Proposed edit — ACCEPTED
**Rationale**: P3 Secrets Hygiene was only phrased for OUTBOUND Guzzle calls.
Inbound webhook endpoints authenticated via `?api_key=` are just as bad — the
key leaks into Nginx/Apache access logs, reverse-proxy logs, browser history,
and Referer headers on any redirect. Generalizing P3 to cover both directions
closes the gap with minimal addition.

**Diff** (SKILL.md, Section `### P3. Secrets Hygiene for API Calls`):
```diff
-Every plan that introduces an external API call MUST specify:
-- API key passed via **header**, NEVER query string
-- Why: Guzzle exception messages include the full URL; URL-key leaks into
-  `storage/logs/laravel.log` on any HTTP failure.
+Every plan that introduces an API call OR an inbound webhook endpoint MUST specify:
+- API key / shared secret passed via **header**, NEVER query string — in BOTH directions
+- Why (outbound): Guzzle exception messages include the full URL; URL-key leaks into
+  `storage/logs/laravel.log` on any HTTP failure.
+- Why (inbound): `?api_key=` in a webhook URL leaks into Nginx/Apache access logs,
+  reverse-proxy logs, browser history, and Referer headers on any redirect. Require
+  `$request->header('X-...-Signature')` + constant-time compare, never `$request->query('api_key')`.
```

## Final JSON
```json
{"iter":2,"mode":"free","score":7,"baseline":3,"action":"edit","bugs_planted":8,"bugs_caught":8,"bugs_missed":0,"friction_notes":3,"token_cost":"medium"}
```
