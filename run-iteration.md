# Code Guardian Evolution Loop — Iteration Runner (v4)

This file is executed by a Claude Code session fired by cron every 3 minutes.
Each run = one iteration of the skill's self-improvement loop.

## What changed in v4 (post-edit re-verification)
- **Every accepted edit is re-verified against the same task that motivated it.**
  User directive: "Wenn er eine Korrektur gemacht hat bei Fall X dann muss danach
  der gleiche Fall nochmal gecheckt werden um zu prüfen ob es was gebracht hat."
- **Two-phase dispatch per edit iter**: (1) attack subagent invents task +
  simulates + proposes edit; (2) if gate accepts the edit, a verify subagent
  is dispatched with the NEW SKILL.md + the SAME task + the ground truth. It
  simulates again and reports bugs_caught_post_edit.
- **Decision rule**:
  - `post_caught >= pre_caught` AND targeted miss (if any) now caught → **keep**
  - `post_caught >= pre_caught` AND no targeted miss declared (pure generalization
    edit) → **keep**
  - `post_caught < pre_caught` → **REGRESSION** — revert the edit on the spot,
    action=`revert_verify_fail`, log the harmful edit
  - Targeted miss still missed AND no other improvement → **keep but flag**
    (the edit didn't hurt, but didn't fix what it claimed either — useful data
    for tuning future iterations)
- **Cost**: edit iters now dispatch 2 subagents (attack + verify). Wall time
  ~2× on edit iters (~2 min → ~4 min). Noop iters stay single-dispatch.
- **Ledger gains 4 fields**: `pre_caught`, `post_caught`, `verify_delta`,
  `verify_target_hit` (null for generalization edits).

## What changed in v3 (generality + optimization mandate)
- **Generality Principle (user directive, mid-loop)**: the skill must work for
  ANY project and ANY stack. No framework-locked examples. Proposed edits that
  bake in framework-specific APIs (`Cache::remember`, `ShouldQueue`, `storeAs`,
  `public_path`, `Str::uuid`, `Http::pool`, `Mail::to`, `Eloquent`, `Inertia`,
  `Blade`, `Vue`, `Laravel`, `Django`, `Rails`, `Express`, ...) must either (a)
  be rewritten in framework-agnostic wording with at most ONE brief example, or
  (b) be rejected as noop.
- **Optimization bias**: prefer TIGHTENING / REMOVING / DEDUPLICATING over
  ADDING. The skill should get shorter or stay flat across iterations — NOT
  longer. New content must carry its weight (>= 1 real bug class not covered
  anywhere else, AND framework-agnostic).
- **Line-count watch**: SKILL.md line count is logged in every ledger entry. A
  3-iter trend of line-count growth without proportional coverage gain is a
  signal to generalize/deduplicate.

## What changed in v2 (kept)
- Score-based gate removed. Score is diagnostic, not gated.
- Structural gate only for free mode.
- Benchmark mode = pure regression test every 10th iter.
- Consecutive noops only increment on free-mode noops.

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

### Generality gate (v3)
Before applying any edit, scan `new_string` for framework-locked tokens:
`Laravel`, `Eloquent`, `Blade`, `Inertia`, `Vue`, `Cache::`, `Http::pool`,
`storeAs`, `storage_path`, `public_path`, `$request->`, `->file(`, `Str::`,
`ShouldQueue`, `Mail::to`, `config('`, `env('`, `Artisan::`, `Schema::`,
`Eloquent`, `php artisan`, `DB::`, `Route::`, `->make(`, `->pluck(`.
Count the hits. Judgment call:
- **>= 3 framework tokens** AND the edit is > 10 lines of new content → **reject
  as noop**. Too framework-specific.
- **1–2 framework tokens** AND they're brief examples illustrating a general
  principle → **allow**, but only if the principle itself is stated in
  framework-agnostic terms FIRST.
- **0 framework tokens** AND the edit tightens/removes/generalizes existing
  content → **preferred**, allow.

