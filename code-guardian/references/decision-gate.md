# DECISION GATE — recommendation before every option question (v12)

> Loaded when the DECISION GATE fires: you are about to present the user an option
> question — A/B/C, variant 1/2/3, "which approach?", any `AskUserQuestion` call or
> inline option list. Orthogonal to mode selection: fires in PLAN, BUILD, DEBUG,
> CLEANUP alike, and also outside any mode.

## The Law

**The gate recommends; the user decides.** Every option question presented to the
user MUST carry a reasoned recommendation. The gate NEVER decides autonomously —
even when one option scores maximally better, the question is still asked and the
user makes the final call. Two symmetric failure modes are forbidden:

1. **Asking blind** — presenting options without a recommendation ("A, B oder C?").
   That outsources analysis the agent is better positioned to do.
2. **Deciding silently** — picking an option and proceeding without asking.
   That takes authority the user has explicitly reserved.

The gate does not CREATE questions: a question that need not be asked (answer
derivable from the task, the code, or an explicit standing directive) should not be
asked at all — Operating Principle 2 (act when ready) is untouched by this gate.

## Triage — which tier runs

T1 always runs. T2/T3 are escalations layered on top of T1, strictly gated to
prevent recommendation fatigue (same rationale as the 1e AND-of-4 gate: a noisy
gate destroys its own signal).

| Tier | Fires when | Process |
|---|---|---|
| **T1 Rubric** | every option question, always | score all options against the 5-criteria rubric below, inline |
| **T2 Advocates ⚡** | options materially diverge (different architecture, data model, or dependency footprint) AND T1 produces no clear winner (top-2 gap ≤ 1 point) | one parallel advocate subagent per option; each argues its option as strongly as possible AND names its honest weakest point; then compare verdicts |
| **T3 Council** | hard to reverse (data migration, public API, published contract) OR ≥ 5 consumers affected (1d LEDGER) OR foundation decision (schema, auth, payment, framework/library choice) | convene `llm-council` (bundled); frame as "Option A vs B vs C for <decision>", invite an option D, supply the rubric matrix + LEDGER; the Chairman verdict feeds the recommendation |

When unsure which tier applies, take the higher one. T3 subsumes T2.

## T1 Rubric

Score each option 1–5 per criterion; show the matrix when it fits in a few lines,
otherwise summarize the decisive rows. The criteria encode the standing directive
*long-term best, no compromises, cleanest solution*:

| Criterion | Asks |
|---|---|
| **Longevity / Maintainability** | still the right call in 2–5 years? maintainable by someone else? |
| **Architectural cleanliness** | fits the existing architecture without hacks, special cases, hidden coupling? |
| **Reversibility / Lock-in** | how expensive is changing course later? vendor/framework/data lock-in? |
| **Follow-up cost** | operational burden, upgrade path, monitoring, failure modes it introduces |
| **Best-practice conformity** | matches current documented best practice? (unsure → web-search official docs, never guess from stale assumptions) |

**Tie-break: long-term beats short-term — always.** A cheap-now option only wins
if it is not materially worse long-term. "Half solutions" (works now, known rework
later) lose to clean solutions unless the user's constraints say otherwise — and
if such a constraint exists, name it in the justification.

## Binding output format

Every option question presented to the user MUST follow this shape — in
`AskUserQuestion` calls AND in plain-text option lists:

1. **Recommended option FIRST**, its label suffixed **" (Empfohlen)"** (German
   sessions) or **" (Recommended)"** (English sessions).
2. **1–2 sentence justification** along the rubric — name the criteria that
   decided it, not generic praise.
3. **Every other option presented fairly** with its honest trade-off — no straw
   men; if an alternative wins on some criterion, say so.
4. **T3 ran → append one line:** `Council-Verdict: <recommendation> — <one thing to do first>`.
5. No meaningful recommendation possible (pure taste, missing facts only the user
   has) → append `[keine-empfehlung: <reason>]` to the question text instead of a
   fake recommendation. This is the rare exception, not a loophole — a rubric that
   scores a tie is still a recommendation situation (recommend the tie-break winner).

## Boundaries

- **Advises, never verifies.** The gate produces a recommendation, not proof.
  Whatever option the user picks still passes every verification gate (pre-flight,
  audit, P1–P6, R1–R5) untouched. Council output is never a verification substitute.
- **No scope creep.** The recommendation may not smuggle in extra work; it ranks
  the offered options and may propose at most ONE additional option (clearly
  labeled as new) when all offered options fail the rubric badly.
- **Enforcement (optional, deterministic).** A `PreToolUse` hook on
  `AskUserQuestion` can deny any call whose options lack an "(Empfohlen)" /
  "(Recommended)" marker; the deny reason instructs the model to run this gate and
  re-issue the question. Hook snippet: repo README → "Recommended Companion
  Settings". Doc-backed mechanics: PreToolUse stdout is NOT visible to the model;
  `permissionDecisionReason` IS fed back — that feedback loop is what makes the
  hook self-correcting.
