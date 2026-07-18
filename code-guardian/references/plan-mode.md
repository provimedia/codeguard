# PLAN MODE — full protocol

> Loaded when a spec/plan exists. The router lives in `SKILL.md`; this file holds the full reflex text. Operating Principles (in SKILL.md) govern every reflex below.

Bugs that survive the audit usually originated in the plan. Run these 7 reflexes against any spec/plan before implementation is dispatched — and again when receiving a plan from another author. Run them, record PASS/FAIL with proof, move on (Principle 2).

Senior view first: re-read senior-dev `references/senior-card.md` §B and answer its architecture questions against this plan before auditing (right problem? already exists? simplest design? trade-offs named? DB normalized?).

**P1. Cross-Layer Trace for Every New Field.** Walk each new field end-to-end: DB column → model allowlist/visibility → serializer/response builder → transport payload → client template. A model-layer allowlist does NOT guarantee client delivery — if the serializer uses an explicit key whitelist, an absent field is dropped silently. *Check:* grep the response builders for explicit key lists; if any exist, the plan must include the serializer change.

**P2. Scale Verification for DB Iteration.** Every row-iterating command/job names its streaming method by expected count: `<1000` → `->get()` · `1k–100k` → `->cursor()`/`->lazy(N)` · `100k+` → `->lazyById(N)` + job queue. Gotchas: some streaming primitives silently re-drive the query and ignore an upstream `LIMIT` — if you need streaming AND a cap, verify the actual processed row count. Aggregates (`SUM/COUNT/AVG/MAX/MIN`) scan rows: verify with `EXPLAIN` that an index is used and the row estimate is bounded; consider a denormalized counter for hot paths.

**P3. Secrets Hygiene for API Calls.** Keys/secrets/signatures travel in **headers**, never query strings (`?key=` leaks via exception logs, access logs, Referer). Inbound webhook signatures compare with constant-time equality (`hash_equals`, never `==`/`===` — PHP type-juggling makes two `^0+e\d+$` hashes compare equal as floats; bcrypt → `password_verify`). User-facing magic links: signed, time-limited, bound to route+expiry; store only a SHA-256 hash of the token; one-time use via `consumed_at` checked+set in one transaction. *Check:* grep the plan for `?key=`, `?api_key=`, `?token=` → any hit blocks that section.

**P4. Cached-Config Safety.** Runtimes that pre-compile config at boot snapshot env vars once; raw env reads outside the config layer return null post-cache. Every new env var goes through the project's config layer. *Check:* grep plan pseudocode for direct env reads outside config files.

**P5. Pattern Source Quality.** When the plan says "follow the pattern of `<file>`", audit that file against P1–P4 first — inherited bugs propagate because "matches existing pattern" reads as approval. Any match → the plan names which inherited bugs to FIX, not copy.

**P6. WIP Staging Discipline for Subagent Briefings.** On a branch with pre-existing uncommitted WIP, subagent prompts must mandate hunk-level staging: `git add <new-file>` or `git add -p <existing-file>` — never `git add .`/`-A`/bare `git add <existing-file>` (sweeps ALL hunks in the file). Fix the briefing template, not the symptom; by audit-time the commit already exists.

**P7. Generalization — examples are data, never code.** When the requirement quantifies universally ("every industry", "any domain", "für jede Branche") and names example values (a domain, a date, an ID), the plan MUST name the **generic mechanism** (classifier, parser, DB/config lookup, AI analysis) and route every example value into test data or config — never into `if`/`switch`/regex/lookup control flow. A plan that enumerates the examples as cases is the overfitting anti-pattern locked in at plan-time. Genuine single-value business rules must be declared as `INTENTIONAL-SPECIAL-CASE` with the business source. *Check:* grep the plan for each example literal; every hit must be in a test/config/seed section, not in described branching logic. Full law + deletion/second-example tests: `references/generalization-gate.md`.

Cockpit: present the P1–P7 run as a checklist tracker (output-style T3, PASS/FAIL marks) before writing the block below into the plan document.

**Output** — append to the plan document:

```markdown
## Plan Audit (Code Guardian PLAN MODE)
P1 Cross-Layer Trace: PASS/FAIL — Verified-by: <grep output>
P2 Scale Verification: PASS/FAIL — Verified-by: <row count + method>
P3 Secrets Hygiene: PASS/FAIL — Verified-by: <grep for ?key=>
P4 Cached-Config Safety: PASS/FAIL — Verified-by: <grep for raw env reads>
P5 Pattern Source Quality: PASS/FAIL — Verified-by: <audit of referenced file>
P6 WIP Staging Discipline: PASS/FAIL — Verified-by: <briefing template check>
P7 Generalization: PASS/FAIL — Verified-by: <example-literal grep: hits only in test/config sections>
```

Any FAIL → the plan is **BLOCKED** until its author updates it. No subagent dispatch before all seven PASS.
