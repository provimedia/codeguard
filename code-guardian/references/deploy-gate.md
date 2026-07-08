# DEPLOY GATE — nothing reaches a server unclassified (v14)

> Loaded when the DEPLOY GATE fires: a deployment/transfer to an external server
> is about to run. Orthogonal to mode selection (like the DECISION GATE): fires in
> PLAN, BUILD, DEBUG, CLEANUP alike, and also outside any mode — including deploys
> with no preceding code change ("deploy das mal eben").

## When it fires

Any of: `deploy.sh` (or any project deploy script) · `rsync`/`scp`/`sftp` with a
remote target · `ftp`/`lftp` upload · `git push` to a prod/production/live remote ·
CI-trigger that publishes · user says "deploy", "deployen", "live stellen",
"auf den Server", "hochladen", "publish", "release", "go-live".

Also fires WITHOUT a deploy — as a server-hygiene audit — when the user asks
"liegt X auf dem Server?" / "check the server for leftovers": run D3+D4 only.

## The Law

Every file that travels to (or already lives on) an external server carries
exactly one class. **Transferring and existing are independent dimensions** —
that is the core nuance:

| Class | Transfer? | Exist on server? | Examples |
|---|---|---|---|
| **DEPLOY** | yes | yes | app code, assets, migrations, vendor/ |
| **SERVER-ONLY** | **never** | **must** — never delete | prod `.env`, `storage/`, uploads, certs, live `.sqlite` |
| **NEVER-ON-SERVER** | never | never → removal candidate | tests/, docs/, `*.sql` dumps, `.git/`, CI/IDE/OS junk, `.audit-log.md` |
| **REVIEW** | agent decides with evidence | — | `node_modules/` (SSR yes, else no), seeders |

Transferring a SERVER-ONLY file is as wrong as transferring a dump: it
**overwrites production state** (the local `.env` clobbers the prod `.env`).
Deleting one server-side takes production down. Both directions are blocked.

Classifier: `python3 ~/.claude/skills/code-guardian/tools/detect-deploy-artifacts.py`
(catalogs are data tables; per-project reality goes into `.code-guardian-deploy.yml`).

## D1 — Manifest check (BEFORE transfer)

Establish the ground truth of what WOULD be transferred, then classify it:

```bash
# rsync-based deploys (incl. deploy.sh wrappers — reuse ITS exact flags/excludes):
rsync --dry-run --itemize-changes <same args as the real deploy> \
  | python3 ~/.claude/skills/code-guardian/tools/detect-deploy-artifacts.py --list - \
      [--config .code-guardian-deploy.yml]

# other channels (ftp scripts, scp of a build dir): inventory the source tree
python3 ~/.claude/skills/code-guardian/tools/detect-deploy-artifacts.py --root <dir> \
  # then verify every finding is excluded by the mechanism (grep its exclude list)
```

Verdict rules:
- **SERVER-ONLY or NEVER[high] in the transfer list → BLOCKED.** No transfer
  until D2 fixed the excludes. No exception for "it was always like this".
- **NEVER[low] in the transfer list → 🟡 warning.** Fix the excludes in the same
  commit; the deploy may proceed.
- **REVIEW → resolve now**: name the evidence (SSR? seeder policy?) and either
  add an exclude or an `allow:` entry in `.code-guardian-deploy.yml` with reason.
- Unknown mechanism / no transfer list obtainable → the gate does not block
  blind; it demands the transfer list first (ask the user how the deploy works).

Paste the tool's `SUMMARY …` footer as Verified-by.

## D2 — Durable exclude fix

Fixes land in the **deploy mechanism itself** — `deploy.sh`'s `--exclude` list,
`.deployignore`, the FTP script's filter — and are **committed**. A one-off
manual filter fixes today's deploy and re-leaks next week (same economics as P6:
fix the template, not the symptom). Re-run D1 after the fix; BLOCKED lifts only
on a clean re-run (SERVER-ONLY/NEVER[high] absent from the transfer list).

## D3 — Server-side retro-check (AFTER deploy + on first gate run per project)

The server may already be polluted by pre-gate deploys. Two channels:

