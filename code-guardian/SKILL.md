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

# Code Guardian

## Mode Selection

```
Task received
  ├─ Bug/Error/Broken? ──→ DEBUG MODE
  ├─ Spec/Plan exists? ──→ PLAN MODE (review plan before implementation)
  └─ Build/Change/Fix?  ──→ BUILD MODE
                              ├─ Pre-Flight (BEFORE code)
                              └─ Audit (AFTER code)
```

---

## PLAN MODE (v5 — born from real bugs that locked in at plan-time)

Bugs that survive the audit phase usually originated in the plan. Run these 6 reflexes against any spec/plan BEFORE implementation is dispatched — and again when receiving a plan from another author.

**The 6 plan-time reflexes:**

### P1. Cross-Layer Trace for Every New Field

For every NEW field/column/property, walk the data path end-to-end and
**prove** each layer is wired up explicitly. A model-layer allowlist does
NOT guarantee client delivery: if the serializer uses an explicit key
whitelist, any field absent from it is dropped silently and the client-side
conditional never fires. **Always grep the serializer, not the model.**

```
DB column / migration
     ↓
Model allowlist + visibility (exposed? hidden? computed?)
     ↓
Serializer / response builder (raw model vs explicit key whitelist?)
     ↓
Transport payload (JSON / props / context)
     ↓
Client template (read + conditional render)
```

**Verification during plan review:** for each new field, grep the response
builders for explicit key lists. If any exist, the plan MUST include a
serializer change — adding the column + model allowlist is not enough.

### P2. Scale Verification for DB Iteration

Every command/job that iterates rows MUST specify the streaming method based
on expected row count:

| Row count    | Method                                | Why                          |
|--------------|---------------------------------------|------------------------------|
| < 1000       | `->get()`                             | Fits in memory               |
| 1000 – 100k  | `->cursor()` (preferred) or `->lazy(N)` | Streams without OOM          |
| 100k+        | `->lazyById(N)` + dedicated job queue | Resilient to crashes         |

**Gotcha:** some streaming primitives silently override upstream row limits
(internal pagination re-drives the query and ignores an earlier `LIMIT` / take).
If the plan needs BOTH streaming AND a hard cap, either pick a primitive that
respects both OR apply the cap server-side — and verify the actual row count
processed, not the primitive name you picked.

**Aggregate trap:** `SUM` / `COUNT` / `AVG` / `MAX` / `MIN` look O(1) but
scan rows. Three failure modes on large tables: (1) no `WHERE` narrowing, so
the aggregate walks the full history every call; (2) the filtered column has
no covering index, so even a narrow `WHERE` still full-scans; (3) computed
live per request where a denormalized counter or materialized rollup would
do. Verify with `EXPLAIN`: index is used AND the row estimate is bounded.

### P3. Secrets Hygiene for API Calls

Every plan that introduces an API call OR an inbound webhook endpoint MUST pass the key / shared secret / signature via **header**, never query string — in BOTH directions. Leakage surface for `?key=` / `?api_key=` / `?token=`: HTTP-client exceptions log the full URL; web-server and reverse-proxy access logs record the query string; browser history and Referer headers forward it on any redirect.
- Inbound webhooks: signature in a header, compared with a constant-time equality function.
- User-facing download/reset/magic-login links: signed, time-limited URL bound to route+expiry and verified server-side; store a SHA-256 HASH of the token in the DB (never the raw value); enforce one-time use via a `consumed_at` column checked+set in a single transaction.

**Verification during plan review:** grep the plan's pseudocode for `?key=`,
`?api_key=`, `?token=`. If found, reject the plan section and require header-based
auth instead.

### P4. Cached-Config Safety

Runtimes that pre-compile config at boot snapshot env vars ONCE; raw env reads outside the config layer return null post-cache. Every new env var MUST go through the project's config layer — grep the plan's pseudocode for direct env reads outside config files; any match → reject.

### P5. Pattern Source Quality Check

When the plan says "follow the pattern of `<referenced-file>`", audit that
file against P1-P4 FIRST. Inherited bugs propagate silently because reviewers
read "matches existing pattern" as approval.

**Plan-time check:** grep the referenced file for each P1-P4 anti-pattern.
Any match → the plan must call out which inherited bugs to FIX in the new
file, not which to copy.

### P6. WIP Staging Discipline for Subagent Briefings

When dispatching subagents on a branch with pre-existing uncommitted WIP, the
subagent prompt MUST instruct hunk-level staging:

```
RIGHT — explicit named files only, hunk-verified:
  git add path/to/new-file.php          # safe: brand-new file
  git add -p path/to/existing-file.php  # interactive: pick only your hunks

WRONG — sweeps in unrelated WIP:
  git add path/to/existing-file.php     # stages ALL changes in the file
  git add .                              # stages everything
  git add -A                             # stages everything
```

**Why plan-time, not audit-time:** the subagent prompt is locked when dispatch fires; by the time the audit catches swept-in WIP, the commit already exists. `git add <path>` sweeps ALL uncommitted hunks in the same file — on a branch with pre-existing WIP, stage per-hunk (`git add -p`) and verify the diff before commit, or unrelated work ships under a wrong message and history needs rewriting to untangle. Fix the briefing template, not the symptom.

### Plan Mode Output

After running all 6 reflexes, append to the plan document a `## Plan Audit` section:

```markdown
## Plan Audit (Code Guardian PLAN MODE)

P1 Cross-Layer Trace: PASS / FAIL
  Verified-by: <grep output proving controller serialization path>
P2 Scale Verification: PASS / FAIL
  Verified-by: <row count + chosen iteration method>
P3 Secrets Hygiene: PASS / FAIL
  Verified-by: <grep for ?key= in plan content>
P4 config:cache Safety: PASS / FAIL
  Verified-by: <grep for env() in plan pseudocode>
P5 Pattern Source Quality: PASS / FAIL
  Verified-by: <audit of referenced existing file>
P6 WIP Staging Discipline: PASS / FAIL
  Verified-by: <subagent prompt template includes git add -p guidance>
```

If any reflex fails, **the plan is BLOCKED** until the spec/plan author updates
it. Do not start subagent dispatch until all 6 are PASS.

---

## BUILD MODE

### Step 1: Pre-Flight (BEFORE writing code)

Runs before the first line is written. Prevents bugs instead of catching them.

**1a. Scope** — What tables, functions, files will this change touch?

**1b. Schema Check** — If the change touches DB, run a single consolidated
introspection query. Adapt the path/credentials to your project's setup
(see CLAUDE.md):

```bash
# Example for MAMP MySQL — adapt to your stack
${MYSQL_BIN} -u ${USER} -p${PASS} -h ${HOST} -P ${PORT} ${DB} -e "
  SELECT c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.COLUMN_KEY, c.IS_NULLABLE,
         s.INDEX_NAME,
         k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME
  FROM information_schema.COLUMNS c
  LEFT JOIN information_schema.STATISTICS s
    ON c.TABLE_SCHEMA = s.TABLE_SCHEMA AND c.TABLE_NAME = s.TABLE_NAME AND c.COLUMN_NAME = s.COLUMN_NAME
  LEFT JOIN information_schema.KEY_COLUMN_USAGE k
    ON c.TABLE_SCHEMA = k.TABLE_SCHEMA AND c.TABLE_NAME = k.TABLE_NAME AND c.COLUMN_NAME = k.COLUMN_NAME
    AND k.REFERENCED_TABLE_NAME IS NOT NULL
  WHERE c.TABLE_SCHEMA = '${DB}'
  ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;
"
```

One query. All columns, indexes, foreign keys at once.
Note: Columns with multiple indexes or FKs appear as duplicate rows — expected and informative.

**1c. Existing Code Scan** — Before writing new logic, grep for existing utilities that already solve the problem. Don't reinvent.

**1d. Dependency Impact Analysis** — This is the most critical pre-flight step.

For EVERY function, method, class, or variable you are about to change:

**Step 1 — Find all consumers.** Grep the name across the entire codebase, not just the file you're working in.
```bash
grep -r "functionName\|ClassName\|methodName" --include="*.php" --include="*.js" --include="*.ts" --include="*.vue" --include="*.blade.php" -l
```

**Step 2 — Read each consumer.** For each file found, read the actual call site. Document:
- What **parameters** does this caller pass?
- What **return value** does it expect (type, structure, null possibility)?
- Does it depend on **side effects** (session, global state, DB writes)?
- What **page/view/form** does this caller belong to?

**Step 3 — Build the impact map** (silent, no output yet):
```
FUNCTION: saveUser()
├── used in: RegisterController.php → passes (name, email, password) → expects User object back
├── used in: ProfileController.php → passes (name, email) → expects User object back
├── used in: AdminUserEdit.php → passes (name, email, role) → expects User object back
└── used in: ApiUserController.php → passes (name, email, password, team_id) → expects JSON
```

