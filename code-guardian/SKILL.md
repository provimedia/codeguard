---
name: code-guardian
description: >
  MANDATORY for ANY code change — no exceptions, no rationalization, no "this is just a small thing".
  Use when: writing code, editing files, changing any function/method/component, fixing bugs,
  adding features, refactoring, integrating libraries, updating imports, changing imports,
  adding images, adding routes, modifying templates, modifying styles, modifying configs,
  adding form fields, changing controllers, changing models, changing services, changing migrations.
  Use when: encountering any error, 404, 500, exception, stack trace, "doesn't work", "is broken",
  "won't load", "shows nothing", "wrong data", "missing X". Run cross-page dependency trace.
  Use when: someone asks "wurde X eingebaut", "funktioniert Y", "warum macht Z das nicht".
  ESPECIALLY trigger when: changing shared functions, helpers, utilities, layouts, middlewares,
  models, migrations — anything used in multiple places.
  TRIGGER PHRASES: "change", "update", "add", "fix", "refactor", "integrate", "build", "create",
  "implement", "aendere", "fuege hinzu", "fixe", "baue", "erstelle", "implementiere".
  Use when (opt-in CLEANUP MODE): "clean up", "räum auf", "aufräumen", "dead code", "toten Code",
  "unused", "ungenutzt", "orphan", "verwaist", "redundant", "remove duplicates" — report-only, never deletes productive code.
  Use when (DECISION GATE): about to present the user ANY option question (A/B/C, variant 1/2/3,
  "which approach?") — a recommendation is mandatory first; the gate recommends, the user decides.
  ANTI-RATIONALIZATION: If you think "this is too small to need an audit" — that IS the trigger.
  If you think "I already understand this" — that IS the trigger.
  If you think "the user is waiting, just do it quickly" — that IS the trigger.
  Bugs that ship are caused by skipped audits. Run the workflow EVERY TIME.
---

# Code Guardian (v12)

## Operating Principles

Stated once; they govern every mode below. The skill defines goals and gates — how you reach a gate is your judgment; whether you pass it is not.

1. **Evidence over assertion.** Before reporting progress or a verdict, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. "Ran X, got Y" with pasted output is proof. "I read the code and it looks right" is not.
2. **Act when ready.** Run a reflex, record the result, move on. Do not re-derive established facts, re-litigate decided questions, or narrate checks you will not run. Pre-flight is preparation for action, not a substitute for it.
3. **Stay in scope — with one carve-out for your own mess.** Findings in code that existed *before this change* are *reported*, never silently fixed or deleted — no refactoring, tidying, or new abstractions beyond the task; a bug fix doesn't need surrounding cleanup. The one exception: AI-slop *this change itself* introduced (unused symbols/imports you just added, debug leftovers, redundant comments, single-use abstractions you just invented) IS in scope — strip it before "done" (the always-on Self-Slop Sweep, `references/build-mode.md` Step 3). Cleaning up pre-existing dead/orphaned/redundant code is a separate, opt-in, **report-only** path (CLEANUP MODE) that never deletes on its own.
4. **Fan out independent work.** When items are independent — consumers to classify, audit layers to verify, hypotheses to argue — dispatch parallel subagents instead of iterating serially. Marked ⚡ in the mode files. Subagents receive: the exact check to run, the diff/symbol context, and the required output format (verdict + command output).
5. **Write down what you learn.** `.audit-log.md` (findings & patterns), `.code-guardian-propagation.md` (open worklists for large changes). Consult both at the start of a run; keep them current. One lesson per entry, with why it mattered.

## Mode Selection

```
Task received
  ├─ Bug/Error/Broken? ───────→ DEBUG MODE
  ├─ Spec/Plan exists? ───────→ PLAN MODE (review plan before implementation)
  ├─ Explicit "clean up / remove dead/unused/redundant EXISTING code"?
  │                          ──→ CLEANUP MODE (opt-in, report-only — never deletes)
  └─ Build/Change/Fix?  ──────→ BUILD MODE
                              ├─ Pre-Flight (BEFORE code)
                              └─ Audit (AFTER code, incl. always-on Self-Slop Sweep on the diff)
```

Each mode is **mutually exclusive** — the full protocol lives in a per-mode reference file. Read ONLY the selected mode's file; that keeps this always-loaded body small (progressive disclosure). The skeleton below is the router, not the whole procedure — **load the mode file before acting.**

The **DECISION GATE** is orthogonal to mode selection: it fires in ANY mode (and outside them) the moment an option question is about to go to the user.

