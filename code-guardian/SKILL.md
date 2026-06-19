---
name: code-guardian
description: >
  MANDATORY for ANY code change — no exceptions, no rationalization, no "this is just a small thing".
  Use when: writing code, editing files, changing any function/method/component, fixing bugs,
  adding features, refactoring, integrating libraries, updating imports, changing imports,
  adding images, adding routes, modifying templates, modifying styles, modifying configs,
  adding form fields, changing controllers, changing models, changing services, changing migrations.
  Use when: encountering any error, 404, 500, exception, stack trace, "doesn't work", "is broken",
  "won't load", "shows nothing", "wrong data", "missing X". Run cross-page dependency trace.
  Use when: someone asks "wurde X eingebaut", "funktioniert Y", "warum macht Z das nicht".
  ESPECIALLY trigger when: changing shared functions, helpers, utilities, layouts, middlewares,
  models, migrations — anything used in multiple places.
  TRIGGER PHRASES: "change", "update", "add", "fix", "refactor", "integrate", "build", "create",
  "implement", "aendere", "fuege hinzu", "fixe", "baue", "erstelle", "implementiere".
  ANTI-RATIONALIZATION: If you think "this is too small to need an audit" — that IS the trigger.
  If you think "I already understand this" — that IS the trigger.
  If you think "the user is waiting, just do it quickly" — that IS the trigger.
  Bugs that ship are caused by skipped audits. Run the workflow EVERY TIME.
---

# Code Guardian (v10)

## Operating Principles

Stated once; they govern every mode below. The skill defines goals and gates — how you reach a gate is your judgment; whether you pass it is not.

1. **Evidence over assertion.** Before reporting progress or a verdict, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. "Ran X, got Y" with pasted output is proof. "I read the code and it looks right" is not.
2. **Act when ready.** Run a reflex, record the result, move on. Do not re-derive established facts, re-litigate decided questions, or narrate checks you will not run. Pre-flight is preparation for action, not a substitute for it.
3. **Stay in scope.** Findings outside the current diff are *reported*, never silently fixed. No refactoring, tidying, or new abstractions beyond the task. A bug fix doesn't need surrounding cleanup.
4. **Fan out independent work.** When items are independent — consumers to classify, audit layers to verify, hypotheses to argue — dispatch parallel subagents instead of iterating serially. Marked ⚡ below. Subagents receive: the exact check to run, the diff/symbol context, and the required output format (verdict + command output).
5. **Write down what you learn.** `.audit-log.md` (findings & patterns), `.code-guardian-propagation.md` (open worklists for large changes). Consult both at the start of a run; keep them current. One lesson per entry, with why it mattered.

## Mode Selection

```
Task received
  ├─ Bug/Error/Broken? ──→ DEBUG MODE
  ├─ Spec/Plan exists? ──→ PLAN MODE (review plan before implementation)
  └─ Build/Change/Fix?  ──→ BUILD MODE
                              ├─ Pre-Flight (BEFORE code)
                              └─ Audit (AFTER code)
```

## Reference Files (progressive disclosure)

The full check catalog lives in `references/` next to this file. Load with the Read tool when the rule below says so — not preemptively.

| File | Contents | Load when |
|---|---|---|
| `references/cross-layer-checks.md` | 36 cross-layer reflexes, each with audit commands + the real bug it came from | Audit triage = STANDARD or FULL; or any index row below matches the diff |
| `references/audit-deep-checks.md` | Full-depth layer checks (DB, Logic, Efficiency, Security) + R1–R5 redundancy detectors in detail | Any audit layer runs at full depth |
| `references/design-rationale.md` | v4–v9 rule history, council-gate rationale | Only when modifying this skill itself |

**Cross-layer index** — if the diff matches a trigger, load `cross-layer-checks.md` and run that reflex even on a LIGHT audit:

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

---

## PLAN MODE

Bugs that survive the audit usually originated in the plan. Run these 6 reflexes against any spec/plan before implementation is dispatched — and again when receiving a plan from another author. Run them, record PASS/FAIL with proof, move on (Principle 2).

**P1. Cross-Layer Trace for Every New Field.** Walk each new field end-to-end: DB column → model allowlist/visibility → serializer/response builder → transport payload → client template. A model-layer allowlist does NOT guarantee client delivery — if the serializer uses an explicit key whitelist, an absent field is dropped silently. *Check:* grep the response builders for explicit key lists; if any exist, the plan must include the serializer change.

