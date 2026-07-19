# Cockpit — the Guardian output style (v16.2)

> Loaded whenever a mode or gate is about to render a report, tracker, or
> verdict to the user. The cockpit reframes HOW results are shown — every
> binding content rule (Verified-by evidence, Full-Picture fields, forbidden
> phrases, verdict definitions, the DECISION GATE "(Empfohlen)" format)
> stays word-for-word. If a template and a binding rule ever conflict, the
> binding rule wins.

## Render laws (non-negotiable)

1. Everything monospace-sensitive goes into ONE fenced code block per
   cockpit element — never split a frame across fences, never mix prose
   into the fence.
2. Open lines only: one `━` header line and one `━` footer line. NEVER
   closed boxes (`╔═╗`, `│` right edges) — a right edge breaks on the
   smallest width drift and reads as broken.
3. Progress bars are EXACTLY 20 cells: `filled = round(percent × 20/100)`,
   `█` filled, `░` empty. Label left of the bar, count right of it.
4. Emoji only at line START (lamps 🟢🟡🔴) or line END — never inside an
   aligned column; emoji are double-width and shift everything after them.
5. Line width ≤ 90 characters. Spaces only, never tabs.
6. NO ANSI escape codes, ever — chat output runs through a markdown
   renderer and raw escapes render as garbage. Color comes from lamp
   emoji, structure from `━` and `█░`.
7. One bar style per element (block bars); never mix with emoji bars.
8. Render at PHASE BOUNDARIES only: intake, mode entry, step completion,
   final verdict. Never after every tool call; never re-render unchanged
   state. A normal task shows a handful of cockpit elements, not dozens.
9. A cockpit element REPLACES the prose report it frames — never render
   both the plain version and the cockpit version of the same content.
10. Proportionality: question and trivial tasks get NO cockpit — a plain
    line beats a ceremonial frame (same law as triage depth and the
    airlock).
11. Before sending: eyeball the fence — bars stacked? counts aligned? A
    crooked frame is worse than no frame.

## T1 — Intake card (senior-dev, class normal and above)

```
━━ SENIOR DEV · INTAKE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Klasse   normal              Route   BUILD MODE
  Tag      api-endpoint        Beweis  php tests/run.php
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Question/trivial: no card — one plain line ("Intake: trivial — …").

## T2 — Mode banner (one line, on mode entry)

```
━━ CODE GUARDIAN · BUILD MODE · Pre-Flight ━━━━━━━━━━━━━━━━
```

Also for DEBUG/PLAN/CLEANUP and gate entries (DECISION/DEPLOY/DATA GATE).

## T3 — Checklist tracker (at step boundaries)

```
━━ CODE GUARDIAN · BUILD · Pre-Flight ━━━━━━━━━━━━━━━━━━━━━
  ✓ 1a Scope             ✓ 1b Schema (live)
  ✓ 1c Existing-Code     ▶ 1d Dependency-Worklist
  ○ 1e Blast-Radius
  Fortschritt  ████████████░░░░░░░░  3/5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Variants (same skeleton, own items): BUILD pre-flight `1a–1e` · audit
layers `DB · Logic · Efficiency · Redundancy · Security · Self-Slop` ·
PLAN `P1–P7` (PASS/FAIL replaces ✓/○ at the end) · DEBUG phases `1–5`.
Render once when the step block starts (all ○) and once when it completes
— not per item.

## T4 — Worklist pulse (single line inside the 1d drain)

```
  Worklist  ██████████████░░░░░░  7/10 Konsumenten geprüft
```

## T5 — Verdict block (audit end and every gate verdict)

```
━━ CODE GUARDIAN · AUDIT-VERDICT ━━━━━━━━━━━━━━━━━━━━━━━━━━
  🟢 DB-Layer      Schema live introspected, FK ok
  🟢 Security      R1-R5 findings=0
  🟡 Efficiency    N+1 in listView — WARN, deferred
  Layer  █████████████████░░░  5/6 grün

  VERDICT: APPROVED (0 critical, 1 warning)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Each lamp line carries the compressed Verified-by evidence; the full
Verified-by command outputs stay in the surrounding report as before.
Verdict wording (`APPROVED` / `NEEDS FIX` / `BLOCKED` + counts) is the
binding rule from build-mode 3e, unchanged.

## T6 — Debug fix verdict (DEBUG MODE Phase 5 close)

```
━━ CODE GUARDIAN · FIX-VERDICT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Root cause   [what, in one line]
  Fix          [old] → [new]              [N lines]
  Proof        [repro test red→green + suite result]
  Blast radius [consumers checked, one line]

  VERDICT: FIXED · VERIFIED  |  NOT FIXED: [reason]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Root-cause and evidence prose come BEFORE the block; the block is the last
word. Field labels left-aligned to one column; no lamps here — a fix is
binary (FIXED · VERIFIED or NOT FIXED), the audit lamps live in T5.