## Reference Files (progressive disclosure)

The full catalog lives in `references/` next to this file. Load with the Read tool when the rule says so — not preemptively. Reference files cost zero tokens until read.

| File | Contents | Load when |
|---|---|---|
| `references/plan-mode.md` | P1–P6 plan reflexes + output template | PLAN MODE selected |
| `references/build-mode.md` | Pre-flight 1a–1e (schema query, 1d worklist engine, 1e gate), Step 2 symbol-loss + re-seed, Step 3 audit (cross-layer index, 6 layers, R1–R5, report/verdict) | BUILD MODE selected — **read before writing code** |
| `references/debug-mode.md` | 5-phase debug protocol + escalation | DEBUG MODE selected |
| `references/cleanup-mode.md` | opt-in report-only dead/orphaned/redundant-code protocol: liveness-veto gate, framework FP-category gate, per-language detectors, redundancy counter-rule | CLEANUP MODE selected (explicit cleanup request only) |
| `references/decision-gate.md` | T1 rubric matrix, T2 advocate / T3 council escalation triggers, binding "(Empfohlen)" output template | DECISION GATE fires (an option question is about to go to the user) |
| `references/cross-layer-checks.md` | 36 cross-layer reflexes, each with audit commands + the real bug it came from | a cross-layer index trigger matches (index is in `build-mode.md` Step 3) |
| `references/audit-deep-checks.md` | Full-depth layer checks (DB, Logic, Efficiency, Security) + R1–R5 redundancy detectors in detail | any audit layer runs at full depth |
| `references/design-rationale.md` | rule history + council-gate rationale | only when modifying this skill itself |

---

## PLAN MODE

Spec/plan exists → **Read `references/plan-mode.md`** and run the 6 plan reflexes against the plan/spec (and again when receiving a plan from another author):

P1 Cross-Layer Trace · P2 Scale Verification · P3 Secrets Hygiene · P4 Cached-Config Safety · P5 Pattern Source Quality · P6 WIP Staging Discipline.

Record each PASS/FAIL with command-output proof. Any FAIL → the plan is **BLOCKED** until its author fixes it; no subagent dispatch before all six PASS. Full reflex text + output template: `references/plan-mode.md`.

---

## BUILD MODE

Build/change/fix → classify pre-flight depth, then **Read `references/build-mode.md`** before writing code and follow Steps 1–3 in full. The trigger never scales — the **depth** does:

| Change shape | Pre-flight depth |
|---|---|
| Comment/doc/copy-text only, zero behavior change | 1a only; audit runs LIGHT |
| Additive, single file, no shared symbol, no DB | 1a–1c; 1d as a one-hop consumer check |
| Touches a shared function/helper/model/layout/middleware, a schema, a status value's semantics, config keys, or deletes anything | Full 1a–1e; 1d driven to fixpoint |

When unsure which row applies, take the deeper one.

- **Step 1 — Pre-Flight (before code):** 1a Scope · 1b Schema Check (live DB introspection) · 1c Existing-Code & Duplicate-Resource scan · **1d Recursive Dependency Propagation** (QUEUE/VISITED/LEDGER worklist to fixpoint — the most critical step) · 1e **Blast-Radius Council Gate**.
- **Step 2 — Post-Change Verification:** run the symbol-loss gate (`detect-symbol-loss.py`), re-seed the 1d worklist from the real diff, drain to fixpoint.
- **Step 3 — Audit (ALWAYS runs; triage scales depth, never existence):** intensity triage → 6 layers (DB · Logic · Efficiency · Redundancy R1–R5 · Security · Self-Slop Sweep [always-on, diff-only]) → report with VERIFIED command output → append `.audit-log.md`. Verification-not-assertion: dump the real payload/grep/endpoint, never "looks right".

Full engine, schema query, cross-layer index, R1–R5 commands, report + verdict rules: `references/build-mode.md`.

---

## DEBUG MODE

Bug/error/broken → **Read `references/debug-mode.md`** and run the 5 phases (no fix before Phase 4):

1. **COLLECT** — symptom · recent changes · read the whole function + 2 levels of callers/callees · cross-page dependency trace (1d worklist).
2. **ROOT CAUSE** — WHAT/WHERE/WHEN/WHY/why-not-caught; 3 ranked candidates (always include "dependency break from a recent shared-function change").
3. **TWO PATHS** — minimal vs structural (⚡ parallel advocates); council gate only when the paths materially diverge.
4. **VALIDATE before touching code** — call-chain trace + recursive consumer verification to fixpoint.
5. **IMPLEMENT + VERIFY** — fix · repro test green · existing tests green · symbol-loss gate + Audit on the fix diff.

