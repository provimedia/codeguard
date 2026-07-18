#!/bin/bash
# Tests for the v16 §D heartbeat in hooks/code-guardian-reminder.sh.
set -u
HOOK="$(cd "$(dirname "$0")/../.." && pwd)/hooks/code-guardian-reminder.sh"
SID="cg-test-$$"
CF="${TMPDIR:-/tmp}/cg-heartbeat-${SID}"
rm -f "$CF"
FAILS=0

edit() { printf '{"session_id":"%s","tool_input":{"file_path":"%s"}}' "$SID" "$1" | bash "$HOOK"; }

O1=$(edit /tmp/proj/a.php); O2=$(edit /tmp/proj/b.php); O3=$(edit /tmp/proj/c.php)
echo "$O1$O2" | grep -qF "Senior view:" && { echo "FAIL: heartbeat before 3rd edit"; FAILS=$((FAILS+1)); }
echo "$O3" | grep -qF "Senior view:" || { echo "FAIL: no heartbeat on 3rd edit"; FAILS=$((FAILS+1)); }
echo "$O3" | grep -qF "(senior-dev card §D)" || { echo "FAIL: heartbeat missing card reference"; FAILS=$((FAILS+1)); }
echo "$O3" | jq -e '.hookSpecificOutput.additionalContext' >/dev/null 2>&1 || { echo "FAIL: 3rd-edit output invalid JSON"; FAILS=$((FAILS+1)); }
edit /tmp/proj/d.php >/dev/null; edit /tmp/proj/e.php >/dev/null; O6=$(edit /tmp/proj/f.php)
# Compare ONLY the heartbeat question (text after "Senior view:"), not the full
# context — that also contains the basename and would differ regardless.
Q3=$(echo "$O3" | jq -r '.hookSpecificOutput.additionalContext' | grep -o 'Senior view:.*')
Q6=$(echo "$O6" | jq -r '.hookSpecificOutput.additionalContext' | grep -o 'Senior view:.*')
[ -n "$Q3" ] && [ "$Q3" = "$Q6" ] \
  && { echo "FAIL: heartbeat question did not rotate between 3rd and 6th edit"; FAILS=$((FAILS+1)); }
OMD=$(edit /tmp/proj/readme.md)
[ -z "$OMD" ] || { echo "FAIL: non-code file produced output"; FAILS=$((FAILS+1)); }
[ "$(cat "$CF")" = "6" ] || { echo "FAIL: counter is $(cat "$CF"), expected 6 (md file must not count)"; FAILS=$((FAILS+1)); }

rm -f "$CF"
[ "$FAILS" -eq 0 ] && echo "ALL PASS" || echo "$FAILS FAILURES"
exit "$FAILS"
