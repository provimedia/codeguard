#!/bin/bash
# Runs all hook tests. Exit 0 only if every suite passes.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL=0
for t in "$DIR"/test_*.sh; do
  echo "== $t"; bash "$t"; TOTAL=$((TOTAL + $?))
done
[ "$TOTAL" -eq 0 ] && echo "HOOK SUITES: ALL PASS" || echo "HOOK SUITES: $TOTAL failures"
exit "$TOTAL"
