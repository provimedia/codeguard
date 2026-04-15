# Code Guardian Evolution Loop — Iteration Runner

This file is executed by a Claude Code session fired by cron every 10 minutes.
Each run = one iteration of the skill's self-improvement loop.

---

## HARD RULES

### Model
**Every subagent you dispatch via the `Agent` tool MUST use `model: "opus"`
(= claude-opus-4-6).** No Sonnet. No Haiku. User was explicit: *immer mit Opus 4.6*.

### Scope
Touch only `/Applications/MAMP/htdocs/code_guard`. Do NOT deploy to
`~/.claude/skills/code-guardian/`. Deployment is a manual step.

### Gate
Apply a `SKILL.md` edit ONLY if the score is >= baseline. On benchmark regression,
revert to the last good commit. "Always edit" is forbidden — it causes drift.

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
Read `evolution/state.json`. Extract:
`iter`, `max_iter`, `baseline_score`, `last_good_commit`, `consecutive_noops`,
`stop_reason`, `cron_job_id`.

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
- `description: "Red-team iter N"`
- `prompt`: the block below, with `{N}`, `{skill_contents}`, and (benchmark mode)
  `{fixture_contents}` substituted verbatim.

---

#### PROMPT (free mode)

```
You are the red-team evaluator for the code-guardian Claude Code skill.
Iteration: {N} / 100.

## Your job

1. INVENT a realistic, NEW Laravel 11 + Vue 3 + MySQL task. Requirements:
   - Include 5+ concrete code snippets (migration, model, controller, resource,
     Vue component, config, helper — pick at least 5)
   - Plant 3+ subtle, realistic bugs that a code-guardian-armed session should catch
   - The task must exercise at least 5 of: P1 (cross-layer trace), P2 (scale),
     P3 (secrets hygiene), P4 (config:cache safety), P5 (pattern source quality),
     P6 (WIP staging discipline), any of the 7-point audit checks, debug-mode
   - Do NOT reuse scenarios from prior iterations. Be creative each run.
   - The task must be different from the benchmark fixtures (no helpful_text on
     Product, no admin API key in URL, no same_site=strict mobile bug).

2. Write a GROUND TRUTH block (hidden from the simulation step): list planted bugs,
   triggers that should fire, forbidden phrases, minimum score expectation.

3. SIMULATE: roleplay step-by-step what a Claude Code session armed with the
   SKILL.md below would ACTUALLY produce when handed this task. Be honest —
   include moments where the skill helps AND moments where it fails, feels
   verbose, produces redundant output, or misses a bug. Do NOT cheat by peeking
   at the ground truth.

4. EVALUATE the simulation against the ground truth. Compute:
   - bugs_planted, bugs_caught
   - bugs_missed: list of {bug, why_missed} — why did the skill fail to catch it?
   - forbidden_phrases_count
   - friction_notes: list of SKILL.md sections that felt redundant, verbose,
     or got in the way during the simulation
   - token_cost: "high" | "medium" | "low"
   - score = bugs_caught - 2*len(bugs_missed) - 2*forbidden_phrases_count
             - (len(friction_notes) >= 3 ? 1 : 0)

5. PROPOSE ONE MINIMAL EDIT to SKILL.md that would fix the #1 failure mode from
   this iteration. The edit MUST be:
   - Concrete: exact `old_string` (verbatim slice from SKILL.md below) and `new_string`
   - Minimal: smallest diff that fixes the issue
   - Token-aware: prefer tightening or replacing existing text over appending
   - Net-improving: do not add yet-another-warning that duplicates existing content
   - `old_string` must appear EXACTLY ONCE in SKILL.md (for a clean Edit-tool replacement)
   - If the skill already handles this case OR no edit clearly improves things,
     return `"proposed_edit": null`

## Output format

End your response with EXACTLY this JSON (wrapped in a single ```json fence,
nothing after it):

```json
{
  "iter": N,
  "mode": "free",
  "task_title": "short title",
  "task_description": "2-3 sentence summary",
  "triggers_expected": ["P1","P4","audit-1"],
  "triggers_hit_in_sim": ["P1"],
  "bugs_planted": 3,
  "bugs_caught": 1,
  "bugs_missed": [{"bug":"...","why_missed":"..."}],
  "forbidden_phrases_count": 0,
  "friction_notes": ["..."],
  "token_cost": "medium",
  "score": -2,
  "proposed_edit": {
    "rationale": "why this edit helps",
    "old_string": "EXACT verbatim slice from SKILL.md",
    "new_string": "replacement"
  }
}
```

Or `"proposed_edit": null` if no warranted edit.

## SKILL.md under test

{skill_contents}
```

---

#### PROMPT (benchmark mode)

Identical to free mode EXCEPT replace step 1 with:

```
1. Use the fixture below verbatim as the task. Do NOT invent a new task.
   Do NOT reveal the ground truth to the simulation step.

