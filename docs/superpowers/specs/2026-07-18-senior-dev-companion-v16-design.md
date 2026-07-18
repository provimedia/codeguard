# Code Guardian v16 — Senior Dev Companion (`senior-dev`) — Design

Date: 2026-07-18 · Status: approved by CEO (brainstorming session, 3 decisions recorded below)

## Problem

Code Guardian starts too late. Every mode (PLAN/BUILD/DEBUG) and every gate fires
*after* a task has already been accepted and shaped — but the team consists of
vibe coders without engineering experience, and the biggest quality gap sits
*before* the first tool call: how a senior full-stack developer **thinks**.

Missing today:

1. **Task intake.** Nobody restates the goal, checks ambiguity, sizes the risk,
   or decides "spike first vs. build now" before work starts.
2. **The senior's inner monologue.** Experienced developers continuously ask
   themselves questions while working — "does this already exist?", "am I
   guessing or do I understand?", "does this still make sense?" — and the team
   does not. A checklist at the start is not enough; the questions must stay
   active through planning, coding, and completion.
3. **Skill-first reflex.** Recurring task types should become skills
   (Anthropic's own finding: verification skills had the most measurable
   quality impact), but nobody notices recurrence.

## Decision

Build a **companion skill `senior-dev`** (bundled and installed exactly like
`llm-council`), loaded at the start of EVERY prompt via the upgraded
prompt-check hook. It takes on the task as a senior full-stack developer,
triages it, routes it into the existing machinery (code-guardian modes,
superpowers process skills) — and keeps the senior's questions in context until
the task is done.

Three CEO decisions (recorded 2026-07-18):

| # | Question | Decision |
|---|---|---|
| 1 | Intake depth | **Tiered triage** — intake always runs, depth scales with task class |
| 2 | Skill-building reflex | **Propose + 1-click** — never auto-build, never silent |
| 3 | Architecture | **Companion skill** — not a new code-guardian mode, not hook-only |

### Components

```
codeguard/
├── senior-dev/
│   ├── SKILL.md                    # triage + routing + card summary (progressive disclosure)
│   └── references/
│       └── senior-card.md          # the full question catalog (§A–§E)
├── hooks/
│   ├── code-guardian-prompt-check.sh   # v16: fires on EVERY prompt (was: code triggers only)
│   └── code-guardian-reminder.sh       # v16: adds rotating §D meta-question every Nth edit
├── install.sh                      # installs senior-dev alongside code-guardian + llm-council
└── code-guardian/references/       # plan/build/debug/audit get one-line §-anchors
```

Per-project memory: **`.task-journal.md`** (same pattern as `.audit-log.md`) —
one line per accepted task: date, task-type tag, triage class, outcome. This is
the evidence base for the Rule-of-Three skill proposal.

### Triage (Stage 0 — every prompt, seconds)

| Class | Criteria | Depth |
|---|---|---|
| Question/discussion | no work product requested | answer; no protocol |
| Trivial | one file, reversible, unambiguous | 3 core checks: restate goal, blast-radius glance, proof plan |
| Normal | multi-file or any data/shared-code touch | short intake (~8 checks from the card) |
| Large / unclear / risky | data, auth, payment, deploy, migrations, or ambiguous ask | full senior protocol incl. spike decision; superpowers:brainstorming → writing-plans → PLAN MODE |

Upgrading mid-task is always allowed; downgrading never.

### The Senior Card (`references/senior-card.md`) — §A–§E

**§A Intake** — restate the goal in own words · acceptance criteria before work
· scope fence (what is explicitly NOT part of the task) · ambiguity → ask ONE
targeted question instead of guessing · known unknowns listed · assumptions
written down as hypotheses · spike decision: enough knowledge to build, or
timeboxed exploration first? · context reading list (which files/docs to read
BEFORE the first edit) · **skill inventory check: is there already a skill for
this?** · **Rule of Three: 2nd–3rd occurrence per journal → propose building a
skill (1-click approval; built via superpowers:writing-skills only after
consent)** · route to the right process (DEBUG/PLAN/BUILD, TDD)

