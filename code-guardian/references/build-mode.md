# BUILD MODE — full protocol

> Loaded before writing any code for a build/change/fix. The router lives in `SKILL.md`; this file holds the full engine, schema query, audit tables, and report formats. Operating Principles (in SKILL.md) govern every step below. The Step 1d worklist engine here is the single definition referenced by DEBUG MODE (`references/debug-mode.md`) Phase 1d/4b and by Step 2 below — do not duplicate it.

### Step 0: Pre-Flight Triage

The trigger never scales — the **depth** does. Classify the change first:

| Change shape | Pre-flight depth |
|---|---|
| Comment/doc/copy-text only, zero behavior change | 1a only; audit runs LIGHT |
| Additive, single file, touches no shared symbol, no DB | 1a–1c; 1d as a one-hop consumer check |
| Touches a shared function/helper/model/layout/middleware, a schema, a status value's semantics, config keys, or deletes anything | Full 1a–1e; 1d driven to fixpoint |

When unsure which row applies, take the deeper one.

### Step 1: Pre-Flight (before writing code)

Senior view: senior-card §B — right problem, already-exists search, simplest
design, named trade-offs — before designing the change.

**1a. Scope** — Which tables, functions, files will this change touch?

**1b. Schema Check** — If the change touches the DB, run one consolidated introspection query against the **live** database (adapt credentials per project CLAUDE.md):

```bash
${MYSQL_BIN} -u ${USER} -p${PASS} -h ${HOST} -P ${PORT} ${DB} -e "
  SELECT c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.COLUMN_KEY, c.IS_NULLABLE,
         s.INDEX_NAME, k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME
  FROM information_schema.COLUMNS c
  LEFT JOIN information_schema.STATISTICS s
    ON c.TABLE_SCHEMA = s.TABLE_SCHEMA AND c.TABLE_NAME = s.TABLE_NAME AND c.COLUMN_NAME = s.COLUMN_NAME
  LEFT JOIN information_schema.KEY_COLUMN_USAGE k
    ON c.TABLE_SCHEMA = k.TABLE_SCHEMA AND c.TABLE_NAME = k.TABLE_NAME AND c.COLUMN_NAME = k.COLUMN_NAME
    AND k.REFERENCED_TABLE_NAME IS NOT NULL
  WHERE c.TABLE_SCHEMA = '${DB}' ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;"
```

All columns, indexes, FKs in one query. Duplicate rows per column = multiple indexes/FKs, expected.

**1c. Existing-Code & Duplicate-Resource Scan** — before writing new logic or constants, grep for what's already there:

- **1c.1 Secrets/constants:** new API key, DSN, URL, email, or endpoint constant → `bash ~/.claude/skills/code-guardian/tools/detect-secrets.sh .` plus a grep for the exact domain/URL. Exists already → reuse via `config(...)`. Never copy-paste a hardcoded literal.
- **1c.2 Functions/classes:** grep the planned name AND 2–3 purpose keywords (`grep -rn "function\s\+<name>\b" --include="*.php" --exclude-dir=vendor .`). Near-name match (`formatPrice` vs planned `formatCurrency`) → read it; extend it or document why a sibling is needed.
- **1c.3 Templates/views:** grep distinctive content (heading, form action, component tag) and list existing partials/components. A matching partial exists → `@include`/`<x-...>`/`<Component/>`, don't duplicate markup.

Output is silent; findings shape the implementation plan before code is written.

**1d. Recursive Dependency Propagation — the worklist engine.** The most critical pre-flight step.

Impact analysis is not "grep the callers and fix them." Fixing a caller can change THAT caller's own contract, which has its own callers — impact propagates **transitively** until it dies out. "Page B broke after I changed Page A" is almost always a propagation that stopped one hop short. Run it as a worklist/fixpoint algorithm; it provably terminates.

Three structures, maintained for the whole change (persist to `.code-guardian-propagation.md` for large/multi-session changes):
- **QUEUE** — pending `(symbol, change-kind, origin)` items (FIFO)
- **VISITED** — `(symbol, change-kind)` pairs already analyzed; guarantees termination, breaks cycles
- **LEDGER** — the propagation tree: every symbol reached, classification, required edit

**Seed** the QUEUE with every symbol you intend to change, tagged with its **change-kind**:

