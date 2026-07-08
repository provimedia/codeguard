# Code Guardian v14 — DEPLOY GATE Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Orthogonal DEPLOY GATE that classifies every file before transfer to an external server (DEPLOY / SERVER-ONLY / NEVER-ON-SERVER / REVIEW), fixes excludes durably, retro-checks the live server, and removes leftovers after one user approval — enforced by a PreToolUse hook.

**Architecture:** v12 DECISION GATE pattern: small router section in `SKILL.md` + full protocol in `references/deploy-gate.md` + dependency-free report-only classifier tool + deterministic Bash-matching hook + installer/package lockstep (v14 markers).

**Tech Stack:** Python 3 stdlib only (tool), Bash + jq fail-open (hook), pytest dual-mode tests.

## Global Constraints

- Tools are dependency-free (stdlib only), report-only (no write path), end with a `SUMMARY … exit=…` footer; exit 0 = clean, 1 = findings, 2 = usage error.
- Hooks fail OPEN without `jq`; deny feedback goes through `hookSpecificOutput.permissionDecisionReason` (plain stdout is invisible to the model).
- Pattern catalogs are DATA tables in the tool, never if-chains (P7/Generalization).
- User-facing docs (UPDATE-ANLEITUNG, README additions) in German; skill files in English.
- v13 → v14 in lockstep: SKILL.md title + frontmatter + core rule, install.sh markers, README, UPDATE-ANLEITUNG, design-rationale.
- rsync commands containing `--dry-run`/`-n` are the gate's own D1 probe — the hook must NEVER block them.

## File Structure

- Create: `code-guardian/tools/detect-deploy-artifacts.py` — classifier (all intelligence as data tables)
- Create: `code-guardian/tools/tests/test_detect_deploy_artifacts.py` — dual-mode unit tests
- Create: `test/deploy/` — planted fixture tree + fake rsync itemize list + oracle README
- Create: `code-guardian/references/deploy-gate.md` — D1–D4 protocol
- Create: `hooks/deploy-gate-check.sh` — PreToolUse(Bash) enforcement
- Modify: `code-guardian/SKILL.md` — frontmatter triggers, DEPLOY GATE section, reference row, core rule, v14 title
- Modify: `install.sh` — hook #4, tool existence check, v14 markers
- Modify: `code-guardian/references/design-rationale.md` — v14 entry
- Modify: `README.md`, `UPDATE-ANLEITUNG.md` — v14 docs
- Rebuild: `~/Desktop/code-guardian-v14-update.zip` (WITHOUT `.pytest_cache`/`__pycache__`/`.DS_Store` — the v13 zip itself contained pytest cache: eat our own dogfood)

---

### Task 1: Classifier tool `detect-deploy-artifacts.py` (TDD)

**Files:**
- Create: `code-guardian/tools/detect-deploy-artifacts.py`
- Test: `code-guardian/tools/tests/test_detect_deploy_artifacts.py`
- Create: `test/deploy/project/…` fixture tree + `test/deploy/rsync-list.txt` + `test/deploy/README.md`

