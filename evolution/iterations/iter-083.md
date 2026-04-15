# Iteration 083 — free mode (v4, 34th targeted win, +1 line, closes iter-82 deferred gap)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: /account/messages.php — authenticated inbox page with reflected XSS sinks

## Task
PHP 8.2 + MySQL 8 customer portal. `/account/messages.php` echoes
`$_GET['q']` raw via `<?= $highlight ?>`, renders `$m['body_html']` raw,
sets Cache-Control/Pragma/Expires/Vary correctly but emits no CSP /
X-Content-Type-Options / Referrer-Policy / Permissions-Policy.

## Bugs planted (3)
- **B1** Authenticated HTML response with XSS sink + NO `Content-Security-Policy` / `X-Content-Type-Options` / `Referrer-Policy` / `Permissions-Policy`. Second line of defense absent. **TARGETED** (closes iter-82 deferred gap)
- **B2** `<p>Showing results for: <?= $highlight ?></p>` reflected XSS sink (zero escaping).
- **B3** `session_start()` without cookie_params (HttpOnly/Secure/SameSite), no `session_regenerate_id` in auth flow.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — Cacheability reflex enumerated exactly 4
response headers (Cache-Control/Pragma/Expires/Vary) and stopped there.
Auditor pattern-matched "all 4 present → PASS" and never asked for CSP
as belt-and-braces against the XSS sink it had just flagged.

## Proposed edit (+1 line, inline list append, topically correct)
Added item 5 to the existing Cacheability audit reflex numbered list:

**"5. Defense-in-depth headers when the body reflects any user-controlled
content (XSS sink present or possible): `Content-Security-Policy` (strict
`default-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'`, no
`unsafe-inline`), `X-Content-Type-Options: nosniff`, `Referrer-Policy:
no-referrer` (or `same-origin`), `Permissions-Policy` locking down unused
features. Absent → BLOCKED — escaping at the sink is the first line; CSP
is the second and they are NOT interchangeable."**

- Topically correct ✓ (extends existing Cacheability reflex that already
  enumerates required response headers on authenticated pages)
- `targeted_miss: "B1"`
- Framework tokens: **0** (all web standards: CSP, HTTP response headers)
- Line count delta: **+1** (list append, no new section)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("Browser bfcache" matched once) ✓
- generality: 0 framework tokens ✓
- line-count: +1 (near-zero-cost) ✓
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

**Verify notes**: *"New Cacheability item 5 explicitly requires
CSP/XCTO/Referrer-Policy/Permissions-Policy when body reflects user
content; XSS sinks in messages.php trip it, B1 now caught."*

**Thirty-fourth v4 targeted win. Closes iter-82 deferred B3 gap.**

## Decision: **edit_verified**

## Progress after 83 iters
- Verified targeted wins: **34**
- Bugs closed cumulatively via v4 verify: **43**
- Benchmark passes: 8
- Regressions: 0
- Zero-cost inline wins: 8
- Near-zero-cost (+1 line) wins: iter-63, 65, 69, 71, 72, 74, 76, 79, 81, 82, 83 (many)
- Deferred gaps closed: **5-for-5** (iter-56→58, 71→72, 75→76, 79→81, 82→83)
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":83,"mode":"free","score":6,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":1,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_closes_prior_deferred","spec_version":4}
```
