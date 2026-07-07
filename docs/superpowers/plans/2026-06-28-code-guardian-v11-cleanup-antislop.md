# Code Guardian v11 — Cleanup & Anti-Slop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The skill being modified IS Code Guardian itself — apply BUILD MODE pre-flight/audit reflexes to every task here (this is a code change like any other).

**Goal:** Add two distinct, safety-separated capabilities to Code Guardian — an always-on **Self-Slop Sweep** that strips the agent's *own* AI-slop from the current diff, and an opt-in, **report-only CLEANUP MODE** that detects (never deletes) pre-existing dead/orphaned/redundant code with a multi-signal liveness gate — without ever deleting productive code.

**Architecture:** The split is risk-driven and is the whole design. *Own slop* = code the agent just wrote this session, not yet wired to anything → safe to remove, lives inside the always-on BUILD MODE audit. *Pre-existing dead code* = foreign code → dangerous → a new opt-in mode that only ever produces a classified report (VERIFIED-DEAD-PRIVATE / ASSERTED-DEAD / LIVE), with the user making every deletion decision. The decision boundary between the two is the git diff. A new dependency-free Python tool (`detect-dead-code.py`, matching the existing `detect-symbol-loss.py` conventions) aggregates liveness evidence; it never mutates files.

**Tech Stack:** Markdown skill files (progressive disclosure), dependency-free Python 3 helper tools (regex extractors, `SUMMARY findings=…` footer, exit codes 0/1/2), Bash installer. No new runtime dependencies. External per-language detectors (knip / ts-prune · vulture / ruff · PHPStan / Psalm / shipmonk-deadcode) are *invoked when present* but never required.

## Global Constraints