**Interfaces (Produces):**
- CLI: `detect-deploy-artifacts.py (--root DIR | --list FILE) [--config FILE]`
- `--root DIR`: inventory mode — walk tree, report every SERVER-ONLY / NEVER-ON-SERVER / REVIEW path (DEPLOY is silent default).
- `--list FILE`: transfer-list mode — classify one path per line; accepts plain paths AND rsync `--itemize-changes` lines (`>f+++++++++ path`, `cd+++++++++ dir/`; `deleting …` lines are skipped); `-` reads stdin.
- `--config FILE`: minimal YAML-lite (`key: value`, `- item` lists; no PyYAML): keys `docroot_url`, `ssh`, `extra_never`, `extra_server_only`, `allow` (entries `pattern: reason` — documented exceptions, reported as `ALLOWED`, never counted).
- Output lines: `NEVER[high|low] <path> — <reason>` · `SERVER-ONLY <path> — <reason>` · `REVIEW <path> — <reason>` · `ALLOWED <path> — <reason>`; footer `SUMMARY deploy=… server-only=… never=… review=… exit=…`.
- Classification is longest/most-specific match over DATA tables: `SERVER_ONLY_PATTERNS`, `NEVER_PATTERNS_HIGH`, `NEVER_PATTERNS_LOW`, `REVIEW_PATTERNS` (dir-name, glob, and exact-basename entries, each with reason). Default class: DEPLOY.
- Catalog (locked): SERVER-ONLY = `.env*` (except `.env.example`, `.env.dist` → DEPLOY), `storage/`, `*.sqlite`/`*.sqlite3`, `*.pem`, `*.key`, `*.crt`, `id_rsa*`, `uploads/`. NEVER[high] = `tests/`, `test/`, `__tests__/`, `spec/`, `cypress/`, `playwright/`, `docs/`, `doc/`, `.git/`, `.github/`, `.gitlab/`, `.gitlab-ci.yml`, `*.sql`, `*.dump`, `*.bak`, `*.orig`, `phpunit.xml*`, `.phpunit.result.cache`, backup archives (`*backup*.tar.gz|zip`, `*.tar.gz` at root), `.audit-log.md`, `.code-guardian-*.md`, `.code-guardian-*.yml`, `.claude/`, `__pycache__/`, `.pytest_cache/`, `*.log`. NEVER[low] = `.DS_Store`, `Thumbs.db`, `.idea/`, `.vscode/`, `.editorconfig`, `.eslintrc*`, `.prettierrc*`, `phpstan.neon*`, `psalm.xml`, `.php-cs-fixer*`, `jest.config.*`, `vitest.config.*`, `cypress.config.*`, `docker-compose*`, `Dockerfile*`, `Makefile`, `webpack.mix.js`, `vite.config.*`, `*.md` (root-level READMEs etc.), `.gitignore`, `.gitattributes`, `*.swp`. REVIEW = `node_modules/`, `database/seeders/`/`seeders/`/`seeds/`, `.env.example`? no → DEPLOY; `bin/`? no. `vendor/` = DEPLOY (shared-hosting reality).

- [ ] **Step 1:** Write failing tests covering: path classification for every catalog class (via `--list` with a written temp list incl. `.git/config`), `.env` vs `.env.example` split, rsync itemize parsing (prefix stripped, `deleting` skipped), tree inventory on the fixture, config overrides (`extra_never`, `allow` suppression), exit codes (clean list → 0, trap list → 1, bad usage → 2), SUMMARY footer format, and "tool has no write path" (source contains no `open(..., 'w')` on scanned files — mirror of the v11 dead-code guarantee: assert scanned tree is byte-identical after run).
- [ ] **Step 2:** `python3 -m pytest code-guardian/tools/tests/test_detect_deploy_artifacts.py -q` → all FAIL (tool missing).
- [ ] **Step 3:** Implement the tool (argparse, data tables with reasons, classify(), rsync-line parser, YAML-lite reader, SUMMARY).
- [ ] **Step 4:** Tests green; then FULL suite `python3 -m pytest code-guardian/tools/tests -q` green.
- [ ] **Step 5:** Build `test/deploy/` fixture tree (planted traps per spec Validation section; `.git/` only via list, not on disk) and validate: `--root test/deploy/project` flags every trap, 0 findings on clean app files; paste SUMMARY into commit message.
- [ ] **Step 6:** Commit `feat(code-guardian): detect-deploy-artifacts.py classifier + deploy fixture (v14)`.

### Task 2: `references/deploy-gate.md` — D1–D4 protocol

**Files:** Create `code-guardian/references/deploy-gate.md`