| Change-kind | Reaches a consumer that… |
|---|---|
| Signature (param add/remove/reorder/retype/now-required) | passes arguments or relies on arity |
| Return type / shape | reads the return (key, index, type, null-ness) |
| Side-effect add/remove (DB write, session, event, cache, mail, queue) | depends on the effect, its absence, or its ordering |
| Thrown / error behavior | has — or lacks — a catch for the new/removed throw |
| Field / column rename, retype, drop | reads, writes, or serializes the field (trace ALL layers — P1) |
| Enum / status / state-value semantics | produces OR consumes that value (→ State-Transition Fan-Out) |
| Visibility / access / auth scope | calls from a context the new scope excludes (→ Auth Parity) |
| Deletion / deprecation | references the symbol at all |
| Config / env key rename or default change | reads the key through the config layer (P4) |

**The loop — until QUEUE is empty:**

1. **Dequeue** `(S, kind, origin)`. In VISITED → skip. Else add to VISITED.
2. **Find ALL consumers of S** — prefer LSP find-references; fall back to grep on name + purpose keywords. Cross-language and cross-layer count: front-end fetch/XHR callers, templates, CLI/cron entry points, queue jobs, webhooks, AND DB triggers.
   ```bash
   grep -rn "<symbol>" --include="*.php" --include="*.js" --include="*.ts" --include="*.vue" --include="*.blade.php" .
   ```
3. **Classify each consumer C** against `kind`:
   - **UNAFFECTED** — `kind` doesn't reach C. Record, stop.
   - **ABSORBS** — C must change, but its OWN contract stays identical. Record the edit as a LEDGER leaf. Do not enqueue.
   - **PROPAGATES** — C must change AND its own contract changes. Record the edit, **enqueue `(C, C's-new-change-kind, S)`** — this is the recursion.
4. Repeat until the QUEUE drains = **fixpoint**. Termination is guaranteed (symbol×change-kind is finite; VISITED admits each pair once) — rely on it, never stop early "to not go too deep."

⚡ **Parallel classification:** when one dequeue yields ≥5 consumers, dispatch one subagent per consumer (or batch of consumers) to classify in parallel. Each gets: the symbol, the change-kind, the consumer's file, and must return `UNAFFECTED|ABSORBS|PROPAGATES + required edit + evidence`. PROPAGATES results re-enter the QUEUE in the main loop — only the loop itself stays serial.

**LEDGER output** (recorded, not silent) — a tree to any depth:
```
SEED  saveUser()                       [Signature: +$role now required]
├─ RegisterController::register()       PROPAGATES → must pass $role; response gains role → ENQUEUED
│  └─ POST /register (JSON contract)    PROPAGATES → payload gains "role" → ENQUEUED
│     └─ mobile RegisterScreen parse     ABSORBS   → tolerant parser · leaf
├─ ProfileController::update()          ABSORBS   → passes $role=current · leaf
└─ database/seeders/UserSeeder          UNAFFECTED → builds via factory
QUEUE empty → FIXPOINT | PROPAGATES 3 (all planned) · ABSORBS 2 · UNAFFECTED 1
```

**Done-ness:** QUEUE empty AND every PROPAGATES node has a planned/applied fix AND no fix introduced a consumer not yet in the LEDGER. When unsure between ABSORBS and PROPAGATES, choose PROPAGATES — under-classifying is what ends the closure one hop short.

