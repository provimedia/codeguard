# Audit Layers — Full-Depth Checks & Redundancy Detectors (R1–R5)

> Loaded on demand from SKILL.md when a layer runs at full depth (see Audit Triage). Contains the exhaustive per-layer check content and the five redundancy detectors with their helper scripts.

## Layer Deep Checks

**DB Integrity** — Fields match live schema? FKs correct AND not runtime-bypassed (any `SET FOREIGN_KEY_CHECKS=0` / `UNIQUE_CHECKS=0` around bulk LOAD/INSERT re-enables in a `finally` AND re-verifies orphans post-load via `SELECT COUNT(*) FROM child LEFT JOIN parent ... WHERE parent.id IS NULL` → 0)? Missing indexes on queried columns? N+1 patterns? ORM attributes match real columns? Money/currency stored as integer minor units (cents) or DECIMAL(p,s), NEVER FLOAT/DOUBLE — float rounding silently corrupts totals across aggregation, and `a*b` in float arithmetic is not associative. **Locale-dependent parse trap**: `(float)`/`floatval()`/`(int)` are C-locale and stop at the first non-numeric byte — `"1.234,56"` → `1.234` (1000x undervalue), `"1,234.56"` → `1.0`, `"12,750"` kg → `12.0`; parse money/quantity strings with a locale-aware normalizer (strip thousands sep, replace decimal comma, validate with regex) BEFORE cast, or reject the input. Grep the diff for `(float)` / `floatval(` / `(int)` applied to ANY string from CSV/JSON/form/API/DB-text-column and prove a prior normalization step. **Counter/quota columns** capacity-checked against realistic peak value — signed `INT` tops at 2^31−1 ≈ 2.1B and under non-strict sql_mode MySQL silently clamps on overflow (warning only, no error); any counter approaching that range needs `BIGINT` / `BIGINT UNSIGNED`, verified by `SELECT DATA_TYPE, COLUMN_TYPE FROM information_schema.COLUMNS WHERE ...` AND an overflow-reproduction query showing the clamp.

**Logic** — Dead code? Unused variables? Unhandled edge cases (null, 0, negative, out-of-range, empty string, empty array)? Missing returns in conditional paths? Off-by-one? Raw environment-variable reads outside the project's single config layer — runtimes that snapshot config at boot return null post-cache, so the service silently falls through to defaults only in production (see PLAN MODE P4 Cached-Config Safety)?

**Efficiency** — Loops replaceable by single query? Sequential awaits that could be parallel? SELECT in loop instead of JOIN? Missing pagination on large sets? `ORDER BY RAND()` over any filtered set larger than a few hundred rows — MySQL assigns RAND() per row then filesorts the WHOLE filtered set to return LIMIT k, so cost is O(filtered rows) regardless of LIMIT and indexes on the WHERE are irrelevant to the sort; fix by sampling on an indexed id (`WHERE id >= FLOOR(RAND()*max_id) ... LIMIT k`), precomputing a shuffled pool, or picking k random ids first and then fetching by PK.

## Redundancy — R1–R5 Detectors

**Redundancy** — Five reflexes, each backed by a helper script in
`~/.claude/skills/code-guardian/tools/`. Every reflex emits either a green
"0 findings" line OR a verbatim block from the script — same v4
verification rule as the rest of the audit. "I checked, looks clean" is
FORBIDDEN. Run all five every audit; LIGHT/FOCUSED triage may skip R2/R3/R5
hash detectors when the diff is < 20 lines AND no new function, template,
or query block was introduced.

**R1. Hardcoded Secrets / Credential Duplication**
Reflex: any added string literal of length ≥ 20 with high entropy or a
known provider prefix is suspect, AND the same secret appearing in 2+
files is a leak even if the prefix is unrecognized.
```bash
bash ~/.claude/skills/code-guardian/tools/detect-secrets.sh <repo>
```
Failure conditions:
- Stage A: known-prefix match (`AIza`, `sk-`, `sk-ant-`, `AKIA`, `ASIA`,
  `ghp_`/`gho_`/`github_pat_`, `xox[baprs]-`, `hf_`, JWT `eyJ.eyJ`,
  Slack/Discord webhook URL, `-----BEGIN ... PRIVATE KEY-----`, SendGrid `SG.`)
