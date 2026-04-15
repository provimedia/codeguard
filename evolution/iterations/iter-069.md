# Iteration 069 — free mode (v4, generalization, +1 line)

**Attack agent**: general-purpose, model: opus (returned clean v4 contract this time)
**Verify agent**: general-purpose, model: opus
**Task title**: Document-share service — revoke doesn't stick + POST share endpoint

## Task
PHP + MySQL document-share service with `DocumentAccess::canRead()` caching
permission lookup for 300s. Revoke controller and ExpireShares command both
mutate `document_shares` rows without flushing the permission cache.
Simultaneously the share endpoint needs to be implemented: no auth/ownership
check, mail-service key passed in query string, Blade exposes share as
`<a href>` GET link with email in querystring.

## Bugs planted (4)
- **B1** Permission cache not invalidated on revoke/expire — `docperm:{user}:{doc}` retained 300s after revoke. **The reported bug.**
- **B2** `Http::post('https://mail.internal/send?key=' . config(...))` leaks mail-service key into logs/Referer.
- **B3** `DocumentController::share` has no ownership check — any authenticated user can share any document.
- **B4** Blade `<a href=".../share?email=...">` is a GET link to a state-changing endpoint; zero-click CSRF if route is later widened.

## Pre-edit simulation
Caught **4/4**. The skill already covers all four classes:
- B1 → Cache Invalidation Coverage + iter-68 row-mutation list-drift sub-section
- B2 → P3 Secrets Hygiene `?key=` grep reflex
- B3 → Auth Enforcement Parity Across Entry Points
- B4 → HTTP Verb Safety for State-Changing Requests

## Friction observed
DEBUG MODE Phase 5 ("IMPLEMENT + VERIFY") ends on a soft bullet *"Confirm:
original bug gone, edge cases handled, dependencies intact"*. A debug-mode
fix is itself a code change and must pass the BUILD MODE 7-point audit, but
the skill never says so inline. Risk: sessions that enter DEBUG MODE can
skip the audit on the fix once the symptom is gone.

## Proposed edit (+1 line, zero framework tokens)
One new step appended to DEBUG MODE Phase 5:

```
5. Run the BUILD MODE Audit (3a-3g) on the fix diff — a fix is a code change
   and gets the same 7-point audit as any other change, no exceptions
```

- `targeted_miss: null` (pure generalization, no bug miss to address)
- Framework tokens in new_string: **0**
- Line count delta: **+1**

## Gate checks (v4)
- edit != null ✓
- old_string unique (line 440) ✓
- generality: 0 framework tokens ✓
- line-count: +1 (near-zero-cost)
- structure intact (code-guardian name + PLAN MODE v5 header both present) ✓

## **v4 — POST-EDIT VERIFY**

```
pre_caught:                 4
post_caught:                4
delta:                      0
targeted_miss:              null (pure generalization)
targeted_miss_now_caught:   null
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"Pre-edit sim was already optimal (4/4); edit is pure
generalization, no delta on this attack. Cache Invalidation Coverage,
P3 Secrets Hygiene, Auth Enforcement Parity, and HTTP Verb Safety all
directly name these bug classes."*

**Generalization edit: keep. Closes a long-standing cross-mode handoff gap
between DEBUG and BUILD mode.**

## Decision: **edit_generalize**

## Progress after 69 iters
- Verified targeted wins: **26**
- Generalization/tightening edits: **accumulating**
- Bugs closed cumulatively via v4 verify: **35**
- Benchmark passes: 6
- Regressions: 0

## Final JSON
```json
{"iter":69,"mode":"free","score":4,"baseline":68,"action":"edit_generalize","skill_md_lines":904,"skill_md_delta":1,"pre_caught":4,"post_caught":4,"verify_delta":0,"verify_target_hit":null,"framework_tokens_in_edit":0,"edit_kind":"cross_mode_handoff","spec_version":4}
```
