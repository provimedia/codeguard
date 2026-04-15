# Code Guardian Evolution Loop — Iteration Runner (v2)

This file is executed by a Claude Code session fired by cron every 3 minutes.
Each run = one iteration of the skill's self-improvement loop.

## What changed in v2
- **Score-based gate removed.** The old rule `score >= baseline` blocked legitimate
  edits on harder tasks (iters 4–5 missed TOCTOU / cache / queue gaps but couldn't
  land fixes because their raw score was below baseline). Score is now **logged,
  not gated**.
- **Structural gate only** for free mode: edit must exist, old_string must be
  unique, post-edit structure must still parse (frontmatter + PLAN MODE marker).
- **Benchmark mode = pure regression test** every 10th iter: simulate the current
  skill against a pinned fixture, compare bugs caught to the fixture's minimum
  threshold, revert to `last_good_commit` on regression. No edits applied in
  benchmark iters.
- **Consecutive noops** only increment on **free-mode** noops (subagent returned
  null, or edit was structurally rejected). Benchmark iters don't count.

---

## HARD RULES

### Model
**Every subagent you dispatch via the `Agent` tool MUST use `model: "opus"`
(= claude-opus-4-6).** No Sonnet. No Haiku. User was explicit: *immer mit Opus 4.6*.

### Scope
Touch only `/Applications/MAMP/htdocs/code_guard`. Do NOT deploy to
`~/.claude/skills/code-guardian/`. Deployment is a manual step.

### Drift protection
The only real drift guard is the benchmark fixture run every 10 iterations. Do
NOT over-protect with per-iter score comparisons — that blocks real improvements.

---

## Paths

- Workspace: `/Applications/MAMP/htdocs/code_guard`
- Skill under test: `code-guardian/SKILL.md`
- State: `evolution/state.json`
- Ledger (append-only JSONL): `evolution/ledger.jsonl`
- Per-iter reports: `evolution/iterations/iter-NNN.md`
- Fixtures: `evolution/benchmark/fixture-0N.md`

---

## Algorithm

### 1. Read state
Parse `evolution/state.json`. Extract:
`iter`, `max_iter`, `baseline_score`, `last_good_commit`, `consecutive_noops`,
`stop_reason`, `cron_job_id`. (`baseline_score` is now "highest score seen so far"
— informational only, not a gate.)

### 2. Check stop conditions
- `stop_reason != null` → print `"loop already stopped: {reason}"`, exit.
- `iter >= max_iter` → set `stop_reason = "max_iter"`, save state, commit, try
  `CronDelete(cron_job_id)` if non-null, exit.
- `consecutive_noops >= 10` → set `stop_reason = "converged"`, save state, commit,
  try `CronDelete(cron_job_id)` if non-null, exit.

### 3. Compute next iter number
`N = iter + 1`

### 4. Determine mode
- If `N % 10 == 0` → **benchmark mode**, fixture index = `((N / 10 - 1) % 3) + 1`,
  read `evolution/benchmark/fixture-{index:02d}.md` into `fixture_contents`.
- Else → **free mode**.

### 5. Read SKILL.md
Read `code-guardian/SKILL.md` into `skill_contents`. This is the version under test.

### 6. Dispatch the red-team subagent

Use the `Agent` tool with:
- `subagent_type: "general-purpose"`
- `model: "opus"` ← **MANDATORY — do not omit, do not change**
- `description: "Red-team iter N"` (free) or `"Benchmark iter N"`

---

#### PROMPT (free mode)

