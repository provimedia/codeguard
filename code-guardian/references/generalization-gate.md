# GENERALIZATION GATE — an example in the requirement is DATA, never CODE (v13)

> Loaded when: PLAN MODE runs P7, the BUILD audit's Logic layer or Self-Slop
> Sweep flags a hardcoded case, or `detect-hardcoded-cases.py` reports findings.

## The Law

When a requirement quantifies universally — "every industry", "any domain",
"all customers", "für jede Branche" — **no literal from the requirement's
example set may appear in a control-flow decision.** Examples the user gives
("treat domain1.de as Solar") illustrate the *class* of inputs; they are test
data and config values, never `if`/`switch`/regex/lookup constants.

The failure mode this kills: the model hardcodes `if ($domain === 'domain1.de')`
so the example's expected result comes out, and the "solution" silently works
for exactly one input. The requirement asked for a **generic mechanism** —
a classifier, a parser, a DB/config lookup, an AI analysis step.

## The two mandatory tests

Apply to any suspect literal (mechanically found or read in review):

1. **Deletion test.** Remove the example literal from the code. Does the
   example input still produce the correct result through the generic path?
   If the behavior for `domain1.de` disappears with the literal, the literal
   WAS the implementation.
2. **Second-example test.** Take an equivalent second value (`domain2.de`,
   same industry). Does it take the SAME code path and produce the analogous
   result? A different (or default/fallback) path → special-cased, FAIL.

## Detector

```bash
# Tree scan (fixture validation, review of a module)
python3 ~/.claude/skills/code-guardian/tools/detect-hardcoded-cases.py --root <dir> [--examples 'domain1.de,Branche X']

# Diff-only (BUILD Self-Slop Sweep — your own just-written lines)
python3 ~/.claude/skills/code-guardian/tools/detect-hardcoded-cases.py --git [--examples '...']
```

Report-only; paste the `SUMMARY findings=… intentional=… exit=…` footer as
Verified-by. Flagged literal classes: domains, URLs, emails, dates — plus every
literal passed via `--examples` (the requirement's own examples: those are
flagged in ANY code context, because they belong in data/config, not source).
Always pass `--examples` when the task named concrete values.

**Low-FP by design** (the v11 lesson: a noisy detector gets ignored): a literal
is only a finding inside a decision context (`if/elif/elseif/switch/case/match`,
comparisons, `in_array`/`.includes`/`str_contains`/`preg_match`/`re.match`, regex
tests) or as a lookup KEY (`'domain1.de' => …` / `'domain1.de': …`). Config,
test, spec, and fixture paths and data files are ignored entirely — concrete
values are CORRECT there.

## The honest exception

Real single-value business rules exist ("this contract customer has a fixed
special price"). They must be visible, not smuggled:

```php
// INTENTIONAL-SPECIAL-CASE: <why this ONE value is genuinely special, source>
if ($host === 'domain1.de') { … }
```

The marker (same line or ≤3 lines above) suppresses the finding and is counted
as `intentional=` in the SUMMARY. A marker without a real reason is slop —
the reason must name the business source (contract, ticket, law), not restate
the code. Marker inflation defeats the gate; challenge it in review.

## Where the gate runs

| Mode | Step | What |
|---|---|---|
| PLAN | **P7 Generalization** | plan names the generic mechanism; examples appear only as test data/config |
| BUILD | Audit → Logic layer | tree/diff scan of the touched module when the task had example values |
| BUILD | Self-Slop Sweep (always-on, diff-only) | `--git` run on your own added lines |

Fix direction: replace the literal branch with the generic mechanism the plan
named (classifier/parser/DB/config/AI analysis), move the concrete values to
config/seed data, and keep the example as a TEST asserting the generic path.