- Stage B: same secret literal in ≥ 2 distinct files (use of one shared
  hardcoded value)
Fix: move to `.env` / `config/`, reference via
`config('services.<provider>.key')`. Rotate the leaked secret if the file
was ever committed to a repo with shared visibility.
**Verified-by**: paste the script's `R1.A` / `R1.B` output blocks AND the
`SUMMARY findings=… stages=… exit=…` footer. If clean: paste the
`SUMMARY findings=0 stages=none exit=0` line as proof.

**R2. Cross-File Code Clones (function/method bodies)**
Reflex: any new/modified function whose first 5 non-trivial body lines
hash-collide with another file's function. Same-file repetition is
ignored — Filament/Resource/framework boilerplate is allowlisted by path.
```bash
python3 ~/.claude/skills/code-guardian/tools/detect-clones.py \
    --root . --kind code --cross-file-only
```
Failure conditions: a clone group involves a file present in the current
diff. (Clone groups not touching the diff are noted but not blocking —
they pre-existed.)
Fix: extract to shared service / trait / helper / utility class. If the
clone is framework-mandated (e.g. Filament Resource boilerplate in
`Filament/Resources/*/Pages/`), the script's default `--exclude` already
suppresses it; if not, add the path to project allowlist with a one-line
reason.
**Verified-by**: paste the `R2.code clone-group …` block(s) showing the
hash, file:line list, and normalized snippet, plus the SUMMARY footer.

**R3. Cross-File Template / Markup Clones**
Reflex: any literal HTML/Blade/Vue block ≥ 200 chars (whitespace-
normalized) appearing in 2+ template files.
```bash
python3 ~/.claude/skills/code-guardian/tools/detect-clones.py \
    --root resources --kind html --min-chars 200
```
Failure conditions:
- Repeated `<header>`/`<footer>`/`<nav>`/`<form>`/`<aside>` block in 2+ views
- Repeated `<head>` meta block (`<meta name="viewport">`, `<meta name="csrf">`,
  Open-Graph tag set) across multiple layouts
- New view file added that does NOT use `@extends` / `<x-layout>` /
  Inertia parent layout while sibling files in the same directory do —
  almost always means inlined-instead-of-included header/footer
Fix: extract to `@include` / `<x-component>` / Inertia layout slot.
**Verified-by**: paste hash group(s) with the first 120-char normalized
snippet, plus SUMMARY.

**R4. Config-as-Code Leaks (URL / email / absolute path)**
Reflex: same absolute URL, email, or filesystem path appearing in ≥ 2
source files.
```bash
bash ~/.claude/skills/code-guardian/tools/detect-config-leaks.sh <repo>
```
Failure conditions:
- Own-domain URL hardcoded in 2+ files (use `config('app.url')` or named
  route helper)
- Support / contact / from-email hardcoded in 2+ files (use
  `config('mail.from.address')`)
- Absolute filesystem path (`/var/...`, `/Users/...`, `C:\...`) in 2+ files
  (use `storage_path()`, `base_path()`, or env-driven config)
Path-based excludes are baked in for `database/seeders`, `database/factories`,
`tests/` (legitimate fixture data). Allowlist in the script covers
ubiquitous schema/spec URLs (schema.org, w3.org, github.com placeholder,
example.* domains, localhost) and `*@email.<tld>` localized form-placeholder
emails (your@email.com, votre@email.fr, ihre@email.de, …).
Fix: introduce a `config/` entry, reference via `config('…')`.
**Verified-by**: paste the `R4.URL` / `R4.EMAIL` / `R4.PATH` blocks plus
SUMMARY.