**Step 4 — Identify what breaks.** Check your planned change against EVERY consumer BEFORE writing a line:
- Changing parameters? → Which callers pass different arguments?
- Changing return type/structure? → Which callers expect the old format?
- Removing a side effect? → Which callers depend on it?
- Adding a required parameter? → Every existing caller breaks.

**If any consumer would break: plan the fix for ALL consumers as part of your implementation. Not after. Before.**

**Output:** Silent. No report. But you now know every place that will break and have planned fixes for all of them.

### Step 2: Write Code

Implement the change AND fix all affected consumers in the same step. Never change a function without updating every caller.

### Step 2b: Post-Change Dependency Verification

After writing code, re-run the consumer grep from Step 1d. For each consumer:
- Open the file, read the call site
- Confirm it works with the new function signature/behavior
- If you find a consumer you missed → fix it now

### Step 3: Audit (AFTER writing code) — ALWAYS. NO EXCEPTIONS.

> **VERIFICATION-NOT-ASSERTION RULE (v4 — born from real bugs that slipped through)**
>
> Audit checks must be **VERIFIED** by command output, not **ASSERTED** by reading code.
> "I read the controller and the keys match the Vue page" is NOT an audit. The audit is:
> dump the actual serialized response (curl, tinker, or Playwright) and prove the values exist.
>
> Three reflexes that the v4 audit drills into:
>
> **A) JSON Inspection over Code Reading**
> Cross-Layer audits do not stop at "producer returns key X, consumer reads key X". Computed
> fields, hidden attributes, omitted serializer opt-ins, and conditional props mean the
> structural match can pass while the actual payload has `key: undefined`. Always dump the
> real serialized response the consumer will receive (HTTP fetch, REPL, or a browser
> assertion that no rendered link contains `undefined`) and confirm every consumed key is
> non-null on the bug-triggering code path.
>
> **B) Hunt-and-Replace Verification**
> When fixing a known pattern (e.g. wrap a hardcoded `/path/` in a helper), DO NOT stop at the
> first occurrence you found. Grep the entire codebase for the same pattern and verify each match
> is either fixed OR has a justified reason to be exempted.
>
> ```bash
> # After one point-fix, grep the WHOLE pattern across the tree, exclude the fixed form:
> grep -rn '<unfixed-pattern>' <source-dirs> | grep -v '<fixed-form>' | grep -v 'codeguardian-ok'
> # Result MUST be empty before claiming the fix is done.
> ```
>
> The same logic applies to any "this kind of mistake" elsewhere in the tree.
> Fix-propagation is the most common audit failure mode — track it explicitly.
>
> **C) Layout-Link → Route Existence Check**
> Every internal link in a layout/nav/shared component must resolve to a registered route.
> Structural-match audits miss this: a handler returning the right keys says nothing about
> whether the URL the nav links TO is even registered (wrong verb, typo, moved, never added).
>
> **Verification (command output, not code reading):**
> 1. Extract every internal href from nav/layout components into a list.
> 2. List every GET route the router registers.
> 3. Diff — any href not in the route list is a guaranteed 404 on click.
>
> If the project has a link-click smoke test (headless browser walks every nav), run it
> BEFORE claiming the audit passes; it must report 0 errors. If no such test exists, the
> diff step above is mandatory — do not substitute "I read the routes file".

**3a. Triage — Determine Audit Intensity**

```bash
git diff --name-only HEAD
```

| Change Size | DB Touched? | Intensity |
|-------------|-------------|-----------|
| < 20 lines  | No          | LIGHT — all layers spot-check, logic + redundancy full depth |
| < 20 lines  | Yes         | FOCUSED — all layers spot-check, + DB integrity full depth |
| 20+ lines   | No          | STANDARD — all layers full depth except DB (spot-check) |
| 20+ lines   | Yes         | FULL — all 5 layers full depth |

**Spot-check** = scan for obvious violations (10 seconds). **Full depth** = exhaustive analysis.
Even a 1-line change gets all 5 layers as spot-check. There is no "skip".

**3b. Read** — All changed files completely. Plus surrounding context (calling functions, called functions). No output yet.

**3c. Audit Log History** — Read `.audit-log.md` if it exists. Note recurring patterns. If a category has fired recently in this codebase, escalate it from spot-check to full depth regardless of triage.

**3d. Analyze** — All layers, every time. Intensity per triage:

**DB Integrity** — Fields match live schema? FKs correct? Missing indexes on queried columns? N+1 patterns? ORM attributes match real columns? Money/currency stored as integer minor units (cents) or DECIMAL(p,s), NEVER FLOAT/DOUBLE — float rounding silently corrupts totals across aggregation, and `a*b` in float arithmetic is not associative. **Counter/quota columns** capacity-checked against realistic peak value — signed `INT` tops at 2^31−1 ≈ 2.1B and under non-strict sql_mode MySQL silently clamps on overflow (warning only, no error); any counter approaching that range needs `BIGINT` / `BIGINT UNSIGNED`, verified by `SELECT DATA_TYPE, COLUMN_TYPE FROM information_schema.COLUMNS WHERE ...` AND an overflow-reproduction query showing the clamp.

**Logic** — Dead code? Unused variables? Unhandled edge cases (null, 0, empty string, empty array)? Missing returns in conditional paths? Off-by-one?

**Efficiency** — Loops replaceable by single query? Sequential awaits that could be parallel? SELECT in loop instead of JOIN? Missing pagination on large sets?

**Redundancy** — Duplicated logic? Utility already exists in codebase? Copy-paste that should be abstracted?

**Security** — Raw user input in queries (SQL injection)? Sensitive fields (password, token, secret) in responses? Missing auth checks? Mass assignment without whitelist? Missing rate limiting on auth endpoints? **Rate-limit key scope** — for every throttle/counter, name the bucket key and ask: is it the stable identity being protected (user_id, verified email after normalization, API-key ID), or something the caller can rotate at will (session_id, raw submitted email, anonymous cookie, request ID, `X-Forwarded-For`)? An attacker-rotatable key is not a rate limit — it's a speed bump they reset between attempts. For pre-auth flows (OTP verify, password reset, signup confirm) key by the PENDING identity, not the session carrying it. IDOR vulnerabilities?

**3e. Report**

The report MUST distinguish between **VERIFIED** checks (proven by command output) and **READ** checks (only inspected via reading code). Read-only checks have ~50% false-positive rate based on real bug data — verified checks are the only ones you can trust.

If clean:
```
✅ [X files | Y lines] clean
   Verified by: <list of commands run, e.g. "link-click-test 39/39, payload dump 4 keys non-null">
```

If findings exist, show ONLY sections with issues:
```
## Audit: [files]

🔴 [category]: [problem] → [fix]
   Verified-by: <command that proved the bug exists>
🟡 [category]: [problem] → [recommendation]
   Verified-by: <command output>

[X] critical | [Y] warnings → [APPROVED/NEEDS FIX/BLOCKED]
```

**Forbidden audit phrases** (these are ASSERTIONS, not VERIFICATIONS):
- "I read the controller and the keys match" — read code does not prove serialized values
- "The route ordering looks correct" — must run `route:list` and visually verify last-route
- "The Vue component should handle this" — must trace through actual rendered HTML
- "This is the same pattern as before" — must grep for ALL occurrences of the pattern

**Required audit phrases** for each verified check:
- "Ran X, got Y" with copy-paste of the actual output snippet
- "Grepped for Z, found 0 unfixed instances"
- "link-click-test 39/39 pass after change"

Verdict: APPROVED (0 critical, ≤2 warnings, all critical-path checks VERIFIED) | NEEDS FIX (0 critical, 3+ warnings) | BLOCKED (any critical OR any unverified critical-path check)

**3f. Audit Log** — Append to `.audit-log.md`:
```
## [DATE] [files] — [VERDICT]
C:[X] W:[Y] | [one-line findings summary]
PATTERN: [if recurring issue detected, name it]
```

**3g. If BLOCKED** — Fix criticals → re-audit only affected layers → confirm "Fix verified" or "Fix incomplete: [reason]"

---

## DEBUG MODE

### Phase 1: COLLECT (no fix, no suggestion, no output)

**1a.** What exactly happens? (exact error, stack trace, expected vs actual)

**1b.** What changed recently?
```bash
git log --oneline -5 && git diff --name-only HEAD~3
```

**1c.** Read the ENTIRE affected function + 2 levels of callers and callees. Not just the error line.

**1d. Cross-Page Dependency Trace** — The bug might not be WHERE the error shows. A change in Page A can break Page B.

Run the consumer-grep + impact-map workflow from **BUILD Step 1d** (Dependency Impact Analysis). Same grep, same "read every call site" discipline. Then add two DEBUG-specific questions per consumer:

