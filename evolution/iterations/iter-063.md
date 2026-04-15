# Iteration 063 — free mode (v4, 23rd targeted win, zero-cost)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: 2FA OTP rate limit keyed to attacker-controlled session_id()

## Task
PHP/MySQL 2FA OTP endpoint. Rate-limit bucket = `'otp:' . session_id()`.
5-attempt cap per 10 minutes enforced via DB transaction + FOR UPDATE.
After 5 failures, attacker drops PHPSESSID cookie, re-enters 2FA step
(password already known — this is the 2FA step), gets fresh 5-attempt
bucket. Unlimited 6-digit OTP guesses.

## Bugs planted (1)
- **B1** Rate-limit bucket keyed to `session_id()` — attacker rotates the key by dropping the cookie. Must key by `pending_user_id` (stable identity being protected). **TARGETED**

## Pre-edit simulation
Caught **0/1**. Security bullet only asked "missing rate limiting on
auth endpoints?" — rate limit is PRESENT here, just keyed wrong.
No reflex asked "is the bucket key attacker-rotatable?".

## Proposed edit (zero-cost inline extension)
Extended the Security bullet in Step 3d with a "Rate-limit key scope"
clause asking whether the bucket key is the stable identity being
protected OR something the caller can rotate (`session_id`, raw
submitted email, anonymous cookie, request ID, `X-Forwarded-For`).
Explicit pre-auth-flow callout: OTP verify / password reset /
signup confirm must key by the PENDING identity, not the session.

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (all HTTP/PHP stdlib generic)
- **Line count delta: 0** (inline extension of existing bullet — zero-cost)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: **0** (zero-cost new coverage) ✓
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

**Verify notes**: *"Security layer now names `session_id` as
attacker-rotatable and explicitly calls out OTP verify pre-auth flows
must key by pending identity — direct textual match."*

**Full 1/1 post-edit. Twenty-third v4 targeted win, zero line cost.**

## Decision: **edit_verified**

## Progress after 63 iters
- Verified targeted wins: **23**
- Bugs closed cumulatively via v4 verify: **30**
- Benchmark passes: 6
- Regressions: 0

## Final JSON
```json
{"iter":63,"mode":"free","score":7,"baseline":68,"action":"edit_verified","skill_md_lines":897,"skill_md_delta":0,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted_zero_cost","spec_version":4}
```
