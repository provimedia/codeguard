# Iteration 090 — benchmark mode (fixture-03, cycle 3, 90% milestone)

**Agent**: general-purpose, model: opus
**Fixture**: fixture-03.md (Debug mobile logout — same_site=strict)
**Minimum expected**: 2 / 3
**Result**: **3 / 3 bugs caught, 0 forbidden phrases — PASSED**

## Bugs caught
- **B1** `same_site=strict` root cause — named explicitly, verified via `git log -p config/session.php` + `grep same_site`
- **B2** P5 pattern-copy risk — explicit guard against lifting SameSite from sibling project
- **B3** Verification discipline — hypothesis formed first, `git log -p` / `grep` run before any edit

## Anti-patterns avoided
- No session-lifetime extension
- No token-refresh shim
- No SecurityHeaders middleware revert (red herring)
- No sibling-project config copy
- Hypothesis-before-edit discipline upheld

## Two-path fix demonstrated
- **Minimal**: `same_site => 'lax'` (one-line revert of that specific hunk)
- **Structural**: keep lax + audit CSRF `$except` list + document decision + add regression test

## Trend
- Fixture-03 history: iter-30 (initial run), iter-60 (caught 3/3), iter-90 (**3/3 clean sweep**)
- Zero regressions across 89 edits since iter-1
- Benchmark passes cumulative: **9**

## 90% milestone snapshot
- Verified targeted wins: 39
- Bugs closed cumulatively via v4 verify: 48
- Tightening/dedup edits: ~15
- Benchmark passes: 9 (3x fixture-01, 3x fixture-02, 3x fixture-03 — full cycle)
- Regressions: 0
- Noops: 2 (iter-75, iter-78)
- Line count: 904 (-4 net from iter-10 peak of 908)

## No SKILL.md change (benchmark mode = pure regression test)

## Final JSON
```json
{"iter":90,"mode":"benchmark","fixture":"fixture-03.md","bugs_planted":3,"bugs_caught":3,"forbidden_phrases_count":0,"fixture_min_expected":2,"passed_threshold":true,"score":3,"skill_md_lines":904,"skill_md_delta":0,"spec_version":4,"milestone":"90_percent","note":"Clean sweep on fixture-03; 9th benchmark pass; completes third full cycle across all three fixtures."}
```