Escalation: failed twice → convene `llm-council` unconditionally. Full protocol: `references/debug-mode.md`.

---

## CLEANUP MODE

Explicit request to clean up / remove dead / orphaned / unused / redundant **existing** code (NOT the current task's own output — that is the always-on Self-Slop Sweep in BUILD MODE). **Read `references/cleanup-mode.md`** and run the report-only protocol:

1. **Inventory** candidates with whatever per-language detectors are installed (knip/ts-prune · vulture/ruff · phpstan/psalm/shipmonk) — candidate lists, never verdicts.
2. **Classify** every candidate via `detect-dead-code.py --liveness … --root <src> --exclude <manifests/docs>` into LIVE / ASSERTED-DEAD / VERIFIED-DEAD-PRIVATE under the liveness-veto law. Scan the source, not the answer key — exclude data manifests/changelogs that name symbols without calling them.
3. **Cross-check** survivors against ALL file types (templates/config/JSON/SQL/i18n) — string-resolved references defeat static graphs.
4. **Redundancy** via R2/R3/R5 with the Rule-of-Three guard (`--extract-threshold 3`); extract only same-knowledge ≥3-site clones, never build the wrong abstraction.
5. **Report only.** Emit a classified report; the skill never deletes. The human decides every removal; if asked to act, one symbol per commit, git-recoverable, tests green, re-audited.

Core invariant: **any single positive signal proves LIVE and vetoes removal; absence of references never proves dead.** Only closed-world (private / non-exported) symbols with 0 refs and no keep-alive flag can ever reach VERIFIED-DEAD-PRIVATE. Full protocol: `references/cleanup-mode.md`.

---

## DECISION GATE

About to present the user an option question (A/B/C, variant 1/2/3, "which approach?", any `AskUserQuestion`) → **Read `references/decision-gate.md`** and run the gate BEFORE asking. No option question leaves without a recommendation; the gate never creates questions that need not be asked.

- **T1 Rubric (always):** score options on Longevity/Maintainability · Architectural cleanliness · Reversibility/Lock-in · Follow-up cost · Best-practice conformity. Tie-break: **long-term beats short-term**.
- **T2 Advocates (⚡):** options materially diverge AND no clear T1 winner → one parallel advocate subagent per option.
- **T3 Council:** hard-to-reverse OR ≥ 5 consumers OR foundation decision (schema/auth/payment/framework) → convene `llm-council` (bundled).
- **Output (binding):** recommended option FIRST, label suffixed "(Empfohlen)" / "(Recommended)", + 1–2 sentence rubric justification; every other option fair, with its honest trade-off.
- **The gate recommends; the user decides.** Autonomous deciding is forbidden — and the gate advises, it never verifies.

Full rubric, escalation triggers, council framing, output template: `references/decision-gate.md`.

---

## Self-Tuning

When reading `.audit-log.md` at audit start:
- A finding type appeared 3+ times recently → flag **SYSTEMIC**, recommend a structural fix, not another point fix.
- A category with 0 findings in the last 10 audits → run at reduced depth.
- A category firing on >50% of audits → run it first and most aggressively.

## Core Rules

- **Pre-flight is not optional** — schema check before code prevents whole bug categories. **The audit always runs** — triage scales depth, never existence.
- **Live DB beats any static file.** No DB access → ask once; if unavailable, audit without the DB layer and mark "⚠️ DB unchecked".
- **Output proportional to findings** — clean code gets one line; problems get detail.
- **The council advises; commands verify.** LLM-council output is never a substitute for command-output proof.
- **Never delete productive code; absence of references never proves dead.** Any single positive signal (a reference, a route/template/DI/DB-dispatch/config hit) vetoes removal. CLEANUP MODE is report-only; the Self-Slop Sweep removes only your own just-added, zero-reference diff code.
- **Duplication is cheaper than the wrong abstraction.** Never extract a shared abstraction to kill duplication unless ≥3 sites (Rule of Three) AND they encode the same knowledge (one reason to change). Cleaning slop must not create slop.
- **The gate recommends; the user decides.** No option question to the user without a "(Empfohlen)" recommendation (DECISION GATE) — and never decide autonomously what the user reserved for themselves.
- Version history and gate rationale: `references/design-rationale.md` (load only when editing this skill).
