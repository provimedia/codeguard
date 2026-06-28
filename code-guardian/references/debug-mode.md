# DEBUG MODE — full protocol

> Loaded when a bug/error/broken behavior is reported. The router lives in `SKILL.md`; this file holds the full 5-phase protocol. Operating Principles (in SKILL.md) govern every phase. The 1d worklist engine and the Audit referenced below are defined once in `references/build-mode.md` — load it when a phase points there.

### Phase 1: COLLECT (no fix, no suggestion yet)

- **1a.** Exact symptom: error text, stack trace, expected vs actual.
- **1b.** What changed recently: `git log --oneline -5 && git diff --name-only HEAD~3`
- **1c.** Read the entire affected function + 2 levels of callers and callees — not just the error line.
- **1d. Cross-page dependency trace** — the bug is often not where the error shows. Run the BUILD MODE 1d worklist engine (`references/build-mode.md`, Step 1d) to fixpoint (same QUEUE/VISITED/LEDGER), plus per consumer: was this consumer recently changed? was the function itself? (`git log --oneline -10 -- <file>`). Function changed + consumer not = likely **dependency break** — the most common root cause of "Page B broke after I worked on Page A".

### Phase 2: ROOT CAUSE (not symptom)

Answer in order — no solutions before question 4:
1. **WHAT** happens (symptom) · 2. **WHERE** in code (and: is the real cause in a different file?) · 3. **WHEN** introduced (`git log` on the broken function) · 4. **WHY** (root cause) · 5. **WHY wasn't it caught** (missing test, no dependency check).

List 3 candidate causes ranked by probability — always include "dependency break from a recent change in a shared function" when the function has multiple consumers. Verify each by reading code or a targeted test before confirming or ruling out.

### Phase 3: TWO PATHS

Never propose just one fix.

⚡ **Parallel advocates:** dispatch two subagents — one argues **Path A (minimal)**, one **Path B (structural)**. Each returns: what changes, effort, risk, and whether it fixes the root cause or the symptom, grounded in the Phase 1d LEDGER. You decide between them on: root-cause resolution, side-effect risk, maintainability, consumer count. (Fresh-context advocates beat self-critique; on a trivial bug where both paths are obvious, argue them yourself inline.)

**Council gate** — convene `llm-council` only when the paths *materially diverge*: (1) Path A doesn't reach the root cause but Path B does; (2) live time-critical incident AND Path B is no same-sitting hotfix; (3) Path B touches shared function/schema/auth/payment OR consumer count > 5; (4) genuine short-vs-long-term tradeoff with no obvious winner. Frame as *"Path A vs B for <bug>"*, invite a Path C, supply both write-ups + Phase 2 analysis + the LEDGER. The council runs once, only when a named condition fires; it advises — verification gates still apply.

### Phase 4: VALIDATE BEFORE TOUCHING CODE

- **4a. Call-chain trace** — walk the fix mentally: call sites, returns, branches, edge cases. Trace shows it won't work → back to Phase 3.
- **4b. Recursive consumer verification** — the fix is itself a change with a change-kind: seed it into the 1d engine (`references/build-mode.md`, Step 1d), drive to fixpoint. The consumer you're fixing FOR is rarely the only one. A fix that repairs one page and breaks three others is not a fix.
- **4c. Gate:** `Call-chain ✅/❌ | ALL consumers verified ✅/❌ ([X]/[Y]) | Edge cases ✅/❌ → Ready ✅/❌` — any ❌ → not ready.

### Phase 5: IMPLEMENT + VERIFY

1. Fix + adjust all affected dependencies → 2. test reproducing the bug (now green) → 3. existing tests still green → 4. confirm bug gone, edge cases handled, dependencies intact → 5. run the BUILD MODE post-change symbol-loss gate and Audit on the fix diff (`references/build-mode.md`, Step 2.1 + Step 3a–3g) — a fix is a code change like any other.

### Escalation

- **Failed once** → document why, mark the hypothesis disproven, restart Phase 1.
- **Failed twice** → convene `llm-council` unconditionally before reporting: *"two distinct root-cause fixes failed for <bug> — what is the council missing?"* with both attempts + Phase 2 analysis. New hypothesis → restart Phase 1 with it. Council finds nothing → STOP and report both attempts + analysis + verdict to the user.
