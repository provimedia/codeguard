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

One skill. Two modes. Zero exceptions.

Born from real bug data: across six development phases, 5 bugs slipped past
audits that "looked correct". Every iteration of this skill is a tightening of
the verification reflex — never assert, always verify against command output.

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

Bugs that survive the audit phase usually originated in the **plan**. Reading
the plan back with these reflexes catches problems before any code is written
and before subagents are dispatched.

**When to run:** After `superpowers:brainstorming` or `superpowers:writing-plans`
produces a spec/plan, BEFORE any implementation subagent is dispatched. Also
when receiving a plan from another author.

**The 6 plan-time reflexes:**

### P1. Cross-Layer Trace for Every New Field

For every NEW field/column/property the plan introduces, walk the data path
end-to-end and **prove** each layer is wired up explicitly. Do not trust
"`$fillable` will propagate it" — many controllers use explicit serialization
whitelists.

```
DB column                ← migration adds it
     ↓
Model $fillable          ← grep model file
     ↓
Model $hidden / $appends ← does the field need to be exposed?
     ↓
Controller serialization ← grep controller for explicit array vs $product->only(...) vs $product directly
     ↓
Inertia/JSON payload     ← does the controller pass the model raw, or build a key whitelist?
     ↓
Vue prop                 ← does the template read product.field_name?
     ↓
v-if / interpolation     ← is rendering conditional or unconditional?
```

**Verification command (run during plan review, not just audit):**
```bash
# For each new field "X":
grep -n "Inertia::render\|->only(\|->toArray()" app/Http/Controllers/*.php | head
# If you see explicit ->only('a', 'b', 'c') OR explicit ['key' => ...] arrays:
#   the plan MUST include a controller change. $fillable alone is not enough.
```

**Lesson:** A model-layer allowlist (e.g. mass-assignment fillable) does NOT
guarantee client delivery — if the controller serializes via an explicit key
whitelist, any field absent from that whitelist is dropped silently and the
client-side conditional never fires. Always grep the controller, not the model.

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

Every plan that introduces an API call OR an inbound webhook endpoint MUST specify:
- API key / shared secret passed via **header**, NEVER query string — in BOTH directions.
- Why (outbound): HTTP-client exceptions typically include the full URL; a URL-embedded
  key leaks into application error logs on any failure.
- Why (inbound): `?api_key=` in a webhook URL leaks into web-server access logs,
  reverse-proxy logs, browser history, and Referer headers on any redirect. Require
  the signature in a header (not the query string) and compare with a constant-time
  equality function.
- Why (user-facing download/reset tokens): same leakage surface applies to `?token=` in
  emailed download/reset/magic-login links. Use a signed, time-limited URL mechanism
  (signature travels in the URL but is bound to route+expiry and verified server-side),
  store a SHA-256 HASH of the token in the DB (never the raw value), and enforce
  one-time use via a `consumed_at` column checked+set in a single transaction.

**Verification during plan review:** grep the plan's pseudocode for `?key=`,
`?api_key=`, `?token=`. If found, reject the plan section and require header-based
auth instead.

### P4. config:cache Safety

Every plan that introduces a new env var MUST specify access via
`config('namespace.key')`, NEVER `env('VAR')` outside `config/*.php` files.

```php
// FORBIDDEN — returns null when production runs `php artisan config:cache`
$key = env('GEMINI_API_KEY');

// REQUIRED — survives config:cache
// 1. Add to config/services.php:
'gemini' => ['key' => env('GEMINI_API_KEY')],
// 2. Read via:
$key = config('services.gemini.key');
```

**Verification during plan review:** if the plan's pseudocode contains
`env('...')` outside a config file, reject it and require a config block.

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

**Why this is plan-time, not audit-time:** the subagent prompt is locked in
when the controller dispatches the agent. By the time the audit catches the
swept-in WIP, the commit is already created. Fix the briefing template, not
the symptom.

**Lesson:** `git add <path>` sweeps in any other uncommitted WIP that already
sits in the same file. On a branch with pre-existing WIP, stage hunks
(`git add -p`) and verify the diff before commit — otherwise unrelated work
ships under an inaccurate message and history needs rewriting to untangle.

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

```
Step 1: Find all consumers
```
Grep for the function/method name across the entire codebase. Not just the file you're working in — EVERY file.
```bash
grep -r "functionName\|ClassName\|methodName" --include="*.php" --include="*.js" --include="*.ts" --include="*.vue" --include="*.blade.php" -l
```

```
Step 2: Read each consumer — understand HOW it uses the function
```
For each file found, read the actual call site. Document:
- What **parameters** does this caller pass?
- What **return value** does it expect (type, structure, null possibility)?
- Does it depend on **side effects** (session, global state, DB writes)?
- What **page/view/form** does this caller belong to?

```
Step 3: Build the impact map (silent, no output yet)
```
```
FUNCTION: saveUser()
├── used in: RegisterController.php → passes (name, email, password) → expects User object back
├── used in: ProfileController.php → passes (name, email) → expects User object back
├── used in: AdminUserEdit.php → passes (name, email, role) → expects User object back
└── used in: ApiUserController.php → passes (name, email, password, team_id) → expects JSON
```

