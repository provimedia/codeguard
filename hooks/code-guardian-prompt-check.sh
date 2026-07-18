#!/bin/bash
# Code Guardian UserPromptSubmit Hook (v16)
#
# Fires on EVERY user prompt (v16: was code-triggers-only). Injects the
# senior-dev intake instruction — take on the request as a senior full-stack
# developer, triage, then route. Appends a mode routing hint when the prompt
# looks like a code change or bug report (de/en trigger words). Silent only
# on empty prompts and slash commands.
#
# Wired into ~/.claude/settings.json → hooks.UserPromptSubmit

PROMPT=$(jq -r '.prompt // empty' 2>/dev/null)
[ -z "$PROMPT" ] && exit 0
case "$PROMPT" in "/"*) exit 0 ;; esac

HINT=""
if echo "$PROMPT" | grep -qiE 'bug|error|fehler|broken|kaputt|funktioniert|geht nicht|404|500|exception|stack trace|fix|repar|change|update|implement|build|create|refactor|integrat|migrat|deploy|[äÄ]nder|aender|anpass|f[üÜ]ge|fuege|hinzu|baue|erstell|einbau|entfern|l[öÖ]sch|loesch|feature|route|controller|model|migration|component|endpoint|api|css|style|template'; then
  HINT=" Routing hint: looks like a code change or bug report — after intake route: bug/error -> code-guardian DEBUG MODE; spec/plan -> PLAN MODE; build/change -> BUILD MODE (pre-flight before code, audit after). Per ~/.claude/CLAUDE.md this is mandatory and runs combined with superpowers."
fi

cat <<JSON
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[senior-dev intake] Load the senior-dev skill first (if not loaded this session) and take on this request as a senior full-stack developer: triage (question/trivial/normal/large), run the intake at that depth, then route.${HINT}"}}
JSON
exit 0