**P2. Scale Verification for DB Iteration.** Every row-iterating command/job names its streaming method by expected count: `<1000` → `->get()` · `1k–100k` → `->cursor()`/`->lazy(N)` · `100k+` → `->lazyById(N)` + job queue. Gotchas: some streaming primitives silently re-drive the query and ignore an upstream `LIMIT` — if you need streaming AND a cap, verify the actual processed row count. Aggregates (`SUM/COUNT/AVG/MAX/MIN`) scan rows: verify with `EXPLAIN` that an index is used and the row estimate is bounded; consider a denormalized counter for hot paths.

**P3. Secrets Hygiene for API Calls.** Keys/secrets/signatures travel in **headers**, never query strings (`?key=` leaks via exception logs, access logs, Referer). Inbound webhook signatures compare with constant-time equality (`hash_equals`, never `==`/`===` — PHP type-juggling makes two `^0+e\d+$` hashes compare equal as floats; bcrypt → `password_verify`). User-facing magic links: signed, time-limited, bound to route+expiry; store only a SHA-256 hash of the token; one-time use via `consumed_at` checked+set in one transaction. *Check:* grep the plan for `?key=`, `?api_key=`, `?token=` → any hit blocks that section.

**P4. Cached-Config Safety.** Runtimes that pre-compile config at boot snapshot env vars once; raw env reads outside the config layer return null post-cache. Every new env var goes through the project's config layer. *Check:* grep plan pseudocode for direct env reads outside config files.

**P5. Pattern Source Quality.** When the plan says "follow the pattern of `<file>`", audit that file against P1–P4 first — inherited bugs propagate because "matches existing pattern" reads as approval. Any match → the plan names which inherited bugs to FIX, not copy.

**P6. WIP Staging Discipline for Subagent Briefings.** On a branch with pre-existing uncommitted WIP, subagent prompts must mandate hunk-level staging: `git add <new-file>` or `git add -p <existing-file>` — never `git add .`/`-A`/bare `git add <existing-file>` (sweeps ALL hunks in the file). Fix the briefing template, not the symptom; by audit-time the commit already exists.

**Output** — append to the plan document:

```markdown
## Plan Audit (Code Guardian PLAN MODE)
P1 Cross-Layer Trace: PASS/FAIL — Verified-by: <grep output>
P2 Scale Verification: PASS/FAIL — Verified-by: <row count + method>
P3 Secrets Hygiene: PASS/FAIL — Verified-by: <grep for ?key=>
P4 Cached-Config Safety: PASS/FAIL — Verified-by: <grep for raw env reads>
P5 Pattern Source Quality: PASS/FAIL — Verified-by: <audit of referenced file>
P6 WIP Staging Discipline: PASS/FAIL — Verified-by: <briefing template check>
```

Any FAIL → the plan is **BLOCKED** until its author updates it. No subagent dispatch before all six PASS.

---

## BUILD MODE

### Step 0: Pre-Flight Triage

The trigger never scales — the **depth** does. Classify the change first:

| Change shape | Pre-flight depth |
|---|---|
| Comment/doc/copy-text only, zero behavior change | 1a only; audit runs LIGHT |
| Additive, single file, touches no shared symbol, no DB | 1a–1c; 1d as a one-hop consumer check |
| Touches a shared function/helper/model/layout/middleware, a schema, a status value's semantics, config keys, or deletes anything | Full 1a–1e; 1d driven to fixpoint |

When unsure which row applies, take the deeper one.

### Step 1: Pre-Flight (before writing code)

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

> **Verification-not-assertion.** Audit checks are **VERIFIED** by command output, not **ASSERTED** by reading code. Dump the actual serialized response (curl/tinker/Playwright), run the actual grep, hit the actual endpoint. Three standing reflexes:
> - **A) JSON inspection over code reading** — dump the real payload the consumer receives; prove every consumed key non-null on the bug path. Structural match ("producer returns X, consumer reads X") passes while the runtime payload is `{X: undefined}`.
> - **B) Hunt-and-replace** — after fixing a pattern once, grep the whole tree for the same pattern: `grep -rn '<unfixed>' <dirs> | grep -v '<fixed-form>' | grep -v 'codeguardian-ok'` — must be empty before "done".
> - **C) Layout-link → route existence** — extract every internal href from nav/layouts, list registered GET routes, diff. Any href not in the route list is a guaranteed 404.

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

