#!/bin/bash
# Code Guardian UserPromptSubmit Hook (v10)
#
# Fires on every user prompt. If the prompt looks like a code change or a bug
# report (de/en trigger words), injects a one-line reminder to invoke the
# code-guardian skill BEFORE touching code. Silent on everything else.
#
# Wired into ~/.claude/settings.json → hooks.UserPromptSubmit

PROMPT=$(jq -r '.prompt // empty' 2>/dev/null)
[ -z "$PROMPT" ] && exit 0

if echo "$PROMPT" | grep -qiE 'bug|error|fehler|broken|kaputt|funktioniert|geht nicht|404|500|exception|stack trace|fix|repar|change|update|implement|build|create|refactor|integrat|migrat|deploy|[äÄ]nder|aender|anpass|f[üÜ]ge|fuege|hinzu|baue|erstell|einbau|entfern|l[öÖ]sch|loesch|feature|route|controller|model|migration|component|endpoint|api|css|style|template'; then
  cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[code-guardian default] This prompt looks like a code change or bug report. Invoke the code-guardian skill before touching code: bug/error -> DEBUG MODE first; spec/plan -> PLAN MODE; build/change -> BUILD MODE (pre-flight before code, audit after). Per ~/.claude/CLAUDE.md this is mandatory and runs combined with superpowers."}}
JSON
fi
exit 0
