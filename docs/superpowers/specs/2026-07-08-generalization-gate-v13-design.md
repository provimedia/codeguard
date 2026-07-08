# Code Guardian v13 — Generalization Gate (Anti-Hardcoding) — Design

**Date:** 2026-07-08 · **Status:** Approved (via /goal) · **Scope:** skill rules + detector + fixture + package

## Problem

AI models hardcode example values from the requirement — `if ($domain === 'domain1.de')`,
regex matching exactly the example, switch chains, lookup arrays — even when the
requirement is universal ("für jede Branche"). The "solution" works for exactly the
named example instead of building the generic mechanism (classifier/parser/DB/AI).

## Decision

- **Law** (`references/generalization-gate.md`): an example in the requirement is
  DATA, never CODE. Universal quantification → no example literal in control flow.
  Two mandatory tests: deletion test, second-example test.
- **Detector** `tools/detect-hardcoded-cases.py`: dependency-free, report-only.
  Flags domains/URLs/emails/dates (+ `--examples` literals, those in ANY code
  context) — but only inside decision contexts (if/elif/elseif/switch/case/match,
  comparisons, in_array/.includes/str_contains/preg_match/re.match/.test, regex)
  or as lookup keys (`'x' => …` / `'x': …`). Ignores config/test/spec/fixture
  paths (relative to scan root) and non-code extensions. Modes: `--root`,
  `--files`, `--git` (added lines only, for the Self-Slop Sweep).
  `SUMMARY findings=… intentional=… files-scanned=… exit=…`.
- **Escape hatch:** `INTENTIONAL-SPECIAL-CASE: <business source>` on the line or
  ≤3 lines above suppresses the finding, counted as `intentional=`.
- **Wiring:** PLAN P7 (plan names the generic mechanism; example-literal grep must
  hit only test/config sections) · BUILD audit Logic layer (`--root <module>
  --examples`) · Self-Slop Sweep (`--git`, always-on, diff-only).
- **Version v12 → v13** in lockstep: SKILL.md title/router/core rule, install.sh
  markers (+`Generalization`, +tool existence), README, UPDATE-ANLEITUNG,
  design-rationale.

## Rejected alternatives

- **Flag literals everywhere (not just decision contexts):** would flag config,
  seeds, tests — FP noise trains users to ignore the tool (v11 lesson).
- **AST-based parsing per language:** heavier, dependency-bearing, contradicts the
  tool suite's dependency-free line-scan convention; regex heuristic + path ignores
  is sufficient for the trap classes and keeps the tool universal.
- **Auto-fix:** never — report-only like every Code Guardian tool.

## Validation

Trap fixture `test/hardcoding/`: 9 traps (literal-if, example-regex, switch chain,
lookup array, hard date, email-if, URL check, elseif ladder, in_array) — ALL must
flag; 6 clean cases (generic classifier, config file, test file, INTENTIONAL
marker, DB lookup, JSON data) — 0 findings. Unit tests (17) dual-mode in
`tools/tests/test_detect_hardcoded_cases.py`; full suite green (48 passed).