- Was **this consumer** recently changed? (`git log --oneline -10 -- <consumer>`)
- Was the **function itself** recently changed? (`git log --oneline -10 -- <file-with-function>`)

If the function was recently changed and a consumer was not: the bug is likely a DEPENDENCY BREAK — someone changed the function and didn't update all consumers. This is the single most common root cause when "Page B broke after I worked on Page A".

**STOP. No fix proposal until Phase 2 is complete.**

### Phase 2: ROOT CAUSE (not symptom)

The error you SEE is often not the error that EXISTS. A 500 error on the profile page might be caused by a function change made while working on the registration page.

Answer in order — you may not skip to solutions until question 4 is answered:

1. **WHAT** exactly happens? (symptom)
2. **WHERE** in code? (file + line — but also: is the REAL cause in a different file?)
3. **WHEN** introduced? (last working state — use `git log` on the broken function)
4. **WHY** does it happen? (root cause — often: function signature/behavior changed, consumer not updated)
5. **WHY** wasn't it caught? (missing test, no dependency check, other pages not tested after change)

Then list 3 possible causes ranked by probability. **Always include "dependency break from recent change in shared function" as a hypothesis when a function is used across multiple pages.** Verify each by reading code or running a targeted test before confirming or ruling out.

### Phase 3: TWO PATHS (mandatory)

Never propose just one fix.

**Path A — Minimal:** What changes, effort, risk, does it fix root cause or just symptom?
**Path B — Structural:** What changes, effort, risk, does it fix root cause?
**Decision:** Which path and why, based on: root cause resolution, side-effect risk, long-term maintainability, dependency count affected.

### Phase 4: VALIDATE BEFORE TOUCHING CODE

**4a. Call-chain trace:** Walk through the fix mentally. Where is it called? Return values? Branches? Edge cases?
If the trace reveals the fix won't work → back to Phase 3.

**4b. Full consumer verification** — Take the dependency list from Phase 1d. For EACH consumer:
- Will this fix change the function's signature, return value, or behavior?
- If yes: does this consumer handle the new behavior correctly?
- If no: does it need to be updated too?

```
FIX: saveUser() now requires $role parameter
├── RegisterController.php  → passes $role? → ❌ NO → must add $role or make param optional
├── ProfileController.php   → passes $role? → ❌ NO → must add $role or make param optional
├── AdminUserEdit.php       → passes $role? → ✅ YES → ok
└── ApiUserController.php   → passes $role? → ❌ NO → must add $role or make param optional
→ Fix plan must include ALL 3 missing consumers, not just the one that errored
```

**Rule: A fix that repairs one page but breaks three others is not a fix. Every consumer must be verified before implementation.**

**4c. Gate:**
```
Call-chain: ✅/❌ | ALL consumers verified: ✅/❌ ([X] of [Y]) | Edge cases: ✅/❌ → Ready: ✅/❌
```
If any consumer is not verified → NOT ready. Go back and check.

### Phase 5: IMPLEMENT + VERIFY

1. Fix + adjust all affected dependencies
2. Test that reproduces the bug (now green)
3. Existing tests still green
4. Confirm: original bug gone, edge cases handled, dependencies intact
5. Run the BUILD MODE Audit (3a-3g) on the fix diff — a fix is a code change and gets the same 7-point audit as any other change, no exceptions

### Escalation

Failed once → Document why. New root-cause analysis from Phase 1. Mark failed hypothesis as disproven.
Failed twice → STOP. Report both attempts + analysis to user. Do not blindly continue.

---

## Cross-Layer Checks (learned from real bugs)

These catch bugs that live BETWEEN components — not inside any single file, but in the handshake between them.

### Cross-Layer Data Contracts
When one layer produces data and another layer consumes it, verify both sides agree.

**Producer → Consumer mismatches** (all silent — no error, just missing data):
- Key rename mid-pipeline: producer emits `status`, consumer reads `success` → null
- Computed/derived property not opted into the serializer (accessor, virtual attribute, getter, lazy field) → absent from payload, consumer reads undefined
- Hardcoded path under a subdirectory / reverse-proxy install bypasses the base-URL helper → resolves to wrong base, 404 only in the non-root deployment

**How to check (READING is not enough):**
1. Trace the data from where it's CREATED to where it's READ.
2. **Dump the actual serialized payload** — hit the endpoint, parse the response, prove every consumed key is non-null on the bug path.
3. Verify key names AND shape (array vs object, nested depth, null possibility) match at every hop.

This is the #1 source of silent bugs. Structural-match audits ("producer returns X, consumer reads X") pass while the runtime payload is `{X: undefined}` — dump, don't read.

### Return Type Completeness
When a function has conditional branches (if/else, early returns, error paths), verify ALL branches return a compatible type.

Common traps:
- Main path returns ResponseObject, error path returns redirect() → different types
- Happy path returns {data: [...]}, edge case returns null → consumer crashes
- Normal flow returns rendered page, self-redirect returns different response type

### Interface Boundary Verification
When new code calls existing services/functions, read the ACTUAL signature — verify parameter count, types, order, return type, and optional defaults all match what you assume.

### ORM/Model Verification
When code references DB fields, verify against BOTH the Model AND the live DB:
- Are mass-assigned fields in the whitelist ($fillable, attr_accessible, etc.)?
- Are type casts correct? Wrong cast = wrong type at runtime.
- Do relationship definitions match the actual FK columns in the DB?
- Is the table name explicitly set if the model name doesn't follow convention?

### Single-Use Resource Consumption (token / coupon / one-time action replay)
Whenever a DB row represents a single-use resource (password-reset token, email-verify token, magic-login code, one-time coupon, invite link, idempotency key, consumed webhook), the consumption MUST be enforced by an **atomic conditional UPDATE** whose `rowCount()` is checked BEFORE any follow-on side effect:

```sql
UPDATE t SET consumed_at = NOW(6)
 WHERE id = :id AND consumed_at IS NULL AND expires_at > NOW(6)
```
Then in code: only if `$stmt->rowCount() === 1` proceed to change the password / grant access / apply the coupon. Otherwise reject as `already_used`.

**Anti-pattern**: `SELECT consumed_at IS NULL → BEGIN → UPDATE users ... → UPDATE resets SET consumed_at = NOW() WHERE id = :id → COMMIT`. Two concurrent replays both pass the SELECT gate, both enter their own transaction, both UPDATE the user row, second silently overwrites first. Wrapping in a transaction does NOT fix it — transactions serialize writes to the same row but do NOT turn a prior read into a lock. `SELECT ... FOR UPDATE` works ONLY if the consumed-flag is re-checked AFTER the lock; the conditional-UPDATE + rowCount gate is simpler and less error-prone.

**Audit reflex**: for every diff that touches a row with `consumed_at` / `used_at` / `redeemed_at` / `verified_at` / `processed_at` / `is_consumed`, grep the diff for `SELECT` followed by `UPDATE` on the same row — if the UPDATE lacks `WHERE ... AND <flag> IS NULL` OR the code doesn't check `rowCount() === 1` before the side effect, FAIL. Verified-by: a concurrent-replay script (`seq 1 20 | xargs -P20 -I{} curl ...`) should show exactly 1 success and 19 `already_used`.

**Timestamp sub-reflex**: expiry / window checks MUST be evaluated in SQL (`WHERE expires_at > NOW(6)`) or via typed `DateTimeImmutable` comparison. Never compare two datetime strings lexicographically — MySQL may return `DATETIME(6)` with or without fractional seconds depending on how the row was inserted, and lex-compare of 19-char vs 26-char strings silently reorders around second boundaries.

### Auth Enforcement Parity Across Entry Points
When a service/domain method is invoked from MORE THAN ONE entry point — web route, CLI command, queue/background worker, scheduled task, admin panel, internal API, webhook handler — the authorization gate MUST be equivalent at every entry point, OR the gate must live INSIDE the service and not at the edge.

Auth-at-the-edge (middleware/policy on the route) is safe ONLY while the service has exactly one caller. The moment a second entry point appears, the route-level gate is bypassed by design — middleware does not run for background workers or CLI invocations.

**Audit reflex** — for every service method touched in the diff, run the consumer grep from BUILD Step 1d and for EACH caller answer out loud:

1. **What auth check guards this entry point?** Name the middleware / policy / gate / inline check.
2. **Is the check equivalent to every OTHER entry point's check?** A route gated by a policy (checks verified / not-banned / has-quota) is NOT equivalent to an admin route checking only an admin flag, and NOT equivalent to a CLI or queue caller with no gate.
3. **If the gates differ, does the difference match intent?** An admin override that explicitly bypasses one invariant is acceptable IF documented AND the non-admin paths still enforce the others.