Pure deletion edits (shortening SKILL.md) always pass the generality gate —
removing is always generalizing.

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
   - **Framework-agnostic**: state the principle in universal terms. Laravel,
     Vue, Rails, Django, Express, Spring, Go — whatever. The skill is used
     across stacks. NO framework class/method/function names in the `new_string`
     unless (a) the principle itself is stated generically first AND (b) the
     example is ONE brief line. Preferred: zero framework tokens. Hard cap:
     >=3 framework tokens OR >10 lines with 1+ framework tokens → main loop
     will reject as a generality violation.
   - **Tightening preferred over adding**: the best edits REMOVE duplication,
     REPLACE verbose content with tighter wording, or DELETE dead weight. Next
     best: one bullet added to an existing section. Worst: new section with
     examples. If your proposed edit is adding lines, you must justify why no
     existing content could be refactored instead.
   - **Concrete**: exact `old_string` (verbatim slice — copy-paste precise) and
     `new_string`. `old_string` must appear EXACTLY ONCE in SKILL.md.
   - **Minimal**: smallest diff that addresses the issue.
   - **Net-improving**: no duplication of existing guidance.
   - If the skill already handles this case well AND you see no friction to
     reduce → return `"proposed_edit": null`. Valid and often correct.
   - Do NOT return null just because your simulation missed bugs. If there's a
     real general gap, propose a general fix. But if the gap is only expressible
     as framework-specific code, prefer `null` over a framework-locked edit.

## Output format (v4)

Write a detailed report. **Include the full task + ground truth in the JSON**
so the main loop can dispatch a verify subagent that re-runs the same task
against the post-edit SKILL.md. END your response with EXACTLY this JSON in a
single ```json fence, nothing after:

```json
{
  "iter": N,
  "mode": "free",
  "task_title": "...",
  "task_description": "full task text including all code snippets (verbatim, enough to re-simulate)",
  "ground_truth": {
    "bugs_planted": [
      {"id":"B1","description":"...","expected_trigger":"P2","severity":"high"}
    ],
    "forbidden_phrases": ["..."]
  },
  "triggers_expected": ["..."],
  "triggers_hit_in_sim": ["..."],
  "bugs_planted": 0,
  "bugs_caught": 0,
  "bugs_missed": [{"bug":"...","why_missed":"...","bug_id":"B3"}],
  "forbidden_phrases_count": 0,
  "friction_notes": ["..."],
  "token_cost": "medium",
  "score": 0,
  "proposed_edit": {
    "rationale": "why this edit helps",
    "targeted_miss": "B3",
    "old_string": "VERBATIM slice from SKILL.md",
    "new_string": "replacement"
  }
}
```

Or `"proposed_edit": null`. For pure generalization/tightening edits (no bug
miss being addressed), set `"targeted_miss": null`.

The `task_description` MUST be self-contained — any future subagent reading
it should be able to re-simulate without access to your prior output. Include
ALL code snippets, the prompt the fictional dev gave, and any context the
ground truth refers to.

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

Let `edit = parsed.proposed_edit`, `score = parsed.score`,
`pre_caught = parsed.bugs_caught`.

Accept edit iff ALL:
1. `edit != null`
2. `edit.old_string` appears EXACTLY ONCE in current SKILL.md (Grep count)
3. **Generality gate**: count framework-locked tokens (`Laravel`, `Eloquent`,
   `Blade`, `Inertia`, `Vue`, `Cache::`, `Http::pool`, `storeAs`, `storage_path`,
   `public_path`, `$request->`, `Str::`, `ShouldQueue`, `Mail::to`, `config('`,
   `env('`, `php artisan`, `Route::`, `DB::`) in `edit.new_string`. If the
   count is >= 3 AND the new content is > 10 lines → reject as noop with
   rationale "generality violation". If the count is 1–2 but they are ONE
   brief example under a generically-stated principle, allow. Pure removal
   edits always pass.
4. **Line-count guard**: if the edit makes SKILL.md grow AND the trend over
   the last 3 iterations is already growing, require the subagent's rationale
   to explicitly name what cannot be refactored/removed instead. Judgment call.

If accepted, APPLY the edit via the Edit tool, THEN:

5. **Structure check**: `grep 'name: code-guardian'` AND `grep '## PLAN MODE (v5'`
   both return 1 line. If fail → manually revert edit (Edit tool with strings
   swapped), action = `"noop_structure_broke"`, consecutive_noops += 1, skip
   verify step.

6. **v4 — Post-edit verification (dispatch verify subagent)**: dispatch a SECOND
   subagent of `subagent_type: "general-purpose"`, `model: "opus"`, with the
   prompt template below. Pass: the NEW SKILL.md file path + the full
   `task_description` + `ground_truth` from the attack agent's output + the
   `targeted_miss` if any.