**R5. Cross-File Query Clones (Eloquent chain / raw SQL)**
Reflex: same Model-where-chain or SQL fragment in 2+ controllers/services
after binding-normalization (string literals → `'?'`, `$vars` → `$?`,
numbers → `?`).
```bash
python3 ~/.claude/skills/code-guardian/tools/detect-clones.py \
    --root app --kind sql --cross-file-only
```
Failure conditions: a normalized query fragment appears in ≥ 2 distinct
files, AND any of those files is in the current diff.
Fix: extract to repository / model scope / query method.
**Particularly load-bearing for validation queries** (invitation codes,
single-use tokens, status flags, quota counters): divergence between
copies is a security gap, not just a cleanliness issue — see also the
single-use-resource and rate-limit-key reflexes.
**Verified-by**: paste the `R5.sql clone-group` block(s) and SUMMARY.

**Severity mapping in audit report**:
- 🔴 BLOCKED: any R1.A known-prefix hit on a live secret · R5 clone touching
  auth/token/quota/rate-limit logic
- 🟡 NEEDS FIX: R2 cross-file body clone touching the diff · R3 with ≥ 3
  occurrences · R4 own-domain leak in ≥ 3 files · R1.B ≥ 2 files
- 🟢 NOTE: R3 / R4 with exactly 2 occurrences (lower priority — track but
  may be deferred)

**Project override**: scripts read optional `.code-guardian-redundancy.yml`
in repo root for project-specific allowlists (paths, allowed-duplicate
URLs, allowlisted clone hashes with documented reason). Absent file = use
defaults.

## Security Layer — Full Depth

**Security** — Raw user input in queries (SQL injection)? Sensitive fields (password, token, secret) in responses? Missing auth checks? JWT/signed-token verifier pins algorithm to the key type on OUR side and NEVER reads `alg` from the token header (`alg=none` skips verify, `RS256`->`HS256` HMACs the signing input with the public key as the shared secret — both forge any claim)? Unsafe PHP sinks on untrusted input — `unserialize()` on any request-shaped byte (cookie, body, query, cache value a user ever wrote) is a PHP object-injection / POP-chain RCE primitive, fix: decode as JSON via `json_decode($s, true, 512, JSON_THROW_ON_ERROR)`, never `unserialize`; `include`/`require`/`include_once`/`require_once` with any user-shaped path segment is local-file-include → RCE, fix: allowlist to a fixed enum of filenames, never concat; `shell_exec`/`passthru`/`system`/`exec`/`popen`/`proc_open` and backtick `` `...` `` with any user byte in the command string is command injection, fix: pass args as an array with a fixed absolute binary path OR `escapeshellarg` every segment; `eval`/`create_function`/`assert($string)` on any dynamic string is arbitrary-code execution, fix: remove, no safe wrapper exists? `DOMDocument::loadXML`/`simplexml_load_string`/`simplexml_load_file`/`XMLReader::xml` on any caller-shaped byte is XXE (external-entity file-read + SSRF via `SYSTEM` entities, and billion-laughs DoS via nested internal entities), fix: parse with `LIBXML_NONET | LIBXML_DTDLOAD` suppressed (pass `LIBXML_NONET` and NEVER `LIBXML_NOENT`, and on PHP <8 call `libxml_disable_entity_loader(true)` around the parse), reject documents whose `$doc->doctype !== null` unless a fixed schema is required, and cap the input bytes BEFORE parse? Mass assignment without whitelist? Missing rate limiting on auth endpoints? **Rate-limit key scope** — for every throttle/counter, name the bucket key and ask: is it the stable identity being protected (user_id, verified email after normalization, API-key ID), or something the caller can rotate at will (session_id, raw submitted email, anonymous cookie, request ID, `X-Forwarded-For`)? An attacker-rotatable key is not a rate limit — it's a speed bump they reset between attempts. For pre-auth flows (OTP verify, password reset, signup confirm) key by the PENDING identity, not the session carrying it. **IP-keyed buckets must mask to a network prefix before hashing** — a raw address is rotatable for free on IPv6 (residential/mobile allocations hand a single attacker a full /64 = 2^64 addresses, often /56 or /48) and cheap on IPv4 behind carrier-grade NAT or cloud egress pools; `inet_pton` the value, mask to 8 bytes for v6 (/64) and 3–4 bytes for v4 (/24 or /32), key on the masked bytes. Trusting raw `REMOTE_ADDR` on an IPv6-reachable endpoint is the same bug class as trusting `X-Forwarded-For`. IDOR vulnerabilities?
