# CLEANUP MODE — full protocol (opt-in, report-only)

> Loaded ONLY when the user explicitly asks to clean up / remove dead / orphaned / unused / redundant code in EXISTING code — not the current task's own output (that is the always-on Self-Slop Sweep in `build-mode.md` Step 3, Layer 6). The router lives in `SKILL.md`. Operating Principles govern every step. **This mode never deletes. It produces a classified report; the human makes every deletion decision.**

## The one law

**Any single positive signal proves a symbol is LIVE and vetoes its removal. Absence of references never proves it is DEAD.** Static "unused" output is a *candidate*, never a verdict — every dead-code tool's own maintainers say so. In dynamic stacks (PHP magic/Eloquent/Blade, Vue templates/auto-imports, Python decorators) false positives are the norm; bias hard toward KEEP. This protocol was validated against a 30-trap adversarial fixture (`test/`): the gate's job is to keep all 30 traps alive (CRITICAL_FP=0) while still surfacing genuinely-dead closed-world symbols.

## When this fires

Opt-in only. Trigger phrases: "räum auf / aufräumen / clean up", "dead code / toten Code", "ungenutzt / unused / orphan / verwaist", "redundant / Duplikate entfernen". A normal build/change/fix does NOT enter CLEANUP MODE — it only runs the Self-Slop Sweep on its own diff. If the user is changing code AND asks for cleanup, run BUILD MODE for the change and CLEANUP MODE for the existing-code sweep separately.

## Step 1 — Inventory candidates (multi-tool, never one tool)

Run whichever per-language detectors are installed; treat each as a *candidate list*, not truth. Absent tools are skipped, not required.

| Stack | Candidate detectors (run if present) |
|---|---|
| JS/TS/Vue | `npx knip`, `npx ts-prune`, `eslint --rule no-unused-vars`, `tsc --noUnusedLocals` |
| PHP/Laravel | `phpstan` (dead-code/private rules), `psalm --find-unused-code`, shipmonk `dead-code-detector`, `composer-unused` |
| Python | `vulture . --min-confidence 80`, `ruff` (F401/F841), `coverage` (as a *liveness* signal only) |

Then, for **every** candidate symbol, run the liveness aggregator — this is the gate, not the per-language tool:

```bash
python3 ~/.claude/skills/code-guardian/tools/detect-dead-code.py --liveness <Name> [<Name> ...] \
    --root <app-source-dir> --exclude '<manifests|generated|docs>'
```

**Scan the source, not the answer key.** Point `--root` at the real application source and **`--exclude` anything that names symbols without calling them** — data manifests, generated code, changelogs, `CHANGELOG.md`, `*.lock`, fixtures, and the cleanup report itself. A symbol named as a quoted string in a JSON/YAML data file is otherwise counted as a keep-alive (`di_config`) — correct for a real DI config under `config/`, wrong for an arbitrary manifest. (This was the single biggest false-signal source in fixture validation: scanning a tree that contained a symbol-name manifest flipped every dead symbol to LIVE.)

## Step 2 — Liveness-veto classification

`detect-dead-code.py --liveness` prints one line per symbol: `NAME class=<…> refs=<n> fp=<flags> private=<y/n>`. Reconcile each candidate to one of:

- **LIVE** (`refs > 0`) — a real code/template reference exists. → **KEEP.**
- **ASSERTED-DEAD** — `refs == 0` BUT either a framework keep-alive flag fired (`route` · `blade_vue` · `magic` (Eloquent `scope*`/accessor/relation) · `di_config` · `db_dispatch` · `entrypoint` (Job/Listener/Observer/Command/webhook) · `test_only`) OR the symbol is public/open-world (external importers unprovable). → **KEEP; recommend deprecate-before-delete** (mark `@deprecated`, block new uses, observe a full business cycle, *then* a human may remove). Never delete now.
- **VERIFIED-DEAD-PRIVATE** — `refs == 0` AND no keep-alive flag AND closed-world (`private` member · Python `_name`/`def _` · **non-exported** JS/TS module-local). → **the only class eligible for removal — and even then the skill only RECOMMENDS it; the human deletes.**

