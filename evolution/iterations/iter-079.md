# Iteration 079 — free mode (v4, 31st targeted win, zero-cost inline)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Partner API — JWT login + HMAC webhook ingest + pre-auth rate limiter

## Task
PHP + MySQL PDO partner API. JWT verifier accepts `alg=none` back-compat;
webhook ingest compares HMAC via `strcmp()`; rate limiter keyed to raw
`X-Forwarded-For`.

## Bugs planted (3)
- **B1** JWT verifier accepts `alg=none` — forged `sub=any_partner_id`.
- **B2** Webhook sig `strcmp($sig, $expected)` — non-constant-time, leaks prefix via timing side channel. Must use `hash_equals`. **TARGETED**
- **B3** Rate limiter keyed to raw `X-Forwarded-For`.

## Pre-edit simulation
Caught **2/3**. Missed **B2** — P3 said "constant-time equality function"
but did not name the PHP anti-patterns (`strcmp`/`==`/`===`) that reviewers
actually see in diffs. `grep strcmp SKILL.md` returned zero hits, so the
spot-check reviewer had nothing to match against.

## Proposed edit (inline, 0 line delta, topically correct)
Extended the existing P3 inbound-webhook bullet inline with PHP anti-patterns:

**"Inbound webhooks: signature in a header, compared with a constant-time
equality function (PHP: `hash_equals`, never `==`/`===`/`strcmp`/`strncmp`
— non-constant-time compare leaks prefix bytes via response-time side
channel)."**

- Topical placement ✓ (anchored on the constant-time bullet in P3, not
  shoehorned into an unrelated section as iter-78 was)
- `targeted_miss: "B2"`
- Framework tokens: **0** (hash_equals/strcmp/strncmp are language stdlib,
  not framework)
- Line count delta: **0** (inline extension to existing bullet)

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
targeted_miss:              B2
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"Line 94 names hash_equals vs strcmp/strncmp/==/===
explicitly; grep for strcmp in webhook_ingest.php hits, B2 recovered.
B3 already covered by line 314 X-Forwarded-For reflex; B1 relies on general
hand-rolled-crypto scrutiny."*

**Thirty-first v4 targeted win.** Sixth zero-cost inline win.

## Decision: **edit_verified**

## Deferred gap (B1 — future iter target)
JWT alg=none / alg-confusion reflex. Currently no explicit reflex; relies
on general hand-rolled-crypto scrutiny. Candidate for a zero-cost inline
extension attached to the Interface Boundary Verification section or the
P3 "Outbound HTTP / crypto primitives" area in a later iter.

## Progress after 79 iters
- Verified targeted wins: **31**
- Bugs closed cumulatively via v4 verify: **40** 🎉
- Benchmark passes: 7
- Regressions: 0
- Zero-cost inline wins: iter-63, 65, 71, 72, 74, 79 (six)
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":79,"mode":"free","score":68,"baseline":68,"action":"edit_verified","skill_md_lines":903,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost","spec_version":4}
```
