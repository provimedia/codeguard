#!/usr/bin/env bash
#
# Code Guardian Skill Installer (v16)
# -----------------------------------
# Installs / updates the code-guardian skill for Claude Code, the bundled
# llm-council and senior-dev companions, and the four session hooks
# (prompt-check — v16: fires on every prompt and loads senior-dev first —
# audit reminder incl. §D heartbeat, DECISION GATE + DEPLOY GATE enforcement)
# incl. settings.json registration.
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
# Bundled companion skill — senior-dev (v16): task intake + persistent senior
# mindset; loaded first on every prompt by the v16 prompt-check hook.
SENIOR_SOURCE_DIR="${SCRIPT_DIR}/senior-dev"
SENIOR_TARGET_DIR="${TARGET_ROOT}/senior-dev"
# Bundled hooks — make the skill the default in EVERY session (prompt-check,
# post-edit audit reminder) and enforce the v12 DECISION GATE (AskUserQuestion).
HOOKS_SOURCE_DIR="${SCRIPT_DIR}/hooks"
HOOKS_TARGET_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
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
for tool in detect-clones.py detect-config-leaks.sh detect-secrets.sh detect-symbol-loss.py detect-dead-code.py detect-hardcoded-cases.py detect-deploy-artifacts.py; do
    [ -f "$SOURCE_DIR/tools/$tool" ] || die "Helper script missing: $SOURCE_DIR/tools/$tool"
done
[ -f "$COUNCIL_SOURCE_DIR/SKILL.md" ] || die "Bundled companion missing: $COUNCIL_SOURCE_DIR/SKILL.md"
[ -f "$SENIOR_SOURCE_DIR/SKILL.md" ] || die "Bundled companion missing: $SENIOR_SOURCE_DIR/SKILL.md"
for hook in code-guardian-prompt-check.sh code-guardian-reminder.sh decision-gate-check.sh deploy-gate-check.sh; do
    [ -f "$HOOKS_SOURCE_DIR/$hook" ] || die "Bundled hook missing: $HOOKS_SOURCE_DIR/$hook"
done

log "Source:  $SOURCE_DIR"
log "Target:  $TARGET_DIR"
log "Companion: $COUNCIL_SOURCE_DIR -> $COUNCIL_TARGET_DIR"
log "Hooks:   $HOOKS_SOURCE_DIR -> $HOOKS_TARGET_DIR (+ settings.json merge)"

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

