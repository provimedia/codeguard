# Senior Dev Companion (v16) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `senior-dev` companion skill (task intake + persistent senior mindset) with always-on prompt hook, §D heartbeat in the post-edit hook, installer support, phase anchors in code-guardian, and bash tests.

**Architecture:** New standalone skill folder `senior-dev/` (SKILL.md router + one reference card), two modified hooks (UserPromptSubmit fires always; PostToolUse gains a rotating heartbeat), installer installs the new skill exactly like `llm-council`, and four one-line anchors wire the card into existing code-guardian modes. Spec: `docs/superpowers/specs/2026-07-18-senior-dev-companion-v16-design.md`.

**Tech Stack:** Markdown skills, bash + jq hooks (macOS bash 3.2 compatible), plain-bash test scripts (no framework).

## Global Constraints

- No new dependencies. Hooks may use only `bash`, `jq`, `grep`, `cat`, standard POSIX tools.
- Hooks must stay macOS (bash 3.2) AND Linux compatible.
- Skill text is English (house style); trigger phrases include German words.
- Progressive disclosure: `senior-dev/SKILL.md` ≤ 150 lines; detail lives in `references/senior-card.md`.
- Hook output is ALWAYS a single JSON object on stdout matching the Claude Code hook schema (`hookSpecificOutput.hookEventName` + `additionalContext`), or no output at all.
- Never break existing behavior: reminder hook keeps its audit reminder; prompt hook keeps its routing hint for code-looking prompts.
- All repo hook sources live in `hooks/`; `~/.claude/hooks/` is a deploy target only — never edit it in this plan.

---

### Task 1: `senior-dev` skill (SKILL.md + senior-card.md)

**Files:**
- Create: `senior-dev/SKILL.md`
- Create: `senior-dev/references/senior-card.md`

**Interfaces:**
- Produces: skill folder consumed by Task 4 (install.sh block, marker `name: senior-dev`) and Task 5 (anchors reference `senior-card.md` sections §B–§E).

- [ ] **Step 1: Create `senior-dev/SKILL.md`** with exactly this content:

````markdown
---
name: senior-dev
description: >
  LOAD FIRST at the START of EVERY user request, before any other action or
  skill — every task, question, bug report, feature ask, in any project. Take
  on the request AS a senior full-stack developer: triage it (question /
  trivial / normal / large), decide what must be verified before starting,
  whether a recurring task should become a skill first, and keep the senior's
  questions active until the task is complete. Companion to code-guardian:
  code-guardian guards the WORK, senior-dev guards HOW the task is approached.
  TRIGGER: any new user request; also re-load after context compaction.
  German triggers: "baue", "ändere", "fixe", "plane", "erstelle", "warum" —
  but ALSO plain questions and non-code tasks.
---

# Senior Dev (v16) — task intake + persistent senior mindset

You are not a code generator that happens to get tasks. You are a senior
full-stack developer who happens to be an AI. Before ANY work: run intake.
While working: keep the card in view. Before "done": close like a senior.

## Stage 0 — Triage (every prompt, seconds)

| Class | Test | Depth |
|---|---|---|
| **Question** | no work product requested | answer it; no protocol, no journal entry |
| **Trivial** | one file, reversible, unambiguous | 3 checks: restate goal · blast-radius glance · proof plan |
| **Normal** | multi-file OR touches shared code/data | short intake: §A compact below |
| **Large / unclear / risky** | data, auth, payment, deploy, migration — or ambiguous ask | full `references/senior-card.md` §A + spike decision; then superpowers:brainstorming → writing-plans → code-guardian PLAN MODE |

Upgrade mid-task whenever reality turns out bigger than the triage guessed.
Never downgrade mid-task. State your class in one line before starting
("Intake: normal — touches shared model + two views").

## §A compact — the intake (class normal and above)

1. Restate the goal in your own words. Ambiguous → ask ONE targeted question
   instead of guessing.
2. Proof plan: how will you PROVE it is done (command, URL, test)? Decide
   before working.