**The safety invariant** (verified by the fixture, do not weaken): `VERIFIED-DEAD-PRIVATE` requires `refs==0` **AND** no `fp` flag **AND** `private=y`. Anything reachable by route/template/DI/db-dispatch/magic gets a flag and stays ASSERTED. Public and `protected` symbols are open-world → never VERIFIED. When unsure between ASSERTED and VERIFIED, choose ASSERTED.

**What `--liveness` cannot answer** (route these elsewhere, don't force a verdict): unused *imports*, unused *local variables*, and *unreachable* code after a return are not named-symbol liveness questions — they belong to a linter (`ruff`/`eslint`/PHPStan) or the `--diff-slop` self-sweep, not this gate.

## Step 3 — Cross-check survivors against ALL file types

Before any symbol stays VERIFIED-DEAD-PRIVATE, spot-verify the surprising ones by hand — string-resolved references defeat static graphs:

```bash
grep -rn "\b<Name>\b" --include="*.php" --include="*.js" --include="*.ts" --include="*.vue" \
  --include="*.blade.php" --include="*.json" --include="*.yaml" --include="*.yml" \
  --include="*.sql" --include="*.env*" . | grep -v vendor | grep -v node_modules
```
Any hit outside the definition (and outside an excluded manifest) → reclassify LIVE.

## Step 4 — Redundancy (counter-rule: duplication is cheaper than the wrong abstraction)

```bash
python3 ~/.claude/skills/code-guardian/tools/detect-clones.py --root . --kind code --cross-file-only --extract-threshold 3
```

- `NOTE-ONLY` groups (< 3 sites) → **leave them.** Two copies do not justify an abstraction.
- `EXTRACT-CANDIDATE` groups (≥ 3 sites) → recommend extraction **only if** the sites encode the *same knowledge* (one concept, one reason to change). If they merely *look* alike but can change independently → coincidental duplication → **leave them; merging creates false coupling.**
- Never recommend introducing a parameter + conditional to fuse two near-miss (Type-3) clones — that is the first step of the wrong-abstraction death spiral. The skill must not itself generate slop while cleaning slop.

## Step 5 — Report (report-only; the skill does not delete)

```
## Cleanup Report: <scope>
VERIFIED-DEAD-PRIVATE (human may delete; one symbol/commit, git-recoverable):
  🟢 <Class::method>  — 0 refs · no fp flag · private   Verified-by: <detect-dead-code line + grep>
ASSERTED-DEAD (KEEP — deprecate-before-delete, observe a business cycle):
  🟡 <name>  — 0 refs BUT <public | route | magic | di_config | …>   Verified-by: <line>
LIVE / vampire (KEEP — looked dead, is reachable):
  ⚪ <name>  — reached via <route|Blade|magic|DI|DB-dispatch|cron|test>   Verified-by: <fp flag + grep hit>
Linter territory (out of --liveness scope — defer to ruff/eslint/PHPStan):
  ⚪ unused import / unused local / unreachable branch
Redundancy:
  🟡 EXTRACT-CANDIDATE <hash> (≥3 sites, same knowledge) → extract to <target>
  ⚪ NOTE-ONLY <hash> (2 sites / coincidental) → leave
N verified-dead-private · M asserted-dead (kept) · K live (kept) → ALL DELETIONS DEFERRED TO HUMAN
```

If the human then asks to act on a VERIFIED-DEAD-PRIVATE candidate: remove one symbol per commit, `git`-recoverable, with a commit message recording the checked signals, run the build + full test suite green after each, and re-run BUILD MODE Step 2 (symbol-loss gate) + the audit on the deletion diff — a removal is a code change like any other.
