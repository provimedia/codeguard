# Iteration 058 — free mode (v4, 21st targeted win, closes iter-56 B2 gap)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Invoice PDF download — READ-path traversal via user-shaped DB column

## Task
PHP invoice download handler. `invoices.pdf_path` was historically
backfilled from user-supplied `filename` (old upload form, now removed).
Handler does `readfile('/var/app/storage/invoices/' . $row['pdf_path'])`
for the current user's row, with an ownership check.

## Bugs planted (1)
- **B1** READ-path traversal: attacker owns their own row and controls `pdf_path`. A row with `pdf_path='../../../../etc/passwd'` exfiltrates arbitrary files through the authenticated endpoint. Ownership check does NOT mitigate. **TARGETED**

## Pre-edit simulation
Caught **0/1**. Iter-8 covered upload WRITE-path traversal, nothing
covered READ sinks. No reflex in SKILL.md said:
- "readfile/fopen/include are traversal sinks"
- "DB columns written by historical user forms count as user-controlled"
- "ownership check does not mitigate attacker-owned rows"

## Proposed edit (trimmed from subagent's +10 to +2)
Zero-cost companion clause appended to Open Redirect section after the
scheme allowlist bullet: **"Companion reflex — Path Traversal via
Filesystem READ"** as a single paragraph.

Contents:
- **Sinks**: `readfile`, `fopen`, `file_get_contents`, `include`, `require`, `SplFileObject`
- **Taint rule**: ANY segment from request input OR from a DB column ANY write path has ever shaped = user-controlled (even if the write form is long gone)
- **Distinction**: upload WRITE-path traversal is a separate reflex
- **Four bypass payloads**: `../../../etc/passwd`, absolute `/etc/passwd`, NUL byte `safe.pdf\x00../...`, symlink-in-base → out-of-base
- **Required defence** in sequence: `realpath($base)` → `realpath($base.'/'.$input)` → `str_starts_with($full . DIRECTORY_SEPARATOR, $base . DIRECTORY_SEPARATOR)`
- **Key anti-mitigation**: "ownership check does NOT mitigate — attacker owns their own row"
- **Verification**: plant `pdf_path = '../../../../etc/passwd'`, expect 404 empty body (NOT 200 with `root:x:0:0:`)

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all PHP stdlib — `Storage::disk()` trimmed by main loop)
- Line count delta: **+2** (inline paragraph in existing section — efficient)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: **+2** (near-zero-cost closure of a deferred gap)
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

**Verify notes**: *"Companion READ-traversal reflex names `readfile`
sink, historical-user-input DB column, ownership-bypass clause, and
`realpath` prefix defence — B1 triggers directly."*

**Full 1/1 post-edit. Twenty-first v4 targeted win. Closes iter-56 B2
deferred gap.**

## Decision: **edit_verified**

## Progress after 58 iters
- Verified targeted wins: **21**
- Bugs closed cumulatively via v4 verify: **28**
- Benchmark passes: 5
- Regressions: 0
- Deferred gaps closed via targeted follow-up: **3** (iter-27 B3 composite index → iter-29, iter-56 B2 path traversal → iter-58, iter-4/5 TOCTOU/cache/queue → iter-7)

## Final JSON
```json
{"iter":58,"mode":"free","score":9,"baseline":68,"action":"edit_verified","skill_md_lines":900,"skill_md_delta":2,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_closes_prior_deferred","spec_version":4}
```
