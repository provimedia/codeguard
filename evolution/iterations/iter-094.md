# Iteration 094 — free mode (v4, 43rd targeted win, zero-cost inline, closes iter-93 deferred gap)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Import supplier CSV prices into products table (German ERP, European numeric format)

## Task
PHP ingestion script for a German ERP CSV with `"1.234,56"` / `"12,750"`
format. Casts via `(float)` / `floatval()` into `DECIMAL(10,2)` and
`DECIMAL(8,3)` columns. Operator reports sum ~EUR 5 instead of EUR 45,000.

## Bugs planted (3)
- **B1** `(float)"1.234,56"` → `1.234`; `floatval("12,750")` → `12.0`. PHP cast is C-locale, stops at first non-numeric byte. 1000x undervalue on every row. **TARGETED** (closes iter-93 deferred gap)
- **B2** CSV header BOM / ragged-row hygiene — `$rec['Artikel']` null on UTF-8 BOM; no length check before `array_combine`.
- **B3** `PriceFormatter::euro(float $value)` typed-float param for money reintroduces binary-float rounding at display boundary.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — money bullet in DB Integrity only
covered STORAGE (cents / DECIMAL / FLOAT ban). The upstream string→float
coercion step was unguarded. Auditor flagged the display-side float but
not the parse-side `(float) $rec['Preis']` which is where the actual
1000x corruption happens.

## Proposed edit (inline, 0 line delta, closes iter-93 deferred gap)
Extended the money bullet inline with a locale-dependent parse trap
clause and a grep reflex:

**"Locale-dependent parse trap: `(float)`/`floatval()`/`(int)` are
C-locale and stop at the first non-numeric byte — `"1.234,56"` → `1.234`
(1000x undervalue), `"1,234.56"` → `1.0`, `"12,750"` kg → `12.0`; parse
money/quantity strings with a locale-aware normalizer (strip thousands
sep, replace decimal comma, validate with regex) BEFORE cast, or reject
the input. Grep the diff for `(float)` / `floatval(` / `(int)` applied
to ANY string from CSV/JSON/form/API/DB-text-column and prove a prior
normalization step."**

- Topically correct ✓ (anchored on DB Integrity money bullet that owns
  the entire money data path — now covers parse AND storage)
- `targeted_miss: "B1"`
- Framework tokens: **0** (`floatval`, `(float)`, `(int)` are PHP casts, not framework)
- Line count delta: **0** (inline extension within existing bullet)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("Money/currency stored as integer minor units" matched once) ✓
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

**Verify notes**: *"Post-edit DB Integrity bullet spells out
`(float)"1.234,56"→1.234` exactly and adds grep-diff-for-`(float)`-on-CSV
reflex; B1 is now a forced catch, B3 flagged by NEVER-FLOAT money rule +
string-cast grep, B2 picked up via Logic-layer null-edge scrutiny on
array_combine."*

**Forty-third v4 targeted win. Fifteenth zero-cost inline win. Closes
iter-93 deferred B2 locale parse gap. Money data path now covered
end-to-end (parse + storage + display).**

## Decision: **edit_verified**

## Progress after 94 iters
- Verified targeted wins: **43**
- Bugs closed cumulatively via v4 verify: **52**
- Benchmark passes: 9
- Regressions: 0
- Zero-cost inline wins: **15**
- Deferred gaps closed: **8-for-8** (iter-56→58, 71→72, 75→76, 79→81, 82→83, 87→88, 89→91, 93→94)
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":94,"mode":"free","score":67,"baseline":68,"action":"edit_verified","skill_md_lines":904,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_closes_prior_deferred","spec_version":4}
```
