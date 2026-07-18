#!/bin/bash
# Tests for hooks/code-guardian-prompt-check.sh (v16 contract).
set -u
HOOK="$(cd "$(dirname "$0")/../.." && pwd)/hooks/code-guardian-prompt-check.sh"
FAILS=0

run() { echo "{\"prompt\":$(printf '%s' "$1" | jq -Rs .)}" | bash "$HOOK"; }
check() { # $1 desc, $2 got, $3 must-contain ('' = must be empty), $4 must-not-contain ('' = skip)
  local desc="$1" got="$2" want="$3" notwant="$4"
  if [ -z "$want" ]; then
    [ -z "$got" ] || { echo "FAIL: $desc — expected no output, got: $got"; FAILS=$((FAILS+1)); return; }
  else
    echo "$got" | grep -qF "$want" || { echo "FAIL: $desc — missing '$want'"; FAILS=$((FAILS+1)); return; }
    echo "$got" | jq -e '.hookSpecificOutput.additionalContext' >/dev/null 2>&1 \
      || { echo "FAIL: $desc — invalid hook JSON"; FAILS=$((FAILS+1)); return; }
  fi
  if [ -n "$notwant" ]; then
    echo "$got" | grep -qF "$notwant" && { echo "FAIL: $desc — unexpected '$notwant'"; FAILS=$((FAILS+1)); return; }
  fi
  echo "ok: $desc"
}

check "code prompt gets intake + routing hint" "$(run 'bitte baue ein neues feature ins backend')" "[senior-dev intake]" ""
echo "$(run 'bitte baue ein neues feature ins backend')" | grep -qF "Routing hint" || { echo "FAIL: routing hint missing on code prompt"; FAILS=$((FAILS+1)); }
check "non-code prompt gets intake, no routing hint" "$(run 'Danke, sieht gut aus')" "[senior-dev intake]" "Routing hint"
check "empty prompt silent" "$(printf '{"prompt":""}' | bash "$HOOK")" "" ""
check "slash command silent" "$(run '/help')" "" ""

[ "$FAILS" -eq 0 ] && echo "ALL PASS" || echo "$FAILS FAILURES"
exit "$FAILS"
