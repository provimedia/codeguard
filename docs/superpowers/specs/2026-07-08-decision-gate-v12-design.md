# Code Guardian v12 — DECISION GATE — Design

**Date:** 2026-07-08 · **Status:** Approved (user: recommend, never decide) · **Scope:** 5 repo files + local hook

## Problem

During development the agent regularly presents option questions (A/B/C, variant
1/2/3) without a recommendation. The user wants every such question to arrive with a
reasoned recommendation for the long-term best, no-compromise, cleanest solution —
while the final decision always stays with the user (explicit: "Er soll eine
Empfehlung geben, nicht final entscheiden").

## Decision

New **DECISION GATE**, orthogonal to all modes (not a sixth mode — option questions
arise inside every mode). Router section in `code-guardian/SKILL.md` + full protocol
in new `references/decision-gate.md`:

- **T1 Rubric (always):** Longevity/Maintainability · Architectural cleanliness ·
  Reversibility/Lock-in · Follow-up cost · Best-practice conformity; tie-break
  long-term beats short-term (encodes the standing user directive).
- **T2 Advocates (⚡):** materially divergent options AND no clear T1 winner → one
  parallel advocate subagent per option.
- **T3 Council:** hard-to-reverse OR ≥ 5 consumers OR foundation decision
  (schema/auth/payment/framework) → bundled `llm-council`.
- **Binding output:** recommended option FIRST with "(Empfohlen)"/"(Recommended)"
  suffix + 1–2 sentence rubric justification; other options fair with honest
  trade-offs; `[keine-empfehlung: <reason>]` escape hatch for pure-preference cases.
- **Prohibitions:** no autonomous deciding; no invented questions; advises-never-verifies.

**Version bump v11 → v12** (real rule addition): SKILL.md title, install.sh marker
greps (+ `DECISION GATE`), README (version line was stale at v7.1 → v12, feature
section, version history), design-rationale v12 entry.

**Deterministic enforcement (optional):** `PreToolUse` hook on `AskUserQuestion`
denies calls whose options lack the recommendation marker; deny reason is fed back
to the model (doc-verified: PreToolUse stdout is NOT model-visible,
`permissionDecisionReason` IS) → self-correcting re-issue loop. Snippet in README;
installed locally as `~/.claude/hooks/decision-gate-check.sh` + settings.json entry
(backup taken; merge preserved all existing keys/hooks).

## Rejected alternatives

- **Autonomous deciding for rubric-derivable questions:** explicitly rejected by the
  user — recommendation only, authority stays with the user.
- **Soft stdout reminder hook:** doc-verified ineffective — PreToolUse stdout never
  reaches the model; only a deny reason does.
- **Sixth mode instead of orthogonal gate:** false either/or with the running mode.

## Verification (Verified-by command output, 2026-07-08)

- `grep` "Code Guardian (v12)" + "DECISION GATE" in SKILL.md: present
- `bash -n install.sh` exit 0; throwaway-HOME install: no "Missing markers" warning
- Hook unit tests: no-recommendation → deny · "(Empfohlen)" → allow ·
  "(Recommended)" → allow · escape hatch → allow; deny reason verbatim correct
- `settings.json` post-merge: valid JSON, all pre-existing keys/hooks intact
- E2E: fresh install in throwaway HOME shows gate markers; T1 rubric functional
  probe (file-upload decision) produced the mandated "(Empfohlen)"-first output