```
You are the red-team evaluator for the code-guardian Claude Code skill.
Iteration: {N} / 100. Mode: free.

FIRST: Read `/Applications/MAMP/htdocs/code_guard/code-guardian/SKILL.md` in full.

## Your job

1. INVENT a realistic, NEW Laravel 11 + Vue 3 + MySQL task. Requirements:
   - 5+ concrete code snippets (migration, model, controller, resource, Vue,
     config, helper, command, middleware — pick at least 5)
   - 3+ subtle, realistic bugs that a code-guardian-armed session should catch
   - Exercise >= 5 of: P1 (cross-layer), P2 (scale), P3 (secrets), P4 (config:cache),
     P5 (pattern source), P6 (WIP staging), 7-point audit, debug-mode
   - Do NOT reuse prior iterations' scenarios (caller will list reserved ones)

2. Write the GROUND TRUTH block: list planted bugs, triggers, forbidden phrases.

3. SIMULATE: roleplay step-by-step what a Claude Code session armed with the
   SKILL.md would produce. Be honest — include hits, misses, friction.

4. EVALUATE — compute and log (NO gate on these numbers):
   - bugs_planted, bugs_caught
   - bugs_missed: list of {bug, why_missed}
   - forbidden_phrases_count
   - friction_notes: sections that felt redundant, verbose, or in-the-way
   - token_cost: high | medium | low
   - score = bugs_caught - 2*len(bugs_missed) - 2*forbidden_phrases - (1 if len(friction_notes)>=3 else 0)
   - **The score is DIAGNOSTIC. It is logged for trend analysis, not used to gate
     your edit.** Propose the best edit you can find regardless of the raw score.

5. PROPOSE ONE MINIMAL EDIT that addresses the #1 failure mode OR friction
   observed in this iteration. The edit MUST be:
   - Concrete: exact `old_string` (verbatim slice from the actual SKILL.md you
     read — copy-paste precise) and `new_string`
   - Minimal: smallest diff that addresses the issue
   - Token-aware: prefer tightening / replacing / deduplicating existing text
     over appending new warnings
   - Net-improving: do NOT add a warning that duplicates existing guidance
   - `old_string` must appear EXACTLY ONCE in SKILL.md
   - If the skill already handles this case well AND you see no real friction
     to reduce → return `"proposed_edit": null`. This is valid and often correct.
     But do NOT return null just because your simulation missed some bugs — if
     there is a real gap, propose the fix. The main loop will decide whether to
     apply it based on structural checks, not on your score.

## Output format

Write a detailed report. END your response with EXACTLY this JSON in a single
```json fence, nothing after:

```json
{
  "iter": N,
  "mode": "free",
  "task_title": "...",
  "task_description": "...",
  "triggers_expected": ["..."],
  "triggers_hit_in_sim": ["..."],
  "bugs_planted": 0,
  "bugs_caught": 0,
  "bugs_missed": [{"bug":"...","why_missed":"..."}],
  "forbidden_phrases_count": 0,
  "friction_notes": ["..."],
  "token_cost": "medium",
  "score": 0,
  "proposed_edit": {
    "rationale": "why this edit helps",
    "old_string": "VERBATIM slice from SKILL.md",
    "new_string": "replacement"
  }
}
```

Or `"proposed_edit": null`.

Do not write files. Do not dispatch other agents.
```

The caller supplies a "Reserved scenarios" block (iter-1 through iter-{N-1}
scenarios) and an "Already applied edits" block (so the subagent doesn't
re-propose prior edits).

---

#### PROMPT (benchmark mode — pure regression test, NO edit proposal)

```
You are the benchmark evaluator for the code-guardian Claude Code skill.
Iteration: {N} / 100. Mode: benchmark. Fixture index: {fixture_index}.

FIRST: Read `/Applications/MAMP/htdocs/code_guard/code-guardian/SKILL.md` in full.

## Your ONLY job

Given the fixture below (task + hidden ground truth), simulate step-by-step what
a Claude Code session armed with the SKILL.md would produce. Then compare the
simulation output against the fixture's ground truth.

DO NOT invent a task. DO NOT propose an edit. You are a pure regression tester.

## Fixture

{fixture_contents}

## Output format

Write a short report covering simulation + comparison. END with EXACTLY this
JSON in a single ```json fence, nothing after:

```json
{
  "iter": N,
  "mode": "benchmark",
  "fixture": "fixture-0N.md",
  "fixture_title": "...",
  "bugs_planted": 5,
  "bugs_caught": 4,
  "bugs_missed": [{"bug":"...","why_missed":"..."}],
  "forbidden_phrases_count": 0,
  "fixture_min_expected": 4,
  "passed_threshold": true,
  "score": 4
}
```

`passed_threshold` is `true` iff `bugs_caught >= fixture_min_expected`
AND `forbidden_phrases_count == 0`.

Do not write files. Do not dispatch other agents.
```

