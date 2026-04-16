# Iteration 091 — free mode (v4, 40th targeted win, zero-cost inline, closes iter-89 P4-in-BUILD-mode gap)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: PDF invoice export endpoint + SMTP mailer fallback

## Task
PHP + MySQL project with single config layer cached at boot
(`bootstrap/config.cache.php` snapshots env once). New
`InvoicePdfExporter` and `SmtpMailer` classes call `getenv()` directly
for `INVOICE_PDF_DIR`, `SMTP_HOST`, `SMTP_USER`, etc. — in prod these
return false and services silently fall through to defaults. Export
endpoint uses `$_GET['email']` as mail destination unvalidated and
renders money via `$total_cents / 100`.

## Bugs planted (3)
- **B1** Raw `getenv()` reads inside services bypass the cached config layer — prod returns false, silent fall-through to `/tmp/invoices`, `localhost:587`, null SMTP creds. **TARGETED** (closes iter-89 meta-gap)
- **B2** `$_GET['email']` as mail destination — unvalidated, open relay for authenticated users.
- **B3** `$invoice['total_cents'] / 100` float money display arithmetic.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — P4 Cached-Config Safety lived only in
PLAN MODE. BUILD MODE audit layers (DB Integrity, Logic, Efficiency,
Redundancy, Security) never pointed at it, so a BUILD-only audit on a
diff containing raw env reads outside the config layer passed every
layer.

## Proposed edit (inline, 0 line delta, closes meta-gap)
Extended the BUILD MODE Logic-layer bullet inline with a pointer back
to P4:

**"Raw environment-variable reads outside the project's single config
layer — runtimes that snapshot config at boot return null post-cache,
so the service silently falls through to defaults only in production
(see PLAN MODE P4 Cached-Config Safety)?"**

- Topically correct ✓ (Logic layer owns production-deployment surprises
  — dead code, missing returns, edge cases that only fire in prod)
- `targeted_miss: "B1"`
- Framework tokens: **0** (phrased as "raw environment-variable reads
  outside the project's single config layer" — no `env(`, `config(`,
  no framework class/method names)
- Line count delta: **0** (inline extension within existing Logic bullet)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("**Logic** — Dead code?" matched once) ✓
- generality: 0 framework tokens ✓
- line-count: **0** (zero-cost inline) ✓
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 2
post_caught:                3
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"Logic-layer bullet now names raw getenv() outside
config + post-cache null + prod-only fall-through; grep surfaces 6
getenv calls in new services, B1 caught alongside B2 (unvalidated $_GET
email destination) and B3 (float money /100)."*

**Fortieth v4 targeted win. 🎉 Twelfth zero-cost inline win. Closes
iter-89 meta-gap (P4 reflex now reachable from BUILD MODE audit).**

## Decision: **edit_verified**

## Progress after 91 iters
- Verified targeted wins: **40** 🎉
- Bugs closed cumulatively via v4 verify: **49**
- Benchmark passes: 9 (full 3x3 cycle complete)
- Regressions: 0
- Zero-cost inline wins: **12**
- Deferred gaps closed: 7-for-7 (iter-56→58, 71→72, 75→76, 79→81, 82→83, 87→88, 89→91)
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":91,"mode":"free","score":67,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_closes_prior_deferred_meta_gap","spec_version":4}
```
