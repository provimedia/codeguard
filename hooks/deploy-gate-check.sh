#!/bin/bash
# Deploy Gate PreToolUse Hook (Code Guardian v14)
#
# Fires before every Bash tool call. Denies DEPLOY commands (rsync/scp/sftp to a
# remote, lftp/ftp, deploy scripts, git push to a prod remote) while no FRESH
# APPROVED gate report exists — forcing the model to run the DEPLOY GATE
# (code-guardian references/deploy-gate.md, D1 manifest check + D2 excludes)
# and write `.code-guardian-deploy-report.md` first. Nothing reaches a server
# unclassified.
#
# Carve-outs (must NEVER be blocked):
#   - rsync --dry-run / -n            -> that IS the gate's D1 probe
#   - rsync/scp without a remote spec -> local copy, not a deploy
#   - git push to non-prod remotes    -> code hosting, not a deploy
#
# Freshness: report mtime < 1800 s AND contains "DEPLOY GATE: APPROVED".
# Report location: $CLAUDE_PROJECT_DIR, else git toplevel, else $PWD.
#
# Doc-backed mechanics (v12 precedent): PreToolUse plain stdout is NOT visible
# to the model; hookSpecificOutput.permissionDecisionReason on a deny IS fed
# back — that feedback is what makes this loop self-correcting.
#
# Wired into ~/.claude/settings.json -> hooks.PreToolUse (matcher "Bash")
# by install.sh (idempotent merge, backup taken).

# No jq -> fail OPEN (never block every Bash call on a machine without jq;
# the skill-level DEPLOY GATE rule still applies).
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -n "$CMD" ] || exit 0

# Self-reference carve-out: commands that test/inspect THIS hook are not a
# deploy — without this, the hook's own filename matches the deploy*.sh
# pattern and every manual `echo … | deploy-gate-check.sh` verification
# (see UPDATE-ANLEITUNG Schritt 3) would be denied. Found live on 2026-07-08:
# the hook blocked its own post-install functional test.
echo "$CMD" | grep -q 'deploy-gate-check\.sh' && exit 0

REMOTE_SPEC='([A-Za-z0-9._-]+@)?[A-Za-z0-9][A-Za-z0-9._-]*:[^ ]'

is_deploy=0
# rsync with a remote host:path spec (dry-run is the gate's own D1 probe -> allow)
if echo "$CMD" | grep -qE "(^|[;&| ])rsync[^;&|]*[ ]${REMOTE_SPEC}"; then
    echo "$CMD" | grep -qE '(^|[;&| ])rsync[^;&|]*[ ](--dry-run|-[a-zA-Z]*n[a-zA-Z]*)([ ]|$)' || is_deploy=1
fi
# scp/sftp with a remote spec
echo "$CMD" | grep -qE "(^|[;&| ])(scp|sftp)[^;&|]*[ ]${REMOTE_SPEC}" && is_deploy=1
# ftp clients are remote by definition
echo "$CMD" | grep -qE '(^|[;&| ])(lftp|ftp)[ ]' && is_deploy=1
# project deploy scripts: ./deploy.sh, bash deploy-prod.sh, ...
echo "$CMD" | grep -qE '(^|[;&| /])(bash |sh )?[.]?/?deploy[A-Za-z0-9._-]*\.sh([ ]|$)' && is_deploy=1
# git push to a production remote
echo "$CMD" | grep -qE '(^|[;&| ])git[ ]+push[^;&|]*[ ](prod|production|live)([ ]|$)' && is_deploy=1

[ "$is_deploy" -eq 1 ] || exit 0

# Locate the gate report: CLAUDE_PROJECT_DIR > git toplevel > PWD
ROOT="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$ROOT" ]; then
    ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
fi
REPORT="$ROOT/.code-guardian-deploy-report.md"

if [ -f "$REPORT" ] && grep -q 'DEPLOY GATE: APPROVED' "$REPORT" 2>/dev/null; then
    now=$(date +%s)
    mtime=$(stat -f %m "$REPORT" 2>/dev/null || stat -c %Y "$REPORT" 2>/dev/null || echo 0)
    age=$(( now - mtime ))
    if [ "$age" -ge 0 ] && [ "$age" -lt 1800 ]; then
        exit 0
    fi
fi

cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"DEPLOY GATE (code-guardian v14): Deploy-Kommando ohne frischen Gate-Report. Erst references/deploy-gate.md durchlaufen: D1 Transferliste klassifizieren (rsync --dry-run --itemize-changes | detect-deploy-artifacts.py --list -), D2 Excludes dauerhaft im Deploy-Mechanismus fixen, dann .code-guardian-deploy-report.md mit 'DEPLOY GATE: APPROVED' ins Projekt-Root schreiben (max. 30 min alt) und das Kommando erneut ausfuehren. SERVER-ONLY (.env, storage/, uploads) und NEVER[high] (Tests, Docs, Dumps, .git, Audit-Logs) duerfen NIE in der Transferliste stehen."}}
EOF
exit 0