**a) HTTP probes** (always possible; docroot URL from `.code-guardian-deploy.yml`
`docroot_url:` or the project's live URL):

```bash
for p in .env .git/config .git/HEAD phpunit.xml tests/ docs/ dump.sql \
         storage/logs/laravel.log .audit-log.md .DS_Store composer.lock; do
  printf '%-28s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/$p")"
done
```

Expected: **403/404 everywhere**. Interpretation:
- NEVER path answers 200 → leftover confirmed → D4 removal list.
- **SERVER-ONLY path answers 200 (e.g. `/.env` → 200) → 🔴 CRITICAL: fix the
  webserver config/docroot (deny rule, move file out of docroot) — NEVER delete
  the file; it is production state.** Verify the fix by re-probe (expect 403/404),
  not by assumption.
- 200 on `tests/`/`docs/` style paths can be a route, not a file — confirm via
  channel b) or content inspection before listing for removal.

**b) SSH find** (when SSH access exists; alias from `.code-guardian-deploy.yml` `ssh:`):

```bash
ssh $ALIAS 'cd $DOCROOT && find . \( -name "*.sql" -o -name "*.dump" -o -name "*.bak" \
  -o -name ".DS_Store" -o -name ".audit-log.md" -o -name "phpunit.xml*" \
  -o -path "*/tests/*" -o -path "*/docs/*" -o -path "*/.git/*" -o -name "*backup*" \) \
  -not -path "*/storage/*" -not -path "*/uploads/*" 2>/dev/null'
```

Pipe the result through `--list -` for classification. No HTTP and no SSH
channel available → mark the report **"⚠️ Server unchecked"** (analog to
"⚠️ DB unchecked") — never claim server hygiene you could not observe.

## D4 — Removal: report → ONE approval → delete → verify

1. **Report** the classified removal list: path · class+risk · evidence
   (HTTP status / find output). SERVER-ONLY findings are NEVER on this list.
2. **One approval**: the user approves the list once as a whole (or strikes
   items). No removal before approval — a misclassified "doc" that is actually
   served would otherwise become an outage. The DECISION GATE applies: the
   list comes with a recommendation per item.
3. **Delete** via the available channel (ssh `rm`, ftp delete) — exactly the
   approved items, nothing more.
4. **Verify**: re-probe every removed path (expect 404) / re-run the find
   (expect empty). Paste the outputs — VERIFIED, not ASSERTED.

## Report artifact — `.code-guardian-deploy-report.md`

The gate writes its result to the project root (the enforcement hook reads it;
fresh = mtime < 30 min):

```markdown
# Code Guardian DEPLOY GATE Report
Date: <ISO timestamp>   Target: <host/path or URL>   Mechanism: <deploy.sh|rsync|ftp|…>
D1: SUMMARY deploy=… server-only=… never=… review=… allowed=… exit=…
D2: <excludes fixed/verified in which file, or "no change needed">
D3: <probe/find summary, or "⚠️ Server unchecked — no channel">
D4: <removals done+verified, pending approval, or "none">
DEPLOY GATE: APPROVED|BLOCKED
```

`APPROVED` requires: D1 clean (no SERVER-ONLY/NEVER[high] in the transfer list)
AND D2 committed (when it changed anything). D3/D4 never block a deploy of clean
content — they clean up the past; run them right after the transfer.

The report is ephemeral working data: gitignore it. It is itself class
NEVER-ON-SERVER (`.code-guardian-*` catalog entry) — the gate's own artifact
must never ship.

## `.code-guardian-deploy.yml` — per-project reality

```yaml
docroot_url: https://www.example.de     # D3 probe base
ssh: prod-alias                         # D3/D4 channel (ssh config alias)
extra_never:                            # project-specific junk
  - internal-notes/
extra_server_only:                      # project-specific server state
  - shared/
allow:                                  # documented exceptions (pattern: reason)
  - 'docs/api-public/: served intentionally as public /docs'
```

Committed to the project repo; `allow:` entries are the honest escape hatch —
visible and reasoned, like INTENTIONAL-SPECIAL-CASE (v13).

## Boundaries

- **The gate classifies and blocks transfers; removal is user-approved.** It
  never deletes server files autonomously, and it never deletes SERVER-ONLY at all.
- **Local-only operations never fire the gate** (local rsync between folders,
  git push to a code host that is not a deploy target).
- **The gate's own D1 dry-run must not be blocked** by the enforcement hook
  (`--dry-run`/`-n` carve-out) — otherwise the gate could never run.
- Deploy standing-authorizations (e.g. a project's auto-deploy directive) cover
  WHEN to deploy — the gate governs WHAT may travel; both apply.
