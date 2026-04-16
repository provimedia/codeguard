# Iteration 093 — free mode (v4, 42nd targeted win, zero-cost inline)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Supplier XML product feed importer (PHP + MySQL)

## Task
Admin-only `/import_feed.php` reads uploaded XML via
`file_get_contents($_FILES['feed']['tmp_name'])` and parses with
`new DOMDocument(); $doc->loadXML($xml_raw)`, then iterates `//product`
nodes and upserts into `products`. Price path does
`(int) round(((float)$price) * 100)`.

## Bugs planted (3)
- **B1** XXE via `DOMDocument::loadXML` — no `LIBXML_NONET`, no entity-loader disable, no DTD rejection. Attacker XML reads local files via SYSTEM entities + SSRF via external entities + billion-laughs DoS. **TARGETED**
- **B2** `(float)"1.234,56"` yields `1.234` (locale-independent, cuts at first non-numeric) → €1,234.56 stored as 1 cent.
- **B3** No cap on uploaded XML bytes / nested depth → billion-laughs DoS.

## Pre-edit simulation
Caught **1/3** (B3 via existing Input Size & Complexity Limits reflex).
Missed B1 — skill had no XXE / libxml / DOMDocument reflex despite XXE
being on the open-candidate-gap list for most of the run.

## Proposed edit (inline, 0 line delta)
Extended the Security-layer PHP sink enumeration (added in iter-92) with
an XXE clause naming the exact PHP parser sink set and the exact fix set:

**"`DOMDocument::loadXML`/`simplexml_load_string`/`simplexml_load_file`/
`XMLReader::xml` on any caller-shaped byte is XXE (external-entity
file-read + SSRF via `SYSTEM` entities, and billion-laughs DoS via nested
internal entities), fix: parse with `LIBXML_NONET | LIBXML_DTDLOAD`
suppressed (pass `LIBXML_NONET` and NEVER `LIBXML_NOENT`, and on PHP <8
call `libxml_disable_entity_loader(true)` around the parse), reject
documents whose `$doc->doctype !== null` unless a fixed schema is
required, and cap the input bytes BEFORE parse?"**

- Topically correct ✓ (same Security-layer inventory as iter-92's
  unserialize/include/shell_exec/eval — all "unsafe PHP sinks on untrusted
  input")
- `targeted_miss: "B1"`
- Framework tokens: **0** (libxml, DOMDocument, simplexml, XMLReader are
  PHP stdlib, not framework classes)
- Line count delta: **0** (inline extension within existing long line)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("no safe wrapper exists? Mass assignment" matched once) ✓
- generality: 0 framework tokens ✓
- line-count: **0** (zero-cost inline) ✓
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 1
post_caught:                2
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [B2 locale float parse]
forbidden_phrases_count:    0
```

**Verify notes**: *"Post-edit Security line explicitly names
`DOMDocument::loadXML` as XXE+billion-laughs sink with concrete fix
(LIBXML_NONET, entity-loader disable, doctype reject, cap bytes
pre-parse); B1 and B3 now both catchable from one reflex; B2 locale-parse
still unaddressed."*

**Forty-second v4 targeted win. Fourteenth zero-cost inline win.
Security-layer sink inventory now covers 5 classes: unserialize /
include / shell_exec / eval / XXE.**

## Decision: **edit_verified**

## Deferred gap (B2 locale parse)
Locale-dependent `(float)` / `floatval` / `number_format` on
caller-shaped numeric input. PHP cast is C-locale; European-format
`1.234,56` silently truncates to `1.234`. No reflex anywhere in the
skill. Candidate future iter target.

## Progress after 93 iters
- Verified targeted wins: **42**
- Bugs closed cumulatively via v4 verify: **51**
- Benchmark passes: 9
- Regressions: 0
- Zero-cost inline wins: **14**
- Deferred gaps closed: 7-for-7
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":93,"mode":"free","score":55,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":0,"pre_caught":1,"post_caught":2,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_xxe_sink","spec_version":4,"deferred_gap":"B2_locale_float_parse"}
```
