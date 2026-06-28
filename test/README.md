# Detector stress-test fixture

A small but realistic **polyglot mini-project** (fake Laravel-ish PHP app + a
JS/TS/Vue frontend + a Python sidecar) built as **ground truth** for a
dead-code / AI-slop / redundancy detector. It does not run — it is *statically*
realistic. Every interesting symbol is tagged in a machine-readable oracle
(`oracle.json`) and scored by `score.py`.

The fixture was designed **from first principles** (not from the detector's
source) so the traps are not overfit to any one implementation.

---

## The CRITICAL safety property

> **No `LIVE_TRAP` may ever be classified `VERIFIED-DEAD-PRIVATE`.**

`VERIFIED-DEAD-PRIVATE` is the only classification that authorizes deletion.
Every `LIVE_TRAP` in this fixture is *productive code that is reached only by
non-static means* (a route string, a Blade tag, a Vue template, a DI class-string,
a DB row, reflection, a macro, an enum name, …). If a detector marks any of them
`VERIFIED-DEAD-PRIVATE`, it would delete working code. `score.py` counts those as
`CRITICAL_FP` and the run **FAILS** (exit 1) if `CRITICAL_FP > 0`, no matter how
good the rest of the scores are.

---

## Layout

```
test/
├── oracle.json          # machine-readable ground truth (58 tagged cases)
├── score.py             # the scoring harness (stdlib only; --self-test offline mode)
├── README.md            # this file
│
├── app/                 # fake Laravel app
│   ├── Models/          # User, Post, Comment, Report  (scopes + accessors = traps)
│   ├── Http/
│   │   ├── Controllers/ # routed-only methods, webhook string-dispatch
│   │   ├── Requests/    # 'iban' rule string keeps IbanRule::validate alive
│   │   └── Sanitizers/  # coincidental-clone pair
│   ├── Services/        # DI-config class-string, DB/reflection dispatch, clones
│   ├── Console/Commands # Artisan command (CLI entry point)
│   ├── Listeners/       # auto-discovered event listener
│   ├── Observers/       # auto-discovered model observer
│   ├── Events/ Jobs/ Rules/ Enums/
│   ├── View/Components/ # <x-alert> Blade component
│   ├── Support/         # Money __call routing, Str::macro
│   └── Providers/       # wires observer + validator rule + macro
│
├── config/              # services.php (class-string), schedule.json (job-as-string)
├── routes/              # web.php (tuple + legacy string routes), api.php
├── database/seeders/    # ReportSeeder.php + reports.sql (DB-driven method names)
├── resources/views/     # Blade templates that consume the accessors/components
├── tests/Feature/       # the ONLY caller of a test-only symbol
│
├── frontend/            # Vue + JS + TS
│   ├── components/      # UserCard (global), SalesChart (:is string), Dashboard
│   ├── utils/           # clones (formatBytes x3, parseQuery x2), dead helper, dynamic import
│   ├── widgets/         # dynamic-import target
│   └── plugins/         # charts.ts (dead non-exported class)
│
├── py/                  # service.py (dead cases), handlers.py + dispatcher.py (traps)
│
└── slop/                # simulated AI-agent diff (reproduced as a git diff by score.py)
```

---

## Oracle schema (`oracle.json`)

A JSON array. Common fields: `id`, `file` (relative to `test/`), `symbol`,
`line`, `kind`, `category`, `note`.

| `kind`                 | extra fields                              | meaning |
|------------------------|-------------------------------------------|---------|
| `DEAD`                 | `expect: VERIFIED-DEAD-PRIVATE`           | private/file-local, **zero** references → genuinely removable |
| `LIVE_TRAP`            | `expect_not: VERIFIED-DEAD-PRIVATE`, `reachable_via`, sometimes `expect_ok` | productive, reached only by non-static means → must **never** be deleted |
| `REDUNDANT_EXTRACT`    | `expect: EXTRACT-CANDIDATE`, `files`      | same knowledge cloned in ≥3 files → extract (Rule of Three) |
| `REDUNDANT_LEAVE`      | `expect: NOTE-ONLY`, `files`              | cloned in exactly 2 files → note only, below Rule of Three |
| `REDUNDANT_COINCIDENTAL` | `expect: NOTE-ONLY`, `files`            | byte-identical but **different knowledge** → must NOT be merged |
| `SLOP`                 | `expect: REMOVABLE` or `DEBUG-LEFTOVER`   | only appears as a git-diff addition under `slop/` |

`expect_ok` is used for the public-API export trap, where `ASSERTED-DEAD` (and
`LIVE`) are acceptable — but `VERIFIED-DEAD-PRIVATE` is still forbidden.

### Case counts

| kind | count |
|------|-------|
| `DEAD` | 11 |
| `LIVE_TRAP` | 30 |
| `REDUNDANT_EXTRACT` | 3 |
| `REDUNDANT_LEAVE` | 2 |
| `REDUNDANT_COINCIDENTAL` | 1 |
| `SLOP` | 11 |
| **total** | **58** |

