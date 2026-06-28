# Design Rationale & Version History (v4–v9)

> Load only when modifying this skill itself. Records why each rule exists and which gate logic is non-negotiable.

## Rules

- **Pre-flight is not optional.** Checking the schema BEFORE writing code prevents entire categories of bugs.
- **The audit ALWAYS runs after code is written.** No exception. No "it's just a small change". No "I'll check later". Triage determines intensity per layer, but all 5 layers are checked every time — at minimum as spot-check.
- **Live DB beats any static file.** Always query the real database when DB access is available.
- **No DB access?** Ask once. If unavailable, run audit without DB layer and mark it "⚠️ DB unchecked".
- **Output proportional to findings.** Clean code gets one line. Problems get detail. No empty sections.

### v4 Verification Rules

- **VERIFICATION beats ASSERTION.** Read code is not proof. The audit must produce command output. The six reflexes this rule covers (JSON dump, hunt-and-replace, layout-link→route, accessor exposure, forbidden phrase list, read-check false-positive rate) are defined in depth in the Audit phase callout and in Cross-Layer Checks above — do not duplicate them here.

### v5 Plan-Time Rules (born from plan-time bugs, not code-time bugs)

- **PLAN MODE is not optional when a spec/plan exists.** Run the 6 plan reflexes (P1-P6) BEFORE dispatching any implementation subagent. A bug locked in at plan-time cascades through every subagent and every review. The reflex content lives in PLAN MODE above — do not duplicate it here.
- **Fix prescriptions themselves need review.** A code reviewer can correctly identify a bug AND prescribe a broken fix. When re-dispatching an implementer to fix quality issues, pre-validate the prescription against the actual call/query shape before shipping it. Don't trust your own review output blindly.

### v6 Redundancy Rules (born from copy-paste bugs that survived the v4 audit)

- **Redundancy is a five-reflex layer, not a one-line spot-check.** R1–R5 each have a helper script in `~/.claude/skills/code-guardian/tools/` and each emits a SUMMARY footer that is the Verified-by proof. "I checked, looks clean" is forbidden — paste the script output. The reflex content lives in BUILD MODE → Audit → Redundancy above — do not duplicate it here.
- **Pre-flight 1c is now three sub-steps**, one per redundancy class (secret/constant pre-check, function/class pre-search, template/view pre-search). Skipping pre-flight grep before adding a new identifier is the single most common source of duplicate hardcoded API keys, parallel utility functions, and inlined-instead-of-included headers/footers.
- **Cross-file is the signal threshold.** Same-file repetition is almost always framework boilerplate (Filament Resources, scaffolded controllers). Clone groups that span 2+ distinct files in the diff are the real DRY violations and must be either fixed or explicitly path-allowlisted with a documented reason in `.code-guardian-redundancy.yml`.

### v7 Council Rules (born from single-perspective decisions on high-stakes fix forks)

- **The LLM Council is a decision aid, NEVER a verification substitute.** It produces reasoned opinion; P1–P6, R1–R5, and every Cross-Layer check produce command-output proof. The council bolts onto the skill's genuine judgment points — DEBUG Phase 3's Path A/B Decision, the Phase-2-twice Escalation, and (v7.1) BUILD MODE Pre-Flight 1e Blast-Radius — and nowhere else. Requires the `llm-council` skill to be installed. The trigger content lives in DEBUG MODE and BUILD MODE Pre-Flight above — do not duplicate it here.
- **Reactive gates are looser; proactive gates are stricter.** Phase 3 uses OR-of-4 conditions (any one fires the gate) because a live bug is concrete evidence of stakes. Pre-Flight 1e uses AND-of-4 (all must fire) because the proactive case has weaker signal and the human is usually already attentive at pre-flight. Escalation has no gate — single-perspective reasoning has already demonstrably failed twice.

### v7.1 Proactive Council Rules (born from build-time architectural divergence that only surfaced in production)

- **Blast-Radius Council Gate runs at pre-flight, not at audit.** The gate fires BEFORE the first line of code is written. Catching architectural divergence at build-time is orders of magnitude cheaper than catching it after the regression ships. The gate content lives in BUILD MODE Pre-Flight 1e above — do not duplicate it here.
- **AND-of-4 is non-negotiable.** Loosening the conjunction to OR would fire the council on routine 5-consumer additive changes and cause council fatigue, which destroys the signal of the council output. If you find yourself wanting to convene the council on a 1e gate where only 2 or 3 conditions fire, the answer is to decide directly — not to relax the gate.

