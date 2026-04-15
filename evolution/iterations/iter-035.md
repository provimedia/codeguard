# Iteration 035 — free mode (v4, tenth targeted win)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: PHP login endpoint — add remember-me + last_login_at

## Task (self-contained, plain PHP/PDO/native sessions)
Existing `login.php` does `password_verify` then `$_SESSION['user_id'] =
$user['id']`. Task: add `remember=1` cookie-lifetime extension and
`UPDATE users SET last_login_at = NOW()`. `bootstrap.php` has
`session.use_strict_mode = 0` (legacy php.ini).

## Bugs planted (1)
- **B1** Session fixation — no `session_regenerate_id(true)` between password verify and `$_SESSION['user_id']` write. Combined with `use_strict_mode=0`, attacker-planted PHPSESSID cookie survives the login and grants attacker the authenticated session. **TARGETED**.

## Pre-edit simulation
Caught **0/1**. Security layer listed SQLi / sensitive-fields / missing-auth /
mass-assign / rate-limit / IDOR — **nothing about session lifecycle**.
Auth Enforcement Parity (iter-25) covers who-can-call across entry points,
not the identity-rebinding step itself. The audit ticks every Security
bullet (the SQL uses prepared statements, password hashing is correct,
rate limiting is a separate concern) and approves.

## Proposed edit (trimmed from subagent's +50 to +27)
New Cross-Layer sub-section **"Session Lifecycle at Auth Boundaries
(fixation, privilege upgrade, cookie drift)"** inserted before Frontend
Reactivity Traps.

- **Principle**: authentication is an identity transition; every transition
  MUST rotate the session ID AND re-assert cookie attributes, OR the
  pre-transition session ID remains valid post-transition.
- **Distinct from Auth Enforcement Parity**: that reflex covers who-can-call
  across entry points; this covers the identity-rebinding step itself.
- **Three failure modes**:
  1. **Session fixation** — principal written into existing session without rotation; `use_strict_mode=0` enables it
  2. **Privilege upgrade without rotation** — role change, sudo mode, 2FA step-up needs same treatment
  3. **Cookie attribute drift** — setting `Secure`/`SameSite`/`HttpOnly`/lifetime AFTER session started doesn't apply to the current cookie; order must be: set params → rotate → write principal → send response
- **Four audit questions** on every session-state write after credential/role check
- **curl-based verification**: capture Set-Cookie pre-login + post-login, MUST differ

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (`$_SESSION`, `session_regenerate_id`, `session.use_strict_mode` are PHP stdlib; `Set-Cookie`, `Secure`, `HttpOnly`, `SameSite`, `Domain` are HTTP standard)
- Subagent originally included `request.session.cycle_key()` (Django) and
  `HttpSession.invalidate()` (Java servlet) — both framework-locked; main
  loop trimmed them out and kept only PHP as the single substrate example.
- Line count delta: **+27** (heavy; new coverage category)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count: +27 (heavy; justified by new general bug class with 3 failure modes + 4 audit questions + verification)
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

**Verify notes**: *"New Session Lifecycle reflex names fixation,
`use_strict_mode=0`, and prescribes `session_regenerate_id(true)` between
verify and principal-write — B1 caught and BLOCKED."*

**Full 1/1 post-edit. Tenth v4 targeted win.**

## Decision: **edit_verified**

## Progress after 35 iters
- Verified targeted wins: **10** (iters 13, 14, 18, 22, 23, 25, 27, 29, 32, 35)
- Bugs closed cumulatively via v4 verify: **12**
- Benchmark passes: 3
- Framework tokens stripped: ~95+ (net of additions)
- SKILL.md: 715 → 811 (+96 net across 35 iters, 10 new general bug categories)

## Final JSON
```json
{"iter":35,"mode":"free","score":0,"baseline":68,"action":"edit_verified","skill_md_lines":811,"skill_md_delta":27,"pre_caught":0,"post_caught":1,"verify_delta":1,"verify_target_hit":true,"framework_tokens_in_edit":0,"edit_kind":"bug_fix_targeted","spec_version":4}
```