**The fix is almost always the same**: push the authorization check INTO the service (it throws on failure regardless of caller). Edge-auth then becomes defense-in-depth, not the only line.

**Silent failure**: the web UI looks locked down in QA, the policy test suite is green, and a banned user still triggers the action via a weekly CLI job or a queue worker — because neither path touches middleware.

### Session Lifecycle at Auth Boundaries (fixation, privilege upgrade, cookie drift)
Authentication is an IDENTITY TRANSITION: the caller arrives as anonymous (or some other identity) and leaves as an authenticated principal. Every identity transition MUST rotate the session identifier AND re-assert the session cookie attributes — or the pre-transition session ID remains valid post-transition and whoever planted it is now logged in as the victim.

Distinct from Auth Enforcement Parity (who-can-call a service across entry points): this reflex covers the identity-rebinding STEP itself.

**Three failure modes:**

1. **Session fixation** — login succeeds, principal is written into the existing session (`$_SESSION['user_id'] = ...`) WITHOUT first rotating the session ID. If the runtime accepts attacker-supplied session IDs (PHP with `session.use_strict_mode = 0`, hand-rolled cookie stores, any session system that mints on first touch without a server-side allowlist), an attacker who planted a session cookie on the victim now holds a valid authenticated session. Fix: rotate the session ID immediately after credentials verify and BEFORE writing the principal (e.g. PHP `session_regenerate_id(true)`).
2. **Privilege upgrade without rotation** — same bug class at a different boundary: a logged-in user becomes admin / enters sudo / completes 2FA step-up. If the session ID is not rotated at the upgrade, a pre-upgrade token captured at a lower trust level now grants the higher trust level. Rotate on every trust-level change, not just at initial login.
3. **Cookie attribute drift** — setting cookie params (remember-me lifetime, `Secure`, `HttpOnly`, `SameSite`, `Domain`) AFTER the session has already started silently does NOT apply to the already-issued cookie for the current request. Correct order: set params → rotate session ID → write principal → send response.

**Audit reflex** — for every assignment into session state that follows a successful credential / MFA / role check in the diff:
1. **Is the session ID rotated between credential-verify and principal-write?** Name the rotation call and its `delete_old_session` argument. Missing → BLOCKED.
2. **Does the runtime reject unknown session IDs?** (`session.use_strict_mode` or equivalent.) If off, rotation is the ONLY defence — no excuses.
3. **If cookie params changed, did the change happen BEFORE the rotation call?** Post-rotation param changes apply only to the NEXT session.
4. **Is the OLD session server-side storage actually destroyed?** `session_regenerate_id(false)` leaves the old session file readable by whoever has the old ID — pass `true`.

**Verification (command output):**
```bash
# 1. Pre-login session cookie:
curl -c jar -b jar -s -o /dev/null -D - https://app/login | grep -i '^set-cookie'
# 2. POST credentials re-using the same cookie jar:
curl -c jar -b jar -s -o /dev/null -D - -d 'email=a&password=b' https://app/login | grep -i '^set-cookie'
# 3. The Set-Cookie session-ID value from step 2 MUST differ from step 1.
#    Same value → no rotation → session fixation present.
```

### HTTP Response Cacheability for Authenticated Pages (shared-proxy cross-user disclosure)
Any HTTP response whose body depends on caller identity (session cookie, bearer token, API key) is a **per-user** response. Most runtimes emit NO `Cache-Control` by default, and RFC 7234 lets shared caches (reverse proxies, CDNs, corporate forward-proxies, browser bfcache) apply a heuristic freshness lifetime to any 200 OK lacking explicit directives. The cache key is typically `(method, host, path)` — the session cookie is NOT part of the key unless `Vary: Cookie` is present. Result: user A's account statement is stored under `/statement.php` and served verbatim to user B hitting the same URL within the heuristic TTL.

Distinct from "sensitive fields in responses" (WHAT is in the body): this reflex covers WHO ELSE can receive the same body via cache replay.

**Required headers on every authenticated response** (sent BEFORE any body output):
```
Cache-Control: private, no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
Vary: Cookie
```
`private` alone is insufficient — a misconfigured proxy that ignores `private` still honors `no-store`. `Vary: Cookie` is the belt to `no-store`'s braces.

**Audit reflex** — for every route/page/endpoint in the diff that reads session state or returns user-scoped data:
1. **What `Cache-Control` does the response emit?** Default / absent → BLOCKED.
2. **Is `Vary: Cookie` (or `Vary: Authorization` for token auth) set?** Absent → BLOCKED.
3. **Auth-failure redirects** (302s) are cacheable too — same headers on the redirect response.
4. **Browser bfcache**: on logout, does the sensitive page still render from bfcache? `no-store` is the only directive that reliably evicts bfcache.

**Verification (command output):**
```bash
curl -b jar -s -o /dev/null -D - https://app/statement | grep -iE '^(cache-control|pragma|expires|vary):'
# Must include: Cache-Control: private, no-store... AND Vary: Cookie. Absent → FAIL.
```

### Error-Path Log Content Hygiene (PII / secrets in logs)
Logs are a secondary data store — whatever lands in them inherits the weakest access control on ANY surface the log reaches (file permissions, backups, log-aggregator retention, SaaS vendor access, support screen-shares). An error-path logger serializing opaque blobs is a secret-leak with a timer. Distinct from P3 (secrets in URLs) and from "sensitive fields in responses" (body content): this covers the LOG sink.

**Forbidden log payloads** — never serialize wholesale into log lines:

| Blob                              | Why it leaks                                                      |
|-----------------------------------|-------------------------------------------------------------------|
| `$_REQUEST` / `$_POST` / `$_GET`  | Arbitrary caller fields: passwords, card numbers, reset tokens    |
| `$_SERVER` / `getallheaders()`    | `Authorization`, `Cookie`, `X-Api-Key`, any custom auth header    |
| `$_ENV` / `getenv()` dump         | Every boot-time secret: DB password, webhook signing key, etc.    |
| Full row from `SELECT *`          | `password_hash`, `api_token_hash`, MFA secret, PII columns        |
| Raw request body                  | On PII/PAN/credential endpoints, the body IS the secret           |
| Stack trace with local variables  | Many runtimes bind SQL params and locals in the trace             |

**Audit reflex** — for every log/write call in the diff (error handler, `catch` block, `error_log`, `file_put_contents` to a log path, SIEM hook), answer three questions:

1. **Allowlist or blob?** Payload must be an explicit allowlist of named, non-secret fields (`['user_id' => $id, 'event_id' => $eventId, 'error_class' => get_class($e)]`), never an opaque blob. Blob → BLOCKED.
2. **Can an UNAUTHENTICATED caller reach this log line?** Pre-auth error paths (bad signature, bad CSRF, bad nonce) let an attacker deliberately trip the path with chosen content — log injection as a reflection primitive.
3. **Does the row fetched for the log contain columns the logger doesn't need?** `SELECT *` feeding an exception path = latent password_hash leak. Project columns at the query.

Also: append-only log writes without an exclusive lock interleave under concurrency and corrupt downstream parsers — use a logger library that locks per write.

### HTTP Header-Value Injection (CRLF + quoted-string breakout)
Any user-controlled string flowing into a response header value is a header-injection sink — even when the runtime claims to reject CRLF. Three ways past the default defence:

1. **Quoted-string breakout**: `Content-Disposition`, `Link`, `WWW-Authenticate` use quoted sub-parameters (`filename="..."`, `rel="..."`). A raw `"` closes the string and lets the attacker inject extra params (`; filename*=UTF-8''evil.html`) — the CRLF filter does NOT filter `"`.
2. **Bare `\r` / `\x00`**: some runtimes and FastCGI bridges block the `\r\n` pair but pass a lone `\r` or NUL byte; downstream proxies may still split on them.
3. **Non-ASCII in ASCII-only fields**: RFC 7230 requires header values to be VCHAR+SP+HTAB. Non-ASCII in `Content-Disposition filename=` without the RFC 5987 `filename*=UTF-8''` encoded form is silently mangled by proxies → cross-browser filename inconsistency that can mask extension-sniffing attacks.

Distinct from XSS (HTML body escaping) and P3 (secrets in URLs): this covers data flowing into `header()` / `setcookie()` / `Location:` / template header pushes.

**Audit reflex** — for every `header(` / `setcookie(` / equivalent in the diff, trace the value to its source and answer:
1. **Is any part user-controlled?** DB columns count if ANY user endpoint ever writes them (grep the write path).
2. **Strictly filtered to the header's grammar?** For `filename=`: ASCII printable minus `"` and `\`, non-ASCII via `filename*=UTF-8''` percent-encoding. For `Location:`: a URL allowlist, not just a CRLF strip. For `Set-Cookie` value: token grammar only.
3. **Validation at WRITE time or READ time?** Write-time reject (at rename/upload) is correct; read-time filtering is defence-in-depth. "We wrote it ourselves" is wrong if ANY path lets a user shape the column.