### v8 State-Machine & Reachability Rules (born from a 20-commit system audit, 2026-05-26)

These nine Cross-Layer reflexes (defined above — do not duplicate here) were each distilled from a *verified* bug that shipped through a green audit. They share one root insight: **a change is not "done" when the file you edited is correct — it is done when every OTHER writer, consumer, dispatch table, and entry point of the same state agrees.**

- **A change to a state's meaning fans out to all its writers AND all its consumers.** Editing one setter is the most common way to ship a silent drift. Reflexes: *State-Transition Side-Effect Fan-Out*, *Producer/Consumer State Liveness & Companion-Column Coupling*. This is the dominant fault family — escalate it FIRST per Self-Tuning if it fires more than once.
- **Grep is insufficient when behavior is data-driven.** "Dead code", "reachable", and trigger correctness require querying the dispatch/schema tables, not just the source tree. Reflexes: *DB-Driven Dispatch Awareness*, *DB Trigger-Change Integrity*.
- **A green unit test is not a working endpoint.** A new `fetch` target must be hit over HTTP (or executed standalone), not asserted by a method-existence test. Reflex: *Direct-Fetch Endpoint Bootstrap*.
- **A guard/throw is only as good as the branch it sits on and the loop it sits in.** Reflexes: *Batch-Loop Throw-Safety*, *Coverage-Claim & Guard-Branch Verification* (the guard must cover the client-supplied branch, not just the fallback; a "system-wide" claim needs a sweep whose pattern-set = the requirement).
- **Data repairs are code.** Commit them as idempotent scripts, and make the heilung selector a superset of the code-fix predicate. Reflex: *Data-Repair (Heilung) Script Discipline*.
- **Renaming a dispatch param silently mis-routes old links** (no 404). Reflex: *Router-Param Rename → Orphan-Link Sweep*.

### v9 Recursive Dependency Rules (born from "Page B broke after I changed Page A" — impact analysis that stopped one hop short)

- **Dependency impact is a worklist, not a grep.** BUILD Step 1d is now a recursive fixpoint algorithm (QUEUE + VISITED + LEDGER), and it is the single definition referenced by DEBUG Phase 1d, DEBUG Phase 4b, and BUILD Step 2. Single-level "find the callers and fix them" is the most common way a change ships a regression in a transitively-coupled consumer. The engine content lives in BUILD MODE Step 1d — do not duplicate it here.
- **PROPAGATES vs ABSORBS is the recursion's branch.** A consumer that must change but keeps its own contract is a leaf (ABSORBS); a consumer whose fix changes its OWN contract is re-enqueued (PROPAGATES) and ITS consumers analyzed. Mis-classifying a PROPAGATES node as ABSORBS is exactly how the closure ends one hop short — when unsure, classify PROPAGATES.
- **Termination is guaranteed — rely on it, don't fear depth.** symbol×change-kind is finite; VISITED admits each pair once; cycles end on the second visit. "I'll stop here so I don't go too deep" is never the reason to halt — depth ends on its own at the fixpoint.
- **The change is done at FIXPOINT, not at first-green.** Post-write (Step 2) re-seeds the worklist from the REAL diff and drains again. An open PROPAGATES node in the LEDGER means the change is unfinished, regardless of whether the file you started in works. For large/multi-session changes the QUEUE is persisted to `.code-guardian-propagation.md` so the closure can be completed across sessions.

### v10.1 Progressive-Disclosure Restructure (token efficiency — physical layout only, zero rule changes)

