# Iteration 052 — free mode (v4, eighteenth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Post-login redirect helper — honor `?next=` return-to-page

## Task (self-contained, PHP)
`redirectAfterLogin(string $next, string $defaultPath)` uses
`str_starts_with($next, '/')` as a same-origin guard before
`header('Location: ' . $next)`.

## Bugs planted (1)
- **B1** `str_starts_with($next, '/')` accepts `//evil.com/x` — browsers resolve `Location: //evil.com/x` to `https://evil.com/x` via protocol-relative URL semantics → open redirect → phishing primitive. **TARGETED**

## Pre-edit simulation
Caught **0/1**. Existing P3 covered secrets in URLs, Session Lifecycle
covered identity rebinding, but neither covered redirect-target validation
where the target is caller-controlled.

## Proposed edit (trimmed from subagent's +50 to +16)
New Cross-Layer sub-section **"Open Redirect via Untrusted Return-To URL
(`?next=`, `?redirect=`, `?returnTo=`)"** inserted before NULL Semantics
in Aggregation.

- **Four traps all passing casual code read**:
  1. Protocol-relative bypass (`//evil.com/x`)
  2. Backslash normalization (`/\evil.com`)
  3. `parse_url` without host assertion
  4. Userinfo trick (`https://app.example.com@evil.com/x`)
- **4-question audit reflex**:
  1. Allowlist mechanism must be enum OR `parse_url` host equality; regex-on-raw-string = BLOCKED
  2. Prove `parse_url($next, PHP_URL_HOST)` returns `null` on accepted forms AND attacker host on trap forms
  3. End-to-end run: hit endpoint with each trap payload, follow `Location`, final hop must stay on app host
  4. Scheme allowlist: null (relative) or http/https with host match only; reject javascript:/data:/vbscript:/file:
- **Scheme trap callout**: inert in `Location:` but active in `<a href>` / `<meta refresh>` where the same helper is often reused

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all PHP stdlib: `parse_url`, `PHP_URL_HOST`, `str_starts_with`, web standard schemes)
- Line count delta: **+16** (subagent proposed +50; main loop dropped userinfo/backslash detailed examples, silent-failure paragraph, PHP verification block, and bash curl loop)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +16 (new general security bug class)
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

**Verify notes**: *"New Open Redirect section explicitly names protocol-
relative bypass trap matching the candidate's `str_starts_with('/')` check;
audit reflex mandates `parse_url` host allowlist + end-to-end Location
follow."*

**Full 1/1 post-edit. Eighteenth v4 targeted win.**

## Decision: **edit_verified**

## Progress after 52 iters
- Verified targeted wins: **18**
- Bugs closed cumulatively via v4 verify: **25**
- Benchmark passes: 5
- Regressions: 0

## Final JSON
```json
{"iter":52,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":878,"skill_md_delta":16,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