=== FIXTURE ===
{fixture_contents}
=== END FIXTURE ===
```

And set `"mode": "benchmark"` in the JSON output.

---

### 7. Parse the JSON
Extract the last fenced ```json block from the agent's output. Parse it.
If parsing fails or required fields are missing:
- Write error to `iterations/iter-{N:03d}.md`
- Ledger action = `"error"`
- Proceed to step 11 (commit, update state)

### 8. Save full report
Use `Write` tool to save the subagent's entire output to
`evolution/iterations/iter-{N:03d}.md`.

### 9. Apply the gate

Let `score = parsed.score`, `edit = parsed.proposed_edit`, `baseline = baseline_score`.

**Free mode:**
- Accept edit iff ALL:
  1. `edit != null`
  2. Grep `edit.old_string` in SKILL.md → exactly 1 occurrence
  3. `baseline == null` OR `score >= baseline`
- If accepted → use `Edit` tool on `code-guardian/SKILL.md` (old_string/new_string).
  After edit, Grep for `name: code-guardian` frontmatter and `## PLAN MODE (v5` to
  verify structural integrity. If either is missing, revert the edit from memory,
  set action = `"noop_edit_broke_structure"`, increment consecutive_noops.
- If accepted and structure OK: `action = "edit"`,
  `new_baseline = max(baseline or -999, score)`, `consecutive_noops = 0`.
- Else: `action = "noop"`, `consecutive_noops += 1`.

**Benchmark mode:**
- If `baseline != null` AND `score < baseline`:
  - REVERT: `git -C <workspace> show {last_good_commit}:code-guardian/SKILL.md > code-guardian/SKILL.md`
    (use Bash tool). If `last_good_commit == null`, skip revert, log warning.
  - `action = "revert"`, `consecutive_noops += 1`, baseline unchanged.
- Elif edit accepted (same conditions as free mode):
  - Apply, `action = "edit"`, update baseline, `consecutive_noops = 0`.
- Else:
  - `action = "noop"`, `consecutive_noops += 1`.

### 10. Ledger entry
Append ONE JSON line to `evolution/ledger.jsonl`:

```json
{"iter":N,"ts":"ISO8601","mode":"free|benchmark","task":"title","score":S,"baseline":B,"action":"edit|noop|revert|error","report":"iterations/iter-NNN.md"}
```

### 11. Update state.json
Write:
```json
{
  "iter": N,
  "max_iter": 100,
  "baseline_score": new_baseline,
  "last_good_commit": (updated_after_commit_if_edit_else_unchanged),
  "consecutive_noops": new_noops,
  "stop_reason": null_or_set,
  "cron_job_id": unchanged,
  "started_at": unchanged,
  "subagent_model": "opus",
  "gate_mode": "on"
}
```

Note: `last_good_commit` will be updated AFTER step 12 (chicken-and-egg). Save
state.json with a placeholder, then after the commit in step 12, do a SECOND
commit that updates `last_good_commit` to `git rev-parse HEAD~0`. Two commits per
iteration is acceptable — keeps the history auditable.

### 12. Commit
```
git -C /Applications/MAMP/htdocs/code_guard add -A
git -C /Applications/MAMP/htdocs/code_guard commit -m "iter N: {action} score={score} | {task_title}"
```

If `action == "edit"` or `"revert"`: run `git rev-parse HEAD`, write that SHA into
`state.json.last_good_commit`, then second commit:
```
git -C ... add evolution/state.json
git -C ... commit -m "iter N: state sha update"
```

### 13. Summary line
Print to stdout / final message:
```
iter N/100 | {mode} | {action} | score={score} baseline={baseline} | noops={noops}
```

---

## Error handling

If ANY step raises an exception:
1. Catch, write short description to `evolution/iterations/iter-{N:03d}.md`
2. Append ledger entry with `"action":"error"`, `"error":"<msg>"`
3. Commit what exists
4. Do NOT CronDelete — let the next cron tick retry
5. Exit cleanly

## Loop termination

- Natural: `iter >= 100` or `consecutive_noops >= 10`
- At termination: try `CronDelete(cron_job_id)`. If the CronDelete tool schema is
  not loaded, call `ToolSearch("select:CronDelete", 1)` first, then call it.
- If CronDelete fails (wrong ID, already gone): just commit the state and exit.
  Cron auto-expires after 7 days regardless.
- Stop-flag fallback: once `stop_reason` is set, all future ticks will immediately
  exit at step 2.

## Things this loop does NOT do

- Does NOT run any real code (the subagent simulates, does not execute)
- Does NOT touch `~/.claude/skills/code-guardian/` (manual `./deploy.sh`)
- Does NOT call any external APIs beyond the Anthropic subagent dispatch
- Does NOT alter files outside `/Applications/MAMP/htdocs/code_guard`
- Does NOT amend commits (global rule: always new commits)