**1e. Blast-Radius Council Gate.** Fires ONLY when **all four** hold: (1) LEDGER ≥ 5 distinct consumers at any depth; (2) non-additive change (modifies existing semantics/signature/shape — pure additions don't fire); (3) sparse consumer test coverage (<~30% of consumers have tests that would fail on a semantic break; "don't know" counts as sparse); (4) non-trivial reversal (coordinated rollback edits, data backfill, or lossy down-migration). Can't name all four → gate did not fire, decide directly, one line: "consumers=2, gate did not fire".

When fired: invoke the `llm-council` skill before writing code. Frame as *"in-place modify vs. fork vs. adapter-wrap for <change>"*, invite a Path C, supply the spec + 1d LEDGER + coverage matrix + reversal note. Record:
```
1e Gate: FIRED|NOT-FIRED — consumers=<n> | non-additive=<y/n> | sparse-coverage=<y/n> | hard-reversal=<y/n>
Council verdict (if fired): <Recommendation> — <One Thing to Do First>
```

### Step 2: Post-Change Verification — second fixpoint

Senior view: senior-card §C+§D while the diff is open — 6-month test, DRY,
scope fence, does-this-still-make-sense.

The edits you actually made are new evidence. After writing code:

1. **Symbol-loss gate (mechanical, before you re-seed by hand).** A re-seed driven by reading the diff can skip a symbol you didn't notice you dropped — especially after a full-file `Write` or a large refactor that regenerates a file from memory. Run the detector over the diff first; it reports every function/method/class that disappeared or changed signature, using `git show <ref>:<file>` as the before-image:
   ```bash
   python3 ~/.claude/skills/code-guardian/tools/detect-symbol-loss.py --git
   ```
   Reconcile each `LOST` / `CHANGED` line against the 1d LEDGER: present as an **intended** removal/signature change → fine; **absent** from the LEDGER → a symbol you dropped or altered without tracing its consumers — restore it, or seed `(symbol, Deletion|Signature, origin)` into the QUEUE. `MOVED` (lost here, re-defined in another changed file) is informational. **Scope:** the tool sees names + signatures, not behaviour — a same-signature body rewrite is invisible to it and still needs the audit + tests. Paste the `SUMMARY findings=…` footer as Verified-by.
2. `git diff --name-only HEAD` + read the hunks; **re-seed the QUEUE** with every symbol whose contract the edits actually altered — the gate above names the structural losses; you still add the semantic/side-effect change-kinds it cannot see. Flag change-kinds you didn't foresee.
3. Re-run the 1d loop to fixpoint on those seeds.
4. Reconcile the LEDGER: every PROPAGATES node is now (a) fixed AND verified at its call site, or (b) re-classified with a reason. One open PROPAGATES node = the change is not done, regardless of how green the original file looks.

A symbol the plan-time LEDGER missed is itself a finding — note why 1d under-scoped it in `.audit-log.md`.

### Step 3: Audit (after writing code — always)

Senior view: senior-card §E closes the task — self-review as foreign code,
plain-language explainability, journal the lesson.

> **Verification-not-assertion.** Audit checks are **VERIFIED** by command output, not **ASSERTED** by reading code. Dump the actual serialized response (curl/tinker/Playwright), run the actual grep, hit the actual endpoint. Three standing reflexes:
> - **A) JSON inspection over code reading** — dump the real payload the consumer receives; prove every consumed key non-null on the bug path. Structural match ("producer returns X, consumer reads X") passes while the runtime payload is `{X: undefined}`.
> - **B) Hunt-and-replace** — after fixing a pattern once, grep the whole tree for the same pattern: `grep -rn '<unfixed>' <dirs> | grep -v '<fixed-form>' | grep -v 'codeguardian-ok'` — must be empty before "done".
> - **C) Layout-link → route existence** — extract every internal href from nav/layouts, list registered GET routes, diff. Any href not in the route list is a guaranteed 404.

**Cross-layer index** — if the diff matches a trigger, load `references/cross-layer-checks.md` and run that reflex even on a LIGHT audit:

