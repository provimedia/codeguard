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