# Version check — confirm v15 structural markers + shipped features are present
if [ "$DRY_RUN" -eq 0 ]; then
    missing=()
    grep -q "Code Guardian (v15)"              "$TARGET_DIR/SKILL.md" || missing+=("Code Guardian (v15)")
    grep -q "DATA GATE"                        "$TARGET_DIR/SKILL.md" || missing+=("DATA GATE")
    [ -f "$TARGET_DIR/references/data-gate.md" ] || missing+=("references/data-gate.md")
    grep -q "DEPLOY GATE"                      "$TARGET_DIR/SKILL.md" || missing+=("DEPLOY GATE")
    grep -q "PLAN MODE"                        "$TARGET_DIR/SKILL.md" || missing+=("PLAN MODE")
    grep -q "BUILD MODE"                       "$TARGET_DIR/SKILL.md" || missing+=("BUILD MODE")
    grep -q "DEBUG MODE"                       "$TARGET_DIR/SKILL.md" || missing+=("DEBUG MODE")
    grep -q "CLEANUP MODE"                     "$TARGET_DIR/SKILL.md" || missing+=("CLEANUP MODE")
    grep -q "DECISION GATE"                    "$TARGET_DIR/SKILL.md" || missing+=("DECISION GATE")
    grep -q "Generalization"                   "$TARGET_DIR/SKILL.md" || missing+=("Generalization")
    grep -q "Self-Slop Sweep"                  "$TARGET_DIR/SKILL.md" || missing+=("Self-Slop Sweep")
    grep -q "Blast-Radius Council Gate"        "$TARGET_DIR/SKILL.md" || missing+=("Blast-Radius Council Gate")
    grep -q "detect-symbol-loss.py"            "$TARGET_DIR/SKILL.md" || missing+=("symbol-loss gate (SKILL.md)")
    [ -f "$TARGET_DIR/tools/detect-symbol-loss.py" ] || missing+=("tools/detect-symbol-loss.py")
    [ -f "$TARGET_DIR/tools/detect-dead-code.py" ] || missing+=("tools/detect-dead-code.py")
    [ -f "$TARGET_DIR/tools/detect-hardcoded-cases.py" ] || missing+=("tools/detect-hardcoded-cases.py")
    [ -f "$TARGET_DIR/tools/detect-deploy-artifacts.py" ] || missing+=("tools/detect-deploy-artifacts.py")
    if [ ${#missing[@]} -eq 0 ]; then
        ok "v15 markers + symbol-loss + dead-code + decision + generalization + deploy + data gates detected in installed skill"
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

# Companion skill: senior-dev (bundled, v16). The prompt-check hook instructs
# every session to load it first; without it installed the instruction dangles.
log "Companion skill: senior-dev"
senior_exists=0
{ [ -d "$SENIOR_TARGET_DIR" ] || [ -L "$SENIOR_TARGET_DIR" ]; } && senior_exists=1
if [ "$senior_exists" -eq 1 ] && [ "$FORCE" -eq 0 ] && [ "$DRY_RUN" -eq 0 ]; then
    warn "Existing senior-dev found — updating with bundled copy (companion is versioned with this package)"
fi
if [ "$DRY_RUN" -eq 0 ]; then
    rm -rf "$SENIOR_TARGET_DIR"
    cp -R "$SENIOR_SOURCE_DIR" "$SENIOR_TARGET_DIR"
    if grep -q "name: senior-dev" "$SENIOR_TARGET_DIR/SKILL.md" 2>/dev/null; then
        ok "senior-dev installed -> $SENIOR_TARGET_DIR (intake gate operational)"
    else
        die "senior-dev verification failed: marker 'name: senior-dev' not found in $SENIOR_TARGET_DIR/SKILL.md"
    fi
else
    ok "senior-dev would be installed -> $SENIOR_TARGET_DIR (dry-run)"
fi

# Hooks: copy scripts + register them in ~/.claude/settings.json (idempotent merge).
# - Scripts are versioned with this package -> always overwritten on update.
# - settings.json: backup first, only OUR three entries are added if absent,
#   everything else in the file is left byte-identical. Corrupt/missing python3
#   -> warn + manual instructions, never touch the file.
log "Hooks: installing scripts + registering in settings.json"
if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$HOOKS_TARGET_DIR"
    for hook in code-guardian-prompt-check.sh code-guardian-reminder.sh decision-gate-check.sh deploy-gate-check.sh; do
        cp "$HOOKS_SOURCE_DIR/$hook" "$HOOKS_TARGET_DIR/$hook"
        chmod +x "$HOOKS_TARGET_DIR/$hook"
    done
    ok "4 hook script(s) installed -> $HOOKS_TARGET_DIR"

    if command -v python3 >/dev/null 2>&1; then
        if [ -f "$SETTINGS_FILE" ]; then
            SETTINGS_BACKUP="${SETTINGS_FILE}.backup-code-guardian.$(date +%Y%m%d-%H%M%S)"
            cp "$SETTINGS_FILE" "$SETTINGS_BACKUP"
            log "settings.json backup: $SETTINGS_BACKUP"
        fi
        if python3 - "$SETTINGS_FILE" "$HOOKS_TARGET_DIR" <<'PY'
import json, os, sys

path, hooks_dir = sys.argv[1], sys.argv[2]
wanted = [
    ("UserPromptSubmit", None,              "code-guardian-prompt-check.sh"),
    ("PostToolUse",      "Write|Edit",      "code-guardian-reminder.sh"),
    ("PreToolUse",       "AskUserQuestion", "decision-gate-check.sh"),
    ("PreToolUse",       "Bash",            "deploy-gate-check.sh"),
]

settings = {}
if os.path.exists(path):
    try:
        with open(path) as f:
            settings = json.load(f)
    except (json.JSONDecodeError, ValueError):
        sys.exit(3)  # corrupt -> never touch

hooks = settings.setdefault("hooks", {})
added = []
for event, matcher, basename in wanted:
    entries = hooks.setdefault(event, [])
    present = any(
        h.get("command", "").endswith(basename)
        for e in entries if isinstance(e, dict)
        for h in e.get("hooks", []) if isinstance(h, dict)
    )
    if present:
        continue
    entry = {"hooks": [{"type": "command", "command": os.path.join(hooks_dir, basename)}]}
    if matcher is not None:
        entry["matcher"] = matcher
    entries.append(entry)
    added.append(f"{event} -> {basename}")

if added:
    with open(path, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("ADDED: " + ", ".join(added))
else:
    print("ALL PRESENT")
PY
        then
            ok "settings.json: hook registration complete (existing entries untouched)"
            python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SETTINGS_FILE" \
                && ok "settings.json is valid JSON" \
                || die "settings.json failed JSON validation after merge — restore the backup!"
        else
            warn "settings.json is not valid JSON — file NOT touched."
            warn "Register the hooks manually (see UPDATE-ANLEITUNG.md / README, section hooks)."
        fi
    else
        warn "python3 not found — hooks copied but NOT registered in settings.json."
        warn "Register them manually (see UPDATE-ANLEITUNG.md / README, section hooks)."
    fi
else
    ok "hooks + settings.json merge would run (dry-run)"
fi

echo
ok "Code Guardian skill installation complete."
echo
if ! command -v jq >/dev/null 2>&1; then
    warn "jq not found — the hooks fail OPEN without it (skill rules still apply)."
    warn "Install it for full hook enforcement:  brew install jq  (macOS) / apt install jq (Linux)"
fi

echo "Next steps:"
echo "  1. RESTART Claude Code — hooks are read at session start; a running"
echo "     session will not pick them up (verify with /hooks in the new session)."
echo "  2. Verify Claude Code sees the skill:"
echo "     claude → type /help and look for code-guardian in the skills list"
echo "  3. The skill is auto-activated when you write/edit code or report a bug;"
echo "     the DECISION GATE blocks option questions without a recommendation;"
echo "     the DEPLOY GATE blocks deploy commands without a fresh gate report."
echo "  4. To uninstall, run:   rm -rf ~/.claude/skills/code-guardian"
echo
if [ "$DRY_RUN" -eq 1 ]; then
    warn "DRY RUN — nothing was actually changed"
fi
