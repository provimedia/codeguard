#!/usr/bin/env bash
#
# Code Guardian Skill Installer (v7.1)
# -----------------------------------
# Installs / updates the code-guardian skill for Claude Code.
# Works on macOS and Linux.
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
# Bundled companion skill — powers the Council Gates that code-guardian invokes
# (DEBUG Phase 3, two-failure Escalation, BUILD Pre-Flight 1e Blast-Radius).
COUNCIL_SOURCE_DIR="${SCRIPT_DIR}/llm-council"
COUNCIL_TARGET_DIR="${TARGET_ROOT}/llm-council"
# Backups live OUTSIDE the skills root — a backup placed under skills/ is
# auto-discovered by Claude Code as a duplicate skill (it has a SKILL.md).
BACKUP_ROOT="${HOME}/.claude/skill-backups"
BACKUP_DIR="${BACKUP_ROOT}/code-guardian.backup.$(date +%Y%m%d-%H%M%S)"

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
[ -d "$SOURCE_DIR/tools" ] || die "tools/ directory not found in source: $SOURCE_DIR/tools"
for tool in detect-clones.py detect-config-leaks.sh detect-secrets.sh detect-symbol-loss.py detect-dead-code.py; do
    [ -f "$SOURCE_DIR/tools/$tool" ] || die "Helper script missing: $SOURCE_DIR/tools/$tool"
done
[ -f "$COUNCIL_SOURCE_DIR/SKILL.md" ] || die "Bundled companion missing: $COUNCIL_SOURCE_DIR/SKILL.md"

log "Source:  $SOURCE_DIR"
log "Target:  $TARGET_DIR"
log "Companion: $COUNCIL_SOURCE_DIR -> $COUNCIL_TARGET_DIR"

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
            mkdir -p "$BACKUP_ROOT"
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

# Verify
if [ "$DRY_RUN" -eq 0 ]; then
    if [ -f "$TARGET_DIR/SKILL.md" ]; then
        line_count=$(wc -l < "$TARGET_DIR/SKILL.md")
        ok "SKILL.md installed ($line_count lines)"
    else
        die "Installation verification failed: $TARGET_DIR/SKILL.md missing"
    fi
    if [ -d "$TARGET_DIR/tools" ]; then
        tool_count=$(find "$TARGET_DIR/tools" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' \) | wc -l | tr -d ' ')
        ok "tools/ installed ($tool_count helper script(s))"
        chmod +x "$TARGET_DIR/tools"/*.sh "$TARGET_DIR/tools"/*.py 2>/dev/null || true
    else
        die "Installation verification failed: $TARGET_DIR/tools missing"
    fi
fi

# Version check — confirm v12 structural markers + shipped features are present
if [ "$DRY_RUN" -eq 0 ]; then
    missing=()
    grep -q "Code Guardian (v12)"              "$TARGET_DIR/SKILL.md" || missing+=("Code Guardian (v12)")
    grep -q "PLAN MODE"                        "$TARGET_DIR/SKILL.md" || missing+=("PLAN MODE")
    grep -q "BUILD MODE"                       "$TARGET_DIR/SKILL.md" || missing+=("BUILD MODE")
    grep -q "DEBUG MODE"                       "$TARGET_DIR/SKILL.md" || missing+=("DEBUG MODE")
    grep -q "CLEANUP MODE"                     "$TARGET_DIR/SKILL.md" || missing+=("CLEANUP MODE")
    grep -q "DECISION GATE"                    "$TARGET_DIR/SKILL.md" || missing+=("DECISION GATE")
    grep -q "Self-Slop Sweep"                  "$TARGET_DIR/SKILL.md" || missing+=("Self-Slop Sweep")
    grep -q "Blast-Radius Council Gate"        "$TARGET_DIR/SKILL.md" || missing+=("Blast-Radius Council Gate")
    grep -q "detect-symbol-loss.py"            "$TARGET_DIR/SKILL.md" || missing+=("symbol-loss gate (SKILL.md)")
    [ -f "$TARGET_DIR/tools/detect-symbol-loss.py" ] || missing+=("tools/detect-symbol-loss.py")
    [ -f "$TARGET_DIR/tools/detect-dead-code.py" ] || missing+=("tools/detect-dead-code.py")
    if [ ${#missing[@]} -eq 0 ]; then
        ok "v12 markers + symbol-loss + dead-code + decision gates detected in installed skill"
    else
        warn "Missing markers: ${missing[*]} — installed version may be outdated"
    fi
fi

# Companion skill: llm-council (bundled). code-guardian invokes it at three judgment
# points, so it now ships with this repo and installs alongside the skill.
# Install-only-if-missing: an existing (possibly customized) council is left untouched
# unless --force is passed, which overwrites it with the bundled copy.
log "Companion skill: llm-council"
council_exists=0
{ [ -d "$COUNCIL_TARGET_DIR" ] || [ -L "$COUNCIL_TARGET_DIR" ]; } && council_exists=1

if [ "$council_exists" -eq 1 ] && [ "$FORCE" -eq 0 ]; then
    ok "llm-council already present — leaving as-is (use --force to overwrite)"
else
    if [ "$council_exists" -eq 1 ]; then
        warn "Existing llm-council found — --force was passed, overwriting with bundled copy"
    else
        log "No llm-council found — installing bundled copy"
    fi
    if [ "$DRY_RUN" -eq 0 ]; then
        rm -rf "$COUNCIL_TARGET_DIR"
        cp -R "$COUNCIL_SOURCE_DIR" "$COUNCIL_TARGET_DIR"
        if grep -q "name: llm-council" "$COUNCIL_TARGET_DIR/SKILL.md" 2>/dev/null; then
            ok "llm-council installed -> $COUNCIL_TARGET_DIR (Council Gates operational out of the box)"
        else
            die "llm-council verification failed: marker 'name: llm-council' not found in $COUNCIL_TARGET_DIR/SKILL.md"
        fi
    else
        ok "llm-council would be installed -> $COUNCIL_TARGET_DIR (dry-run)"
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