| Reflex | Trigger in diff |
|---|---|
| Cross-Layer Data Contracts | data produced in one layer, read in another (API↔client, controller↔view) |
| Return Type Completeness | function with conditional branches / early returns |
| Interface Boundary Verification · ORM/Model Verification | new interface impl; model attributes vs real columns |
| Single-Use Resource Consumption | tokens, coupons, invites, one-time actions |
| Auth Enforcement Parity | endpoint reachable via >1 entry point (web, ajax, cron, CLI, webhook) |
| Session Lifecycle at Auth Boundaries | login, logout, privilege change |
| HTTP Response Cacheability | authenticated pages + proxy/CDN |
| Error-Path Log Content Hygiene | new logging on error paths |
| HTTP Header-Value Injection · Verb Safety (CSRF-on-GET) · Open Redirect | user input in headers; state-change via GET; `?next=`/`?redirect=` |
| Frontend Reactivity Traps | reactive framework state mutation |
| N+1 · Composite Index Order · Coercion Defeating Indexes · Charset Drift · Deep-Offset Pagination | queries in loops; new/changed indexes or WHERE columns; LIMIT/OFFSET |
| Cache Invalidation Coverage | any cache write/read of rows also shown in lists/aggregates |
| Concurrency/TOCTOU | counters, quotas, check-then-write |
| Queue/Task Idempotency · Multi-Step Side-Effect Atomicity · Error-Path Resource Cleanup | jobs, queues, multi-step external effects, acquired resources |
| Long-Running Data Backfill | migration/backfill over large tables |
| Input Size & Complexity Limits | new endpoint accepting user payloads |
| Timezone / Date-Boundary | date comparisons, "today", cron schedules |
| NULL Semantics in Aggregation | COUNT/SUM/AVG/MIN/MAX, LEFT JOIN + WHERE |
| State-Transition Side-Effect Fan-Out | a status value gains/changes a side-effect (mail, flag, hook) |
| Producer/Consumer State Liveness | producing a (status, flag, date) combination consumed by crons/workers |
| DB-Driven Dispatch Awareness | calling anything "dead code"; dispatch via DB rows |
| DB Trigger-Change Integrity | any DROP/CREATE TRIGGER |
| Direct-Fetch Endpoint Bootstrap | new fetch/XHR/AJAX target |
| Batch-Loop Throw-Safety | new throw/assert inside a loop over a work-set |
| Coverage-Claim & Guard-Branch | claiming "all X fixed"; guards on user-suppliable values |
| Data-Repair Script Discipline | one-shot data fixes (Heilung) |
| Router-Param Rename Sweep | renaming a param a router/switch dispatches on |

**3a. Triage:**

```bash
git diff --name-only HEAD
```

| Change size | DB touched? | Intensity |
|---|---|---|
| < 20 lines | No | LIGHT — all layers spot-check; logic + redundancy full depth |
| < 20 lines | Yes | FOCUSED — all layers spot-check; + DB integrity full depth |
| 20+ lines | No | STANDARD — all layers full depth except DB (spot-check) |
| 20+ lines | Yes | FULL — all 5 layers full depth |

Spot-check = scan for obvious violations. Full depth = exhaustive — **load `references/audit-deep-checks.md`** for each full-depth layer, and `references/cross-layer-checks.md` on STANDARD/FULL. Even a 1-line change gets all layers as spot-check; there is no skip — but a spot-check that matches a cross-layer index row escalates that one reflex to full depth. The **Self-Slop Sweep runs at EVERY intensity including LIGHT** — it is cheap (one diff scan) and slop hides in small diffs too; it only ever inspects the current diff.

**3b. Read** all changed files completely, plus calling/called context.

**3c. Audit log history** — read `.audit-log.md`; a category that fired recently in this codebase escalates from spot-check to full depth.

