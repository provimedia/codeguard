# test/deploy — DEPLOY GATE fixture (oracle)

Planted tree for `detect-deploy-artifacts.py` validation (v14).

| Path | Expected class |
|---|---|
| app/, public/, resources/, database/migrations/, .env.example | DEPLOY (silent) |
| .env, storage/, certs/server.key | SERVER-ONLY |
| tests/, docs/, dump.sql, backup-2026.tar.gz, .audit-log.md, phpunit.xml, .github/ | NEVER[high] |
| .DS_Store (root + img/), .idea/ | NEVER[low] |
| node_modules/, database/seeders/ | REVIEW |

`rsync-list.txt` is fake `--dry-run --itemize-changes` output over the same
traps (plus noise lines and a `*deleting` entry that must be skipped).
`.git/` cannot live on disk inside a git repo — covered via `--list` unit test.

Run:
    python3 code-guardian/tools/detect-deploy-artifacts.py --root test/deploy/project
    python3 code-guardian/tools/detect-deploy-artifacts.py --list test/deploy/rsync-list.txt
Expected: exit 1, every trap represented, zero clean-file findings.
