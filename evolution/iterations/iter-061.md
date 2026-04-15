# Iteration 061 — free mode (v4, 22nd targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: CSRF-on-GET — one-click unsubscribe via `Route::get`

## Task
`Route::get('/account/unsubscribe', ...)` handler runs
`UPDATE subscribers SET subscribed=0 WHERE user_id = ?`. CSRF middleware
checks POST/PUT/DELETE/PATCH but not GET (standard exemption).

## Bugs planted (1)
- **B1** State-changing UPDATE served over GET → `<img src="https://app/account/unsubscribe">` zero-click exploit; email scanners pre-fetch; IM previews trigger it. **TARGETED**

## Pre-edit simulation
Caught **0/1**. Existing reflexes covered auth boundaries (Session
Lifecycle), response headers (Header-Value Injection), redirect
destination (Open Redirect), cross-user cache replay (Cacheability) —
**none** covered verb-semantic CSRF (mismatch between request VERB and
handler SIDE-EFFECT).

## Proposed edit (trimmed from subagent's +45 to +13)
New Cross-Layer sub-section **"HTTP Verb Safety for State-Changing
Requests (CSRF-on-GET)"** inserted before Frontend Reactivity Traps.

- **Principle**: RFC 7231 defines GET/HEAD as safe + idempotent; every
  mainstream CSRF middleware exempts them by contract. State-changing
  GET = unauthenticated cross-site write primitive.
- **Zero-click attack surfaces**: `<img src>`, link prefetchers, email
  link scanners (Outlook Safe Links, Gmail image proxy, corporate MTAs),
  IM link previews (Slack/Discord/Teams).
- **2-question audit reflex**:
  1. Does handler mutate state? (grep UPDATE/INSERT/DELETE/save/delete/mail/queue) → MUST be POST/PUT/PATCH/DELETE.
  2. Verb enforcement: enumerate registered verbs via router introspection, NOT by reading the route file (match-any patterns inherit GET).
- **Explicit non-mitigations**: authentication doesn't help (victim IS authenticated), ownership checks don't help (attacker targets victim's own row).
- **Remediations**: change verb to POST + CSRF token; for email unsubscribe use RFC 8058 `List-Unsubscribe-Post`; OR signed single-use URL token (consumed via iter-49's Single-Use Resource Consumption reflex; P3 applies to URL-leakage).

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (subagent originally had Laravel `Route::any`, Django `CsrfViewMiddleware`, Rails `protect_from_forgery`, Symfony, Express `csurf`, `php artisan route:list`, `rails routes` — all stripped)
- Line count delta: **+13**

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +13 (new general security bug class)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 0
post_caught:                1
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New CSRF-on-GET reflex with explicit
UPDATE-in-GET-handler check triggers directly on `Route::get` +
`DB::update`."*

**Full 1/1 post-edit. Twenty-second v4 targeted win.**

## Decision: **edit_verified**

## Progress after 61 iters
- Verified targeted wins: **22**
- Bugs closed cumulatively via v4 verify: **29**
- Benchmark passes: 6
- Regressions: 0

## Final JSON
```json
{"iter":61,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":902,"skill_md_delta":13,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
