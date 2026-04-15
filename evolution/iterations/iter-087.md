# Iteration 087 — free mode (v4, 37th targeted win, +2 lines)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Team logo + member photo importer (SSRF + Zip Slip + CORS + verb)

## Task
PHP + MySQL admin team importer. `file_get_contents($_POST['logo_url'])`
with no validation; ZIP extraction loops `$zip->getNameIndex($i)` into
`$base . $name` with no containment; response emits `Access-Control-Allow-Origin: *`
+ `Access-Control-Allow-Credentials: true`; `bootstrap.php` sets
`session.cookie_samesite = None` without `Secure`; no verb enforcement.

## Bugs planted (4)
- **B1** SSRF via `file_get_contents($logoUrl)` — AWS IMDS, `file://`, `phar://`, `gopher://` all reachable. **TARGETED**
- **B2** Zip Slip via `$base . $name` with no realpath containment.
- **B3** CORS `*` + `Allow-Credentials: true` + `SameSite=None` without `Secure`.
- **B4** No verb enforcement — mutation on any verb, CSRF-on-GET.

## Pre-edit simulation
Caught **2/4**. Missed **B1** — no explicit SSRF reflex anywhere in
SKILL.md. Path Traversal companion at line 857 covered filesystem READ
via paths, not URL-wrapper-enabled fetches.

## Proposed edit (+2 lines, new companion paragraph in Path Traversal neighborhood)
Added a new "Companion reflex — SSRF via server-side URL fetch" paragraph
immediately after the Path Traversal READ reflex:

**"Companion reflex — SSRF via server-side URL fetch.** Any
`file_get_contents` / `curl_exec` / `fopen` / HTTP-client call whose URL
is derived from caller input is an SSRF primitive — scheme allowlist
(`http`/`https` only; reject `file://`, `gopher://`, `phar://`, `dict://`,
`ftp://`) AND resolve the host to an IP (`gethostbynamel` /
`dns_get_record`) and reject RFC1918, loopback, `169.254.0.0/16` (cloud
metadata IMDS), `0.0.0.0/8`, and IPv6 ULA/link-local BEFORE the fetch;
disable follow-redirects or re-validate every hop
(`CURLOPT_FOLLOWLOCATION=false`), and defeat DNS-rebinding by fetching
via the resolved IP with `CURLOPT_RESOLVE` (or re-check the post-resolve
IP before read). An ownership check does NOT mitigate — the attacker
targets THEIR OWN row with a URL pointing at
`http://169.254.169.254/latest/meta-data/iam/security-credentials/`."

- Topically correct ✓ (adjacent to Path Traversal READ companion; both
  are "caller-controlled path/URL → sensitive sink" patterns)
- `targeted_miss: "B1"`
- Framework tokens: **0** (all PHP stdlib + RFC1918 + IMDS addresses)
- Line count delta: **+2** (new paragraph, no new section header)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("expect 404 with empty body" matched once) ✓
- generality: 0 framework tokens ✓
- line-count: +2 (new reflex class, justifies growth)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 2
post_caught:                3
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [B3 CORS + SameSite]
forbidden_phrases_count:    0
```

**Verify notes**: *"New SSRF companion reflex directly catches
`file_get_contents($logoUrl)` + IMDS/file://; Zip Slip caught by Path
Traversal pattern generalization; CORS+SameSite still has no dedicated
reflex."*

**Thirty-seventh v4 targeted win. New reflex class (SSRF).**

## Decision: **edit_verified**

## Deferred gap (B3)
CORS `*` + `Allow-Credentials: true` + `SameSite=None` without `Secure`.
No dedicated reflex. Candidate for a future iter: compact inline clause
on Cookie/CORS policy added to Session Lifecycle or Cacheability neighborhood.

## Progress after 87 iters
- Verified targeted wins: **37**
- Bugs closed cumulatively via v4 verify: **46**
- Benchmark passes: 8
- Regressions: 0
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":87,"mode":"free","score":58,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":2,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_new_reflex_class_ssrf","spec_version":4,"deferred_gap":"B3_cors_samesite"}
```