**3d. Analyze — six layers.** ⚡ On FULL intensity, dispatch the layers as parallel subagents (each gets: the diff, its layer's deep-check section from `references/audit-deep-checks.md`, and the verification rule; each returns findings with command-output proof). On LIGHT/FOCUSED/STANDARD run inline:

- **DB Integrity** — fields match live schema; FKs correct and not runtime-bypassed; indexes on queried columns; money never FLOAT; locale-safe numeric parsing; counter capacity. Full depth → reference §Layer Deep Checks.
- **Logic** — dead code, unhandled edge cases (null/0/negative/empty), missing returns in branches, off-by-one, raw env reads outside config (P4), **Generalization**: no example literal from the requirement in `if`/`switch`/regex/lookup control flow (law + tests: `references/generalization-gate.md`); when the task named concrete values run `python3 ~/.claude/skills/code-guardian/tools/detect-hardcoded-cases.py --root <module> --examples '<values>'` and paste the SUMMARY.
- **Efficiency** — loops replaceable by one query, sequential awaits that could parallelize, SELECT-in-loop, missing pagination, `ORDER BY RAND()` on filtered sets.
- **Redundancy** — five script-backed detectors, every audit; paste each script's output or SUMMARY footer as proof ("checked, looks clean" is not a result). LIGHT/FOCUSED may skip R2/R3/R5 when the diff is <20 lines AND introduces no new function/template/query:

| | Detector | Command |
|---|---|---|
| R1 | Hardcoded secrets / credential duplication | `bash ~/.claude/skills/code-guardian/tools/detect-secrets.sh <repo>` |
| R2 | Cross-file code clones | `python3 ~/.claude/skills/code-guardian/tools/detect-clones.py --root . --kind code --cross-file-only` |
| R3 | Cross-file template/markup clones | `python3 ~/.claude/skills/code-guardian/tools/detect-clones.py --root resources --kind html --min-chars 200` |
| R4 | Config-as-code leaks (URL/email/path in ≥2 files) | `bash ~/.claude/skills/code-guardian/tools/detect-config-leaks.sh <repo>` |
| R5 | Cross-file query clones | `python3 ~/.claude/skills/code-guardian/tools/detect-clones.py --root app --kind sql --cross-file-only` |

  Failure conditions, fixes, severity mapping, and `.code-guardian-redundancy.yml` overrides → reference §R1–R5.
- **Security** — SQL injection, sensitive fields in responses, missing auth, JWT alg pinning, unsafe sinks (`unserialize`/`include`/`shell_exec`/`eval`/XXE), mass assignment, rate-limit key scope (attacker-rotatable keys are not rate limits; mask IPv6 to /64), IDOR. Full depth → reference §Security Layer.
- **Self-Slop Sweep (always-on, diff-only — the agent cleans up after ITSELF).** Strip the AI-slop *this change* introduced; scope is the current diff, never pre-existing code (that is opt-in CLEANUP MODE — `references/cleanup-mode.md`). Run:
  ```bash
  python3 ~/.claude/skills/code-guardian/tools/detect-dead-code.py --diff-slop
  python3 ~/.claude/skills/code-guardian/tools/detect-hardcoded-cases.py --git [--examples '<task values>']
  ```
  The second run catches the overfitting anti-pattern in your OWN added lines: an example literal from the requirement sitting in an `if`/`switch`/regex/lookup you just wrote (law + fix direction: `references/generalization-gate.md`). Findings → replace with the generic mechanism; genuine single-value rules get an `INTENTIONAL-SPECIAL-CASE:` marker with the business source.
  Act on each label: **REMOVABLE** (a symbol you added with zero references anywhere) → remove it; **DEBUG-LEFTOVER** (`var_dump`/`dd`/`dump`/`console.log`/`print`/`print_r`, or `TODO`/`FIXME`/`PLACEHOLDER`/`example` you just added) → remove it; **REVIEW** (added, currently unreferenced, but matches a route/handler/command/component entry-point pattern) → keep, it is likely wired up next. The tool catches the **mechanical** slop reliably (unused additions, debug lines). It does NOT catch **semantic** slop — those you remove by reading: a comment that merely restates the next line → delete; a single-use abstraction you just invented (interface/factory/wrapper with exactly one caller) → inline it (YAGNI / Rule of Three); a helper you wrote that duplicates one your 1c.2 pre-flight grep should have found → reuse the existing one (grep the tree for it); any *new* dependency/import → confirm the package actually exists (anti-slopsquatting). This layer removes ONLY your own just-written additions; if a removal would touch anything present before this diff, stop and report instead (that is CLEANUP MODE's job, and it is report-only). **Verified-by**: paste the `--diff-slop` `SUMMARY findings=… exit=…` footer.

**3e. Report.**

Clean:
```
✅ [X files | Y lines] clean
   Verified by: <commands run, e.g. "link-click-test 39/39, payload dump 4 keys non-null, R1–R5 SUMMARY findings=0">
```

Findings (only sections with issues):
```
## Audit: [files]
🔴 [category]: [problem] → [fix]      Verified-by: <command output proving it>
🟡 [category]: [problem] → [recommendation]   Verified-by: <command output>
[X] critical | [Y] warnings → APPROVED / NEEDS FIX / BLOCKED
```

Forbidden phrases (assertions, not verifications): "I read the controller and the keys match" · "the route ordering looks correct" · "the component should handle this" · "same pattern as before". Required form: "Ran X, got Y" with pasted output · "Grepped for Z, 0 unfixed instances".

Verdict: **APPROVED** (0 critical, ≤2 warnings, all critical-path checks VERIFIED) · **NEEDS FIX** (0 critical, 3+ warnings) · **BLOCKED** (any critical OR any unverified critical-path check).

**3f. Audit log** — append to `.audit-log.md`:
```
## [DATE] [files] — [VERDICT]
C:[X] W:[Y] | [one-line findings summary]
PATTERN: [name it if recurring]
```

**3g. If BLOCKED** — fix criticals → re-audit affected layers → "Fix verified" or "Fix incomplete: [reason]".
