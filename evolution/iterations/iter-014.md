# Iteration 014 — free mode (v4)

**Attack agent**: general-purpose, model: opus
**Verify agent**: general-purpose, model: opus
**Task title**: SendDailyDigest — per-tenant yesterday-summary mail job

## Task (self-contained, PHP/MySQL, framework-agnostic)
Scheduled job at 03:00 server time (Frankfurt/Europe-Berlin worker) iterates
tenants across every continent, computes yesterday's orders + revenue per
tenant, emails digest. Queue is at-least-once. Tenants have explicit
`timezone` column ('Asia/Tokyo', 'America/Los_Angeles', …). MySQL session
`time_zone = SYSTEM`. Full PHP code snippet included.

## Bugs planted (4)
- **B1** Day-boundary computed in server TZ ignoring per-tenant `timezone` column; plus `DATE(created_at)` in MySQL session TZ vs `$yesterday` in PHP server TZ — **TARGETED**
- **B2** `orders.amount DOUBLE` — float-money rule (iter-13 added)
- **B3** `$tenant->orders()` inside `foreach Tenant::all()` — N+1 relationship access
- **B4** `mail()` before `digest_log` insert, no UNIQUE index, no dedup check → double email on retry

## Pre-edit simulation (attack subagent)
Caught **3/4**: B2 (float money via iter-13 rule), B3 (N+1), B4 (queue idempotency).
Missed: **B1** — skill had zero mentions of `timezone`, `TZ`, `CURDATE`, `UTC`, `DST`, or `DATE(col)`. The generic "off-by-one" one-word bullet in Logic layer is too vague to cue TZ thinking.

## Proposed edit
New sub-section **"Timezone / Date-Boundary Sanity"** appended after Queue/Task Idempotency:

```
Any code that computes a day-boundary string ("yesterday", "today", "this month")
OR compares it to a SQL DATE(col) / CURDATE() has THREE timezones in play: the
PHP process TZ, the DB session TZ, and — if rows are owned by an entity with its
own TZ column — that entity's TZ. If all three are not explicitly named and
aligned, the boundary is wrong at least once per day and twice per DST transition.

Audit reflex — for every date(), strtotime(), DateTime, DATE(col), CURDATE(), NOW(),
or BETWEEN over datetimes in the diff:
- Name the TZ of the producer (PHP default vs explicit DateTimeZone)
- Name the TZ of the consumer (DB session @@time_zone, or entity TZ column)
- Prove they match, OR comparison uses CONVERT_TZ(col, @@session.time_zone, ?)
  with the entity TZ bound as a parameter
- For recurring/"N days from now" math: verify DST — +1 day is not +86400 seconds
- Store as UTC; day-group in the READER's TZ, not the server's

Silent failure: same-TZ developer sees green tests forever; breaks only for users
in other zones near midnight.
```

- `targeted_miss: "B1"`
- Framework tokens in new_string: **0** (PHP stdlib functions + vanilla SQL)
- Line count delta: +12 (726 → 738)

## Gate checks (v4)
- edit != null ✓
- old_string unique ✓
- generality: 0 framework tokens ✓
- line-count guard: +12 (justified — distinct general gap with no prior coverage,
  100% framework-agnostic, fills a documented miss from iter-13)
- structure intact ✓

## **v4 — POST-EDIT VERIFY**

Independent verify subagent re-simulated the same task against the post-edit SKILL.md:

```
pre_caught:                 3
post_caught:                4
delta:                      +1
targeted_miss:              B1
targeted_miss_now_caught:   TRUE ✓
post_missed:                [] (none)
forbidden_phrases_count:    0
```

**Verify notes**: *"New Timezone/Date-Boundary Sanity section directly triggers
on date()/strtotime()/DATE(col) with tenant TZ column; all 4 bugs caught."*

**Full 4/4 post-edit.** Perfect targeted win.

## Decision: **edit_verified** (targeted win)

## Trend
```
iter  lines  delta  action             verify_delta  target_hit
7     789    +55    edit (v2)          n/a           n/a
9     734    -11    edit_generalize    n/a           n/a  (retro)
11    734    0      edit_generalize    n/a           n/a
12    726    -8     edit_generalize    n/a           n/a
13    726    0      edit_verified      +1            YES (B1 money)
14    738    +12    edit_verified      +1            YES (B1 TZ)
```

## Final JSON
```json
{"iter":14,"mode":"free","score":3.75,"baseline":68,"action":"edit_verified","skill_md_lines":738,"skill_md_delta":12,"pre_caught":3,"post_caught":4,"verify_delta":1,"verify_target_hit":true,"edit_kind":"bug_fix_targeted","spec_version":4}
```
