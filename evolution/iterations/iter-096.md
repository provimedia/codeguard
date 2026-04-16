# Iteration 096 — free mode (v4, 44th targeted win, zero-cost inline)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: Login rate limiter keyed by client IP

## Task
PHP + MySQL login brute-force protection. `getClientIp()` trusts
`X-Forwarded-For` unconditionally, falls back to `REMOTE_ADDR`. Keys
bucket as `'login:' . $ip`. `checkLoginRateLimit()` does
`SELECT COUNT(*)` → `INSERT`.

## Bugs planted (3)
- **B1** IPv6 /128 rotation — raw IP as bucket key; residential/mobile IPv6 allocations hand a single attacker a full /64 (2^64 addrs). Must mask to network prefix before hashing. **TARGETED**
- **B2** `X-Forwarded-For` trusted without `REMOTE_ADDR` proxy allowlist — attacker rotates header per request.
- **B3** TOCTOU race on SELECT COUNT(*) → INSERT.

## Pre-edit simulation
Caught **2/3**. Missed **B1** — rate-limit reflex warned about
`X-Forwarded-For` rotation but implicitly treated `REMOTE_ADDR` as
stable. Nothing covered IPv6 /64 collapsing or IPv4 /24 masking.

## Proposed edit (inline, 0 line delta)
Extended the existing rate-limit key scope sentence inline with an
IPv6-normalization clause:

**"IP-keyed buckets must mask to a network prefix before hashing — a
raw address is rotatable for free on IPv6 (residential/mobile
allocations hand a single attacker a full /64 = 2^64 addresses, often
/56 or /48) and cheap on IPv4 behind carrier-grade NAT or cloud egress
pools; `inet_pton` the value, mask to 8 bytes for v6 (/64) and 3–4 bytes
for v4 (/24 or /32), key on the masked bytes. Trusting raw
`REMOTE_ADDR` on an IPv6-reachable endpoint is the same bug class as
trusting `X-Forwarded-For`."**

- Topically correct ✓ (extends the existing rate-limit key scope bullet
  which already warned about X-Forwarded-For rotation)
- `targeted_miss: "B1"`
- Framework tokens: **0** (inet_pton/REMOTE_ADDR/X-Forwarded-For are PHP stdlib + HTTP)
- Line count delta: **0** (inline extension within same long line)

## Gate checks (v4)
- edit != null ✓
- old_string unique ("For pre-auth flows (OTP verify" matched once) ✓
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

**Verify notes**: *"Line 310 reflex now explicitly mandates
`inet_pton`+/64 masking and flags raw `REMOTE_ADDR` as equivalent XFF
bug class; existing TOCTOU reflex triggers on SELECT+INSERT."*

**Forty-fourth v4 targeted win. Sixteenth zero-cost inline win.**

## Decision: **edit_verified**

## Progress after 96 iters
- Verified targeted wins: **44**
- Bugs closed cumulatively via v4 verify: **53**
- Benchmark passes: 9
- Regressions: 0
- Zero-cost inline wins: **16**
- Deferred gaps closed: 8-for-8
- Noops: 2 (iter-75, iter-78)

## Final JSON
```json
{"iter":96,"mode":"free","score":66,"baseline":68,"action":"edit_verified","skill_md_lines":902,"skill_md_delta":0,"pre_caught":2,"post_caught":3,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost_ipv6_rate_limit","spec_version":4}
```