Verify: `curl -D -` on the endpoint after injecting a quote-breakout payload at write time; response MUST contain exactly one `Content-Disposition` parameter with no raw `"`, `\r`, `\n`, `\x00`, or non-ASCII outside `filename*=`.

### HTTP Verb Safety for State-Changing Requests (CSRF-on-GET)
RFC 7231 marks GET/HEAD as **safe** and every mainstream CSRF middleware exempts them from token checks. A `GET` route that mutates state (INSERT/UPDATE/DELETE, mail, counter, external POST) is therefore a cross-site write primitive: `<img src="https://app/action">` fires it with the victim's cookie (zero-click, no JS). Link prefetchers, email-link scanners, and IM link previews also pre-fetch every URL in reach — tripping state-changing GETs before the user sees the message. Distinct from Session Lifecycle, Open Redirect, Header-Value Injection, and Cacheability: this covers the VERB vs SIDE-EFFECT mismatch.

**Audit reflex** — for every route declaration in the diff:
1. **Does the handler mutate persistent state or call a side-effecting external API?** Grep the handler body for `UPDATE` / `INSERT` / `DELETE` / `save` / `update` / `delete` / mail send / queue dispatch / external POST. Any match → the route MUST be POST/PUT/PATCH/DELETE, never GET or HEAD.
2. **Is the verb actually enforced?** A route reachable via a "match any method" / "match get+post" form inherits the GET exemption. Enumerate the registered verbs with the router's introspection command — do NOT read the route file.

**Not a valid defence**: requiring authentication. The victim IS authenticated — that's the whole point of CSRF. Ownership checks also do NOT mitigate: the attacker targets the victim's own row via the victim's own session.

**Valid remediations**: change the verb to POST and require a CSRF token; for email "one-click unsubscribe" RFC 8058 supports `List-Unsubscribe-Post` directly. OR bind the action to a signed, single-use, time-limited token in the URL itself (HMAC of `user_id + action + expiry`, consumed via the Single-Use Resource Consumption reflex; note this trades CSRF risk for URL-leakage risk — P3 applies).

### Frontend Reactivity Traps
These cause bugs that no linter catches:
- **Destructured reactive state**: Extracting values from reactive objects into plain variables loses reactivity. Always use computed/derived state.
- **Non-reactive async data**: Data fetched via polling or async calls that updates UI must be stored in reactive containers.
- **Stale closures**: Event handlers or watchers that capture a value at creation time instead of reading current state.

### N+1 Query Detection
Watch for these patterns in any ORM OR external-call loop:
- Accessing relationships inside a loop without prior eager loading
- Counting related records in a loop instead of using aggregation
- Loading full objects when only a count or existence check is needed
- External HTTP/RPC call inside a row loop — require a bulk endpoint, a parallel-request primitive (concurrent fan-out), or justify per-row cost against the row count

### Composite Index Column-Order (leading-column rule)
"Column X appears in an index" is NOT the same as "a query on X can use that index". A composite index `(A, B, C)` is a B-tree keyed on A first, then B within each A, then C within each (A,B). The engine can only seek the tree for predicates that include the LEADING column — `WHERE A = ?`, `WHERE A = ? AND B = ?`, `WHERE A = ? AND B > ?`. A bare `WHERE B = ?` or `WHERE C = ?` cannot seek and degrades to a full scan. (Skip-scan exists in some engines but is narrow and planner-dependent — never assume it.)

Distinct from "missing index": the index exists, the queried column appears in it, a schema-reading audit ticks the box, and the query still full-scans at 10M+ rows.

**Audit reflex** — for every `WHERE col = ?` / `WHERE col IN (...)` / `ORDER BY col` / `GROUP BY col` in the diff, do NOT stop at "col is listed in some index". Answer two questions out loud:

1. **Is `col` the LEADING key_part of an index, OR does the same query constrain every earlier key_part to an equality?** If neither, no index is usable — name the leading-matching index, or add one.
2. **Range-before-equality trap.** An index `(created_at, user_id)` used for `WHERE user_id = ? AND created_at > ?` can only seek the range on `created_at`; the later equality becomes a filter, not a seek. Put equality columns FIRST and range columns LAST.

**Verification (command output, not schema reading):**
```sql
EXPLAIN SELECT COUNT(*) FROM <t> WHERE <col> = ?;
-- `key`  column: must name an index whose FIRST key_part is <col> (or earlier key_parts all equality-constrained by this query).
-- `type` column: must be ref / eq_ref / range / const — NOT `ALL` and NOT `index`.
-- `rows` column: bounded (small multiple of result set), NOT ≈ table row count.
```

**Failure signature**: `key: idx_user_status_created`, `type: ALL`, `rows: 17834221` on `WHERE status = ?` — the planner considered the composite and declined it because `user_id` is leading and unconstrained. Schema reading would have said "status is in an index"; EXPLAIN proves it isn't usable.

### Implicit Coercion Defeating Indexes (type & collation mismatch)
"The column is indexed" is NOT the same as "a query comparing this column can use the index". If the planner must implicitly convert EITHER side of a comparison to match the OTHER side's type or collation, the index on the converted side becomes unusable — the engine wraps it in an implicit `CONVERT(col USING ...)` or `CAST(col AS ...)` and that expression is not sargable. Schema-reading audits tick the box ("`idx_x` exists"); `EXPLAIN` shows `type: ALL` at production row counts.

Distinct from column-order: here the index IS the leading key_part and there's no range-before-equality problem — the coercion alone kills the seek.

**Three common sources:**
1. **Type mismatch**: `WHERE bigint_col = '42'` (string literal against BIGINT) or `WHERE varchar_col = 42` (int literal against VARCHAR). Always bind parameters with the correct type; never interpolate a numeric ID as a string.
2. **Collation mismatch on JOIN**: two tables with different column collations (common after a partial utf8mb4 migration — one table still `utf8_general_ci`). `JOIN ON a.col = b.col` forces a per-row `CONVERT(... USING ...)` on one side → full scan even though both columns are individually indexed.
3. **Charset mismatch on literal/connection**: connection charset ≠ column charset forces conversion on every comparison.

**Audit reflex** — for every `WHERE col = ?`, `JOIN ON a.x = b.y`, or `IN (...)` in the diff on a string column:
1. **Does the bound/literal type EXACTLY match the column type?**
2. **For JOINs on string columns: do BOTH sides share charset AND collation?** Check `information_schema.COLUMNS.CHARACTER_SET_NAME` and `COLLATION_NAME` for both columns — column-level settings override the table default.

**Verification (command output):**
```sql
EXPLAIN <query>;
-- key / type / rows must indicate a real seek, AND Extra must NOT mention CONVERT/CAST wrapping an indexed column.

SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE() AND (TABLE_NAME, COLUMN_NAME) IN (('t1','col'), ('t2','col'));
-- Both rows MUST match on CHARACTER_SET_NAME AND COLLATION_NAME.
```

### Client-Connection Charset Drift (READ-path data corruption, not index cost)
Implicit Coercion above covers charset mismatch as an INDEX-usability problem. The same missing DSN parameter also CORRUPTS read-path DATA silently — and looks nothing like the index case, so the index reflex doesn't trip. Every DB driver negotiates a client-side charset for results delivery; if the DSN (`mysql:host=...;dbname=...;charset=utf8mb4`) or equivalent is missing, the server falls back to `character_set_results` from its config — on legacy/distro defaults that's often `latin1`. `utf8mb4` columns are then TRANSCODED on delivery: emoji, CJK, curly quotes, en/em dash become `?` or invalid-UTF-8 byte sequences.

**Three silent failure modes riding one DSN bug:**
1. **`json_encode` returns `false`** (JSON_ERROR_UTF8) on non-UTF-8 bytes; unchecked, `echo json_encode($rows)` emits literal `"false"` at HTTP 200 with no log.
2. **Silent data loss on round-trip** — read transcodes to `?`, write stores `?`, original is gone with no error.
3. **Index lookups by string value miss rows** — `WHERE name = :emoji` binds the transcoded `?` and matches zero rows; looks like "user not found", not a charset bug.

**Audit reflex** — for every DB driver connect in the diff:
1. Is the client charset named explicitly in the DSN or connect options? Absent → BLOCKED. `SET NAMES` via init-command is belt-and-braces, not a substitute (it runs after handshake).
2. Does the named charset match the storage charset of every column the connection reads? Use the `information_schema.COLUMNS` query above — `utf8mb4` columns with a 3-byte client silently degrade supplementary-plane codepoints.
3. Response `Content-Type` carries `charset=utf-8`? A JSON endpoint without it is sniffed wrong by legacy middleboxes; pair the DSN check with the outbound header check.
4. Is the serializer return value checked? `json_encode` returning `false` without a log entry is how `HTTP 200 body="false"` reaches production.