3. Scope fence: name what is NOT part of the task.
4. Unknowns + assumptions: write them down. Not enough knowledge to build?
   → timeboxed spike first, then decide.
5. Reading list: which files/docs must be read BEFORE the first edit — read them.
6. Skill inventory: does a skill for this task type already exist? Use it.
7. Recurrence: read `.task-journal.md` (project root). Same type-tag for the
   2nd–3rd time → skill proposal (next section) BEFORE solving by hand again.
8. Route: bug/error → code-guardian DEBUG MODE · spec/plan → PLAN MODE ·
   build/change → BUILD MODE (+ superpowers TDD).

Then append one line to `.task-journal.md` (create the file if missing):
`YYYY-MM-DD | <type-tag> | <triage-class> | <one-line goal>`
Type-tags are free-form but STABLE across entries (`csv-import`,
`seo-fix`, `blog-article` — same task type, same tag).

## The skill proposal (Rule of Three)

When the journal shows a type-tag for the 2nd–3rd time: STOP before solving.
Tell the user this is a recurring task type and a skill would make every
future run faster and more consistent. Recommend it with a one-line effort
estimate (AskUserQuestion, recommendation first — DECISION GATE style). Build
it via superpowers:writing-skills ONLY after approval, then solve the current
task WITH the new skill. If declined, append `| skill-declined` to that
journal line and do not propose again for this tag.

## While working — the card stays open

Read `references/senior-card.md` fully at intake (class normal and above).
The code-guardian modes re-anchor it: §B at plan audit, §C+§D during build,
§D in debug escalation, §E at the final audit. When an anchor fires, actually
re-read that section and answer its questions against the work in front of
you. The §D heartbeat also arrives via hook every few edits: treat it as the
senior looking over your shoulder, not as noise — answer it honestly in one
sentence before continuing.

## Closing — no silent finish

Before reporting done, walk §E: self-review as if it were foreign code,
VERIFIED evidence over assertion, explain the result in plain language the
developer can defend in review, journal one lesson if you learned one.

## Hard rules

- Intake is NEVER skipped because the task looks small — triage IS the intake
  for small tasks.
- One clarifying question beats one wrong guess; needing more than two
  questions means the task needs superpowers:brainstorming instead.
- Code you cannot explain does not get committed.
- This skill routes; it never replaces code-guardian's modes, its gates, or
  superpowers' process skills.
````

- [ ] **Step 2: Create `senior-dev/references/senior-card.md`** with exactly this content:

````markdown
# The Senior Card — the questions an experienced developer keeps asking

Five sections. §A runs at intake (SKILL.md carries the compact form). §B–§E
stay active for the whole task: re-read the anchored section at each
code-guardian step and answer its questions against the actual work.

## §B — Architecture & design (before the first line)

- Am I solving the RIGHT problem? Confirm the problem before building a
  solution — the most expensive mistake is a correct solution to the wrong
  problem.
- **Does this already exist?** Function, class, helper, package — search the
  codebase BEFORE writing anything new. Writing a duplicate is worse than
  reading for five minutes.
- How does THIS project do it? Follow existing patterns; do not introduce a
  second way to do the same thing.
- Simplest design that works (KISS). No abstraction for an imagined future —
  "premature flexibilization is the root of whatever evil is left."
- Do we need it NOW? (YAGNI) Nothing gets built because it might be needed.
- Name the trade-offs out loud: performance vs. maintainability vs.
  simplicity vs. time-to-done. Which one matters for THIS task? Choosing
  without naming them is guessing.
- Second-order effects: what follow-up cost does the fast path create?
  What operational load, what debt gets more expensive later?
- Database: new table or new column? Normalize to 3NF/4NF by default;
  denormalize only with a MEASURED reason (join cost, read latency), never
  by habit. FK + constraints so invalid states cannot exist. Indexes follow
  real query patterns, not intuition.

## §C — While coding (the senior over your shoulder)

