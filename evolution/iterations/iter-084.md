# Iteration 084 — free mode (v4, 35th targeted win, zero-cost inline, fixes dangling forward reference)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: PHP avatar upload — MIME trust, directory listing, predictable filenames

## Task
Framework-agnostic PHP + MySQL. `/upload-avatar.php` validates
`$_FILES['type']` against an allowlist, moves the file into
`/public/uploads/avatars/` under deterministic `user_id.ext` basename,
directory inherits `Options +Indexes`.

## Bugs planted (3)
- **B1** `$allowed[$f['type']]` trusts client-supplied Content-Type — `shell.php` uploads with `Content-Type: image/jpeg`. Must use `finfo_file(FILEINFO_MIME_TYPE)` magic-byte sniff. **TARGETED**
- **B2** Upload dir inside webroot + inherited `Options +Indexes` → IDOR enumeration + future `AddHandler` makes files executable. Must store outside webroot + serve via handler.
- **B3** Deterministic basename `user_id.ext` → TOCTOU race + cache poisoning + known-path shell landing.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — no dedicated upload-WRITE reflex. Line 859
contained a **dangling forward reference**: *"Distinct from the upload
WRITE-path traversal reflex: this covers the READ sink."* — but no such
reflex existed anywhere in SKILL.md. Auditor hit the dead-end reference
and had no concrete rule to apply.

## Proposed edit (inline, 0 line delta, dual-purpose)
Replaced the dangling reference on line 859 with a concrete inline
upload-WRITE validation rule, naming all three must-have controls:

**"Distinct from upload WRITE-path validation (extension allowlist AND
magic-byte sniff via `finfo_file($tmp, FILEINFO_MIME_TYPE)` — NEVER
`$_FILES['type']`, which is caller-supplied and forgeable; store under a
randomly generated basename OUTSIDE the webroot and serve through a
handler that emits `Content-Disposition: attachment` +
`X-Content-Type-Options: nosniff`, so a forged `.jpg.php` cannot be
executed by the web server): this covers the READ sink."**

Dual purpose:
1. **Fixes a bug in the skill itself**: dangling forward reference removed.
2. **Closes B1/B2/B3**: all three now named concretely.

- Topically correct ✓ (next to filesystem path-traversal on READ — the
  natural companion position for upload-WRITE validation)
- `targeted_miss: "B1"`
- Framework tokens: **0** (`finfo_file`, `FILEINFO_MIME_TYPE`, `$_FILES`
  are PHP stdlib; `Content-Disposition`/`X-Content-Type-Options` are HTTP
  standards)
- Line count delta: **0** (prose extension, same paragraph)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
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

**Verify notes**: *"Line 859 parenthetical concretely names
`finfo_file(FILEINFO_MIME_TYPE)`, forbids `$_FILES['type']`, requires
random basename outside webroot + Content-Disposition/nosniff — all
three bugs land."*

**Thirty-fifth v4 targeted win. Ninth zero-cost inline win. Dual purpose:
upload-WRITE reflex created + dangling forward reference fixed.**

## Decision: **edit_verified**

## Progress after 84 iters
- Verified targeted wins: **35**
- Bugs closed cumulatively via v4 verify: **44**
- Benchmark passes: 8
- Regressions: 0
- Zero-cost inline wins: 9
- Deferred gaps closed: 5-for-5
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":84,"mode":"free","score":62,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_fixes_dangling_reference","spec_version":4}
```