- **No productive code is ever deleted by the skill.** CLEANUP MODE is **report-only** — it classifies and recommends, the human deletes. The Self-Slop Sweep removes only symbols **added in the current diff** that have **zero references** anywhere (the agent's own unused additions); anything ambiguous is reported, not removed.
- **Liveness asymmetry is law:** any single positive signal (a static reference, a hit in a template/config/route/DI/DB-dispatch/i18n string, a coverage hit) proves LIVE and **vetoes** removal. Absence of references never proves DEAD.
- **Tools stay dependency-free** (Python 3 stdlib only) and follow the existing convention: human-readable body + final `SUMMARY findings=N … exit=E` line; exit `0` clean, `1` findings, `2` usage/env error. Tools **never write to source files.**
- **Version label moves `v10 → v11`** (real rule additions, not a layout refactor). `install.sh` version-marker greps must be updated in lockstep (`Code Guardian (v10)` → `Code Guardian (v11)`, plus new markers `CLEANUP MODE`, `Self-Slop`, `detect-dead-code.py`) and `detect-dead-code.py` added to the tool-existence loop.
- **Staging discipline:** the working tree already has pre-existing uncommitted WIP. Every commit uses **explicit file paths** (`git add code-guardian/SKILL.md …`), never `git add -A`/`-p` sweeps (PLAN MODE P6).
- **Redundancy counter-rule:** the skill must never create an abstraction to kill duplication unless Rule-of-Three (≥3 occurrences) AND a "same-knowledge" judgment both pass. Duplication is cheaper than the wrong abstraction.
- **Skill prose stays English** (consistency with the rest of the skill); commit messages English.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `code-guardian/tools/detect-dead-code.py` | **Create** | Dependency-free liveness-evidence aggregator. Two modes: `--diff-slop` (own unused additions) and `--liveness NAME…` (classify a pre-existing symbol). Report-only. |
| `code-guardian/tools/detect-clones.py` | Modify | Add Rule-of-Three extract-threshold so clone groups are labelled `EXTRACT-CANDIDATE` (≥3 sites) vs `NOTE-ONLY` (2 sites), and print a wrong-abstraction caution banner. |
| `code-guardian/references/cleanup-mode.md` | **Create** | Full opt-in CLEANUP MODE protocol: liveness-veto gate, framework false-positive category gate, per-language detector commands, report-only output format, redundancy counter-rule. |
| `code-guardian/references/build-mode.md` | Modify | Add Step 3 audit **Layer 6 — Self-Slop Sweep** (always-on, diff-only) + its triage row. |
| `code-guardian/SKILL.md` | Modify | Version `v11`; refine Principle 3 (scope-split); add CLEANUP MODE branch + skeleton; add `cleanup-mode.md` to reference table; note Self-Slop in BUILD skeleton; extend frontmatter triggers; add redundancy counter-rule line to Core Rules. |
| `code-guardian/references/design-rationale.md` | Modify | Add the `### v11` rationale entry (why the scope-split, why report-only, why the liveness asymmetry). |
| `install.sh` | Modify | Update version markers to v11; add new markers + `detect-dead-code.py` to existence checks. |
| `README.md` | Modify | Document Self-Slop Sweep + CLEANUP MODE in the user-facing feature list. |

---

## Task 1: `detect-dead-code.py` — liveness-evidence aggregator (report-only)

**Files:**
- Create: `code-guardian/tools/detect-dead-code.py`
- Test: `code-guardian/tools/tests/test_detect_dead_code.py` (new dir; tests are not shipped by the installer's `.py` glob check but live in-repo for CI)

**Interfaces:**
- Consumes: nothing (stdlib + `git` CLI, like `detect-symbol-loss.py`).
- Produces (the contract later tasks rely on verbatim):
  - CLI: `detect-dead-code.py --diff-slop [--ref HEAD] [path ...]`
  - CLI: `detect-dead-code.py --liveness NAME [NAME ...] [--root .]`
  - Importable funcs: `extract_added_symbols(before_text, after_text) -> dict[name -> kind]`, `count_refs(name, root, exclude_re) -> dict`, `classify_symbol(name, refs, fp_flags, is_private) -> str` returning one of `"LIVE" | "ASSERTED-DEAD" | "VERIFIED-DEAD-PRIVATE"`.
  - Final line always: `SUMMARY findings=N live=L asserted=A verified=V exit=E`
  - Exit codes: `0` no actionable findings · `1` ≥1 finding (slop to remove, or a VERIFIED-DEAD-PRIVATE candidate) · `2` usage/env error.

### Design (the classification logic the user is approving)

**Mode `--diff-slop` (Self-Slop, always-on in BUILD MODE):**
1. `git diff --name-only <ref>` → changed code files (reuse `CODE_EXTS`).
2. Per file: before = `git show <ref>:<path>` (empty if new), after = working tree. `extract_added_symbols` = symbols defined in *after* but not in *before* (regex extractor copied from `detect-symbol-loss.py`'s `DEF_PATTERNS`).
3. For each **added** symbol, `count_refs(name)` across the whole repo, excluding its own definition line(s). `refs == 0` → **own-slop candidate**, labelled:
   - `REMOVABLE` — zero refs AND the symbol does **not** match an intended-entry-point heuristic (not a `Route::`/controller method, not a public Blade/Vue component, not in `app/Console`, not exported). The agent wrote it and nothing uses it → strip it.
   - `REVIEW` — zero refs BUT matches an entry-point pattern (could be a route/handler/command wired up later). Report, don't auto-strip.
4. Also flag, from the **added diff lines only** (not whole file): debug leftovers — `var_dump(`, `\bdd(`, `\bdump(`, `console\.log(`, `\bprint(` (python), `print_r(`, plus `TODO`/`FIXME`/`XXX`/`PLACEHOLDER`/`example` markers — labelled `DEBUG-LEFTOVER`. These are slop the agent should remove before "done".
5. Report-only output; the agent decides (own-diff removals are in scope per refined Principle 3).

**Mode `--liveness NAME…` (CLEANUP MODE, opt-in):**
1. `count_refs(name, root)` = grep across **all** text files (code + `.blade.php`/`.vue`/`.html`/`.twig` + `.json`/`.yaml`/`.yml`/`.env*` + `.sql` + `.md`), minus the definition occurrences. Default exclude = `DEFAULT_EXCLUDE` from `detect-clones.py` (vendor/node_modules/etc.).
2. Compute **framework false-positive flags** (`fp_flags`) — each is a *keep-alive veto*:
   - `route` — name appears in a `routes/` file or adjacent to `Route::`/`->name(`.
   - `blade_vue` — kebab/Pascal form of name used as `<x-name`/`<Name`/`<name-…` in a template.
   - `magic` — a public method whose name has an Eloquent-magic shape (`scope*`, accessor `get*Attribute`, relation-like) → reachable via `__call`/`__get`.
   - `di_config` — `Name::class` or `'Name'`/`"Name"` literal inside `config/` or a `.json`/`.yaml`.
   - `db_dispatch` — name literal appears in `database/migrations`/`database/seeders` or a `*.sql` (possibly a stored dispatch value).
   - `entrypoint` — defined under `app/Console`, a `Job`/`Listener`/`Observer`/webhook path, or a CLI/cron file.
   - `test_only` — the only references found are under `tests/`.
3. `classify_symbol`:
   - any non-FP references → **LIVE** (vetoed).
   - zero references AND any `fp_flag` set → **ASSERTED-DEAD** (looks dead, framework could reach it → keep, investigate).
   - zero references AND no `fp_flag` AND symbol is `private`/file-local/closed-world → **VERIFIED-DEAD-PRIVATE** (eligible for a human-approved deletion).
   - zero references AND no `fp_flag` AND public → **ASSERTED-DEAD** (public/open-world → needs a deprecation cycle before it could ever be removed).
4. **Never deletes.** Output is a table per symbol with the evidence (ref count, every fp_flag, classification) so the human can decide.

- [ ] **Step 1: Write the failing test for `classify_symbol`**

Create `code-guardian/tools/tests/test_detect_dead_code.py`:

```python
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "ddc", pathlib.Path(__file__).resolve().parents[1] / "detect-dead-code.py")
ddc = importlib.util.module_from_spec(spec); spec.loader.exec_module(ddc)

def test_any_reference_is_live():
    assert ddc.classify_symbol("foo", refs=3, fp_flags=set(), is_private=True) == "LIVE"

def test_zero_refs_with_fp_flag_is_asserted_dead():
    assert ddc.classify_symbol("scopeActive", refs=0, fp_flags={"magic"}, is_private=False) == "ASSERTED-DEAD"

def test_zero_refs_private_no_flags_is_verified_dead_private():
    assert ddc.classify_symbol("helperX", refs=0, fp_flags=set(), is_private=True) == "VERIFIED-DEAD-PRIVATE"

def test_zero_refs_public_no_flags_is_asserted_dead():
    # public/open-world is never auto-verifiable — external callers may exist
    assert ddc.classify_symbol("publicApi", refs=0, fp_flags=set(), is_private=False) == "ASSERTED-DEAD"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest code-guardian/tools/tests/test_detect_dead_code.py -v`
Expected: FAIL — `ModuleNotFoundError`/`AttributeError` (file/func not defined yet).

- [ ] **Step 3: Implement `detect-dead-code.py`**

Write the full tool. Reuse, verbatim where possible, from `detect-symbol-loss.py`: the module docstring header style, `EXT_LANG`/`CODE_EXTS`, `DEF_PATTERNS`, `KEYWORD_NAMES`, `read_file`, `git_show`, `git_changed_files`, and the `SUMMARY`-footer/exit-code reporting shape. Add:

```python
def classify_symbol(name, refs, fp_flags, is_private):
    """Liveness verdict. ANY reference => LIVE (veto). Absence never proves dead."""
    if refs > 0:
        return "LIVE"
    if fp_flags:
        return "ASSERTED-DEAD"      # framework-reachable; keep, investigate
    if is_private:
        return "VERIFIED-DEAD-PRIVATE"  # closed-world, no caller => deletable by a human
    return "ASSERTED-DEAD"          # public/open-world: needs deprecation cycle first
```

`extract_added_symbols(before, after)` = `set(extract_symbols(after)) - set(extract_symbols(before))` (where `extract_symbols` is copied from `detect-symbol-loss.py`). `count_refs(name, root, exclude_re)` walks all text files, counts whole-word `\bname\b` occurrences, subtracts definition matches. `fp_flags` computed by the heuristics in the Design section above (each a cheap regex over the candidate's file + repo grep). DEBUG-LEFTOVER detection scans only added diff lines (`git diff <ref> -- <path>` `^+` lines).

Two `argparse` modes (`--diff-slop`, `--liveness`) mirroring `detect-symbol-loss.py`'s `--git`/`--before/--after` structure. **No file writes anywhere in the tool.**

- [ ] **Step 4: Run the classify tests to verify they pass**

Run: `python3 -m pytest code-guardian/tools/tests/test_detect_dead_code.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Add an integration test for `--diff-slop` on a temp git repo**

Append to the test file a test that: inits a temp git repo, commits a file with `function used(){}` referenced elsewhere, then adds `function orphanHelper(){}` (referenced nowhere) + a `console.log("x")` line, runs `main(["--diff-slop"])` with cwd in the repo, and asserts `orphanHelper` is reported `REMOVABLE` and the `console.log` is `DEBUG-LEFTOVER`, exit code `1`.

```python
import subprocess, os, tempfile, contextlib
@contextlib.contextmanager
def _repo():
    d = tempfile.mkdtemp()
    run = lambda *a: subprocess.run(a, cwd=d, check=True, capture_output=True)
    run("git","init","-q"); run("git","config","user.email","t@t"); run("git","config","user.name","t")
    yield d, run

def test_diff_slop_flags_unused_addition_and_debug(capsys, monkeypatch):
    with _repo() as (d, run):
        (pathlib.Path(d)/"a.js").write_text("function used(){}\nused();\n")
        run("git","add","a.js"); run("git","commit","-qm","base")
        (pathlib.Path(d)/"a.js").write_text(
            "function used(){}\nused();\nfunction orphanHelper(){}\nconsole.log('x');\n")
        monkeypatch.chdir(d)
        rc = ddc.main(["--diff-slop"])
        out = capsys.readouterr().out
        assert "orphanHelper" in out and "REMOVABLE" in out
        assert "DEBUG-LEFTOVER" in out
        assert rc == 1
```

- [ ] **Step 6: Run the full tool test suite**

Run: `python3 -m pytest code-guardian/tools/tests/test_detect_dead_code.py -v`
Expected: PASS (all). Also smoke-run on this repo: `python3 code-guardian/tools/detect-dead-code.py --liveness extract_symbols --root code-guardian` → prints a classification table + `SUMMARY` line, exit 0/1.

- [ ] **Step 7: Commit**

```bash
git add code-guardian/tools/detect-dead-code.py code-guardian/tools/tests/test_detect_dead_code.py
git commit -m "feat(code-guardian): add detect-dead-code.py liveness aggregator (report-only, v11)"
```

---

## Task 2: Rule-of-Three guard in `detect-clones.py`

**Files:**
- Modify: `code-guardian/tools/detect-clones.py:207-306` (argparse + output loop)
- Test: `code-guardian/tools/tests/test_detect_clones_rule_of_three.py` (create)

**Interfaces:**
- Consumes: existing `detect-clones.py` CLI.
- Produces: new flag `--extract-threshold N` (default `3`); each flagged group's line gains a label `EXTRACT-CANDIDATE` (locs ≥ threshold) or `NOTE-ONLY` (locs < threshold); a one-line caution banner prints once when any `EXTRACT-CANDIDATE` exists.

- [ ] **Step 1: Write the failing test**

```python
import subprocess, sys, pathlib, tempfile
TOOL = pathlib.Path(__file__).resolve().parents[1] / "detect-clones.py"

def _run(root):
    return subprocess.run([sys.executable, str(TOOL), "--root", root, "--kind", "code",
                           "--cross-file-only"], capture_output=True, text=True)

def test_two_site_clone_is_note_only_three_is_extract_candidate():
    d = tempfile.mkdtemp()
    body = "function f(){\n  const a = compute(1);\n  const b = compute(2);\n  return a+b;\n}\n"
    for i in range(2):
        (pathlib.Path(d)/f"f{i}.js").write_text(body.replace("f(", f"f{i}("))
    out2 = _run(d).stdout
    assert "NOTE-ONLY" in out2 and "EXTRACT-CANDIDATE" not in out2
    (pathlib.Path(d)/"f2.js").write_text(body.replace("f(", "f2("))
    out3 = _run(d).stdout
    assert "EXTRACT-CANDIDATE" in out3
    assert "wrong abstraction" in out3.lower()  # caution banner
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m pytest code-guardian/tools/tests/test_detect_clones_rule_of_three.py -v`
Expected: FAIL — labels not present.

- [ ] **Step 3: Implement the guard**

Add to argparse (after `--cross-file-only`):
```python
    ap.add_argument("--extract-threshold", type=int, default=3,
                    help="min occurrences before a clone is an EXTRACT-CANDIDATE "
                         "(Rule of Three); fewer => NOTE-ONLY (default 3)")
```
In the human-format output loop, compute the label per group and print it on the group header line; before the loop, if any group meets the threshold, print once:
```python
    any_extract = any(len(locs) >= args.extract_threshold for _, locs in flagged)
    if flagged and not args.json and any_extract:
        print("# CAUTION: duplication is cheaper than the wrong abstraction. "
              "Extract only when the sites encode the SAME knowledge (one reason to change). "
              "NOTE-ONLY groups (<%d sites) are below the Rule of Three — leave them.\n"
              % args.extract_threshold)
```
Group header gains: `label = "EXTRACT-CANDIDATE" if len(locs) >= args.extract_threshold else "NOTE-ONLY"` appended to the existing `clone-group …` line.

- [ ] **Step 4: Run to verify it passes**

Run: `python3 -m pytest code-guardian/tools/tests/test_detect_clones_rule_of_three.py -v`
Expected: PASS.

- [ ] **Step 5: Regression-check existing behavior unchanged**

Run: `python3 code-guardian/tools/detect-clones.py --root code-guardian --kind code --cross-file-only`
Expected: still exits 0/1, `SUMMARY findings=… kind=code exit=…` footer intact (the existing R2 contract is preserved — only labels/banner added).

- [ ] **Step 6: Commit**

```bash
git add code-guardian/tools/detect-clones.py code-guardian/tools/tests/test_detect_clones_rule_of_three.py
git commit -m "feat(code-guardian): Rule-of-Three extract-threshold + wrong-abstraction caution in detect-clones (v11)"
```

---

## Task 3: `references/cleanup-mode.md` — the opt-in CLEANUP MODE protocol

**Files:**
- Create: `code-guardian/references/cleanup-mode.md`

**Interfaces:**
- Consumes: `detect-dead-code.py --liveness` (Task 1), `detect-clones.py --extract-threshold` (Task 2).
- Produces: the `CLEANUP MODE` protocol referenced by `SKILL.md` (Task 5).

- [ ] **Step 1: Write the file**

Create `code-guardian/references/cleanup-mode.md` with exactly this content:

````markdown
# CLEANUP MODE — full protocol (opt-in, report-only)

> Loaded ONLY when the user explicitly asks to clean up / remove dead / orphaned / unused / redundant code in EXISTING code (not the current task's own output — that is the always-on Self-Slop Sweep in `build-mode.md` Step 3, Layer 6). The router lives in `SKILL.md`. Operating Principles govern every step. **This mode never deletes. It produces a classified report; the human makes every deletion decision.**

## The one law

**Any single positive signal proves a symbol is LIVE and vetoes its removal. Absence of references never proves it is DEAD.** Static "unused" output is a *candidate*, never a verdict — every dead-code tool's own maintainers say so. In dynamic stacks (PHP magic/Eloquent/Blade, Vue templates/auto-imports, Python decorators) false positives are the norm; bias hard toward KEEP.

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
python3 ~/.claude/skills/code-guardian/tools/detect-dead-code.py --liveness <Name> [<Name> ...] --root .
```

## Step 2 — Liveness-veto classification

The aggregator emits one verdict per symbol. Reconcile every candidate to one of:

- **LIVE** — ≥1 real reference, OR any framework false-positive flag fired (route target · Blade/Vue component · Eloquent magic (`scope*`/accessor/relation) · DI/config class-string · DB-driven dispatch value · CLI/cron/webhook/queue entry point · public library export · test-only usage). → **KEEP. Remove from the report or list as "looked dead, is live (vampire)".**
- **ASSERTED-DEAD** — zero static references but the symbol is public/open-world OR a FP flag fired. → **KEEP; recommend deprecate-before-delete** (mark `@deprecated`, block new uses, observe a full business cycle, *then* a human may remove). Never delete now.
- **VERIFIED-DEAD-PRIVATE** — zero references AND closed-world (private/file-local) AND no FP flag AND no live side effects. → **the only class eligible for removal — and even then the skill only RECOMMENDS it; the human deletes.**

When unsure between ASSERTED and VERIFIED → choose ASSERTED (under-claiming death is the safe error).

## Step 3 — Cross-check every candidate against ALL file types

Static graphs miss string-resolved references. Before any symbol stays VERIFIED-DEAD-PRIVATE, grep the whole tree (the aggregator does this, but spot-verify the surprising ones):

```bash
grep -rn "\b<Name>\b" --include="*.php" --include="*.js" --include="*.ts" --include="*.vue" \
  --include="*.blade.php" --include="*.json" --include="*.yaml" --include="*.yml" \
  --include="*.sql" --include="*.env*" . | grep -v vendor | grep -v node_modules
```
Any hit outside the definition → reclassify LIVE.

## Step 4 — Redundancy (counter-rule: duplication is cheaper than the wrong abstraction)

For redundant/duplicated code, run the existing R2/R3/R5 clone detectors with the Rule-of-Three guard:

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
  🟢 <Class::method>  — 0 refs (AST+grep-all-filetypes) · no FP flag · private   Verified-by: <detect-dead-code SUMMARY + grep output>
ASSERTED-DEAD (KEEP — deprecate-before-delete, observe a business cycle):
  🟡 <name>  — 0 static refs BUT public/open-world (external callers may exist)   Verified-by: <output>
LIVE / vampire (KEEP — looked dead, is reachable):
  ⚪ <name>  — reached via <route|Blade|magic|DI|DB-dispatch|cron|test>           Verified-by: <fp flag + grep hit>
Redundancy:
  🟡 EXTRACT-CANDIDATE <hash> (≥3 sites, same knowledge) → extract to <target>
  ⚪ NOTE-ONLY <hash> (2 sites / coincidental) → leave
N verified-dead-private · M asserted-dead (kept) · K live (kept) → ALL DELETIONS DEFERRED TO HUMAN
```

If the human then asks to act on a VERIFIED-DEAD-PRIVATE candidate: remove one symbol per commit, `git`-recoverable, with a commit message recording the checked signals, run the build + full test suite green after each, and re-run BUILD MODE Step 2 (symbol-loss gate) + the audit on the deletion diff — a removal is a code change like any other.
````

- [ ] **Step 2: Verify structure**

Run: `grep -c "report-only\|VERIFIED-DEAD-PRIVATE\|liveness\|duplication is cheaper" code-guardian/references/cleanup-mode.md`
Expected: ≥ 4 (all key concepts present).

- [ ] **Step 3: Commit**

```bash
git add code-guardian/references/cleanup-mode.md
git commit -m "feat(code-guardian): add opt-in report-only CLEANUP MODE protocol (v11)"
```

---

## Task 4: Self-Slop Sweep layer in `build-mode.md`

**Files:**
- Modify: `code-guardian/references/build-mode.md` — Step 3 audit section (the five-layer block around line 178-194) and the triage table (line 165-172).

**Interfaces:**
- Consumes: `detect-dead-code.py --diff-slop` (Task 1).
- Produces: Layer 6 "Self-Slop Sweep" referenced by `SKILL.md` BUILD skeleton (Task 5).

- [ ] **Step 1: Add the Self-Slop Sweep layer**

In `code-guardian/references/build-mode.md`, in Step 3d's layer list, after the `Security` bullet, add a new layer:

```markdown
- **Self-Slop Sweep (always-on, diff-only — the agent cleans up after ITSELF).** Strip the AI-slop *this change* introduced; scope is the current diff, never pre-existing code (that is opt-in CLEANUP MODE — `references/cleanup-mode.md`). Run:
  ```bash
  python3 ~/.claude/skills/code-guardian/tools/detect-dead-code.py --diff-slop
  ```
  Act on each label: **REMOVABLE** (a symbol you added with zero references anywhere) → remove it; **DEBUG-LEFTOVER** (`var_dump`/`dd`/`dump`/`console.log`/`print`/`print_r`, or `TODO`/`FIXME`/`PLACEHOLDER`/`example` you just added) → remove it; **REVIEW** (added, currently unreferenced, but matches a route/handler/command/component entry-point pattern) → keep, it is likely wired up next. Plus, by reading (not the tool): redundant comments that merely restate the code → delete; a single-use abstraction you just invented (interface/factory/wrapper with exactly one caller) → inline it (YAGNI / Rule of Three); a helper you wrote that duplicates an existing one your 1c.2 pre-flight grep should have found → reuse the existing one; any *new* dependency/import → confirm the package actually exists (anti-slopsquatting). This layer removes ONLY your own just-written additions; if removal would touch anything present before this diff, stop and report instead. **Verified-by**: paste the `--diff-slop` `SUMMARY findings=… exit=…` footer.
```

- [ ] **Step 2: Add the triage row**

In the Step 3a triage table, add a sentence under it (after line 172):
```markdown
The Self-Slop Sweep runs at EVERY intensity including LIGHT — it is cheap (one diff scan) and slop hides in small diffs too. It only ever inspects the current diff.
```

- [ ] **Step 3: Verify**

Run: `grep -n "Self-Slop Sweep\|--diff-slop\|REMOVABLE\|DEBUG-LEFTOVER" code-guardian/references/build-mode.md`
Expected: ≥ 4 matches across the new layer + triage note.

- [ ] **Step 4: Commit**

```bash
git add code-guardian/references/build-mode.md
git commit -m "feat(code-guardian): add always-on Self-Slop Sweep audit layer (v11)"
```

---

## Task 5: `SKILL.md` — router, principle, frontmatter, version

**Files:**
- Modify: `code-guardian/SKILL.md` (frontmatter, Principle 3, Mode Selection, Reference table, BUILD skeleton, new CLEANUP skeleton, Core Rules, version).

**Interfaces:**
- Consumes: `references/cleanup-mode.md` (Task 3), Self-Slop layer in `build-mode.md` (Task 4).

- [ ] **Step 1: Bump the version heading**

`code-guardian/SKILL.md:22` — change `# Code Guardian (v10)` → `# Code Guardian (v11)`.

- [ ] **Step 2: Refine Operating Principle 3 (scope-split)**

Replace the Principle 3 line (`code-guardian/SKILL.md:30`) with:
```markdown
3. **Stay in scope — with one carve-out for your own mess.** Findings in code that existed *before this change* are *reported*, never silently fixed or deleted — no refactoring, tidying, or new abstractions beyond the task; a bug fix doesn't need surrounding cleanup. The one exception: AI-slop *this change itself* introduced (unused symbols/imports you just added, debug leftovers, redundant comments, single-use abstractions you just invented) IS in scope — strip it before "done" (the always-on Self-Slop Sweep, `references/build-mode.md` Step 3). Cleaning up pre-existing dead/orphaned/redundant code is a separate, opt-in, **report-only** path (CLEANUP MODE) that never deletes on its own.
```

- [ ] **Step 3: Add CLEANUP MODE to the Mode Selection router**

`code-guardian/SKILL.md:36-43` — extend the diagram:
```markdown
Task received
  ├─ Bug/Error/Broken? ──────→ DEBUG MODE
  ├─ Spec/Plan exists? ──────→ PLAN MODE (review plan before implementation)
  ├─ Explicit "clean up / remove dead/unused/redundant EXISTING code"? ──→ CLEANUP MODE (opt-in, report-only)
  └─ Build/Change/Fix?  ─────→ BUILD MODE
                              ├─ Pre-Flight (BEFORE code)
                              └─ Audit (AFTER code, incl. always-on Self-Slop Sweep on the diff)
```

- [ ] **Step 4: Add the reference-table row**

In the Reference Files table (`code-guardian/SKILL.md:51-58`), add after the `debug-mode.md` row:
```markdown
| `references/cleanup-mode.md` | opt-in report-only dead/orphaned/redundant-code protocol: liveness-veto gate, framework FP-category gate, per-language detectors, redundancy counter-rule | CLEANUP MODE selected (explicit cleanup request only) |
```

- [ ] **Step 5: Add the CLEANUP MODE skeleton section**

After the DEBUG MODE section (`code-guardian/SKILL.md:104`, before `## Self-Tuning`), insert:
```markdown
---

## CLEANUP MODE

Explicit request to clean up / remove dead / orphaned / unused / redundant **existing** code (NOT the current task's own output — that is the always-on Self-Slop Sweep in BUILD MODE). **Read `references/cleanup-mode.md`** and run the report-only protocol:

1. **Inventory** candidates with whatever per-language detectors are installed (knip/ts-prune · vulture/ruff · phpstan/psalm/shipmonk) — candidate lists, never verdicts.
2. **Classify** every candidate via `detect-dead-code.py --liveness` into LIVE / ASSERTED-DEAD / VERIFIED-DEAD-PRIVATE under the liveness-veto law (any positive signal → KEEP).
3. **Cross-check** survivors against ALL file types (templates/config/JSON/SQL/i18n) — string-resolved references defeat static graphs.
4. **Redundancy** via R2/R3/R5 with the Rule-of-Three guard; extract only same-knowledge ≥3-site clones, never build the wrong abstraction.
5. **Report only.** Emit a classified report; the skill never deletes. The human decides every removal; if asked to act, one symbol per commit, git-recoverable, tests green, re-audited.

Core invariant: **any single positive signal proves LIVE and vetoes removal; absence of references never proves dead.** Full protocol: `references/cleanup-mode.md`.
```

- [ ] **Step 6: Note Self-Slop in the BUILD MODE skeleton**

In the SKILL.md BUILD MODE Step 3 bullet (`code-guardian/SKILL.md:86`), change the layer list `→ 5 layers (DB · Logic · Efficiency · Redundancy R1–R5 · Security)` to `→ 6 layers (DB · Logic · Efficiency · Redundancy R1–R5 · Security · Self-Slop Sweep [always-on, diff-only])`.

- [ ] **Step 7: Add the redundancy counter-rule to Core Rules**

In `## Core Rules` (`code-guardian/SKILL.md:113-119`), add a bullet:
```markdown
- **Duplication is cheaper than the wrong abstraction.** Never extract a shared abstraction to kill duplication unless ≥3 sites (Rule of Three) AND they encode the same knowledge (one reason to change). Cleaning slop must not create slop.
```

- [ ] **Step 8: Extend the frontmatter triggers**

In the frontmatter `description` (`code-guardian/SKILL.md:3-19`), add one line before the ANTI-RATIONALIZATION block:
```markdown
  Use when (opt-in CLEANUP MODE): "clean up", "räum auf", "aufräumen", "dead code", "toten Code",
  "unused", "ungenutzt", "orphan", "verwaist", "redundant", "remove duplicates" — report-only, never deletes productive code.
```

- [ ] **Step 9: Verify all markers present**

Run:
```bash
grep -n "Code Guardian (v11)\|CLEANUP MODE\|Self-Slop Sweep\|cleanup-mode.md\|wrong abstraction" code-guardian/SKILL.md
```
Expected: all five present.

- [ ] **Step 10: Commit**

```bash
git add code-guardian/SKILL.md
git commit -m "feat(code-guardian): v11 router — CLEANUP MODE + Self-Slop + scope-split Principle 3"
```

---

## Task 6: `design-rationale.md` — v11 entry

**Files:**
- Modify: `code-guardian/references/design-rationale.md` (append after the v10.1 section, end of file).

- [ ] **Step 1: Append the rationale**

Add at the end of `code-guardian/references/design-rationale.md`:
```markdown
### v11 Cleanup & Anti-Slop Rules (born from "AI agents leave dead scaffolding and slop behind")

- **Own slop vs. pre-existing dead code are two problems with opposite risk — split them.** Code the agent just wrote and never wired up is safe to strip (Self-Slop Sweep, always-on, diff-only). Foreign pre-existing code is dangerous; cleaning it is opt-in and **report-only** (CLEANUP MODE) — the skill classifies, the human deletes. The boundary between the two is the git diff. Principle 3's carve-out encodes exactly this: your own mess is in scope, everyone else's is reported.
- **The liveness asymmetry is the safety guarantee.** Any single positive signal (a static ref, a template/config/route/DI/DB-dispatch/i18n hit, a coverage hit) proves LIVE and vetoes removal; absence of references never proves dead. Static "unused" output is a candidate, never a verdict — this is why even VERIFIED-DEAD-PRIVATE is only ever *recommended*, never auto-deleted.
- **Closed-world is the confidence line.** Private/file-local symbols can reach VERIFIED-DEAD-PRIVATE; public/open-world symbols are always ASSERTED-DEAD (external callers unprovable) and require a deprecate-before-delete cycle. Framework false-positive categories (Eloquent magic, Blade/Vue auto-discovery, routes, DI strings, DB-driven dispatch, CLI/cron/webhook entry points, reflection) each veto deletion.
- **Cleaning slop must not create slop.** The redundancy counter-rule (Rule of Three + same-knowledge) is non-negotiable: duplication is cheaper than the wrong abstraction (Metz). Two clones never justify an abstraction; near-miss clones are never fused with a flag+conditional.
- **`detect-dead-code.py` is an evidence aggregator, not a deleter.** Like every Code Guardian tool it is dependency-free, emits a `SUMMARY` footer, and — critically — never writes to a source file. It corroborates multiple signals and classifies; it cannot remove code.
```

- [ ] **Step 2: Verify & commit**

Run: `grep -c "v11\|liveness asymmetry\|report-only" code-guardian/references/design-rationale.md` (expect ≥ 3)
```bash
git add code-guardian/references/design-rationale.md
git commit -m "docs(code-guardian): v11 design rationale (scope-split, liveness asymmetry)"
```

---

## Task 7: `install.sh` — v11 markers & tool check

**Files:**
- Modify: `install.sh:50-52` (tool-existence loop) and `install.sh:105-119` (version-marker block).

- [ ] **Step 1: Add the new tool to the source-existence loop**

`install.sh:50` — change:
```bash
for tool in detect-clones.py detect-config-leaks.sh detect-secrets.sh; do
```
to:
```bash
for tool in detect-clones.py detect-config-leaks.sh detect-secrets.sh detect-symbol-loss.py detect-dead-code.py; do
```

- [ ] **Step 2: Update version markers v10 → v11 and add new ones**

`install.sh:105-119` — change the comment to `v11`, change the `grep -q "Code Guardian (v10)"` to `(v11)`, and add three markers + the tool file check:
```bash
    grep -q "Code Guardian (v11)"              "$TARGET_DIR/SKILL.md" || missing+=("Code Guardian (v11)")
    grep -q "CLEANUP MODE"                     "$TARGET_DIR/SKILL.md" || missing+=("CLEANUP MODE")
    grep -q "Self-Slop Sweep"                  "$TARGET_DIR/SKILL.md" || missing+=("Self-Slop Sweep")
    [ -f "$TARGET_DIR/tools/detect-dead-code.py" ] || missing+=("tools/detect-dead-code.py")
```
and update the success line `ok "v10 markers …"` → `ok "v11 markers …"`.

- [ ] **Step 3: Verify the installer end-to-end (dry run + real)**

Run: `./install.sh --dry-run` → no errors, exit 0.
Run: `./install.sh` then re-read output → `[ok] v11 markers + symbol-loss gate detected` and `tools/ installed (5 helper script(s))` (now 5 with `detect-dead-code.py`).

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "build(code-guardian): installer v11 markers + detect-dead-code.py check"
```

---

## Task 8: `README.md` — document the new capabilities

**Files:**
- Modify: `README.md` (feature list / modes section).

- [ ] **Step 1: Add the two capabilities to the README**

Read `README.md`, locate the feature/mode list, and add concise entries: (a) **Self-Slop Sweep** — every code change auto-strips the agent's own AI-slop (unused additions, debug leftovers, redundant comments, single-use abstractions) from the diff; (b) **CLEANUP MODE (opt-in, report-only)** — on explicit request, classifies pre-existing dead/orphaned/redundant code as LIVE / ASSERTED-DEAD / VERIFIED-DEAD-PRIVATE under a liveness-veto gate and reports it for human decision — never deletes productive code. Mention `detect-dead-code.py` alongside the other helper tools.

- [ ] **Step 2: Verify & commit**

Run: `grep -c "Self-Slop\|CLEANUP MODE\|detect-dead-code" README.md` (expect ≥ 3)
```bash
git add README.md
git commit -m "docs: document Self-Slop Sweep + report-only CLEANUP MODE (v11)"
```

---

## Self-Review

**Spec coverage** — user's four asks mapped to tasks:
- "räumt Code auf während des Programmierens" → Task 4 (Self-Slop Sweep, always-on in BUILD) + Task 1 `--diff-slop`.
- "verwaisten alten Code erkennt und bereinigt" → Task 3 (CLEANUP MODE) + Task 1 `--liveness`. Report-only per the user's decision — detect & report, human deletes.
- "darf keinen produktiven Code löschen, 100% sicher" → Global Constraints (liveness asymmetry, report-only, VERIFIED-DEAD-PRIVATE only ever recommended) + Task 1 `classify_symbol` + Task 3 FP-category gate.
- "AI Slop gelöst" → Task 1 DEBUG-LEFTOVER + REMOVABLE detection, Task 4 layer (redundant comments, single-use abstraction, re-implementation, hallucinated deps).
- "redundanter Code" → Task 2 (Rule-of-Three guard) + Task 3 Step 4 (counter-rule) + existing R2/R3/R5.

**Placeholder scan** — Task 8 Step 1 is the only descriptive (non-verbatim) step, because the README's exact current structure must be read first; its target content + verification grep are specified. All rule/protocol text (the judgment-bearing parts the user must approve) is verbatim. Tool behavior is pinned by complete test code (Tasks 1–2).

**Type consistency** — `classify_symbol(name, refs, fp_flags, is_private) -> {"LIVE"|"ASSERTED-DEAD"|"VERIFIED-DEAD-PRIVATE"}` used identically in Task 1 tests, Task 3 report classes, Task 5 skeleton, Task 6 rationale. `--diff-slop` labels `REMOVABLE`/`REVIEW`/`DEBUG-LEFTOVER` consistent across Tasks 1 & 4. `--extract-threshold`/`EXTRACT-CANDIDATE`/`NOTE-ONLY` consistent across Tasks 2 & 3.

## Open question for approval

One thing to confirm before implementation: **should the Self-Slop Sweep actually remove the agent's own `REMOVABLE`/`DEBUG-LEFTOVER` findings, or also only report them?** This plan has it *remove* them (they are the agent's own just-written, zero-reference additions — that is the "clean up while coding" the user asked for, and it cannot touch pre-existing code). If you'd rather it report even those and never auto-edit, say so and I'll change Task 4 to report-only across the board.