**Content contract (from spec):** The Law (4 classes, table), When-it-fires list (deploy.sh, rsync/scp/sftp/ftp/lftp remote, git push prod/production/live, "live stellen"…), D1 manifest check (rsync `--dry-run --itemize-changes` as ground truth piped to `--list -`; other channels → `--root` minus mechanism excludes; BLOCKED on SERVER-ONLY or NEVER[high] in transfer list, 🟡 on NEVER[low]), D2 durable exclude fix (edit deploy.sh exclude list / `.deployignore`, commit it; never one-off flags), D3 server retro-check (HTTP probe table with expected 403/404: `/.env`, `/.git/config`, `/.git/HEAD`, `/phpunit.xml`, `/tests/`, `/docs/`, `/storage/logs/laravel.log`, `/dump.sql`, `/.audit-log.md`, `/.DS_Store`; SSH `find` command with NEVER pattern set; SERVER-ONLY reachable over HTTP = 🔴 fix webserver, never delete), D4 removal protocol (classified list → ONE user approval → remove via ssh/ftp → re-probe VERIFIED; SERVER-ONLY exempt by law), report artifact `.code-guardian-deploy-report.md` (template with `DEPLOY GATE: APPROVED|BLOCKED` line — consumed by the hook, ephemeral, itself class NEVER + gitignored), degradation rules ("⚠️ Server unchecked"), `.code-guardian-deploy.yml` reference.

- [ ] **Step 1:** Write the reference file (≈120–150 lines, same voice as decision-gate.md).
- [ ] **Step 2:** Commit `feat(code-guardian): deploy-gate reference — D1-D4 protocol (v14)`.

### Task 3: SKILL.md wiring (v14)

**Files:** Modify `code-guardian/SKILL.md`

- [ ] **Step 1:** Frontmatter: add DEPLOY GATE trigger block (deploy, deployen, rsync, scp, ftp, hochladen, "live stellen", "auf den Server", publish, release, go-live).
- [ ] **Step 2:** Title → `# Code Guardian (v14)`; Mode-Selection note "DECISION GATE and DEPLOY GATE are orthogonal"; reference-table row for `references/deploy-gate.md`; new `## DEPLOY GATE` section (router skeleton: law + D1–D4 one-liners + tool + report artifact + "Read references/deploy-gate.md"); Core Rules: add "Nothing reaches a server unclassified…" rule.
- [ ] **Step 3:** Commit `feat(code-guardian): v14 DEPLOY GATE — SKILL.md router wiring`.

### Task 4: Hook `deploy-gate-check.sh`

**Files:** Create `hooks/deploy-gate-check.sh`

**Logic (locked):** fail-open without jq → read stdin JSON → `.tool_input.command` → NOT a deploy command → exit 0. Deploy detection (ERE): rsync with remote spec (`(^|[;&| ])rsync[^;&|]*([A-Za-z0-9._-]+@)?[A-Za-z0-9._%+-]+:[^ ]`), but exit 0 if `--dry-run` or ` -n ` present; `scp|sftp` with `:`; `lftp|ftp `; `(^|[ /;&|])(bash )?deploy[^ ]*\.sh`; `git push +(prod|production|live)\b`. If deploy: look for `${CLAUDE_PROJECT_DIR:-$PWD}/.code-guardian-deploy-report.md` (fallback: git rev-parse toplevel); require line `DEPLOY GATE: APPROVED` AND mtime < 1800 s (portable `stat -f %m` || `stat -c %Y`). Fresh+approved → exit 0; else deny JSON (German reason: run DEPLOY GATE per references/deploy-gate.md D1–D2, write report, re-run command).

- [ ] **Step 1:** Write hook.
- [ ] **Step 2:** Manual matrix test with `echo '{"tool_input":{"command":"…"}}' | hooks/deploy-gate-check.sh`: remote rsync → deny; rsync `--dry-run` → allow; LOCAL rsync (no colon) → allow; `./deploy.sh` → deny; `git push origin main` → allow; `git push production main` → deny; then create fresh APPROVED report in a temp dir → allow; stale (touch -t old) → deny. Paste matrix output.
- [ ] **Step 3:** Commit `feat(hooks): deploy-gate-check.sh — deterministic DEPLOY GATE enforcement (v14)`.

