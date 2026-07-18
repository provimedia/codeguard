#!/bin/bash
# Code Guardian PostToolUse Hook (v16)
#
# Fires after every Write|Edit on a code file: injects the audit reminder
# (unchanged since v10) and — new in v16 — a rotating senior-dev §D
# meta-question every 3rd counted edit (session-scoped counter in
# ${TMPDIR}/cg-heartbeat-<session_id>). Non-code files stay silent and do
# not advance the counter.

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

    # v16 §D heartbeat: every 3rd counted code edit, rotate one senior meta-question
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "nosession"')
    COUNTER_FILE="${TMPDIR:-/tmp}/cg-heartbeat-${SESSION_ID}"
    COUNT=$(( $(cat "$COUNTER_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$COUNT" > "$COUNTER_FILE"
    HEARTBEAT=""
    if [ $((COUNT % 3)) -eq 0 ]; then
      case $(( (COUNT / 3 - 1) % 4 )) in
        0) Q="Senior view: does this still make sense, seen from outside?" ;;
        1) Q="Senior view: are you writing something that already exists in this codebase?" ;;
        2) Q="Senior view: still inside the task scope — no drive-by refactoring?" ;;
        3) Q="Senior view: two failed attempts on the same spot? Stop, write assumptions down, change approach." ;;
      esac
      HEARTBEAT=" ${Q} Answer honestly in one sentence before continuing. (senior-dev card §D)"
    fi

    cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[code-guardian] ${BASENAME} edited. The change is not done until the skill's Step 3 audit ran on the full diff (triage 3a decides depth; every check Verified-by command output, and Step 2 re-seeds the dependency worklist).${HINT}${HEARTBEAT}"}}
EOF
    ;;
esac
exit 0