---

## Running the scorer

```bash
# Offline self-test: validates oracle parsing + matrix math with an inline MOCK
# classifier. Requires no detector tools. Also proves the harness DETECTS an
# injected critical false positive. Exits 0.
python3 test/score.py --self-test

# Real run against the detector tools in ../code-guardian/tools/:
python3 test/score.py
```

`score.py` has four sections:

1. **Liveness** (`DEAD` + `LIVE_TRAP`) — invokes
   `detect-dead-code.py --liveness <symbol> --root test` per symbol and parses
   the `class=…` classification. Computes `TP` / `FN` / **`CRITICAL_FP`** / `SAFE`.
2. **Slop** — builds a throwaway git repo (baseline = fixture **without** `slop/`),
   lays the `slop/` additions into the working tree (`git add -N`), runs
   `detect-dead-code.py --diff-slop`, and checks each slop case is flagged
   `REMOVABLE`/`DEBUG-LEFTOVER`.
3. **Redundancy** — runs `detect-clones.py --kind code --cross-file-only
   --extract-threshold 3` for clones, and routes the *config-duplication* case to
   `detect-config-leaks.sh`. Verifies `EXTRACT-CANDIDATE` vs `NOTE-ONLY`, and that
   the coincidental pair is **never** an extract target.
4. **Scorecard** — prints a table and a final
   `CRITICAL_FP=<n>` / `RESULT: PASS|FAIL`.

**Pass condition:** `RESULT: PASS` (exit 0) iff `CRITICAL_FP == 0` **and**
≥ 70 % of `DEAD` cases are true positives. Otherwise `RESULT: FAIL` (exit 1).

**Graceful degradation:** if `detect-dead-code.py` is absent, the liveness + slop
sections are skipped and the run exits 0 with `RESULT: SKIPPED` (redundancy still
runs if `detect-clones.py` is present). Use `--self-test` to exercise everything
without any tools.

---

## Trap catalogue (the 30 `LIVE_TRAP`s)

**Framework-magic (looks dead, fully wired by convention):** Eloquent query
scopes (`scopeActive`/`scopePublished`/`scopeWithTrashedAdmins`), Eloquent
accessors (`getFullNameAttribute` → `$user->full_name`, `getInitialsAttribute`,
`getExcerptAttribute`), controller methods reached only via a route tuple
`[PostController::class,'show']` and the legacy string `'PostController@index'`,
a `<x-alert>` Blade component class + template-only method, a globally-registered
Vue component (`<UserCard/>`, no JS import), a DI class-string service
(`config/services.php`), an Artisan command, an auto-discovered event listener,
an auto-discovered model observer, a public package API export, and a symbol
referenced only from `tests/`.

**Dynamic dispatch:** DB-driven method names (`run('monthlyRevenue')` from a
seeded row / `.sql`), reflection via `call_user_func`, and a JS symbol reached
only through a computed-path `import('../widgets/${name}.js')`.

**Novel / adversarial traps invented for this fixture:**

1. **Vue `<component :is="'SalesChart'">`** — component chosen by a runtime
   string; the name never appears as a tag or an import.
2. **PHP magic `__call` routing** — `Money::of(x)->eur()` routes through `__call`
   to `renderEur()`; the per-currency methods have no literal call site.
3. **Enum-name dispatch** — `process(PayoutStatus::Settled)` builds
   `'handle'.$status->name` → `handleSettled()`.
4. **Job class referenced only as a string in JSON** — `GenerateMonthlyReportJob`
   is scheduled solely via its FQ class string in `config/schedule.json`.
5. **`Str::macro` runtime method** — `Str::slugifyTitle()` exists only because a
   macro closure was registered at boot.
6. **Webhook string-dispatch** — `$this->{'handle'.Str::studly($type)}()` builds
   the handler name from the inbound payload.
7. **`Validator::extend('iban', …)`** — `IbanRule::validate` is reachable only
   through the `'iban'` rule string in a form request.
8. **Python `getattr` dispatch** — `getattr(handlers, f'handle_{event}')`.
9. **Python registry decorator** — `@register('refund.created')` stores the
   handler under a string key.

---

## Notes / caveats

- The local-variable and unreachable-branch `DEAD` cases (`unused_buffer`,
  `unreachable`) are intra-function and not classic top-level symbols; a
  symbol-based `--liveness` query may not resolve them. They are kept in the
  oracle for completeness; the 70 % TP gate still leaves margin without them.
- The config-duplication redundancy case is detected by `detect-config-leaks.sh`,
  not by the code-clone detector, so `score.py` routes it accordingly.
- A reimplementation slop case is a *rewrite* of an existing helper (different
  code, same knowledge) — deliberately NOT a byte-identical clone, so it does not
  contaminate the clone-detection groups.
