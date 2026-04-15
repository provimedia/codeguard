# Iteration 074 — free mode (v4, 29th targeted win, zero-cost inline)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Sequential invoice-number generator + PDF handler for B2B billing portal

## Task
PHP 8.2 + MySQL 8 B2B billing portal. `InvoiceNumberService::next()` mints per-tenant
invoice numbers via SELECT-MAX; `CreateInvoiceHandler` INSERTs then renders PDF
then UPDATEs pdf_path; `ReissueInvoiceCommand` concatenates `$oldId` into raw SQL
and bypasses web route auth; `PdfRenderer::render()` fopen→throw→fclose leak.

## Bugs planted (3)
- **B1** Uniqueness race: SELECT-MAX + INSERT with no UNIQUE index on (tenant_id, invoice_no). Two concurrent callers see same max and both INSERT. Transaction alone doesn't help under REPEATABLE READ. **TARGETED**
- **B2** SQLi via raw `'WHERE id='.$oldId` AND CLI entry point has no auth parity with web `requireTenantAdmin`.
- **B3** Multi-step side-effect saga (INSERT→render→UPDATE) leaves orphan `status='issued'` rows on PDF failure. Compound: PdfRenderer fopen/throw/fclose leaks fh.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — Concurrency/TOCTOU reflex was counter-mutation-framed
("for every counter mutation in the diff, name the atomicity mechanism"). A
business-key uniqueness race has the same shape (read-then-write under
concurrency) but the reader scans for "counter mutation" and "FOR UPDATE"
keywords; SELECT-MAX + plain INSERT doesn't match either template.

## Proposed edit (inline, 0 line delta)
Extended the TOCTOU atomicity reflex inline with a business-key clause:

**"Same reflex for business-key uniqueness (invoice number, slug, SKU,
external reference, tenant-scoped sequence): SELECT-MAX / SELECT-by-key
followed by INSERT is a race unless a `UNIQUE` index on the key catches
the collision AND the handler catches the duplicate-key error and retries
— the SELECT alone proves nothing, both concurrent callers see the same
max and both INSERT. Wrapping in a transaction does NOT help: under InnoDB
REPEATABLE READ the SELECT is a consistent snapshot and the INSERT has
nothing to collide with at the row level."**

- `targeted_miss: "B1"`
- Framework tokens: **0** (InnoDB, REPEATABLE READ, SELECT-MAX are DB standards)
- Line count delta: **0** (inline extension)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("for every counter mutation in the diff") ✓
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

**Verify notes**: *"Concurrency/TOCTOU reflex now explicitly enumerates
business-key uniqueness with SELECT-MAX+INSERT race and UNIQUE-index
requirement — B1 matches the lexical pattern and fires; B2 (SQLi+auth
parity) and B3 (saga+fh leak) caught by existing reflexes."*

**Twenty-ninth v4 targeted win. Third consecutive zero-cost inline win.**

## Decision: **edit_verified**

## Progress after 74 iters
- Verified targeted wins: **29**
- Bugs closed cumulatively via v4 verify: **38**
- Benchmark passes: 7
- Regressions: 0
- Zero-cost inline wins: iter-63, iter-65, iter-71, iter-72, iter-74 (five)
- 3-iter streak of zero-cost reflex extensions (iter-71, 72, 74) — pattern
  holds: extend existing reflex scope rather than add new sections

## Final JSON
```json
{"iter":74,"mode":"free","score":67,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_reflex_extension","spec_version":4}
```
