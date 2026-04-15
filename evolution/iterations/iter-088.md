# Iteration 088 — free mode (v4, 38th targeted win, zero-cost inline, closes iter-87 deferred gap)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: PHP SPA API — CORS-enabled login endpoint for cross-origin frontend

## Task
PHP + MySQL API. `cors.php` emits `Access-Control-Allow-Origin: *` +
`Access-Control-Allow-Credentials: true`. `login.php` calls
`session_set_cookie_params([...'samesite'=>'None'])` without `'secure'=>true`.
`/me` returns user data with no Cache-Control/Vary.

## Bugs planted (3)
- **B1** Compound CORS/cookie bug: (a) `Allow-Origin: *` + `Allow-Credentials: true` invalid per Fetch spec; (b) `SameSite=None` without `Secure` silently drops Set-Cookie. **TARGETED** (closes iter-87 deferred gap)
- **B2** `banned_at` SELECTed but never checked — banned user can still authenticate.
- **B3** `/me` endpoint returns user data with no `Cache-Control`/`Vary: Cookie`.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — Session Lifecycle Cookie attribute drift
bullet only enforced param-assignment ORDER. No reflex covered the
SameSite=None→Secure browser-side coupling or CORS wildcard + credentials
rule. Auditor ticked "params set before session_start, rotation present"
and moved on.

## Proposed edit (inline, 0 line delta)
Extended the existing Cookie attribute drift bullet inline with two new
attribute-compatibility rules:

**"Attribute-compatibility rule: `SameSite=None` without `Secure` is
rejected by every modern browser (Chrome/Edge/Firefox drop the Set-Cookie
entirely, no error surfaced server-side) — the pair is load-bearing, not
independent. CORS credentialed-request rule: `Access-Control-Allow-Origin:
*` combined with `Access-Control-Allow-Credentials: true` is invalid per
the Fetch standard and browsers silently reject the response; credentialed
cross-origin requests require reflecting the exact Origin against an
allowlist AND `Vary: Origin`."**

- Topically correct ✓ (anchored on Cookie attribute drift bullet that
  already enumerates Secure/SameSite)
- `targeted_miss: "B1"`
- Framework tokens: **0** (all web standards — Fetch spec, SameSite, Secure,
  Access-Control-Allow-*, Vary)
- Line count delta: **0** (inline extension within same paragraph)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("Cookie attribute drift" matched once) ✓
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

**Verify notes**: *"Line 521 inline rules (SameSite=None+Secure coupling
and CORS `*`+credentials invalidity) fire on cors.php and login.php diff;
B2 via Auth Enforcement Parity banned-user example; B3 via Cacheability
reflex."*

**Thirty-eighth v4 targeted win. Tenth zero-cost inline win. Closes
iter-87 deferred B3 gap.**

## Decision: **edit_verified**

## Progress after 88 iters
- Verified targeted wins: **38**
- Bugs closed cumulatively via v4 verify: **47**
- Benchmark passes: 8
- Regressions: 0
- Zero-cost inline wins: **10**
- Deferred gaps closed: **6-for-6** (iter-56→58, 71→72, 75→76, 79→81, 82→83, 87→88)
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":88,"mode":"free","score":66,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_closes_prior_deferred","spec_version":4}
```