Spot-check = scan for obvious violations. Full depth = exhaustive — **load `references/audit-deep-checks.md`** for each full-depth layer, and `references/cross-layer-checks.md` on STANDARD/FULL. Even a 1-line change gets all 5 layers as spot-check; there is no skip — but a spot-check that matches a cross-layer index row escalates that one reflex to full depth.

**3b. Read** all changed files completely, plus calling/called context.

**3c. Audit log history** — read `.audit-log.md`; a category that fired recently in this codebase escalates from spot-check to full depth.

**3d. Analyze — five layers.** ⚡ On FULL intensity, dispatch the five layers as parallel subagents (each gets: the diff, its layer's deep-check section from `references/audit-deep-checks.md`, and the verification rule; each returns findings with command-output proof). On LIGHT/FOCUSED/STANDARD run inline:

- **DB Integrity** — fields match live schema; FKs correct and not runtime-bypassed; indexes on queried columns; money never FLOAT; locale-safe numeric parsing; counter capacity. Full depth → reference §Layer Deep Checks.
- **Logic** — dead code, unhandled edge cases (null/0/negative/empty), missing returns in branches, off-by-one, raw env reads outside config (P4).
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

---

## DEBUG MODE

### Phase 1: COLLECT (no fix, no suggestion yet)

- **1a.** Exact symptom: error text, stack trace, expected vs actual.
- **1b.** What changed recently: `git log --oneline -5 && git diff --name-only HEAD~3`
- **1c.** Read the entire affected function + 2 levels of callers and callees — not just the error line.
- **1d. Cross-page dependency trace** — the bug is often not where the error shows. Run the BUILD 1d worklist engine to fixpoint (same QUEUE/VISITED/LEDGER), plus per consumer: was this consumer recently changed? was the function itself? (`git log --oneline -10 -- <file>`). Function changed + consumer not = likely **dependency break** — the most common root cause of "Page B broke after I worked on Page A".

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
- **4b. Recursive consumer verification** — the fix is itself a change with a change-kind: seed it into the 1d engine, drive to fixpoint. The consumer you're fixing FOR is rarely the only one. A fix that repairs one page and breaks three others is not a fix.
- **4c. Gate:** `Call-chain ✅/❌ | ALL consumers verified ✅/❌ ([X]/[Y]) | Edge cases ✅/❌ → Ready ✅/❌` — any ❌ → not ready.

### Phase 5: IMPLEMENT + VERIFY

1. Fix + adjust all affected dependencies → 2. test reproducing the bug (now green) → 3. existing tests still green → 4. confirm bug gone, edge cases handled, dependencies intact → 5. run the BUILD post-change symbol-loss gate (Step 2.1) so the fix didn't silently drop a sibling function, then the Audit (3a–3g) on the fix diff — a fix is a code change like any other.

### Escalation

- **Failed once** → document why, mark the hypothesis disproven, restart Phase 1.
- **Failed twice** → convene `llm-council` unconditionally before reporting: *"two distinct root-cause fixes failed for <bug> — what is the council missing?"* with both attempts + Phase 2 analysis. New hypothesis → restart Phase 1 with it. Council finds nothing → STOP and report both attempts + analysis + verdict to the user.

---

## Self-Tuning

When reading `.audit-log.md` at audit start:
- A finding type appeared 3+ times recently → flag **SYSTEMIC**, recommend a structural fix, not another point fix.
- A category with 0 findings in the last 10 audits → run at reduced depth.
- A category firing on >50% of audits → run it first and most aggressively.

## Core Rules

- **Pre-flight is not optional** — schema check before code prevents whole bug categories. **The audit always runs** — triage scales depth, never existence.
- **Live DB beats any static file.** No DB access → ask once; if unavailable, audit without the DB layer and mark "⚠️ DB unchecked".
- **Output proportional to findings** — clean code gets one line; problems get detail.
- **The council advises; commands verify.** LLM-council output is never a substitute for command-output proof.
- Version history and gate rationale: `references/design-rationale.md` (load only when editing this skill).