```
Step 4: Identify what breaks
```
Before writing a single line: check your planned change against EVERY consumer.
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

```
VERIFY: saveUser() — 4 consumers
├── RegisterController.php  → ✅ updated
├── ProfileController.php   → ✅ updated
├── AdminUserEdit.php       → ✅ updated
└── ApiUserController.php   → ❌ MISSED — still passes old params → FIX NOW
```

### Step 3: Audit (AFTER writing code) — ALWAYS. NO EXCEPTIONS.

The audit runs every single time code is written or changed. It is never skipped, never deferred, never "done later". The triage determines WHICH layers run at full depth — but every layer runs at minimum as a spot-check.

> **VERIFICATION-NOT-ASSERTION RULE (v4 — born from real bugs that slipped through)**
>
> Audit checks must be **VERIFIED** by command output, not **ASSERTED** by reading code.
> "I read the controller and the keys match the Vue page" is NOT an audit. The audit is:
> dump the actual serialized response (curl, tinker, or Playwright) and prove the values exist.
>
> Three reflexes that the v4 audit drills into:
>
> **A) JSON Inspection over Code Reading**
> When auditing Cross-Layer Data Contracts, do not stop at "controller returns key X, Vue reads key X".
> Eloquent accessors, hidden attributes, $appends omissions, and conditional `when()` props mean
> the structural match can pass while the actual JSON has `key: undefined`. Always verify the
> actual payload:
>
> ```bash
> # Inertia render JSON — adapt the URL to your project
> curl -s "${APP_URL}/<route>" \
>   | grep -oE 'data-page="[^"]+"' \
>   | python3 -c 'import sys, html, json; raw=html.unescape(sys.stdin.read()[11:-1]); print(json.dumps(json.loads(raw), indent=2)[:2000])'
>
> # Or use Playwright to assert non-undefined hrefs:
> page.locator('a[href*="undefined"]').count()  // must be 0
>
> # Or via tinker — for Eloquent paginators:
> php artisan tinker --execute="echo json_encode(\App\Models\X::paginate(3)->toArray()['data'][0], JSON_PRETTY_PRINT);"
> ```
>
> If the value the Vue side reads is `undefined`/`null` in the actual JSON when the bug-causing
> code path is exercised → that's the bug. Not what you read in the controller's PHP.
>
> **Real bug this prevents:** `getLocalPathAttribute()` was a model accessor not in
> `$appends`. Controller code looked correct. Vue defineProps looked correct. But
> `paginate()->toArray()` never invoked the accessor → 1,142 article links rendered as
> `/undefined`.
>
> **B) Hunt-and-Replace Verification**
> When fixing a known pattern (e.g. wrap a hardcoded `/path/` in a helper), DO NOT stop at the
> first occurrence you found. Grep the entire codebase for the same pattern and verify each match
> is either fixed OR has a justified reason to be exempted.
>
> ```bash
> # After fixing one instance of router.post('/foo', ...) → router.post(url('/foo'), ...)
> # IMMEDIATELY grep for all unfixed siblings:
> grep -rn "router\.\(post\|get\|put\|patch\|delete\|visit\)\s*(\s*[\`'\"]/" \
>   resources/js --include='*.vue' --include='*.js' \
>   | grep -v 'url(' \
>   | grep -v 'codeguardian-ok'
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

**DB Integrity** — Fields match live schema? FKs correct? Missing indexes on queried columns? N+1 patterns? ORM attributes match real columns? Money/currency stored as integer minor units (cents) or DECIMAL(p,s), NEVER FLOAT/DOUBLE — float rounding silently corrupts totals across aggregation, and `a*b` in float arithmetic is not associative.

**Logic** — Dead code? Unused variables? Unhandled edge cases (null, 0, empty string, empty array)? Missing returns in conditional paths? Off-by-one?

**Efficiency** — Loops replaceable by single query? Sequential awaits that could be parallel? SELECT in loop instead of JOIN? Missing pagination on large sets?

**Redundancy** — Duplicated logic? Utility already exists in codebase? Copy-paste that should be abstracted?

**Security** — Raw user input in queries (SQL injection)? Sensitive fields (password, token, secret) in responses? Missing auth checks? Mass assignment without whitelist? Missing rate limiting on auth endpoints? IDOR vulnerabilities?

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

### Escalation

Failed once → Document why. New root-cause analysis from Phase 1. Mark failed hypothesis as disproven.
Failed twice → STOP. Report both attempts + analysis to user. Do not blindly continue.

---

## Cross-Layer Checks (learned from real bugs)

These catch bugs that live BETWEEN components — not inside any single file, but in the handshake between them.

### Cross-Layer Data Contracts
When one layer produces data and another layer consumes it, verify both sides agree.

**Producer → Consumer mismatches:**
- Backend sends field `status` → Frontend reads `success` → Data silently lost
- Service returns `{score: 85}` → Controller maps it to `{compatibility: 85}` → View reads `score` → undefined
- Middleware shares `['flash' => ['status' => ...]]` → Controller sets `->with('success', ...)` → Frontend reads `flash.success` → empty
- Eloquent accessor not in `$appends` → `paginate()->toArray()` skips it → Vue receives `key: undefined` → renders `href="/undefined"` → 404
- Subdir-install: Vue calls `router.post('/foo')` (no helper) → resolves to wrong base → 404 silent under MAMP, fine under root domain

**How to check (READING is not enough):**
1. Trace the data from where it's CREATED to where it's READ
2. **Dump the actual serialized payload** — curl the route, parse data-page JSON, check that every key the Vue reads has a non-null value
3. Verify the key names match at every hop
4. Verify the data structure matches (array vs object, nested keys, null possibility)

This is the #1 source of silent bugs — no error, no crash, just missing data.

**Derived-property exposure check:** any time a serializer (`toArray` / `toJSON` / marshal) walks a model whose consumer reads a property that is COMPUTED (accessor, virtual attribute, getter, lazy/`@property` field), verify the serializer opts-in to computed output — otherwise the property is silently absent from the payload and the consumer reads undefined.

### Return Type Completeness
When a function has conditional branches (if/else, early returns, error paths), verify ALL branches return a compatible type.

Common traps:
- Main path returns ResponseObject, error path returns redirect() → different types
- Happy path returns {data: [...]}, edge case returns null → consumer crashes
- Normal flow returns rendered page, self-redirect returns different response type

### Interface Boundary Verification
When new code calls existing services/functions:
1. Read the ACTUAL function signature, not what you assume it is
2. Verify parameter count, types, and order match
3. Verify the return type is what you expect
4. Verify optional parameters have correct defaults

### ORM/Model Verification
When code references DB fields, verify against BOTH the Model AND the live DB:
- Are mass-assigned fields in the whitelist ($fillable, attr_accessible, etc.)?
- Are type casts correct? Wrong cast = wrong type at runtime.
- Do relationship definitions match the actual FK columns in the DB?
- Is the table name explicitly set if the model name doesn't follow convention?

### Auth Enforcement Parity Across Entry Points
When a service/domain method is invoked from MORE THAN ONE entry point — web route, CLI command, queue/background worker, scheduled task, admin panel, internal API, webhook handler — the authorization gate MUST be equivalent at every entry point, OR the gate must live INSIDE the service and not at the edge.

Auth-at-the-edge (middleware/policy on the route) is safe ONLY while the service has exactly one caller. The moment a second entry point appears, the route-level gate is bypassed by design — middleware does not run for background workers or CLI invocations.

**Audit reflex** — for every service method touched in the diff, run the consumer grep from BUILD Step 1d and for EACH caller answer out loud:

1. **What auth check guards this entry point?** Name the middleware / policy / gate / inline check.
2. **Is the check equivalent to every OTHER entry point's check?** A route gated by a policy (checks verified / not-banned / has-quota) is NOT equivalent to an admin route checking only an admin flag, and NOT equivalent to a CLI or queue caller with no gate.
3. **If the gates differ, does the difference match intent?** An admin override that explicitly bypasses one invariant is acceptable IF documented AND the non-admin paths still enforce the others.

**The fix is almost always the same**: push the authorization check INTO the service (it throws on failure regardless of caller). Edge-auth then becomes defense-in-depth, not the only line.

**Silent failure**: the web UI looks locked down in QA, the policy test suite is green, and a banned user still triggers the action via a weekly CLI job or a queue worker — because neither path touches middleware.

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

### Input Size & Complexity Limits (DoS budget)
Every untrusted input has three dimensions — **bytes**, **cardinality**, and **complexity** — and ALL three need an explicit cap BEFORE the input reaches code that allocates memory or CPU proportional to it. An uncapped input is a DoS vector with a timer.

Audit reflex — for every new endpoint, webhook, file parser, or upload handler in the diff, name the cap out loud per dimension OR reject the change:

| Dimension           | Vector                                   | Required cap                                                                              |
|---------------------|------------------------------------------|-------------------------------------------------------------------------------------------|
| Raw bytes           | JSON body, multipart upload, webhook     | Web-server body limit + per-route override; reject before parsing                         |
| Array length        | `items: [...]`, bulk-create, ID lists    | `count($arr) <= N` validated BEFORE iteration                                             |
| Nested depth        | User JSON / YAML / XML                   | Decode with explicit `$depth` (default is often 512, too deep for recursion)              |
| Decompression ratio | gzip / zip upload, `Content-Encoding`    | Stream-decode with max output bytes; reject ratio > ~100x (zip bomb)                      |
| Regex input size    | Server-side text validation              | Length cap BEFORE the regex; reject patterns with nested quantifiers (catastrophic backtracking like `(a+)+$`) |
| Page size           | `?per_page=`, `?limit=`                  | Clamp server-side to a hard max (`min($n, 100)`); NEVER trust client                      |
| Pixel area          | Image upload, thumbnail generation       | Reject width*height > N BEFORE decode; image bombs allocate on decode, not on read        |

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
