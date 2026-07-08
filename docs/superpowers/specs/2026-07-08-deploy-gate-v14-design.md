# Code Guardian v14 — DEPLOY GATE (Deploy-Artifact Hygiene) — Design

**Date:** 2026-07-08 · **Status:** Approved (user, 3× "(Empfohlen)" accepted) · **Scope:** skill rules + classifier tool + hook + fixture + package

## Problem

No Code Guardian check looks at the deploy step itself. P3/R1/R4 catch secrets in
*code*, but nothing verifies WHICH FILES travel to an external server (rsync/scp/
ftp/deploy.sh) or what already sits there wrongly: tests, docs, `*.sql` dumps,
`.audit-log.md`, `.DS_Store`, `.git`, CI configs — and nothing ensures leftovers
get removed. Classic production leaks (`/.env` readable, `/phpunit.xml`, dump
files in the docroot) ship silently through green audits.

## Decision

- **Anchoring: orthogonal DEPLOY GATE** (v12 DECISION GATE precedent, NOT a fifth
  mode and NOT a BUILD-audit layer): fires in ANY mode — and outside them — the
  moment a deploy action to an external server is about to run, including deploys
  with no preceding code change. Router skeleton in `SKILL.md`, full protocol in
  `references/deploy-gate.md`.
- **The Law:** no file travels to an external server unclassified. Four classes:
  - **DEPLOY** — app code/assets/migrations; belongs on the server.
  - **SERVER-ONLY** — never transfer, MUST exist server-side, never delete
    (prod `.env`, `storage/`, uploads, certs). Transferring would overwrite prod
    state; deleting would take prod down.
  - **NEVER-ON-SERVER** — neither transfer nor tolerate on the server (tests/,
    docs/, `*.sql`/dump/backup archives, `.git`, CI/IDE/OS junk, Code Guardian
    artifacts `.audit-log.md` / `.code-guardian-*.md`, scratch scripts).
  - **REVIEW** — context-dependent, agent decides conservatively with evidence
    (`node_modules/` — needed for SSR, not otherwise; seeders; lockfiles).
- **Protocol D1–D4** (`references/deploy-gate.md`):
  - **D1 Manifest check (before transfer):** classify what WOULD be transferred.
    rsync → `--dry-run --itemize-changes` output is ground truth; other channels →
    source tree minus the mechanism's excludes. Any NEVER-ON-SERVER or SERVER-ONLY
    file in the transfer list → **BLOCKED**.
  - **D2 Durable exclude fix:** the fix lands in the project's deploy mechanism
    (`deploy.sh` exclude list / `.deployignore`) and is committed — never a
    one-off manual filter (same economics as P6: fix the template, not the symptom).
  - **D3 Server-side retro-check:** after every gated deploy AND on first gate run
    per project. Channel a) HTTP probes on classic leak paths (`/.env`,
    `/.git/config`, `/.git/HEAD`, `/phpunit.xml`, `/tests/`, `/docs/`, dumps,
    `/storage/logs/*.log`, `/.DS_Store`, `/.audit-log.md`) expecting 403/404;
    channel b) where SSH exists, `find` over the docroot with the
    NEVER-ON-SERVER pattern set. A SERVER-ONLY file reachable over HTTP
    (`/.env` → 200) is a 🔴 finding → fix webserver config/docroot, NEVER delete.
  - **D4 Removal (report → ONE approval → delete → verify):** classified removal
    list (path + class + evidence) → user approves once per list → agent removes
    via ssh/ftp → re-probe proves gone (VERIFIED, not ASSERTED). SERVER-ONLY is
    exempt from removal by law.
- **Tool** `tools/detect-deploy-artifacts.py`: dependency-free, report-only, like
  every Code Guardian tool. Modes: `--root <dir>` (tree classification),
  `--list <file>` (classify an explicit transfer list, e.g. rsync dry-run),
  `--config .code-guardian-deploy.yml` (per-project overrides: docroot URL, ssh
  alias, extra patterns, documented exceptions). Output: one `CLASS path reason`
  line per finding + `SUMMARY deploy=… server-only=… never=… review=… exit=…`;
  exit 1 when the transfer list contains NEVER-ON-SERVER/SERVER-ONLY.
- **Hook** `hooks/deploy-gate-check.sh` (PreToolUse, matcher `Bash`): detects
  deploy commands (`rsync` with remote target, `scp`, `sftp`, `lftp`/`ftp`,
  `*deploy*.sh`, `git push` to prod/production/live remotes) and denies while no
  fresh gate report exists (`.code-guardian-deploy-report.md`, verdict APPROVED,
  mtime < 30 min, in CWD or git root). Deny reason instructs the model to run the
  DEPLOY GATE — the self-correcting v12 loop (`permissionDecisionReason` is fed
  back; plain stdout is not). Fails OPEN without `jq`, like the three existing hooks.
- **Gate report artifact** `.code-guardian-deploy-report.md`: written by the gate
  (D1 result + transfer summary + verdict); consumed by the hook for freshness;
  findings additionally appended to `.audit-log.md` as usual.
- **Degradation:** no SSH/HTTP access → D3 runs reduced and the report is marked
  "⚠️ Server unchecked" (analog to "⚠️ DB unchecked"). Unknown deploy mechanism →
  the gate does not block blind; it demands the transfer list first.
- **Version v13 → v14** in lockstep: SKILL.md title/frontmatter-triggers (deploy,
  rsync, "live stellen", "auf den Server", upload, publish, go-live)/gate
  section/core rule, install.sh markers (+`DEPLOY GATE`, +hook Nr. 4 registration,
  +tool existence), README, UPDATE-ANLEITUNG, design-rationale v14 entry.

## Rejected alternatives

- **Fifth mutually exclusive DEPLOY MODE:** modes classify TASKS; a deploy is an
  event at the end of a task and would compete with BUILD MODE for selection.
- **BUILD-audit layer 7:** cheapest wiring, but misses deploys without a preceding
  code change ("deploy das mal eben") and the retro-check of already-polluted servers.
- **Auto-remove on the server (even with quarantine):** a misclassified file hits
  prod directly; contradicts the liveness-veto philosophy. Removal happens after
  ONE explicit user approval per list.
- **Report-only without removal:** fails the requirement "dafür sorgen, dass diese
  wieder entfernt werden" — leftovers would stay indefinitely.
- **Hook-only enforcement:** the classification intelligence (4 classes,
  SERVER-ONLY nuance) lives in the skill; a hook can only block.

## Validation

Trap fixture `test/deploy/`: planted project tree — `tests/`, `docs/`, `dump.sql`,
`backup.tar.gz`, `.env`, `.DS_Store`, `.audit-log.md`, `.git/`, `.github/`,
`storage/` — plus a fake rsync `--itemize-changes` transfer list. Expected: every
NEVER-ON-SERVER trap flagged; `.env`/`storage/` classified SERVER-ONLY (blocked
from transfer, exempt from removal); clean app files (controllers, views,
migrations, public assets) → 0 false positives. Unit tests dual-mode in
`tools/tests/`; hook tested with fixture commands (rsync remote vs. local rsync —
local must NOT trigger). Full suite green before packaging.
