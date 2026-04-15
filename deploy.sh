#!/usr/bin/env bash
# Deploy the local SKILL.md to the live Claude Code skills directory.
# Usage: ./deploy.sh [--dry-run]

set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/code-guardian/SKILL.md"
DEST_DIR="$HOME/.claude/skills/code-guardian"
DEST="$DEST_DIR/SKILL.md"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) echo "Usage: $0 [--dry-run]"; exit 0 ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: source not found: $SRC" >&2
  exit 1
fi

if [[ -f "$DEST" ]] && diff -q "$SRC" "$DEST" >/dev/null 2>&1; then
  echo "Already up to date: $DEST"
  exit 0
fi

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$DEST_DIR.backup.$TS"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] would backup $DEST_DIR -> $BACKUP"
  echo "[dry-run] would copy   $SRC -> $DEST"
  if [[ -f "$DEST" ]]; then
    echo "--- diff (live vs local) ---"
    diff -u "$DEST" "$SRC" || true
  fi
  exit 0
fi

if [[ -d "$DEST_DIR" ]]; then
  cp -R "$DEST_DIR" "$BACKUP"
  echo "Backup: $BACKUP"
fi

mkdir -p "$DEST_DIR"
cp "$SRC" "$DEST"
echo "Deployed: $DEST"