7. **Parse verify output**, extract `post_caught`, `post_missed`, and
   `targeted_miss_now_caught`.

8. **Decision**:
   - `post_caught < pre_caught` → **REGRESSION**. Revert the edit:
     `git -C <workspace> show HEAD:code-guardian/SKILL.md > code-guardian/SKILL.md`
     (note: HEAD is the pre-edit commit, because we haven't committed the edit
     yet). action = `"revert_verify_fail"`. consecutive_noops += 1. baseline unchanged.
   - `post_caught >= pre_caught` AND `targeted_miss != null` AND
     `targeted_miss_now_caught == true` → **TARGETED WIN**. Keep the edit.
     action = `"edit_verified"`. `new_baseline_score = max(baseline or -999, score)`.
     consecutive_noops = 0.
   - `post_caught >= pre_caught` AND `targeted_miss != null` AND
     `targeted_miss_now_caught == false` → **WEAK EDIT** (didn't hit its target
     but didn't hurt). Keep. action = `"edit_weak"`. consecutive_noops = 0.
   - `post_caught >= pre_caught` AND `targeted_miss == null` → **GENERALIZATION
     OK**. Keep. action = `"edit_generalize"`. consecutive_noops = 0.

If rejected at steps 1–5 (edit null, old_string non-unique, generality violation,
structure broken): action = `"noop"`, consecutive_noops += 1, baseline unchanged.

---

#### PROMPT (verify subagent, v4)

```
You are the VERIFY subagent for the code-guardian Claude Code skill.
Iteration: {N}. Your job: re-simulate the task below against the NEW SKILL.md
and report how many bugs the skill-following session would catch.

FIRST: Read `/Applications/MAMP/htdocs/code_guard/code-guardian/SKILL.md` in
full. This is the POST-EDIT version. The edit was just applied and has NOT
been committed yet.

## The task (verbatim from the attack subagent)

{task_description}

## The ground truth (hidden from the simulated session)

Bugs planted in this task:
{ground_truth.bugs_planted}

Forbidden phrases the skill-following session must avoid:
{ground_truth.forbidden_phrases}

The attack subagent reported PRE-EDIT catch rate: {pre_caught} / {bugs_planted}
Bugs it said were missed: {bugs_missed}
The proposed edit targeted this specific miss: {targeted_miss or "none (pure generalization)"}

## Your job

1. Simulate step-by-step what a Claude Code session armed with the POST-EDIT
   SKILL.md would ACTUALLY produce when handed this exact task. Do NOT cheat
   by using the ground truth during simulation. Do NOT assume the pre-edit
   simulation was optimal — run your own independent honest simulation.
2. Compare your simulation output vs the ground truth.
3. Report:
   - post_caught (int, how many bugs your simulation caught)
   - post_missed (list of {bug_id, bug, why_missed})
   - targeted_miss_now_caught (bool — true iff {targeted_miss} is in your
     caught list; null if targeted_miss was "none")
   - forbidden_phrases_count
   - delta_vs_pre (post_caught - pre_caught)
   - notes (one-line commentary: did the edit make the difference, or was
     the pre-edit sim pessimistic, or was the post-edit sim pessimistic?)

## Output

END your response with EXACTLY this JSON in a single ```json fence:

```json
{
  "iter": N,
  "phase": "verify",
  "pre_caught": 0,
  "post_caught": 0,
  "delta": 0,
  "post_missed": [{"bug_id":"B3","bug":"...","why_missed":"..."}],
  "targeted_miss": "B3",
  "targeted_miss_now_caught": true,
  "forbidden_phrases_count": 0,
  "notes": "one-line"
}
```

Do not write files. Do not dispatch other agents.
```

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
Append ONE JSON line to `evolution/ledger.jsonl`. Include v4 verify fields
(null for noop/benchmark iters):

```json
{"iter":N,"ts":"ISO","mode":"free|benchmark","task":"title","score":S,"baseline":B,"action":"edit_verified|edit_weak|edit_generalize|noop|revert_verify_fail|benchmark_pass|error","report":"iterations/iter-NNN.md","agent_model":"opus","skill_md_lines":NNN,"skill_md_delta":±N,"pre_caught":N,"post_caught":N,"verify_delta":±N,"verify_target_hit":true|false|null}
```

A negative `skill_md_delta` (skill got shorter) is a GOOD signal under v3+.
A positive `verify_delta` is the v4 strong signal: the edit actually helped
close a gap that was previously missed.

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