### Task 5: Installer + docs + rationale (v14 lockstep)

**Files:** Modify `install.sh`, `README.md`, `UPDATE-ANLEITUNG.md`, `code-guardian/references/design-rationale.md`

- [ ] **Step 1:** install.sh: add `detect-deploy-artifacts.py` to tool existence loop; add `deploy-gate-check.sh` to hook sanity list, copy loop, and `wanted` merge table (`("PreToolUse", "Bash", "deploy-gate-check.sh")`); version markers → `Code Guardian (v14)` + `DEPLOY GATE` + tool file check; header text “four session hooks”; next-steps text.
- [ ] **Step 2:** `./install.sh --dry-run` → OK lines, no die.
- [ ] **Step 3:** UPDATE-ANLEITUNG: retitle v14, add "### v14 — Deploy Gate" section (German, what/why/how), Schritt-3 checks updated (10 references, 7 tools, 4 hooks, hook function test). README: v14 section analog to v12/v13 entries. design-rationale.md: v14 entry (anchoring rationale, 4-class law incl. SERVER-ONLY delete-exemption, one-approval removal, dry-run carve-out, lockstep markers).
- [ ] **Step 4:** Commit `feat(installer): register deploy-gate hook + v14 markers & docs`.

### Task 6: Verification + package

- [ ] **Step 1:** Full pytest suite green; fixture validation re-run; `bash -n` on both new/changed shell files; BUILD-MODE audit on the whole diff (symbol-loss gate, Self-Slop Sweep incl. `detect-hardcoded-cases.py --git`, R1–R5) → append `.audit-log.md`.
- [ ] **Step 2:** `./install.sh` (real run) locally; verify markers + 4 hooks in `~/.claude/settings.json`; verify `/hooks`-relevant files executable.
- [ ] **Step 3:** Build zip: `cd repo && zip -r ~/Desktop/code-guardian-v14-update.zip UPDATE-ANLEITUNG.md install.sh README.md code-guardian hooks llm-council -x '*.DS_Store' -x '*__pycache__*' -x '*.pytest_cache*'`; verify with `unzip -l` (no cache/DS_Store entries); smoke-test: unzip to scratchpad, `./install.sh --dry-run` from there.
- [ ] **Step 4:** Final commit + report.

## Self-Review

Spec coverage: 4-class law → T1 catalog; D1–D4 → T2; orthogonal anchoring + triggers → T3; hook → T4; installer/zip/docs → T5/T6; degradation + report artifact → T2/T4; fixture validation → T1/T6. Types/names consistent: `detect-deploy-artifacts.py`, `.code-guardian-deploy-report.md`, `.code-guardian-deploy.yml`, marker `DEPLOY GATE: APPROVED` used identically in T1/T2/T4. No placeholders.

## Plan Audit (Code Guardian PLAN MODE)
P1 Cross-Layer Trace: PASS — no new DB field/serializer (grep column|serializer → 0)
P2 Scale Verification: PASS — no DB iteration in scope (grep → 0)
P3 Secrets Hygiene: PASS — no API calls; grep '?key=|?api_key=|?token=' → 0
P4 Cached-Config Safety: PASS — no env reads; config via .code-guardian-deploy.yml file (grep getenv|env( → 0)
P5 Pattern Source Quality: PASS — sources are v12 decision-gate-check.sh + v13 tool conventions, both shipped through their own audits; inherited fail-open-without-jq is intentional and documented
P6 WIP Staging Discipline: PASS — tree clean at start; every task commits explicit paths, no `git add .`
P7 Generalization: PASS — pattern catalog is DATA tables with reasons; no requirement literal in control flow (grep if (\$|switch ( → 0)
