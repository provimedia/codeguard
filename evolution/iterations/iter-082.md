# Iteration 082 — free mode (v4, 33rd targeted win, zero-cost inline)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Document vault — share-by-token download + admin PIN override

## Task
PHP + MySQL document vault. `verify_admin.php` does `md5($pin) == $row['pin_hash']`,
`share_download.php` has an inverted `if (!$row['is_public']) { /* allow */ }`
dead branch, `shares.php` renders titles via `innerHTML` concatenation with
only Cache-Control/Vary (no CSP).

## Bugs planted (3)
- **B1** `md5($pin) == $row['pin_hash']` — PHP `==` type-juggling: two strings matching `^0+e\d+$` compare as `0.0 == 0.0` → auth bypass. Also wrong-algorithm md5 vs bcrypt column. **TARGETED**
- **B2** Inverted permission logic `if (!$row['is_public']) { /* allow */ }` dead branch + no re-validation of current public/ownership state (permission TOCTOU).
- **B3** `innerHTML` XSS sink + no `Content-Security-Policy` header for defense-in-depth on an authenticated page.

## Pre-edit simulation
Caught **1/3**. Missed B1 (type-juggling) and B3 (CSP defense-in-depth).
B2 dead-branch caught by logic layer. Line 94's `==` prohibition was scoped
only to webhook signatures — reader didn't transfer the rule to PIN/bcrypt
equality in non-webhook paths.

## Proposed edit (inline, 0 line delta)
Extended line 94's existing forbidden-operator clause so the `==` prohibition
applies to **ANY** secret/hash/PIN/token compare (not just webhook signatures)
AND explicitly names the `^0+e\d+$` type-juggling trap:

**"...same rule for ANY secret/hash/PIN/token equality — `==` type-juggles
two strings matching `^0+e\d+$` to the float `0.0 == 0.0`, so bcrypt hashes,
md5 hashes, PINs and API keys MUST use `hash_equals` (or `password_verify`
for bcrypt), never `==`/`===`)."**

- Topically correct ✓ (extends the only existing home for equality-operator rules)
- `targeted_miss: "B1"`
- Framework tokens: **0** (hash_equals/password_verify are PHP stdlib)
- Line count delta: **0** (inline extension within same bullet)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
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
post_missed:                [B3 CSP defense-in-depth]
forbidden_phrases_count:    0
```

**Verify notes**: *"Line 94 generalization to ANY secret/hash/PIN/token
compare with explicit `0e`-prefix trap directly matches
`md5($pin)==$row['pin_hash']`; B2 dead-branch caught by logic layer;
B3 CSP half still outside checklist."*

**Thirty-third v4 targeted win. Eighth zero-cost inline win.**

## Decision: **edit_verified**

## Deferred gap (B3 CSP)
**CSP / security-response-header defense-in-depth on authenticated HTML
pages.** HTTP Response Cacheability reflex covers Cache-Control / Vary /
Pragma but stops short of CSP / X-Content-Type-Options / Referrer-Policy /
Permissions-Policy. Candidate for a zero-cost inline extension to the
Cacheability section in a later iter.

## Progress after 82 iters
- Verified targeted wins: **33**
- Bugs closed cumulatively via v4 verify: **42**
- Benchmark passes: 8
- Regressions: 0
- Zero-cost inline wins: 8 (iter-63, 65, 71, 72, 74, 79, 81, 82)
- Deferred gaps closed: 4-for-4 (iter-56→58, iter-71→72, iter-75→76, iter-79→81)
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":82,"mode":"free","score":62,"baseline":68,"action":"edit_verified","skill_md_lines":903,"skill_md_delta":0,"pre_caught":1,"post_caught":2,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_generalize_equality_rule","spec_version":4,"deferred_gap":"B3_csp_defense_in_depth"}
```