**Verify**: `SHOW SESSION VARIABLES LIKE 'character_set_%'` — all three of `client` / `connection` / `results` must be `utf8mb4`. Then `curl -sD -` the endpoint with a row containing an emoji; body must be valid JSON starting with `[` or `{`, and `Content-Type` must contain `charset=utf-8`.

### Deep-Offset Pagination (LIMIT/OFFSET at depth)
`LIMIT N OFFSET M` is **O(N+M)**, NOT O(N). The engine walks M+N rows through the chosen index, discards the first M, returns the tail. Under a narrowing predicate (`WHERE user_id = ?` → ~10k rows) the cost is invisible. On a large unpartitioned table with no filter it degrades catastrophically — page 1000 of a 50/page feed touches 50,050 index rows; page 100,000 touches 5M. Each slow request also pins a DB connection, so deep-offset is both latency and pool-exhaustion.

**Audit reflex** — for every `LIMIT ? OFFSET ?` in the diff, answer three questions out loud:

1. **What narrows the scan BEFORE the OFFSET?** Name the WHERE predicate and prove an index covers it AND bounds the filtered set to a small multiple of page size. No narrowing WHERE → unbounded.
2. **Is the filtered set itself bounded?** If unbounded (global firehose, audit log, telemetry, append-only table without retention), OFFSET is NOT acceptable — use keyset pagination: `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT N`. Cost stays O(N) regardless of depth.
3. **Is the `page` parameter capped?** `?page=999999999` on a large table forces a walk of the entire index — a one-request DoS. Clamp `page` like you clamp `per_page`.

**Verification** (command output, not code reading):
```sql
EXPLAIN SELECT id FROM <t> WHERE <pred> ORDER BY <col> DESC LIMIT 50 OFFSET 500000;
-- `rows` must NOT be ≈ 500050. If it is, the query is O(offset) and FAILS.
```

**Copy-paste trap**: a safe OFFSET paginator over a narrow predicate is often copy-pasted into a global-firehose variant by dropping the WHERE — identical shape, runtime cost differs by 4+ orders of magnitude. "Follow the existing pagination pattern" is safe ONLY if the new call site keeps the source's narrowing predicate; LIMIT/OFFSET shape alone is never what makes a paginator safe on a large table.

### Cache Invalidation Coverage
Every cached read is a promise that EVERY mutation to the backing data also invalidates the cache entry. A cache without invalidation is a bug with a timer.

**The check (VERIFIED, not asserted):** for every cache key this change introduces or reads, grep EVERY write path to the backing table — request handlers, scheduled tasks, background workers, inline increments, raw SQL, ad-hoc scripts — and prove each one invalidates (or tag-flushes) the same key. Audit reflex: name 0 unguarded mutation paths out loud before the check passes.

Also check the inverse direction: a background process that mutates the DB outside the request cycle must STILL invalidate. Shared cache is global; stale reads do not self-heal.

**Row mutation → list/aggregate cache drift.** Invalidation must reach DERIVED cache entries that EMBED the mutated row without being keyed by it: list pages, feeds, search result pages, leaderboards, `COUNT(*)` rollups, homepage modules, first-page CDN objects. A write to `post:123` that only flushes `cache[post:123]` leaves `cache[posts:list:page1]` holding the stale row 123 for the full TTL — and list endpoints are typically the higher-traffic path, so the stale-read surface is strictly LARGER than the row-keyed one. Same trap for aggregates: updating one `orders` row flushes `cache[order:987]` but not `cache[dashboard:revenue:today]`. Audit reflex: for every cache WRITE in the diff, ask "what OTHER cache keys encode rows from this table?" — grep the cache-get call sites for every key prefix reading the same table and prove each is tag-flushed, versioned (read key includes a generation counter bumped on every write), OR has a TTL short enough to bound the inconsistency. "I flushed the row key" is not enough.

### Concurrency / TOCTOU on Counters and Quotas
Any `check-then-act` pattern on a counter (`uses_left`, `stock`, `seats_remaining`, `credits`) is a race unless the check and the mutation happen in ONE atomic step — a conditional `UPDATE` with affected-row check, a row-level lock inside a transaction (`SELECT ... FOR UPDATE`), or an equivalent CAS primitive. Reading from a cache and then decrementing is ALWAYS wrong: the cache value is already stale relative to concurrent writers.

```sql
-- WRONG: read-then-write leaks a race window
SELECT uses_left FROM promo WHERE id = ?;        -- both concurrent requests see 1
UPDATE promo SET uses_left = 0 WHERE id = ?;      -- both reach here, quota oversubscribed

-- RIGHT: atomic conditional decrement, check affected rows
UPDATE promo SET uses_left = uses_left - 1 WHERE id = ? AND uses_left > 0;
-- PHP then checks PDOStatement::rowCount(); 0 = race lost, reject.
```

Audit reflex: for every counter mutation in the diff, name the atomicity mechanism out loud or reject the change.

**`SELECT ... FOR UPDATE` without a transaction is a no-op.** Under autocommit (PDO MySQL default and most driver defaults), each statement is its own transaction — the row lock acquired by `FOR UPDATE` is released the instant the SELECT finishes, BEFORE the follow-up UPDATE runs. The code READS as locked-then-updated but executes as unlocked. Verification: grep every `FOR UPDATE` in the diff and prove a `BEGIN`/`START TRANSACTION` opens before it AND a `COMMIT` closes after the UPDATE. Missing either → the lock is decorative. Same failure applies to advisory locks (`GET_LOCK`) released at session end when the connection is returned to a pool mid-request.

**The inverse: a transaction without `FOR UPDATE` does NOT lock the rows it reads.** Under InnoDB REPEATABLE READ (default), a bare `SELECT` inside `BEGIN`/`COMMIT` is a *consistent snapshot read* — concurrent writers are invisible. Two callers can both read the same starting value, both compute `new = old - amount` from the same basis, and both UPDATE; the second commit is a lost update and any predicate checked against the snapshot (`if (new < limit) throw`) is also defeated. Distinct from counter TOCTOU above — this is multiple real rows inside an explicit transaction where the reviewer sees `BEGIN/COMMIT` and wrongly reads it as a lock. Fixes: (a) every row later UPDATEd is read with `SELECT ... FOR UPDATE` in the same transaction, OR (b) the entire mutation is one atomic conditional UPDATE whose WHERE re-asserts the business predicate and whose `rowCount()` is checked. Audit reflex: for every `beginTransaction` in the diff, name each row read-then-updated and prove either option. Verification: a two-connection race script must show the second committer's final value reflecting BOTH mutations.

**Lock ordering for multi-row locks.** Once `FOR UPDATE` is added on N rows, the next latent bug is deadlock from inconsistent acquisition order: `transfer(A,B)` locks A→B, `transfer(B,A)` locks B→A, they meet in the middle. Acquire locks in a globally consistent order — sort IDs ascending and `SELECT ... WHERE id IN (?, ?) ORDER BY id FOR UPDATE`, or issue each `FOR UPDATE` in sorted order. Verify by running the two-connection race with argument order swapped and confirming no `ERROR 1213 Deadlock found`.

### Queue/Task Idempotency (at-least-once by contract)
Virtually every queue/task runner is at-least-once by contract: a worker crash between side-effect and ack re-runs the SAME payload. Every job that sends mail, charges money, increments a counter, writes a file, or calls an external API needs a dedup key checked-and-set in one transaction (e.g. a `UNIQUE` index on `(aggregate_id, operation_id)`) OR must be provably pure. Unguarded side-effects inside a retry-eligible handler = duplicate side-effect on every retry. Audit reflex: for every enqueued job type in the diff, name the idempotency key or justify purity.

### Multi-Step Side-Effect Atomicity (saga / compensation)
A single handler that performs 2+ side-effects — even without concurrency or retries — is a saga. If any step after the first throws and nothing undoes the earlier steps, the system is left in a partial state no error log reconciles: customer charged with no order row, file written with no DB record, email referencing a row that doesn't exist.

Distinct from Queue Idempotency (same payload across retries) and TOCTOU (concurrent races). This is ONE request, sequential steps, partial-commit window between them.

**Audit reflex** — for every handler in the diff with 2+ side-effects (local write, external API, payment, file write, email, queue dispatch, cache mutation), enumerate steps IN ORDER and for each transition answer out loud: **"If step N+1 throws, what automatically undoes step N?"** If the answer is "nothing" for any transition, the handler is broken.

