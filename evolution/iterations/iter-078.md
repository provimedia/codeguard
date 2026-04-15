# Iteration 078 — free mode (v4, noop — edit rejected on topical misfit)

**Attack agent**: general-purpose, model: opus
**Verify**: N/A (noop)
**Task title**: Password Reset Flow with Rate Limiting + Email Delivery

## Task
Vanilla PHP + MySQL password reset: `password_resets`/`rate_limits` tables,
`PasswordReset` model (sha256 token, 1h TTL, consumed_at gate), controller
with request/confirm, DB-backed `RateLimiter` keyed on
`HTTP_X_FORWARDED_FOR`, `Mailer` passing API key as `?key=`.

## Bugs planted (5)
- **B1** `X-Forwarded-For` trusted directly — rate-limit bypass via spoofed header.
- **B2** Mailer API key in URL query string (`?key=`) — P3 Secrets Hygiene violation.
- **B3** `password_hash(..., ['cost' => 8])` below modern minimum (≥12).
- **B4** `consume()` called AFTER password update, not atomic — double-submit race allows second reset to overwrite.
- **B5** `REPLACE INTO` in rate-limiter window reset — drops row locks, breaks FK cascades. Should be `INSERT ... ON DUPLICATE KEY UPDATE`. **TARGETED**

## Pre-edit simulation
Caught **4/5**. Missed **B5** — REPLACE INTO semantic trap is
database-engine specific and the skill has no dedicated SQL-primitive
smell list.

## Proposed edit (REJECTED)
Subagent proposed adding a new "SQL primitive smell list" paragraph
underneath the P3 Secrets Hygiene "?key= grep" reflex — +4 lines, covering
`REPLACE INTO`, `TRUNCATE inside txn`, `SELECT FOR UPDATE without txn`,
`ON DELETE SET NULL on NOT NULL FK`.

**Rejection rationale**:
1. **Topical misfit** — SQL primitive safety has zero conceptual connection
   to the P3 Secrets Hygiene section it was being placed under. A session
   running the P3 ?key= grep would not inherit the SQL primitive check.
2. **Scope creep** — the targeted miss is B5 (`REPLACE INTO`). Extending
   to 4 unrelated SQL primitives is content expansion beyond the targeted
   gap. Per v3 rule: new content must carry its weight and be tightly
   scoped to a real gap.
3. **+4 lines** after the iter-77 tightening (-2) would reverse the trend.
4. **Marginal value**: 4/5 pre-edit is already a strong catch rate; B5 is
   a niche MySQL-specific pitfall (REPLACE INTO is rarely used in modern
   code; most teams use ON DUPLICATE KEY UPDATE already).

## Deferred gap
**B5 — REPLACE INTO lock-drop / FK-cascade trap.** If revisited, the right
home is the Concurrency/TOCTOU section (extending the atomicity reflex
added in iter-74) or the Multi-Step Atomicity section — NOT the P3
Secrets Hygiene section. Candidate for a zero-cost inline extension in a
future iteration when the exact right anchor is identified.

## Decision: **noop**

- edit rejected on topical misfit + scope creep
- structure intact ✓
- consecutive_noops: 0 → 1

## Progress after 78 iters
- Verified targeted wins: 30
- Bugs closed cumulatively via v4 verify: 39
- Benchmark passes: 7
- Regressions: 0
- Noops: 2 (iter-75, iter-78)
- Line count: 903 (stable after iter-77 tightening)

## Final JSON
```json
{"iter":78,"mode":"free","score":0,"baseline":68,"action":"noop","skill_md_lines":903,"skill_md_delta":0,"pre_caught":4,"post_caught":null,"verify_delta":null,"verify_target_hit":null,"framework_tokens_in_edit":0,"spec_version":4,"edit_kind":"noop_topical_misfit","deferred_gap":"B5_replace_into_lock_drop","note":"subagent edit rejected on topical placement (P3 Secrets Hygiene is wrong home for SQL primitive safety) + scope creep (4 primitives for 1 targeted miss)"}
```
