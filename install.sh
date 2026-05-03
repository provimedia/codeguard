#!/usr/bin/env bash
#
# Code Guardian Skill Installer (v6)
# ---------------------------------
# Installs / updates the code-guardian skill for Claude Code.
# Works on macOS and Linux.
#
# v6 changes: ships a tools/ directory with three helper scripts
# (detect-secrets.sh, detect-clones.py, detect-config-leaks.sh)
# referenced by the new R1-R5 redundancy reflexes in the audit phase.
#
# Usage:
#   ./install.sh                 # Install to ~/.claude/skills/code-guardian/
#   ./install.sh --force         # Overwrite without backup
#   ./install.sh --dry-run       # Show what would happen, change nothing
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/code-guardian"
TARGET_ROOT="${HOME}/.claude/skills"
TARGET_DIR="${TARGET_ROOT}/code-guardian"
BACKUP_DIR="${TARGET_ROOT}/code-guardian.backup.$(date +%Y%m%d-%H%M%S)"

FORCE=0
DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        --dry-run) DRY_RUN=1 ;;
        -h|--help)
            sed -n '2,14p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

log()  { printf '\033[0;36m[install]\033[0m %s\n' "$*"; }
ok()   { printf '\033[0;32m[ok]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\033[0;31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }

# Sanity checks
[ -d "$SOURCE_DIR" ] || die "Source directory not found: $SOURCE_DIR"
[ -f "$SOURCE_DIR/SKILL.md" ] || die "SKILL.md not found in source: $SOURCE_DIR/SKILL.md"

log "Source:  $SOURCE_DIR"
log "Target:  $TARGET_DIR"

# Create parent directory if needed
if [ ! -d "$TARGET_ROOT" ]; then
    log "Creating $TARGET_ROOT (Claude Code skills root)"
    if [ "$DRY_RUN" -eq 0 ]; then
        mkdir -p "$TARGET_ROOT"
    fi
fi

# Backup existing installation
if [ -d "$TARGET_DIR" ]; then
    if [ "$FORCE" -eq 1 ]; then
        warn "Existing installation found — --force was passed, skipping backup"
        if [ "$DRY_RUN" -eq 0 ]; then
            rm -rf "$TARGET_DIR"
        fi
    else
        log "Existing installation found — backing up to $BACKUP_DIR"
        if [ "$DRY_RUN" -eq 0 ]; then
            mv "$TARGET_DIR" "$BACKUP_DIR"
        fi
        ok "Backup created: $BACKUP_DIR"
    fi
fi

# Copy skill files
log "Copying skill files..."
if [ "$DRY_RUN" -eq 0 ]; then
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
fi

# Make helper scripts executable (v6+)
if [ "$DRY_RUN" -eq 0 ] && [ -d "$TARGET_DIR/tools" ]; then
    chmod +x "$TARGET_DIR/tools/"*.sh "$TARGET_DIR/tools/"*.py 2>/dev/null || true
fi

# Verify
if [ "$DRY_RUN" -eq 0 ]; then
    if [ -f "$TARGET_DIR/SKILL.md" ]; then
        line_count=$(wc -l < "$TARGET_DIR/SKILL.md")
        ok "SKILL.md installed ($line_count lines)"
    else
        die "Installation verification failed: $TARGET_DIR/SKILL.md missing"
    fi
    # tools/ check (v6+)
    tool_count=0
    for tool in detect-secrets.sh detect-clones.py detect-config-leaks.sh; do
        if [ -x "$TARGET_DIR/tools/$tool" ]; then
            tool_count=$((tool_count + 1))
        fi
    done
    if [ "$tool_count" -eq 3 ]; then
        ok "Helper scripts installed ($tool_count/3 executable in tools/)"
    else
        warn "Helper scripts incomplete ($tool_count/3) — R1-R5 redundancy reflexes may not work"
    fi
fi

# Version check — confirm v5 + v6 markers are present
if [ "$DRY_RUN" -eq 0 ]; then
    if grep -q "PLAN MODE (v5" "$TARGET_DIR/SKILL.md" && grep -q "v5 Plan-Time Rules" "$TARGET_DIR/SKILL.md"; then
        ok "v5 plan-time reflexes detected in installed SKILL.md"
    else
        warn "v5 markers not found — installed version may be outdated"
    fi
    if grep -q "v6 Redundancy Rules" "$TARGET_DIR/SKILL.md" && grep -q "R1\. Hardcoded Secrets" "$TARGET_DIR/SKILL.md"; then
        ok "v6 redundancy reflexes (R1-R5) detected in installed SKILL.md"
    else
        warn "v6 redundancy markers not found — installed version may be outdated"
    fi
fi

echo
ok "Code Guardian skill installation complete."
echo
echo "Next steps:"
echo "  1. Verify Claude Code sees the skill:"
echo "     claude → type /help and look for code-guardian in the skills list"
echo "     (or restart Claude Code if it was already running)"
echo "  2. The skill is auto-activated when you write/edit code or report a bug."
echo "  3. To uninstall, run:   rm -rf ~/.claude/skills/code-guardian"
echo
if [ "$DRY_RUN" -eq 1 ]; then
    warn "DRY RUN — nothing was actually changed"
fi
