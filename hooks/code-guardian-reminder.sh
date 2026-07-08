#!/bin/bash
# Code Guardian PostToolUse Hook (v10)
#
# Fires after every Write|Edit. If the touched file is a code file (any stack,
# not just Laravel), injects a short reminder that the change is not done until
# the code-guardian Step 3 audit ran on the full diff. v10 style: one line,
# triage decides depth — the skill itself carries the detail.
#
# Wired into ~/.claude/settings.json → hooks.PostToolUse (Write|Edit)
# Previous v4 version: code-guardian-reminder.sh.v4.bak

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_response.filePath // empty')
[ -z "$FILE_PATH" ] && exit 0

# Skip non-code and third-party paths
case "$FILE_PATH" in
  */vendor/*|*/node_modules/*|*/.git/*|*.md|*.txt|*.log|*.lock|*.csv|*.json|*.yml|*.yaml) exit 0 ;;
esac

case "$FILE_PATH" in
  *.php|*.js|*.mjs|*.ts|*.tsx|*.jsx|*.vue|*.py|*.sql|*.sh|*.css|*.scss|*.html|*.twig|*.blade.php)
    BASENAME=$(basename "$FILE_PATH")

    HINT=""
    case "$FILE_PATH" in
      */Layouts/*|*routes/web.php|*[Nn]av*.vue|*[Nn]av*.php)
        HINT=" Nav/route file: the audit includes the layout-link-to-route check." ;;
      */Controllers/*.php|*/Models/*.php|*/Services/*.php)
        HINT=" Backend data file: verify by dumping the real serialized payload, not by reading code." ;;
    esac

    cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[code-guardian] ${BASENAME} edited. The change is not done until the skill's Step 3 audit ran on the full diff (triage 3a decides depth; every check Verified-by command output, and Step 2 re-seeds the dependency worklist).${HINT}"}}
EOF
    ;;
esac
exit 0