**§B Architecture & design** — am I solving the RIGHT problem? (validate the
problem before building a solution) · **does this already exist?** function,
class, helper, package — search the codebase before writing anything new ·
how does THIS project do it? (follow existing patterns) · simplest design that
works (KISS; no abstraction for an imagined future — "premature flexibilization
is the root of whatever evil is left") · do we need it NOW? (YAGNI) · name the
trade-offs: performance vs. maintainability vs. simplicity vs. time — which one
matters for THIS task? · second-order effects: what follow-up costs does the
fast path create? · **database: new table or new column? normalize to 3NF/4NF
by default, denormalize only with a MEASURED reason; FK + constraints against
invalid states; indexes follow real query patterns**

**§C While coding (the senior looks over your shoulder)** — do I understand
what I am writing, or am I guessing? code I cannot explain does not get
committed · the 6-month test: does the code tell its own story? names express
intent, no magic numbers · am I repeating myself? second copy of the same logic
→ is there a shared place for it? · is this function/class/file getting too
big? one responsibility per unit · edge cases: null, empty, zero, huge,
concurrent, error path · does it scale? works at 10 rows AND at 1 million
(loops, N+1, missing indexes) · comments explain WHY, never WHAT · am I still
in scope? no drive-by refactoring

**§D Meta view (continuous — "does this make sense?")** — does this still make
sense, seen from outside? · rabbit-hole check: two failed attempts → stop,
write down assumptions, change approach (aligns with the existing two-failure
Escalation) · sunk-cost test: would I still choose this path if I started
fresh today? · am I fighting the framework? when everything feels hard, the
approach is usually wrong, not the framework

**§E Completion** — self-review as if it were someone else's code · proof over
assertion (VERIFIED, existing rule) · **explainability: summarize the result in
plain language; the developer must be able to explain every line in review** ·
write what you learned into the journal

### Context-persistence mechanics (the actual innovation of v16)

Three layers keep the card active from intake to completion:

1. **Load at intake.** The hook instructs loading `senior-dev` on every prompt;
   the card enters conversation context once per session and stays there.
2. **Phase anchors.** One-line references in the existing mode files re-invoke
   the card at each step: plan-mode → §B, build-mode → §C+§D, debug-mode → §D,
   final audit → §E. Small edits; no restructuring.
3. **Deterministic heartbeat.** `code-guardian-reminder.sh` (PostToolUse on
   Edit/Write) injects one rotating §D question every Nth edit (default N=3;
   session-scoped counter file). Research finding: guardrails that do not
   depend on model discretion are the ones that hold — and the heartbeat
   survives context compaction.

### Hook contract (v16)

`code-guardian-prompt-check.sh`: fires on EVERY prompt. Output = ONE JSON
additionalContext line: "load senior-dev first, triage, then route". The
existing code-trigger detection stays as a routing hint appended to the same
line (bug → DEBUG, build → BUILD, plan → PLAN). No double injection.

`code-guardian-reminder.sh`: keeps its existing audit-reminder behavior;
additionally rotates through the §D questions (counter in
`${TMPDIR}/cg-heartbeat-<session>`), one short line every Nth Edit/Write.

## Rejected alternatives

- **New INTAKE MODE inside code-guardian** — the skill is already 7 modes/gates
  deep; intake must also cover non-code tasks where a "code guardian" is the
  wrong persona. Anthropic's catalog finding: skills that do too much confuse
  the agent.
- **Hook-only (inject the full checklist every prompt)** — permanent context
  bloat; violates the v10 progressive-disclosure principle.
- **Auto-building skills on recurrence** — skill sprawl by inexperienced users;
  contradicts the house rule "the gate recommends, the user decides".
- **Full protocol on every prompt** — a 20-point protocol on a button-color fix
  teaches the team to bypass the gate.

## Validation

1. **Unit:** bash tests for both hooks (always-fires, valid JSON, routing hint
   correctness, heartbeat rotation & counter reset).
2. **Fixtures:** triage table — representative prompts → expected class
   (question/trivial/normal/large) documented in the skill; spot-checked in
   monitored sessions.
3. **Integration (testbed):** standalone PHP+SQLite mini-project outside the
   repo. Monitored headless sessions: build a feature, inject + report + fix a
   bug, plan a feature, update, deletion. Transcript review: hook fired, skill
   loaded, triage class correct, §-anchors visible in behavior, heartbeat
   present, skill proposal appears on repeated task type.
4. **Regression:** existing test suite stays green; deployed skill diff clean
   after install.sh.

Done = the skill demonstrably does in live sessions what this spec describes.

## Addendum v16.1 (2026-07-19, post-monitoring)

Two design changes after live monitoring, both already shipped:

1. **Tag law (fix from monitoring S6a/b):** journal type-tags name the task
   TYPE, never the instance (`api-endpoint`, not `stats-endpoint`); exactly ONE
   journal line per task; recurrence is counted by TYPE across older narrower
   tags. Without this, sessions invent instance tags and Rule of Three never
   fires (observed live, fixed, re-verified in S6c).
2. **Plan-Mode airlock (CEO request):** triage class large/unclear/risky calls
   `EnterPlanMode` before ANY analysis — the whole §A/§B/planning phase runs
   hard read-only; `ExitPlanMode` presents the plan as the approval artifact,
   building starts only after the developer's approval. Headless fallback:
   same discipline by hand (read-only, present plan, stop). Trivial/normal
   never enter the airlock.