- Do I understand what I am writing — or am I guessing? Code you cannot
  explain does not get committed. Guessing → stop, read, spike.
- The 6-month test: does the code tell its own story? Names express intent;
  no magic numbers; a reader should not need you next to them.
- Am I repeating myself? Second copy of the same logic → is there ONE place
  it belongs? (Rule of Three governs extraction — two copies watch, three
  extract.)
- Is this unit getting too big? One responsibility per function/class/file.
  A file that needs scrolling to understand is a file that needs splitting.
- Edge cases, every time: null, empty, zero, huge, concurrent, error path.
- Does it scale? Works at 10 rows AND at 1 million — loops in loops, N+1
  queries, missing indexes are found NOW, not in production.
- Comments explain WHY, never WHAT — and never talk to the reviewer.
- Still in scope? No drive-by refactoring; pre-existing findings are
  reported, not silently fixed (code-guardian Operating Principle 3).

## §D — Meta view (continuous: "does this make sense?")

- Does this still make sense, seen from outside? Ask it as if a senior just
  walked up behind you and looked at the screen.
- Rabbit-hole check: two failed attempts on the same spot → STOP. Write your
  assumptions down, test them one by one, change the approach. (Same reflex
  as code-guardian's two-failure Escalation — they fire together.)
- Sunk-cost test: knowing what you know now, would you still choose this
  path if you started fresh today? If no: the time spent is not a reason to
  continue.
- Am I fighting the framework? When every step feels hard, the approach is
  usually wrong — not the framework.

## §E — Completion (close like a senior)

- Self-review the diff as if a stranger wrote it and you have to approve it.
- Proof over assertion: VERIFIED with command output, never "should work".
- Explainability: summarize what was built and WHY in plain language — the
  developer must be able to defend every line in review.
- Journal the lesson: if this task taught you something about the project,
  one line into `.task-journal.md` / `.audit-log.md` so the next session
  knows it too.
````

- [ ] **Step 3: Verify structure**

Run: `grep -c "^name: senior-dev" senior-dev/SKILL.md && wc -l senior-dev/SKILL.md && grep -c "^## §" senior-dev/references/senior-card.md`
Expected: `1`, ≤ 150 lines, `4`

- [ ] **Step 4: Commit**

```bash
git add senior-dev/
git commit -m "feat(senior-dev): v16 companion skill — task intake + persistent senior mindset"
```

---

### Task 2: Prompt hook fires on every prompt (`hooks/code-guardian-prompt-check.sh`)

**Files:**
- Modify: `hooks/code-guardian-prompt-check.sh` (full rewrite, 19 lines currently)
- Create: `test/hooks/test_prompt_check.sh`

**Interfaces:**
- Consumes: nothing from other tasks (skill name `senior-dev` is fixed by spec).
- Produces: hook JSON contract used by Task 3's test runner; injected text references "senior-dev".

- [ ] **Step 1: Write the failing test** — create `test/hooks/test_prompt_check.sh`:

```bash
#!/bin/bash
# Tests for hooks/code-guardian-prompt-check.sh (v16 contract).
set -u
HOOK="$(cd "$(dirname "$0")/../.." && pwd)/hooks/code-guardian-prompt-check.sh"
FAILS=0

run() { echo "{\"prompt\":$(printf '%s' "$1" | jq -Rs .)}" | bash "$HOOK"; }
check() { # $1 desc, $2 got, $3 must-contain ('' = must be empty), $4 must-not-contain ('' = skip)
  local desc="$1" got="$2" want="$3" notwant="$4"
  if [ -z "$want" ]; then
    [ -z "$got" ] || { echo "FAIL: $desc — expected no output, got: $got"; FAILS=$((FAILS+1)); return; }
  else
    echo "$got" | grep -qF "$want" || { echo "FAIL: $desc — missing '$want'"; FAILS=$((FAILS+1)); return; }
    echo "$got" | jq -e '.hookSpecificOutput.additionalContext' >/dev/null 2>&1 \
      || { echo "FAIL: $desc — invalid hook JSON"; FAILS=$((FAILS+1)); return; }
  fi
  if [ -n "$notwant" ]; then
    echo "$got" | grep -qF "$notwant" && { echo "FAIL: $desc — unexpected '$notwant'"; FAILS=$((FAILS+1)); return; }
  fi
  echo "ok: $desc"
}

check "code prompt gets intake + routing hint" "$(run 'bitte baue ein neues feature ins backend')" "[senior-dev intake]" ""
echo "$(run 'bitte baue ein neues feature ins backend')" | grep -qF "Routing hint" || { echo "FAIL: routing hint missing on code prompt"; FAILS=$((FAILS+1)); }
check "non-code prompt gets intake, no routing hint" "$(run 'Danke, sieht gut aus')" "[senior-dev intake]" "Routing hint"
check "empty prompt silent" "$(printf '{"prompt":""}' | bash "$HOOK")" "" ""
check "slash command silent" "$(run '/help')" "" ""

[ "$FAILS" -eq 0 ] && echo "ALL PASS" || echo "$FAILS FAILURES"
exit "$FAILS"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash test/hooks/test_prompt_check.sh`
Expected: FAIL lines (current v10 hook is silent on non-code prompts and has no `[senior-dev intake]` marker), non-zero exit.

- [ ] **Step 3: Rewrite the hook** — replace the full content of `hooks/code-guardian-prompt-check.sh` with:

```bash
#!/bin/bash
# Code Guardian UserPromptSubmit Hook (v16)
#
# Fires on EVERY user prompt (v16: was code-triggers-only). Injects the
# senior-dev intake instruction — take on the request as a senior full-stack
# developer, triage, then route. Appends a mode routing hint when the prompt
# looks like a code change or bug report (de/en trigger words). Silent only
# on empty prompts and slash commands.
#
# Wired into ~/.claude/settings.json → hooks.UserPromptSubmit

PROMPT=$(jq -r '.prompt // empty' 2>/dev/null)
[ -z "$PROMPT" ] && exit 0
case "$PROMPT" in "/"*) exit 0 ;; esac

HINT=""
if echo "$PROMPT" | grep -qiE 'bug|error|fehler|broken|kaputt|funktioniert|geht nicht|404|500|exception|stack trace|fix|repar|change|update|implement|build|create|refactor|integrat|migrat|deploy|[äÄ]nder|aender|anpass|f[üÜ]ge|fuege|hinzu|baue|erstell|einbau|entfern|l[öÖ]sch|loesch|feature|route|controller|model|migration|component|endpoint|api|css|style|template'; then
  HINT=" Routing hint: looks like a code change or bug report — after intake route: bug/error -> code-guardian DEBUG MODE; spec/plan -> PLAN MODE; build/change -> BUILD MODE (pre-flight before code, audit after). Per ~/.claude/CLAUDE.md this is mandatory and runs combined with superpowers."
fi

cat <<JSON
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[senior-dev intake] Load the senior-dev skill first (if not loaded this session) and take on this request as a senior full-stack developer: triage (question/trivial/normal/large), run the intake at that depth, then route.${HINT}"}}
JSON
exit 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash test/hooks/test_prompt_check.sh`
Expected: `ALL PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add hooks/code-guardian-prompt-check.sh test/hooks/test_prompt_check.sh
git commit -m "feat(hooks): v16 prompt hook fires on every prompt — senior-dev intake first"
```

---

### Task 3: §D heartbeat in the post-edit hook (`hooks/code-guardian-reminder.sh`)

**Files:**
- Modify: `hooks/code-guardian-reminder.sh:23-35` (inside the code-file case, before the `cat <<EOF`)
- Create: `test/hooks/test_reminder_heartbeat.sh`
- Create: `test/hooks/run.sh`

**Interfaces:**
- Consumes: existing reminder hook structure (INPUT/FILE_PATH/HINT variables, heredoc output).
- Produces: heartbeat lines containing `Senior view:` and `(senior-dev card §D)`; `test/hooks/run.sh` used by Task 6 verification and CI.

- [ ] **Step 1: Write the failing test** — create `test/hooks/test_reminder_heartbeat.sh`:

```bash
#!/bin/bash
# Tests for the v16 §D heartbeat in hooks/code-guardian-reminder.sh.
set -u
HOOK="$(cd "$(dirname "$0")/../.." && pwd)/hooks/code-guardian-reminder.sh"
SID="cg-test-$$"
CF="${TMPDIR:-/tmp}/cg-heartbeat-${SID}"
rm -f "$CF"
FAILS=0

edit() { printf '{"session_id":"%s","tool_input":{"file_path":"%s"}}' "$SID" "$1" | bash "$HOOK"; }

O1=$(edit /tmp/proj/a.php); O2=$(edit /tmp/proj/b.php); O3=$(edit /tmp/proj/c.php)
echo "$O1$O2" | grep -qF "Senior view:" && { echo "FAIL: heartbeat before 3rd edit"; FAILS=$((FAILS+1)); }
echo "$O3" | grep -qF "Senior view:" || { echo "FAIL: no heartbeat on 3rd edit"; FAILS=$((FAILS+1)); }
echo "$O3" | grep -qF "(senior-dev card §D)" || { echo "FAIL: heartbeat missing card reference"; FAILS=$((FAILS+1)); }
echo "$O3" | jq -e '.hookSpecificOutput.additionalContext' >/dev/null 2>&1 || { echo "FAIL: 3rd-edit output invalid JSON"; FAILS=$((FAILS+1)); }
edit /tmp/proj/d.php >/dev/null; edit /tmp/proj/e.php >/dev/null; O6=$(edit /tmp/proj/f.php)
# Compare ONLY the heartbeat question (text after "Senior view:"), not the full
# context — that also contains the basename and would differ regardless.
Q3=$(echo "$O3" | jq -r '.hookSpecificOutput.additionalContext' | grep -o 'Senior view:.*')
Q6=$(echo "$O6" | jq -r '.hookSpecificOutput.additionalContext' | grep -o 'Senior view:.*')
[ -n "$Q3" ] && [ "$Q3" = "$Q6" ] \
  && { echo "FAIL: heartbeat question did not rotate between 3rd and 6th edit"; FAILS=$((FAILS+1)); }
OMD=$(edit /tmp/proj/readme.md)
[ -z "$OMD" ] || { echo "FAIL: non-code file produced output"; FAILS=$((FAILS+1)); }
[ "$(cat "$CF")" = "6" ] || { echo "FAIL: counter is $(cat "$CF"), expected 6 (md file must not count)"; FAILS=$((FAILS+1)); }

rm -f "$CF"
[ "$FAILS" -eq 0 ] && echo "ALL PASS" || echo "$FAILS FAILURES"
exit "$FAILS"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash test/hooks/test_reminder_heartbeat.sh`
Expected: FAIL (no `Senior view:` in current hook), non-zero exit.

- [ ] **Step 3: Implement the heartbeat.** In `hooks/code-guardian-reminder.sh`, inside the code-file case after the existing `HINT` block (after line 31 `esac`) and before the `cat <<EOF`, insert:

```bash
    # v16 §D heartbeat: every 3rd counted code edit, rotate one senior meta-question
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "nosession"')
    COUNTER_FILE="${TMPDIR:-/tmp}/cg-heartbeat-${SESSION_ID}"
    COUNT=$(( $(cat "$COUNTER_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$COUNT" > "$COUNTER_FILE"
    HEARTBEAT=""
    if [ $((COUNT % 3)) -eq 0 ]; then
      case $(( (COUNT / 3 - 1) % 4 )) in
        0) Q="Senior view: does this still make sense, seen from outside?" ;;
        1) Q="Senior view: are you writing something that already exists in this codebase?" ;;
        2) Q="Senior view: still inside the task scope — no drive-by refactoring?" ;;
        3) Q="Senior view: two failed attempts on the same spot? Stop, write assumptions down, change approach." ;;
      esac
      HEARTBEAT=" ${Q} Answer honestly in one sentence before continuing. (senior-dev card §D)"
    fi
```

Then change the heredoc line 34 so `${HEARTBEAT}` is appended after `${HINT}`:

```bash
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[code-guardian] ${BASENAME} edited. The change is not done until the skill's Step 3 audit ran on the full diff (triage 3a decides depth; every check Verified-by command output, and Step 2 re-seeds the dependency worklist).${HINT}${HEARTBEAT}"}}
```

And update the header comment block (lines 2–10) to say `(v16)` and mention the heartbeat:

```bash
# Code Guardian PostToolUse Hook (v16)
#
# Fires after every Write|Edit on a code file: injects the audit reminder
# (unchanged since v10) and — new in v16 — a rotating senior-dev §D
# meta-question every 3rd counted edit (session-scoped counter in
# ${TMPDIR}/cg-heartbeat-<session_id>). Non-code files stay silent and do
# not advance the counter.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash test/hooks/test_reminder_heartbeat.sh`
Expected: `ALL PASS`, exit 0.

- [ ] **Step 5: Create the runner** `test/hooks/run.sh`:

```bash
#!/bin/bash
# Runs all hook tests. Exit 0 only if every suite passes.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL=0
for t in "$DIR"/test_*.sh; do
  echo "== $t"; bash "$t"; TOTAL=$((TOTAL + $?))
done
[ "$TOTAL" -eq 0 ] && echo "HOOK SUITES: ALL PASS" || echo "HOOK SUITES: $TOTAL failures"
exit "$TOTAL"
```

- [ ] **Step 6: Run the full hook suite**

Run: `bash test/hooks/run.sh`
Expected: both suites `ALL PASS`, `HOOK SUITES: ALL PASS`, exit 0.

- [ ] **Step 7: Commit**

```bash
git add hooks/code-guardian-reminder.sh test/hooks/test_reminder_heartbeat.sh test/hooks/run.sh
git commit -m "feat(hooks): v16 §D heartbeat — rotating senior meta-question every 3rd edit"
```

---

### Task 4: Installer ships `senior-dev` (`install.sh`)

**Files:**
- Modify: `install.sh` (header lines 3–9; vars after line 27; sanity check after line 66; new install block after the llm-council block ending line 177)

**Interfaces:**
- Consumes: `senior-dev/SKILL.md` from Task 1 (marker `name: senior-dev`).
- Produces: installed skill at `~/.claude/skills/senior-dev/` for the monitoring phase.

- [ ] **Step 1: Add source/target vars.** After line 27 (`COUNCIL_TARGET_DIR=...`), insert:

```bash
# Bundled companion skill — senior-dev (v16): task intake + persistent senior
# mindset; loaded first on every prompt by the v16 prompt-check hook.
SENIOR_SOURCE_DIR="${SCRIPT_DIR}/senior-dev"
SENIOR_TARGET_DIR="${TARGET_ROOT}/senior-dev"
```

- [ ] **Step 2: Add sanity check.** Next to the existing council check (line 66), insert:

```bash
[ -f "$SENIOR_SOURCE_DIR/SKILL.md" ] || die "Bundled companion missing: $SENIOR_SOURCE_DIR/SKILL.md"
```

- [ ] **Step 3: Add install block.** After the llm-council block (after line 177), insert a mirrored block — same overwrite/force/dry-run semantics, `senior_exists` variable name, and verification marker:

```bash
# Companion skill: senior-dev (bundled, v16). The prompt-check hook instructs
# every session to load it first; without it installed the instruction dangles.
log "Companion skill: senior-dev"
senior_exists=0
{ [ -d "$SENIOR_TARGET_DIR" ] || [ -L "$SENIOR_TARGET_DIR" ]; } && senior_exists=1
if [ "$senior_exists" -eq 1 ] && [ "$FORCE" -eq 0 ] && [ "$DRY_RUN" -eq 0 ]; then
    warn "Existing senior-dev found — updating with bundled copy (companion is versioned with this package)"
fi
if [ "$DRY_RUN" -eq 0 ]; then
    rm -rf "$SENIOR_TARGET_DIR"
    cp -R "$SENIOR_SOURCE_DIR" "$SENIOR_TARGET_DIR"
    if grep -q "name: senior-dev" "$SENIOR_TARGET_DIR/SKILL.md" 2>/dev/null; then
        ok "senior-dev installed -> $SENIOR_TARGET_DIR (intake gate operational)"
    else
        die "senior-dev verification failed: marker 'name: senior-dev' not found in $SENIOR_TARGET_DIR/SKILL.md"
    fi
else
    ok "senior-dev would be installed -> $SENIOR_TARGET_DIR (dry-run)"
fi
```

Note the deliberate difference from llm-council: senior-dev is ALWAYS updated
(it is versioned with the package), while llm-council is left as-is unless
`--force` (it may be user-customized). This is per spec: the companion and the
hooks must stay in lockstep.

- [ ] **Step 4: Bump the header.** Replace lines 3–9 with:

```bash
# Code Guardian Skill Installer (v16)
# -----------------------------------
# Installs / updates the code-guardian skill for Claude Code, the bundled
# llm-council and senior-dev companions, and the four session hooks
# (prompt-check — v16: fires on every prompt and loads senior-dev first —
# audit reminder incl. §D heartbeat, DECISION GATE + DEPLOY GATE enforcement)
# incl. settings.json registration.
# Works on macOS and Linux.
```

- [ ] **Step 5: Verify with dry-run**

Run: `./install.sh --dry-run 2>&1 | grep -E "senior-dev|v16"`
Expected: `senior-dev would be installed -> /Users/<user>/.claude/skills/senior-dev (dry-run)` and no `die` output; exit 0.

- [ ] **Step 6: Commit**

```bash
git add install.sh
git commit -m "feat(installer): bundle senior-dev companion (v16) — always versioned with package"
```

---

### Task 5: Phase anchors in code-guardian (+ v16 bump)

**Files:**
- Modify: `code-guardian/SKILL.md` (title line 37; Mode Selection section ~line 49)
- Modify: `code-guardian/references/plan-mode.md` (under `## Plan Audit`, line 24)
- Modify: `code-guardian/references/build-mode.md` (under Step 1 line 17, Step 2 line 105, Step 3 line 120)
- Modify: `code-guardian/references/debug-mode.md` (under `### Escalation`, line 38)

**Interfaces:**
- Consumes: `senior-dev/references/senior-card.md` §B–§E from Task 1.
- Produces: nothing downstream; pure wiring.

- [ ] **Step 1: SKILL.md.** Change line 37 `# Code Guardian (v15)` → `# Code Guardian (v16)`. In the `## Mode Selection` section, add as the first paragraph:

```markdown
Task intake happens upstream in the **senior-dev** companion skill (bundled,
loaded first on every prompt by the v16 hook): it triages every request and
routes here. If no intake ran this session, run senior-dev Stage 0 triage
before picking a mode.
```

- [ ] **Step 2: plan-mode.md.** As its own paragraph directly after the intro paragraph ("Bugs that survive the audit…", line 5) and BEFORE P1 — NOT inside the fenced output template at the bottom (its `## Plan Audit` line is template text, not a section heading) — add:

```markdown
Senior view first: re-read senior-dev `references/senior-card.md` §B and
answer its architecture questions against this plan before auditing (right
problem? already exists? simplest design? trade-offs named? DB normalized?).
```

- [ ] **Step 3: build-mode.md.** Directly under `### Step 1: Pre-Flight (before writing code)` add:

```markdown
Senior view: senior-card §B — right problem, already-exists search, simplest
design, named trade-offs — before designing the change.
```

Directly under `### Step 2: Post-Change Verification — second fixpoint` add:

```markdown
Senior view: senior-card §C+§D while the diff is open — 6-month test, DRY,
scope fence, does-this-still-make-sense.
```

Directly under `### Step 3: Audit (after writing code — always)` add:

```markdown
Senior view: senior-card §E closes the task — self-review as foreign code,
plain-language explainability, journal the lesson.
```

- [ ] **Step 4: debug-mode.md.** Directly under `### Escalation` add:

```markdown
Senior view: this is senior-card §D — two failed attempts means stop, write
assumptions down, change approach; sunk cost is not a reason to continue.
```

- [ ] **Step 5: Verify anchors**

Run: `grep -rn "senior-card\|senior-dev" code-guardian/ | wc -l`
Expected: ≥ 6 hits (1 SKILL.md, 1 plan-mode, 3 build-mode, 1 debug-mode).

- [ ] **Step 6: Commit**

```bash
git add code-guardian/
git commit -m "feat(code-guardian): v16 — senior-card phase anchors in plan/build/debug modes"
```

---

### Task 6: Full verification sweep

**Files:**
- Test: `test/hooks/run.sh`, existing suite `test/`

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Hook suite**

Run: `bash test/hooks/run.sh`
Expected: `HOOK SUITES: ALL PASS`, exit 0.

- [ ] **Step 2: Existing detector tests (regression)**

Run: `cd /Applications/MAMP/htdocs/codeguard && python3 -m pytest code-guardian/tools/tests/ -q 2>/dev/null || for f in code-guardian/tools/tests/test_*.py; do python3 "$f"; done`
Expected: all pass, zero failures.

- [ ] **Step 3: Shellcheck-style sanity (no shellcheck dependency — bash -n)**

Run: `bash -n hooks/code-guardian-prompt-check.sh && bash -n hooks/code-guardian-reminder.sh && bash -n install.sh && bash -n test/hooks/run.sh && echo SYNTAX-OK`
Expected: `SYNTAX-OK`

- [ ] **Step 4: Commit anything outstanding, then code-guardian BUILD Step 3 audit over the full v16 diff** (`git diff main...HEAD`) — every finding fixed or reported before proceeding to install/monitoring.

## Plan Audit (Code Guardian PLAN MODE)

P1 Cross-Layer Trace: PASS — Verified-by: name/path consistency grep — `senior-dev` 50 hits, marker `name: senior-dev` present in Task 1 content AND Task 4 install verification, `references/senior-card.md` referenced 8× (created Task 1, consumed Tasks 3/5).
P2 Scale Verification: PASS (N/A) — Verified-by: grep for cursor/lazyById/SELECT/query → 0 hits; plan touches no DB.
P3 Secrets Hygiene: PASS — Verified-by: grep `?key=|?api_key=|?token=|secret` → 0 hits.
P4 Cached-Config Safety: PASS — Verified-by: env-read grep → only `${TMPDIR:-/tmp}` in bash hooks (execution-time read, no cached-config runtime involved).
P5 Pattern Source Quality: PASS — Verified-by: pattern sources are the llm-council installer block (v12-audited) and the v10 reminder hook (v10-audited); the one deliberate deviation (senior-dev ALWAYS updated vs council leave-as-is) is documented in Task 4 Step 3 with reason (companion versioned in lockstep with hooks).
P6 WIP Staging Discipline: PASS — Verified-by: grep `git add .`/`-A` → 0 hits; all commit steps use explicit paths; working tree WIP (untracked zip, this plan file) does not overlap any task path.
P7 Generalization: PASS — Verified-by: example-literal-in-control-flow grep → 0 hits. Heartbeat questions are a fixed content rotation (data), not example-driven branching; the routing-hint regex is a non-correctness-bearing UX hint (intake fires on every prompt regardless) — INTENTIONAL-SPECIAL-CASE: heuristic hint only.
