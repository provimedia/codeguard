# Iteration 020 — BENCHMARK mode (fixture-02)

**Agent**: general-purpose, model: opus
**Fixture**: fixture-02.md — "Admin API key check (secrets + config:cache + routing)"
**Mode**: pure regression test (no edit proposal)

## Purpose
Second benchmark iter. Validates that all the generalization/tightening/new-coverage
edits from iter-11 through iter-19 did NOT regress the skill's ability to catch
the canonical P3/P4/routing/scale scenario.

Edits since iter-10 under test:
- iter-11: N+1 bullet dropped Http::pool token
- iter-12: P3 Secrets Hygiene generalized (Guzzle/Nginx/Apache/$request->header/URL::temporarySignedRoute stripped)
- iter-13: money-as-FLOAT rule added to DB Integrity (verified win)
- iter-14: Timezone/Date-Boundary Sanity sub-section added (verified win)
- iter-15: P1 anecdote compressed (Vue token dropped)
- iter-16: Input Size & Complexity Limits (DoS budget) new section
- iter-17: P2 Critical Laravel gotcha block tightened (-11 lines)
- iter-18: Multi-Step Side-Effect Atomicity sub-section added (verified win)
- iter-19: P5 + P6 anecdotes compressed

## Simulation outcome
| # | Bug (planted) | Trigger fired | Caught? |
|---|---|---|---|
| 1 | `?key={key}` in URL route + `$request->query('key')` | P3 Secrets Hygiene grep (`?key=` / `?api_key=`) | ✓ |
| 2 | `env('ADMIN_API_KEY')` in controller | P4 config:cache Safety grep (`env(`) | ✓ |
| 3 | Invalid route syntax `?key={key}` as path → 404 | P3 grep collides + routing/interface boundary check | ✓ |
| 4 | `Order::sum('total')` on all orders, no date range, no cache | P2/audit-2 scale reflex (borderline — skill frames P2 around iteration primitives, but aggregate still gets caught) | ✓ |

**Bugs caught: 4 / 4**
**Forbidden phrases: 0**
**Fixture minimum expected: 3**
**Threshold passed: YES (4 >= 3)**

## Gate decision: **benchmark_pass**
- SKILL.md unchanged
- `last_good_commit` unchanged
- `consecutive_noops` unchanged (benchmark iters don't count)

## Notes
- Bug 4 (unbounded aggregate) was flagged as borderline by the verify
  subagent — the P2 section is oriented around row iteration primitives
  (get/cursor/lazy-by-id) rather than pure aggregates. Could be sharpened
  in a future iter, but currently it still catches via "general scale
  concern" reasoning. Not a regression, a clarity opportunity.
- All 9 edits since iter-10 passed this regression check without degrading
  fixture-02 catch-rate. The skill's principles travel across the
  generalization rounds.

## Final JSON
```json
{"iter":20,"mode":"benchmark","fixture":"fixture-02.md","bugs_planted":4,"bugs_caught":4,"bugs_missed":0,"forbidden_phrases_count":0,"fixture_min_expected":3,"passed_threshold":true,"score":4,"action":"benchmark_pass","skill_md_lines":753}
```
