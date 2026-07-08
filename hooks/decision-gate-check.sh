#!/bin/bash
# Decision Gate PreToolUse Hook (Code Guardian v12)
#
# Fires before every AskUserQuestion. Denies the call when no option label
# carries an "(Empfohlen)" / "(Recommended)" marker — forcing the model to run
# the DECISION GATE (code-guardian references/decision-gate.md) and re-issue
# the question WITH a recommendation. The gate recommends; the user decides.
#
# Doc-backed mechanics (verified 2026-07-08): PreToolUse plain stdout is NOT
# visible to the model; hookSpecificOutput.permissionDecisionReason on a deny
# IS fed back — that feedback is what makes this loop self-correcting.
#
# Escape hatch: pure-preference questions where no recommendation is possible
# must carry "[keine-empfehlung: <reason>]" (or "no-recommendation") in the
# question text — visible to the user, so the exception stays honest.
#
# Wired into ~/.claude/settings.json → hooks.PreToolUse (AskUserQuestion)
# by install.sh (idempotent merge, backup taken).

# No jq -> fail OPEN (never block every question on a machine without jq;
# the skill-level DECISION GATE rule still applies).
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
LABELS=$(echo "$INPUT" | jq -r '[.tool_input.questions[]?.options[]?.label // empty] | join("\n")' 2>/dev/null)
QUESTIONS=$(echo "$INPUT" | jq -r '[.tool_input.questions[]?.question // empty] | join("\n")' 2>/dev/null)

# Recommendation present -> allow
echo "$LABELS" | grep -qiE '\((Empfohlen|Recommended)\)' && exit 0
# Declared no-recommendation exception -> allow
echo "$QUESTIONS" | grep -qi 'keine-empfehlung\|no-recommendation' && exit 0

cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"DECISION GATE (code-guardian v12): Optionsfrage ohne Empfehlung. Erst references/decision-gate.md durchlaufen (T1-Rubrik, ggf. T2 Advokaten / T3 Council), dann die Frage erneut stellen: empfohlene Option AN ERSTER STELLE, Label-Suffix ' (Empfohlen)', plus 1-2 Saetze Rubrik-Begruendung; alle anderen Optionen fair mit ehrlichem Trade-off. Das Gate empfiehlt; der User entscheidet. Ausnahme (reine Geschmacksfrage): '[keine-empfehlung: <Grund>]' in den Fragetext aufnehmen."}}
EOF
exit 0