- **What moved, and why.** The three modes are mutually exclusive per run, yet the old single-file SKILL.md loaded ALL of PLAN + BUILD + DEBUG into context on every activation. Per Anthropic's skill-authoring guidance (split mutually-exclusive paths into separate files; reference files cost no tokens until read), each mode's full protocol moved out of SKILL.md into `references/plan-mode.md`, `references/build-mode.md`, `references/debug-mode.md`. SKILL.md is now a router: frontmatter + Operating Principles + Mode Selection + a per-mode skeleton with a mandatory "Read references/<mode>-mode.md" pointer + Self-Tuning + Core Rules. The always-loaded body shrank ~60% with no semantic change.
- **Where "above" now points.** Older entries in this file say things like "the engine content lives in BUILD MODE Step 1d above" or "PLAN MODE above". As of v10.1 those refer to the per-mode reference files: PLAN MODE → `references/plan-mode.md`; BUILD MODE (Steps 0–3, the 1d worklist engine, 1e Blast-Radius gate, audit, cross-layer index, R1–R5) → `references/build-mode.md`; DEBUG MODE (5 phases) → `references/debug-mode.md`.
- **Single-definition principle preserved.** The 1d worklist engine still has exactly ONE definition — in `references/build-mode.md` — referenced (not duplicated) by `references/debug-mode.md` Phase 1d/4b and by build-mode Step 2. The DEBUG Phase 5 audit also points to build-mode Step 3 rather than re-stating it. DRY across files is intentional.
- **Version label stays v10.** This is a layout refactor, not a rule change, so the title remains `Code Guardian (v10)` and `install.sh`'s version-marker greps (`Code Guardian (v10)`, `PLAN MODE`, `BUILD MODE`, `DEBUG MODE`, `Blast-Radius Council Gate`, `detect-symbol-loss.py`) all still match in SKILL.md by design — the installer was not touched.

### v11 Cleanup & Anti-Slop Rules (born from "AI agents leave dead scaffolding and slop behind"; validated against a 30-trap adversarial fixture)

- **Own slop vs. pre-existing dead code are two problems with opposite risk — split them.** Code the agent just wrote and never wired up is safe to strip (Self-Slop Sweep, always-on, diff-only). Foreign pre-existing code is dangerous; cleaning it is opt-in and **report-only** (CLEANUP MODE) — the skill classifies, the human deletes. The boundary between the two is the git diff. Principle 3's carve-out encodes exactly this: your own mess is in scope, everyone else's is reported.
- **The liveness asymmetry is the safety guarantee.** Any single positive signal (a static ref, a template/config/route/DI/DB-dispatch/i18n hit, a coverage hit) proves LIVE and vetoes removal; absence of references never proves dead. Static "unused" output is a candidate, never a verdict — this is why even VERIFIED-DEAD-PRIVATE is only ever *recommended*, never auto-deleted.
- **Closed-world is the confidence line.** Private/file-local symbols (PHP `private`, Python `_name`, **non-exported** JS/TS) can reach VERIFIED-DEAD-PRIVATE; public, `protected`, and exported symbols are always ASSERTED-DEAD (external callers unprovable) and require a deprecate-before-delete cycle. Framework false-positive categories (Eloquent magic, Blade/Vue auto-discovery, routes, DI strings, DB-driven dispatch, CLI/cron/webhook entry points, reflection, test-only) each veto deletion.
- **Scan the source, not the answer key.** Fixture validation's single biggest false-signal: a tree containing a manifest that *names* symbols (an oracle, a changelog, a data file) flipped every dead symbol to LIVE, because a quoted name counts as a reference/keep-alive. `detect-dead-code.py --exclude` (threaded through every scan — `count_refs`, `find_definition`, AND `fp_flags_for`) exists for exactly this; CLEANUP MODE must exclude manifests/generated/docs and point `--root` at real code.
- **The tool catches mechanical slop, not semantic slop.** `--diff-slop` reliably flags unused own-additions and debug leftovers (validated). Reimplementation of an existing helper and comments that restate code are *semantic* — they need a reuse-grep / clone detector / human judgment, not a regex. The skill says so honestly rather than pretending the tool is complete.
- **Cleaning slop must not create slop.** The redundancy counter-rule (Rule of Three + same-knowledge) is non-negotiable: duplication is cheaper than the wrong abstraction (Metz). Two clones never justify an abstraction; near-miss clones are never fused with a flag+conditional. `detect-clones.py --extract-threshold` labels ≥3-site groups EXTRACT-CANDIDATE and 2-site groups NOTE-ONLY.
- **`detect-dead-code.py` is an evidence aggregator, not a deleter.** Like every Code Guardian tool it is dependency-free, emits a `SUMMARY` footer, and — verified by audit — contains no write path: it never mutates a source file. It corroborates multiple signals and classifies; it cannot remove code.
- **Version label moves to v11.** Real rule additions (new mode, new always-on layer, new tool), not a layout refactor — so the title becomes `Code Guardian (v11)` and `install.sh`'s markers were updated in lockstep (`Code Guardian (v11)`, `CLEANUP MODE`, `Self-Slop`, `detect-dead-code.py`) plus the tool-existence loop.
