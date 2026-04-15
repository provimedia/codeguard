# Iteration 056 — free mode (v4, twentieth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Invoice download — CRLF / quoted-string breakout in Content-Disposition

## Task
PHP invoice download endpoint. Users can rename invoices (writes to
`invoices.filename` column). Download endpoint reads the DB row and puts
the filename directly into `Content-Disposition: attachment; filename="..."`.
Plus `__DIR__ . '/storage/' . $row['pdf_path']` for `readfile()`.

## Bugs planted (3)
- **B1** CRLF / quoted-string breakout via user-writable DB column in `Content-Disposition` header. **TARGETED**
- **B2** Path traversal via `readfile(__DIR__ . '/storage/' . $row['pdf_path'])`
- **B3** Missing `Vary: Cookie` + missing `X-Content-Type-Options: nosniff`

## Pre-edit simulation
Caught **1/3**: B3 partially (Vary: Cookie via iter-54's cacheability
reflex, but nosniff NOT covered). B1 missed — no header-value-injection
reflex; default auditors assume `header()` auto-rejects all injection
and miss quote-breakout in `filename=` sub-parameters. B2 missed — no
path-traversal / `realpath()` / `basename()` guidance anywhere in SKILL.md.

## Proposed edit (trimmed from subagent's +30 to +16)
New Cross-Layer sub-section **"HTTP Header-Value Injection (CRLF +
quoted-string breakout)"** inserted before Frontend Reactivity Traps.

- **Principle**: user-controlled strings flowing into response headers are
  injection sinks even when runtime blocks `\r\n`
- **Three bypass paths**:
  1. **Quoted-string breakout**: raw `"` in `Content-Disposition filename="..."` closes the string and lets attacker inject `; filename*=UTF-8''evil.html`
  2. **Bare `\r` / `\x00`**: some runtimes block the pair but pass lone `\r` or NUL
  3. **Non-ASCII in ASCII-only fields**: RFC 7230 grammar violation, mangled by proxies
- **Distinction**: not XSS (HTML escaping), not P3 (secrets in URLs); this is header grammar
- **3-question audit reflex**:
  1. Is any part user-controlled? DB columns count if ANY write path lets users shape them
  2. Strictly filtered to header grammar? (printable-ASCII minus `"\`, RFC 5987 for non-ASCII)
  3. Validation at WRITE time or READ time? (write-time reject preferred)
- **Verification**: `curl -D -` after injecting quote-breakout at write time; response must have exactly one `Content-Disposition` parameter

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all RFC / PHP stdlib `header()` / `setcookie()`)
- Line count delta: **+16**

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +16
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 1
post_caught:                2
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [B2 path traversal — no filesystem reflex]
forbidden_phrases_count:    0
```

**Verify notes**: *"B1 caught by new Header-Value Injection section
(quoted-string breakout + write-path DB column reflex); B3 `Vary: Cookie`
caught, nosniff still absent; B2 path traversal remains uncovered."*

**Twentieth v4 targeted win.** B2 (path traversal) remains a candidate
for future iter — distinct reflex from header-value injection.

## Decision: **edit_verified**

## Progress after 56 iters
- Verified targeted wins: **20**
- Bugs closed cumulatively via v4 verify: **27**
- Benchmark passes: 5
- Regressions: 0

## Final JSON
```json
{"iter":56,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":908,"skill_md_delta":16,"pre_caught":1,"post_caught":2,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
