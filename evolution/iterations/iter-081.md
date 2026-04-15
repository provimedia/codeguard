# Iteration 081 — free mode (v4, 32nd targeted win, zero-cost inline, closes iter-79 deferred gap)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Partner API — hand-rolled JWT bearer auth on /api/v1/partner/me

## Task
PHP + PDO/MySQL hand-rolled JWT verifier. `$alg = $header['alg'] ?? 'none'`,
switch accepts `alg=none` (no verify) and `HS256` while `$key` is an RSA
public key PEM. Endpoint also interpolates `$claims['sub']` directly into
SQL.

## Bugs planted (3)
- **B1** JWT verifier trusts header.alg — accepts `alg=none` AND `RS256`→`HS256` (HMACs signing input with public key as shared secret). Classic alg-confusion. **TARGETED** (closes iter-79 deferred gap)
- **B2** `$expected == $sig` non-constant-time compare — timing side channel.
- **B3** SQL injection via `"WHERE id = $sub"` interpolation. Combined with B1, forged token → SQLi primitive.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — Security layer enumerated auth-check presence
but had zero JWT-alg-pinning language. Structural audit sees `jwt_verify()`
called + returns null on failure and ticks "auth check present" as PASS.
P3 covers transport + constant-time but not algorithm pinning; Interface
Boundary Verification is scoped to signature matching, not trust boundaries.

## Proposed edit (inline, 0 line delta)
Extended the existing Security-layer "Missing auth checks?" bullet inline
with a JWT alg-pinning clause:

**"JWT/signed-token verifier pins algorithm to the key type on OUR side and
NEVER reads `alg` from the token header (`alg=none` skips verify,
`RS256`->`HS256` HMACs the signing input with the public key as the shared
secret — both forge any claim)?"**

- Topically correct ✓ (anchored on Security-layer auth-check bullet)
- `targeted_miss: "B1"`
- Framework tokens: **0** (JWT, HS256, RS256, HMAC, alg are RFC 7518
  protocol identifiers — not framework tokens per spec gate list)
- Line count delta: **0** (inline extension within existing bullet)

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

**Verify notes**: *"Security bullet now explicitly names alg=none skip and
RS256->HS256 public-key-as-HMAC confusion, giving auditor exact vocabulary
to flag jwt_verify() reading header.alg; SQLi and == compare caught
alongside."*

**Thirty-second v4 targeted win. Seventh zero-cost inline win. Closes
iter-79 deferred B1 gap.**

## Decision: **edit_verified**

## Progress after 81 iters
- Verified targeted wins: **32**
- Bugs closed cumulatively via v4 verify: **41**
- Benchmark passes: 8
- Regressions: 0
- Zero-cost inline wins: iter-63, 65, 71, 72, 74, 79, 81 (seven)
- Deferred gaps closed: iter-56→58 (path traversal), iter-71→72 (inbound datetime), iter-75→76 (BIGINT JSON precision), iter-79→81 (JWT alg-confusion) — **4-for-4 on deferred-gap follow-up**
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":81,"mode":"free","score":55,"baseline":68,"action":"edit_verified","skill_md_lines":903,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_closes_prior_deferred","spec_version":4}
```