Three acceptable remediations:
1. **Single atomic boundary** — all steps inside ONE DB transaction, zero external side-effects inside. Only works when every step is a local DB write.
2. **External-last ordering** — reorder so the irreversible external step (payment, email, third-party POST) runs AFTER all local writes commit. A throw on the external step still fails the request, but local state stays consistent and retriable. Usually the minimal fix.
3. **Explicit compensation** — wrap each external step in a try/catch whose catch calls the documented undo (refund, reversal, delete). The compensation itself must be idempotent and logged.

**Anti-pattern**: `local decrement → external charge → INSERT order` — if the INSERT throws (unique-index conflict, lock timeout, disk full), the customer is charged with no order row and no refund. Fix: INSERT with `status='pending'` FIRST, then charge, then UPDATE to `status='paid'`. The confirmation email moves AFTER commit.

Verification: for each handler in the diff, mark each step as L (local) or X (external), point at the L step that must come LAST. If the last step is X and irreversible, the audit is BLOCKED until compensation or reordering is added.

### Error-Path Resource Cleanup (finally-block discipline)
Distinct from Multi-Step Side-Effect Atomicity (which covers UNDO ordering between 2+ side-effects). This reflex covers SINGLE resources whose lifetime must span every exit path — happy return, early return, AND every throw reachable from the acquire. A release call that sits on the happy path AFTER the work leaks the resource on every non-happy exit.

PDO's transaction state is the most dangerous case: PHP does NOT auto-rollback on exception, so a throw between `beginTransaction()` and `commit()` leaves the connection with an open transaction. When the connection returns to a pool or long-running worker, the next unrelated query runs inside the stale transaction and either auto-commits partial writes or is silently rolled back by the next `beginTransaction()`.

**Resources that leak on throw unless released in `finally` (or a catch that releases before re-throwing):**

| Resource                          | Release call                                              |
|-----------------------------------|-----------------------------------------------------------|
| PDO transaction                   | `$pdo->rollBack()` in catch, `commit()` only on success   |
| File handle (`fopen`, `tmpfile`)  | `fclose`                                                  |
| Advisory lock (`GET_LOCK`, `flock`) | `RELEASE_LOCK` / `flock(LOCK_UN)`                       |
| Temp file / directory             | `unlink` / `rmdir`                                        |
| Process / pipe (`proc_open`)      | `proc_close` + close stdin/out/err                        |
| External keep-alive connection    | framework-specific close                                  |

**Audit reflex** — for every resource-acquiring call in the diff, draw the function's exit graph (happy return, early return, every throw reachable from the acquire — INCLUDING throws inside library calls that consume the resource) and answer out loud for EACH exit: **"Is the release call reached on this exit?"** The only safe answer on all exits simultaneously is `try { ... } finally { release(); }` wrapping the acquire, OR a catch that releases before re-throwing.

**PDO-transaction canonical fix:**
```php
$pdo->beginTransaction();
try {
    $stmt->execute([...]);
    $pdo->commit();
} catch (\Throwable $e) {
    if ($pdo->inTransaction()) { $pdo->rollBack(); }
    throw $e;
}
```
(The `inTransaction()` guard prevents masking the original exception when an implicit commit — e.g. DDL in MySQL — already closed the transaction.)

### Long-Running Data Backfill Shape (undo log, resumability, replica lag)
One-shot data migrations and backfill commands fail in three ways that no query-correctness reflex catches. Distinct from P2 (READ streaming), from deep-offset pagination (LIMIT/OFFSET shape), and from queue idempotency (retry of the same payload). This reflex is about the OPERATIONAL shape of a handler that mutates N million rows in one run.

**Three failure modes:**

1. **Single-statement UPDATE / undo log blow-up.** `UPDATE t SET col = expr WHERE ...` on 10M rows runs in ONE transaction whether you asked for one or not. InnoDB must keep the entire pre-image in the undo log until commit — `innodb_log_file_size` cannot absorb it and the transaction either aborts or locks the table for minutes. Fix: chunked keyset loop, 1k–5k rows per chunk, each chunk in its own short transaction. Same trap applies to `DELETE ... WHERE` and to `INSERT ... SELECT` over large source sets.
2. **No resumability.** The command runs under `nohup`, the box reboots at row 7M, the operator restarts — and unless progress is persisted (checkpoint table OR the WHERE is naturally idempotent: `WHERE col IS NULL AND id > ?`), the restart re-processes finished rows or starts from zero.
3. **Replica lag / write-rate unbounded.** A tight loop of chunk UPDATEs generates binlog faster than an async replica can apply it. No sleep between chunks, no watch on `Seconds_Behind_Master`, and the replica falls behind SLA invisibly — the primary looks fine, the command finishes on time, and read-replica-backed endpoints serve stale data for hours.

**Audit reflex** — for every long-running mutation command / migration / backfill in the diff, answer out loud:
1. **Chunk size + commit per chunk?** Name the chunk size and prove each chunk commits before the next begins. Single unbounded UPDATE → BLOCKED.
2. **Resume key?** Name the column the WHERE advances on AND prove finished rows are excluded (self-excluding predicate like `WHERE col IS NULL`, or a checkpoint row updated transactionally with the chunk).
3. **Throttle?** Name the sleep-between-chunks AND the replication-lag check (polling `SHOW REPLICA STATUS` or equivalent). Missing → BLOCKED unless the job explicitly documents "primary-only / no replicas / maintenance window covers any lag".

**Verification** (command output, not code reading):
```sql
SHOW PROCESSLIST;               -- backfill MUST appear as many short UPDATEs, not one long one
SHOW ENGINE INNODB STATUS\G    -- 'History list length' must not grow unbounded
SHOW REPLICA STATUS\G          -- Seconds_Behind_Master stays within SLA while the job runs
```

### Input Size & Complexity Limits (DoS budget)
Every untrusted input has three dimensions — **bytes**, **cardinality**, and **complexity** — and ALL three need an explicit cap BEFORE the input reaches code that allocates memory or CPU proportional to it. An uncapped input is a DoS vector with a timer.

Audit reflex — for every new endpoint, webhook, file parser, or upload handler in the diff, name the cap out loud per dimension OR reject the change:

| Dimension           | Vector                                   | Required cap                                                                              |
|---------------------|------------------------------------------|-------------------------------------------------------------------------------------------|
| Raw bytes           | JSON body, multipart upload, webhook     | Web-server body limit + per-route override; reject before parsing                         |
| Array length        | `items: [...]`, bulk-create, ID lists    | `count($arr) <= N` validated BEFORE iteration. **SQL follow-up** when the array becomes an `IN (...)` list: HTTP cap alone is insufficient. Past `eq_range_index_dive_limit` (MySQL default 200) the planner stops per-value dive and may bail to `type: ALL`; each distinct arity is also a new prepared-statement plan-cache entry. EXPLAIN at the CAP value (not at 3), confirm `type: range` and `rows ≈ list size`, and chunk the IN list into fixed-size batches OR join against a temp/VALUES table for a single cached plan shape. |
| Nested depth        | User JSON / YAML / XML                   | Decode with explicit `$depth` (default is often 512, too deep for recursion)              |
| Decompression ratio | gzip / zip upload, `Content-Encoding`    | Stream-decode with max output bytes; reject ratio > ~100x (zip bomb)                      |
| Regex input size    | Server-side text validation              | Length cap BEFORE the regex; reject patterns with nested quantifiers (catastrophic backtracking like `(a+)+$`) |
| Page size           | `?per_page=`, `?limit=`                  | Clamp server-side to a hard max (`min($n, 100)`); NEVER trust client                      |
| Pixel area          | Image upload, thumbnail generation       | Reject width*height > N BEFORE decode; image bombs allocate on decode, not on read        |
| String length       | Any text field persisted to a sized column (`VARCHAR(N)`, `CHAR(N)`, `TINYTEXT`) | PHP-side `mb_strlen($s) <= N` BEFORE the INSERT/UPDATE. Under non-strict sql_mode (`@@sql_mode` does NOT contain `STRICT_TRANS_TABLES`) MySQL SILENTLY truncates oversize strings — statement returns success, `rowCount()==1`, stored value is cut. Verify: `SELECT @@sql_mode` AND `information_schema.COLUMNS.CHARACTER_MAXIMUM_LENGTH`; if non-strict, every bound string must be length-capped in app code. Under utf8mb4, `CHARACTER_MAXIMUM_LENGTH` is in characters but a 4-byte emoji still counts as 1 — use `mb_strlen` with the right encoding. |

**Two silent failure modes:** (1) OOM under load — cap "works" at p50 because the average payload is tiny, p99.9 takes the worker down and the stack trace points at the allocator, not the missing cap. (2) CPU lock — a regex with nested quantifiers on a 50KB string hangs the worker for minutes with no error, no log, just a queue that stops draining.

Verification: for each new input-accepting endpoint in the diff, produce command output showing behavior at 2x the documented cap — expect 413/422, NOT 500 / OOM / hang.