---

### 7. Parse the JSON
Extract the last fenced ```json block. Parse it.
On parse failure or missing required fields:
- Write error to `iterations/iter-{N:03d}.md`
- Ledger action = `"error"`
- Free mode: `consecutive_noops += 1`
- Benchmark mode: no noop increment
- Proceed to commit (step 11).

### 8. Save full report
Use `Write` tool to save the subagent's output to
`evolution/iterations/iter-{N:03d}.md`.

### 9. Apply the gate

#### Free mode

Let `edit = parsed.proposed_edit`, `score = parsed.score`.

Accept edit iff ALL:
1. `edit != null`
2. `edit.old_string` appears EXACTLY ONCE in current SKILL.md (Grep count)
3. (After Edit tool) structure check: `grep 'name: code-guardian'` AND
   `grep '## PLAN MODE (v5'` both return 1 line

If accepted:
- Use `Edit` tool on `code-guardian/SKILL.md` with the proposed strings
- Run structure check; if it fails, manually revert (Edit with strings swapped)
  and treat as noop
- `action = "edit"`
- `new_baseline_score = max(baseline or -999, score)` (informational only)
- `consecutive_noops = 0`

If rejected (edit null, old_string missing or non-unique, structure broken):
- `action = "noop"`
- `consecutive_noops += 1`
- baseline unchanged

#### Benchmark mode

Let `passed = parsed.passed_threshold`, `score = parsed.score`.

- If `passed == true`:
  - No change to SKILL.md
  - `action = "benchmark_pass"`
  - `consecutive_noops` unchanged (benchmark doesn't count)
- If `passed == false`:
  - **REGRESSION** — revert SKILL.md to `last_good_commit`:
    `git -C <workspace> show {last_good_commit}:code-guardian/SKILL.md > code-guardian/SKILL.md`
  - `action = "revert"`
  - `consecutive_noops` unchanged
  - baseline unchanged
  - If `last_good_commit == null`, log a warning and skip the revert

### 10. Ledger entry
Append ONE JSON line to `evolution/ledger.jsonl`:

```json
{"iter":N,"ts":"ISO","mode":"free|benchmark","task":"title","score":S,"baseline":B,"action":"edit|noop|revert|benchmark_pass|error","report":"iterations/iter-NNN.md","agent_model":"opus"}
```

### 11. Update state.json
Write new state with updated `iter`, `baseline_score`, `consecutive_noops`,
`last_good_commit` (PENDING placeholder for edit/revert actions — to be filled
in the second commit). Keep `cron_job_id`, `max_iter`, `started_at` unchanged.

### 12. Commit
```
git -C /Applications/MAMP/htdocs/code_guard add -A
git -C /Applications/MAMP/htdocs/code_guard commit -m "iter N: {action} score={score} | {task_title}"
```

If `action == "edit"` or `"revert"`:
1. Run `git rev-parse HEAD` → SHA
2. Replace the `"PENDING"` placeholder in `state.json` with the actual SHA
3. `git add evolution/state.json && git commit -m "iter N: state sha update"`

### 13. Summary line
Print:
```
iter N/100 | {mode} | {action} | score={score} baseline={baseline} | noops={consecutive_noops}
```

---

## Error handling
- Catch any exception
- Write short error to `iterations/iter-{N:03d}.md`
- Append ledger entry with `"action":"error"`
- Commit what exists
- Do NOT CronDelete — next tick retries
- Exit cleanly

## Loop termination
- Natural: `iter >= 100` or `consecutive_noops >= 10`
- At termination: try `CronDelete(cron_job_id)` via `ToolSearch("select:CronDelete", 1)`
  then call. If it fails, commit the state and exit — cron auto-expires after 7 days.

## What this loop does NOT do
- Does NOT run any real code (simulation only)
- Does NOT touch `~/.claude/skills/code-guardian/` (manual `./deploy.sh`)
- Does NOT touch files outside the workspace
- Does NOT amend commits (always new commits)
- Does NOT use Sonnet or Haiku — Opus 4.6 only
