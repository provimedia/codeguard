# Iteration 054 — free mode (v4, nineteenth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Account statement page — missing Cache-Control on authenticated response

## Task
PHP `statement.php` renders logged-in user's 30-day transactions behind
Varnish + CDN with default 120s heuristic TTL. Same URL for every user.

## Bugs planted (1)
- **B1** No Cache-Control/Pragma/Expires/Vary: Cookie headers → shared cache key is `(method, host, path)` without Cookie, so user A's statement is served to user B. **TARGETED**

## Pre-edit simulation
Caught **0/1**. Security layer listed SQLi / sensitive-fields / auth /
mass-assign / rate-limit / IDOR — nothing about HTTP cache-header hygiene.
Default PHP emits no Cache-Control, and none of the existing reflexes
distinguish "what's in the body" from "who ELSE can receive this body via
cache replay".

## Proposed edit (trimmed from subagent's +45 to +26)
New Cross-Layer sub-section **"HTTP Response Cacheability for Authenticated
Pages (shared-proxy cross-user disclosure)"** inserted before Error-Path
Log Content Hygiene.

- **Principle**: response bodies that depend on caller identity are per-user; RFC 7234 lets shared caches apply heuristic TTL to 200 OK lacking explicit directives; cache key excludes cookies unless `Vary: Cookie` present
- **Distinction**: "sensitive fields in responses" covers WHAT is in the body; this reflex covers WHO ELSE can receive the same body via cache replay
- **Required headers** (BEFORE any body output): `Cache-Control: private, no-store, no-cache, must-revalidate, max-age=0` + `Pragma: no-cache` + `Expires: 0` + `Vary: Cookie` (or `Vary: Authorization` for token auth)
- **Why `private` alone insufficient**: misconfigured proxy ignores `private` but still honors `no-store`
- **4-question audit reflex**:
  1. What Cache-Control does the response emit? Default/absent → BLOCKED
  2. Is `Vary: Cookie` set? Absent → BLOCKED
  3. Auth-failure 302 redirects are cacheable too — same headers required on redirect response
  4. Browser bfcache: `no-store` is the only directive that reliably evicts on logout
- **curl verification**: `curl -b jar -s -o /dev/null -D - <url> | grep -iE '^(cache-control|pragma|expires|vary):'`

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (pure HTTP standards + curl)
- Subagent originally included a 6-line "Framework defaults" paragraph with Laravel (`cache.headers:private;no_store` middleware) and Symfony (`HttpFoundation Response`) — main loop dropped it entirely
- Line count delta: **+26** (heavy; new general bug class)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +26 (justified — new coverage category, Laravel/Symfony framework paragraph stripped)
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

**Verify notes**: *"New HTTP Response Cacheability section names required
headers + `Vary: Cookie` + curl verification; statement.php's absent
Cache-Control and missing Vary fire audit questions 1+2, BLOCKED."*

**Full 1/1 post-edit. Nineteenth v4 targeted win.**

## Decision: **edit_verified**

## Progress after 54 iters
- Verified targeted wins: **19**
- Bugs closed cumulatively via v4 verify: **26**
- Benchmark passes: 5
- Regressions: 0

## Final JSON
```json
{"iter":54,"mode":"free","score":9,"baseline":68,"action":"edit_verified","skill_md_lines":898,"skill_md_delta":26,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
