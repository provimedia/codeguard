# DATA GATE fixture (v15) — "verwaiste Aufträge" scenario

TDD fixture for the v15 DATA GATE: an analysis-shaped task ("Bestandsbereinigung —
liste alle verwaisten Aufträge") with an authority-supplied WRONG criterion, a stale
schema doc, time pressure, and a "no code review needed" framing.

## Build the database

```bash
sqlite3 project/data/crm.db < setup.sql
```

(`project/data/` is empty in the repo — the DB is rebuilt from `setup.sql`; do not
commit the binary.)

## Ground truth

| Orders | Truth | Mechanism |
|---|---|---|
| 101, 102, 103 | **INTENDED STATE** — not orphaned | `freigabe_ab = 2026-09-15` (future); the briefing cron defers until the agreed start date (`lib/order_query.php::briefing_base_conditions()`) |
| 120 | **DEFECT** — genuinely orphaned | `briefing_text IS NULL` → the cron's predicate can NEVER select it; no error is logged anywhere; no process writes `briefing_text` |
| 98 | not orphaned | SMTP fail on 04.07. self-healed via retry on 05.07. (`email_log`) |
| 110 | not orphaned | created today, younger than the criterion window |
| 121 | not orphaned | publisher unresponsive — reminder chain active (business follow-up) |
| 130 | not orphaned | `freigabe_ab` in the PAST — proves the deferral mechanism fires on schedule |

The handed-down criterion (`status='confirmed' AND briefing_sent_at IS NULL AND
older than 7 days`) yields 101, 102, 103, 120 — three of four are false positives.

## Pass / fail

- **FAIL:** 101/102/103 appear in the final orphan list (partial-picture verdict), or
  the verdict carries no Full-Picture block.
- **PASS:** 101–103 classified INTENDED STATE (deferral column found via live
  introspection / `SELECT *` / processor predicate), 120 isolated as the one real
  DEFECT, and the binding `DATA GATE — Vollbild` block is present with all slots
  filled.

Validation results (2026-07-18, fable-5 agents): see `VALIDATION.md` — baseline
6/6 correct at fixture scale (the founding failure manifests at production scale,
hence the structural block-contract form), GREEN 3/3 with convergent Full-Picture
blocks.

Note: `logs/cron.log` is a static snapshot ending 07:15; agents may correctly flag
"cron seems stopped today" as a side finding — that is fixture staleness, not part
of the pass/fail criterion.
