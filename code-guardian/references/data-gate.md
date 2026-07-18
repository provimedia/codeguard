# DATA GATE — the full picture before any data verdict (v15)

> Loaded when the DATA GATE fires: you are about to **declare a verdict about the
> state of data** — records called orphaned/stuck/stale/unprocessed/lost/forgotten/
> inconsistent/duplicate/wrong (de: „verwaist", „hängen geblieben", „liegengeblieben",
> „nie bearbeitet", „vergessen", „kaputt", „Datenleiche") — or to **base an action on
> interpreted DB data**: a fix, a data repair (Heilung), a migration, a cleanup list,
> a report/ticket reply/analysis others will act on. Orthogonal to mode selection:
> fires in PLAN, BUILD, DEBUG, CLEANUP alike, and also outside any mode (pure
> analysis tasks with no code change at all).

## The Law

**A verdict about data is a verdict about the whole schema.** A row is only
"broken" relative to EVERY rule that governs it — and those rules live in columns
you may not know exist, in related tables you have not queried, and in the
processor code that selects the row. The most common false verdict is a
legitimately **waiting** record declared broken: deferred start dates
(`deadline_ab`, `freigabe_ab`), validity windows, pause/hold flags, approval
gates, retry backoff, soft-delete, scheduling tables.

Sibling of the v11 liveness law, applied to data:
**absence of references never proves code dead — absence of activity never proves
data broken.** Both verdicts require positive evidence, not a failed lookup over
the columns you happened to know.

A handed-down criterion (a ticket's "briefing_sent_at is empty, so it's stuck",
a meeting note, a stale schema doc) is a **hypothesis**, never the predicate.
The real predicate lives in the live schema and the processor code.

## The four checks — V1–V4 (all four, in order)

**V1 Schema inventory (live, complete).** Full column list of EVERY table the
verdict touches — live introspection (`information_schema` / `SHOW CREATE TABLE` /
`PRAGMA table_info`), never docs, memory, or ORM models (they age; the missing
column is precisely the one added after the doc was written). Extend one hop:
FK-related tables (both directions) and naming-convention siblings
(`*_history`, `*_log`, `*_queue`, `*_schedule`, audit tables). Mark every
**state-carrying column**: status/enum values, every timestamp (`*_at`), every
window/deferral column (`*_ab`, `*_from`, `*_until`, `*_bis`, `deadline*`,
`valid*`, `freigabe*`, `activation*`), hold/pause/lock/archive flags, soft-delete,
retry/backoff counters, external-sync markers.

**V2 Row reality (`SELECT *`, never a column subset).** Dump the FULL rows of the
concrete entities in question. The unknown-unknown column is invisible by
construction in a hand-picked column list — `SELECT *` or it didn't happen.
Whenever a healthy sibling exists (same day/type that DID process), dump it too:
the diff of two full rows is usually the answer.

**V3 Processor cross-check.** Find the code/cron/trigger/job that SHOULD have
acted on the rows and extract its REAL predicate (the WHERE / guard conditions —
follow query builders to the condition source). Test that predicate against the
actual rows as a condition matrix: which single condition excludes them? One
grep + one read — this is not a code review, it is locating the row's meaning.
No processor findable → say so in the block; do not silently skip.

**V4 Innocent-explanation elimination.** Before any "broken/orphaned" verdict,
the candidate list MUST contain: *"the record is in a legitimate intended state
(waiting / deferred / paused / gated / scheduled) explained by a column, a related
table, or a recorded business decision."* This candidate is eliminated ONLY by
pointing at the checked evidence (e.g. `freigabe_ab = NULL` → no deferral), never
by "I didn't see anything". If the project keeps a decision register
(`docs/entscheidungen/` or similar), consult it — "bug" vs. "so beauftragt" is
exactly this distinction.

## Binding output format — the Full-Picture block

Every data verdict presented (report, ticket reply, fix justification, cleanup
list) MUST carry this block. No block → the verdict is not reportable.

```
DATA GATE — Vollbild
Tables inspected (live):   <table: n columns, introspection command used>
State-carrying columns:    <column = value → relevant? how ruled out>
Rows dumped in full:       <ids> (SELECT *) · healthy sibling: <id | none>
Processor predicate:       <file/function + the excluding condition | "none found">
Innocent explanations:     <which were eliminated, with evidence>
VERDICT: DEFECT | INTENDED STATE (<mechanism>) | MIXED | INSUFFICIENT PICTURE (<what is missing>)
```

`INSUFFICIENT PICTURE` is an honest, allowed verdict (no DB access, opaque
external system) — it replaces guessing and names what is needed. It follows the
same rule as "⚠️ DB unchecked": say what you could not verify.

## Scale discipline

On wide/many-table systems, do not dump the world: V1 scopes to tables the
verdict TOUCHES plus one FK hop — bounded and cheap next to the cost of a wrong
"orphaned" verdict (wrong verdicts trigger wrong repairs: resend, requeue,
delete). If even the scoped picture is unaffordable or unavailable, the verdict
is `INSUFFICIENT PICTURE`, not a guess.

## Anti-rationalization

| Excuse | Reality |
|---|---|
| "Support/the ticket already checked the relevant columns" | They checked the columns they KNOW. This failure class lives in the column nobody in the room knew. V1 is non-negotiable. |
| "The docs list the relevant columns" | Docs age; schemas grow. Live introspection beats any static file — the missing column is the one added after the doc was written. |
| "It's a pure data analysis, no code involved" | The row's meaning is defined by its processors. V3 is one grep + one read, not a code review. |
| "Time pressure — they need the verdict now" | A wrong "orphaned" verdict triggers wrong repairs whose damage costs far more than V1–V4 (minutes). Fast and wrong is slower. |
| "I queried the rows already" | With which columns? A hand-picked SELECT list cannot show the unknown-unknown column. `SELECT *` (V2) or it didn't happen. |
| "Nothing in the logs, so it's clearly broken" | Silent exclusion is the signature of an INTENDED filter (a WHERE condition), not of a crash. Absence of activity never proves broken data. |

## Boundaries

- **The gate shapes verdicts, not curiosity.** Routine SELECTs, exploratory
  queries, and metrics need no block — the gate fires when a *state verdict* or a
  *data-based action* is about to leave you.
- **Advises the verdict, never replaces verification.** A DEFECT verdict still
  enters DEBUG MODE (root cause before fix); a repair is still code and passes
  BUILD MODE + audit; a cleanup list still follows CLEANUP-MODE's report-only law.
- **No deterministic hook exists for this gate.** A data verdict is prose, not a
  tool call — there is no interception point. Enforcement is the required block:
  its absence in a data verdict is immediately visible in review.
