# Iteration 027 — free mode (v4, targeted win +2)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Paid-subscribers KPI widget

## Task (self-contained, PHP/MySQL)
Admin dashboard KPI showing active users + paid subscribers via PDO query.
`users.stripe_customer_id` is nullable. Draft uses
`COUNT(DISTINCT u.stripe_customer_id)` + `LEFT JOIN payments p ON ... WHERE p.status = 'succeeded'`.

## Bugs planted (3)
- **B1** `COUNT(DISTINCT stripe_customer_id)` silently drops users with NULL — paid users without backfilled Stripe IDs are uncounted. Fix: `COUNT(DISTINCT u.id)`. **TARGETED**
- **B2** `LEFT JOIN payments p ... WHERE p.status = 'succeeded'` is INNER in disguise — the WHERE filters NULL rows the LEFT JOIN produced
- **B3** Composite index `(user_id, status)` — column-order vs filter mismatch

## Pre-edit simulation
Caught **0/3**. SKILL.md had no reflex for:
- COUNT(col) vs COUNT(*) on nullable columns (P2 aggregate trap covers SCAN COST, not CORRECTNESS)
- LEFT JOIN → INNER degradation when WHERE references right-side
- Composite index column-order mismatch

Auditor reads the SQL, sees `COUNT(DISTINCT)`, assumes it "deduplicates correctly" → approve. Staging numbers "look reasonable" because low-NULL data hides it.

## Proposed edit (trimmed from subagent's +40 to +12)
New Cross-Layer sub-section **"NULL Semantics in Aggregation"** inserted after
Timezone/Date-Boundary Sanity, before Self-Tuning. Names **four traps**:

1. `COUNT(col)` / `COUNT(DISTINCT col)` ignore NULL — prefer `COUNT(DISTINCT pk)` when intent is "how many distinct entities"
2. `SUM`/`AVG` over empty set = NULL (not 0) → downstream arithmetic silently wrong or throws; wrap with `COALESCE`
3. `AVG(col)` ignores NULL in both numerator and denominator — explicit fix: `SUM(COALESCE(col, 0)) / COUNT(*)`
4. `LEFT JOIN p ON ... WHERE p.X = ?` silently degrades to INNER — move predicate into ON clause

**Audit reflex**: for every `COUNT/SUM/AVG/MIN/MAX`, check `IS_NULLABLE` from Pre-Flight schema introspection; say NULL-exclusion intent out loud. For every LEFT JOIN, grep WHERE for right-side column references.

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all SQL standard: COUNT, SUM, AVG, LEFT JOIN, INNER JOIN, WHERE, ON, COALESCE, IS_NULLABLE)
- Line count delta: **+12** (subagent proposed +40)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +12 (moderate; new coverage category with 4 distinct correctness traps)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 0
post_caught:                2
delta:                      +2
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [B3 composite-index column-order — not targeted]
forbidden_phrases_count:    0
```

**Verify notes**: *"New NULL Semantics sub-section directly names
`COUNT(DISTINCT nullable-col)` and `LEFT JOIN → INNER WHERE-degradation` —
B1 and B2 land as explicit audit reflexes; B3 still lacks a dedicated
composite-index-order check."*

**2/3 post-edit, delta +2. Seventh v4 targeted win.**

B3 (composite index column order mismatch) is a candidate for a future iter
— distinct bug class from "missing index", needs a dedicated reflex.

## Decision: **edit_verified**

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
13    726    0      edit_verified      +1            money-FLOAT ✓
14    738    +12    edit_verified      +1            timezone ✓
18    760    +16    edit_verified      +1            saga ✓
22    762    +2     edit_verified      +1            FOR-UPDATE-autocommit ✓
23    779    +17    edit_verified      +2            deep offset + page cap ✓✓
25    787    +15    edit_verified      +1            auth parity ✓
27    794    +12    edit_verified      +2            NULL aggr + LEFT JOIN degrade ✓✓
7 targeted wins, 9 bugs closed cumulatively, 0 regressions
```

## Final JSON
```json
{"iter":27,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":794,"skill_md_delta":12,"pre_caught":0,"post_caught":2,"verify_delta":2,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_double_hit","spec_version":4}
```