### Timezone / Date-Boundary Sanity
Any code that computes a day-boundary string ("yesterday", "today", "this month") OR compares it to a SQL `DATE(col)` / `CURDATE()` has THREE timezones in play: the PHP process TZ, the DB session TZ, and — if rows are owned by an entity with its own TZ column (tenant, user, venue, subscription) — that entity's TZ. If all three are not explicitly named and aligned, the boundary is wrong at least once per day and twice per DST transition.

Audit reflex — for every `date()`, `strtotime()`, `DateTime`, `DATE(col)`, `CURDATE()`, `NOW()`, or `BETWEEN` over datetimes in the diff:
- Name the TZ of the producer (PHP default vs explicit `new DateTimeZone(...)`).
- Name the TZ of the consumer (DB session `@@time_zone`, or the entity's TZ column).
- Prove they match, OR that the comparison uses `CONVERT_TZ(col, @@session.time_zone, ?)` with the entity TZ bound as a parameter.
- For recurring-event generation or "N days from now" math, verify DST: spring-forward and fall-back make `+1 day` non-equivalent to `+86400 seconds`.
- Store timestamps as UTC (or a single fixed zone) in the DB; do day-grouping in the READER's TZ, not the server's.

Silent failure mode: for a same-TZ developer the code works every day in local testing, and breaks only for users in other zones near midnight — invisible until a support ticket from a far-away customer.

### Open Redirect via Untrusted Return-To URL (`?next=`, `?redirect=`, `?returnTo=`)
Any endpoint that reads a URL/path from caller input and emits `Location:` (meta-refresh or `window.location = ...` count too) is an open-redirect primitive unless the target is allowlisted BEFORE the header is sent. `?next=//evil.com/fake-login` bounces the post-login victim to an attacker clone for credential re-entry. Distinct from P3 and Session Lifecycle: this covers the DESTINATION of a caller-controlled redirect.

**Four payload shapes that bypass naive checks** (all defeated by `parse_url` + host-component equality, NOT by string prefix / regex):

1. **Protocol-relative** `//evil.com/x` — `starts_with('/')` passes; `Location:` resolves off-host.
2. **Backslash normalization** `/\evil.com` — some browsers/proxies rewrite to `//evil.com`, defeats `^/[^/]`.
3. **Empty-scheme with host** `//evil.com/x` — scheme is null but `parse_url(..., PHP_URL_HOST)` is NOT null; assert host null OR equals app host.
4. **Userinfo** `https://app.example.com@evil.com/x` — substring match on app host passes; actual host is `evil.com`.

**Audit reflex** — for every `Location:` / `redirect($var)` / `location.href = ...` in the diff where the target is derived from request input:
1. **Allowlist mechanism**: a fixed enum of route names, or `parse_url` host-component equality check against the app host. Regex on raw string → BLOCKED (fails at least one trap above).
2. **Prove the empty-host path**: demonstrate `parse_url($next, PHP_URL_HOST)` returns `null` on the accepted form AND the attacker host on each trap form.
3. **End-to-end run**: hit the endpoint with each trap payload and follow `Location`; final hop MUST stay on the app host.
4. **Scheme allowlist**: only null (relative) or `http`/`https` with host === app host. Reject `javascript:`, `data:`, `vbscript:`, `file:` — they may be inert in `Location:` but the same helper is often reused for `<a href>` or `<meta refresh>` where they DO execute.

**Companion reflex — Path Traversal via Filesystem READ.** The same normalization-bypass shape applies to any `readfile` / `fopen` / `file_get_contents` / `include` / `require` / `SplFileObject` sink where ANY segment of the resolved path is derived from request input OR from a DB column that ANY write path has ever shaped from user input (the column is user-controlled for audit purposes, even if the write form is long gone). Distinct from the upload WRITE-path traversal reflex: this covers the READ sink. Bypass payloads that defeat naive defences: `../../../etc/passwd` (raw concat), absolute `/etc/passwd` (collapsed `//base`), NUL byte `safe.pdf\x00../../etc/passwd` (suffix-check bypass on legacy bridges), symlink-in-base pointing out-of-base (defeats string-prefix check on INPUT but caught by `realpath()` on RESOLVED path). Required defence: `$base = realpath('/var/app/storage/x')` → `$full = realpath($base . '/' . $input)` → reject unless `$full !== false && str_starts_with($full . DIRECTORY_SEPARATOR, $base . DIRECTORY_SEPARATOR)`. `basename()` alone is NOT sufficient. An ownership check (`row.user_id === session.user_id`) does NOT mitigate — the attacker owns their own row. Verify: plant a row with `pdf_path = '../../../../etc/passwd'`, hit the endpoint, expect 404 with empty body (NOT 200 with `root:x:0:0:`).

### NULL Semantics in Aggregation
Aggregate functions treat NULL inconsistently — the wrong choice silently produces the wrong number with no error. Distinct from the P2 aggregate trap (SCAN COST): this reflex is about CORRECTNESS.

**Four traps:**

1. **`COUNT(col)` vs `COUNT(*)`** — `COUNT(col)` (and `COUNT(DISTINCT col)`) ignore rows where `col IS NULL`. A nullable column is NEVER the right thing to `COUNT(DISTINCT ...)` when the intent is "how many distinct entities" — count the primary key instead: `COUNT(DISTINCT u.id)`.
2. **`SUM` / `AVG` over empty set returns NULL, not 0** — downstream arithmetic silently becomes NULL in loose-typed code and throws in strict-typed code. Wrap with `COALESCE(SUM(col), 0)` at the query boundary.
3. **`AVG(col)` ignores NULL rows in BOTH numerator and denominator** — `AVG(rating)` over 100 rows where 60 are NULL returns the average of 40, not `sum/100`. If intent is "unrated = 0", use `SUM(COALESCE(rating, 0)) / COUNT(*)`.
4. **`LEFT JOIN` silently degrades to `INNER JOIN`** — `LEFT JOIN p ON p.fk = u.id WHERE p.status = 'X'` is INNER in disguise: the WHERE filters out NULL rows the LEFT JOIN produced. Keep LEFT semantics by moving the predicate into the ON clause.

**Audit reflex** — for every `COUNT`/`SUM`/`AVG`/`MIN`/`MAX` in the diff, check if the aggregated column is nullable (use `IS_NULLABLE` from the Pre-Flight schema introspection); if yes, say out loud whether NULL-exclusion is intended. For every LEFT JOIN, grep the WHERE for references to the right-side table — any match means the LEFT has degraded to INNER; confirm intent or move the predicate into ON.

---

## Self-Tuning

When reading `.audit-log.md` at the start of an audit:
- If a finding type (N+1, missing index, SQL injection, etc.) appeared 3+ times in recent audits → flag as **SYSTEMIC** and recommend structural fix, not another point fix.
- If a check category has had 0 findings in the last 10 audits → run it at reduced depth (spot-check instead of exhaustive).
- If a check category fires on >50% of audits → run it FIRST and most aggressively.

This keeps audit effort focused where this specific codebase actually has problems.

---

## Rules

- **Pre-flight is not optional.** Checking the schema BEFORE writing code prevents entire categories of bugs.
- **The audit ALWAYS runs after code is written.** No exception. No "it's just a small change". No "I'll check later". Triage determines intensity per layer, but all 5 layers are checked every time — at minimum as spot-check.
- **Live DB beats any static file.** Always query the real database when DB access is available.
- **No DB access?** Ask once. If unavailable, run audit without DB layer and mark it "⚠️ DB unchecked".
- **ORM-aware.** Eloquent, Prisma, etc. — read model definitions and verify against live DB columns.
- **One consolidated MySQL query.** Never run 4 separate introspection queries.
- **Output proportional to findings.** Clean code gets one line. Problems get detail. No empty sections.
- **The thought "I don't need this for such a small change" is the trigger to run it.** Small changes cause production outages precisely because they skip review.

### v4 Verification Rules

- **VERIFICATION beats ASSERTION.** Read code is not proof. The audit must produce command output. The six reflexes this rule covers (JSON dump, hunt-and-replace, layout-link→route, accessor exposure, forbidden phrase list, read-check false-positive rate) are defined in depth in the Audit phase callout and in Cross-Layer Checks above — do not duplicate them here.

### v5 Plan-Time Rules (born from plan-time bugs, not code-time bugs)

- **PLAN MODE is not optional when a spec/plan exists.** Run the 6 plan reflexes (P1-P6) BEFORE dispatching any implementation subagent. A bug locked in at plan-time cascades through every subagent and every review. The reflex content lives in PLAN MODE above — do not duplicate it here.
- **Fix prescriptions themselves need review.** A code reviewer can correctly identify a bug AND prescribe a broken fix. When re-dispatching an implementer to fix quality issues, pre-validate the prescription against the actual call/query shape before shipping it. Don't trust your own review output blindly.
