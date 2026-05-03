#!/usr/bin/env bash
#
# detect-secrets.sh — Code Guardian Reflex R1
# --------------------------------------------
# Scans a directory for hardcoded credentials in two stages:
#   Stage A — known-prefix patterns (high precision)
#   Stage B — same secret appearing in 2+ files (duplication)
#
# Stage C (high-entropy literals) is OFF by default; opt in with
# --strict-entropy. It produces noise without project tuning.
#
# Usage:
#   detect-secrets.sh <root-dir> [--strict-entropy]
#
# Exit codes:
#   0 — no findings
#   1 — at least one finding (caller may treat as BLOCKED)
#   2 — usage error
#
# Output ends with a SUMMARY line the caller can paste as "Verified-by".

set -u

ROOT="${1:-}"
STRICT_ENTROPY=0
shift || true
for arg in "$@"; do
    case "$arg" in
        --strict-entropy) STRICT_ENTROPY=1 ;;
        -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

if [ -z "$ROOT" ] || [ ! -d "$ROOT" ]; then
    echo "usage: $0 <root-dir> [--strict-entropy]" >&2
    exit 2
fi

# Common excludes — never scan these (paths or globs)
EXCLUDE_DIRS=(
    --exclude-dir=vendor
    --exclude-dir=node_modules
    --exclude-dir=.git
    --exclude-dir=storage
    --exclude-dir=public
    --exclude-dir=dist
    --exclude-dir=build
)
EXCLUDE_FILES=(
    --exclude='*.lock'
    --exclude='*.min.*'
    --exclude='*.map'
    --exclude='*.svg'
    --exclude='*.png'
    --exclude='*.jpg'
    --exclude='*.jpeg'
    --exclude='*.gif'
    --exclude='*.webp'
)
# Note: .env / .env.* are intentionally NOT included. Hardcoded secrets in
# .env are CORRECT (that's the configured-out-of-source path). Stage A is
# about secrets leaking into source/config files where they don't belong.
INCLUDE_FILES=(
    --include='*.php'
    --include='*.js'
    --include='*.ts'
    --include='*.tsx'
    --include='*.jsx'
    --include='*.vue'
    --include='*.py'
    --include='*.rb'
    --include='*.go'
    --include='*.java'
    --include='*.kt'
    --include='*.cs'
    --include='*.sh'
    --include='*.yml'
    --include='*.yaml'
    --include='*.json'
    --include='*.config'
    --include='*.conf'
)

# Mask a secret literal: first 6 + last 4, middle redacted.
mask() {
    awk -v s="$1" 'BEGIN {
        n = length(s)
        if (n <= 12) { printf "%s***", substr(s,1,3); next }
        printf "%s...%s", substr(s,1,6), substr(s,n-3,4)
    }'
}

stages=""
findings=0

#####################################################################
# Stage A — known-prefix patterns
#####################################################################
PATTERN_A='(AIza[A-Za-z0-9_-]{35}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}|xox[baprs]-[A-Za-z0-9-]{10,}|hf_[A-Za-z0-9]{30,}|eyJ[A-Za-z0-9_=-]{15,}\.eyJ[A-Za-z0-9_=-]{15,}|https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+|https://discord(app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----|SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43})'

raw_a=$(grep -rEn "$PATTERN_A" "${INCLUDE_FILES[@]}" "${EXCLUDE_DIRS[@]}" "${EXCLUDE_FILES[@]}" "$ROOT" 2>/dev/null || true)

if [ -n "$raw_a" ]; then
    echo "R1.A known-prefix matches:"
    while IFS= read -r line; do
        # extract: file:line:rest
        file_line="${line%%:*}"
        rest="${line#*:}"
        lineno="${rest%%:*}"
        body="${rest#*:}"
        # extract the matching token from the body
        token=$(echo "$body" | grep -oE "$PATTERN_A" | head -1)
        masked=$(mask "$token")
        echo "  ${file_line}:${lineno}  ${masked}"
        findings=$((findings + 1))
    done <<< "$raw_a"
    stages="${stages}A"
fi

#####################################################################
# Stage B — same secret in N files (duplication of a hardcoded value)
#####################################################################
# POSIX-portable: macOS bash 3.2 has no `declare -A`. We build (token, file)
# pairs via a temp file, sort -u to dedupe, then awk groups by token.
if [ -n "$raw_a" ]; then
    pairs_file=$(mktemp -t cg-secrets.XXXXXX)
    trap 'rm -f "$pairs_file"' EXIT
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        file_line="${line%%:*}"
        rest="${line#*:}"
        body="${rest#*:}"
        token=$(printf '%s' "$body" | grep -oE "$PATTERN_A" | head -1)
        [ -n "$token" ] && printf '%s\t%s\n' "$token" "$file_line" >> "$pairs_file"
    done <<< "$raw_a"

    # Group by token, emit only those with >= 2 distinct files.
    dup_tokens=$(sort -u "$pairs_file" | awk -F'\t' '{c[$1]++} END {for (t in c) if (c[t] >= 2) print t}')

    if [ -n "$dup_tokens" ]; then
        echo
        echo "R1.B duplicate secrets across files:"
        stages="${stages}B"
        while IFS= read -r tok; do
            [ -z "$tok" ] && continue
            masked=$(mask "$tok")
            # collect distinct files for this token
            files_for_tok=$(sort -u "$pairs_file" | awk -F'\t' -v t="$tok" '$1==t {print $2}')
            file_count=$(printf '%s\n' "$files_for_tok" | grep -c .)
            echo "  ${file_count} files share secret ${masked}:"
            printf '%s\n' "$files_for_tok" | sed 's/^/    /'
            findings=$((findings + 1))
        done <<< "$dup_tokens"
    fi
fi

#####################################################################
# Stage C (opt-in) — high-entropy literals in assignments
#####################################################################
if [ "$STRICT_ENTROPY" -eq 1 ]; then
    raw_c=$(grep -rEn "['\"=]\s*([A-Za-z0-9+/_=-]{32,})\s*['\"]" \
        "${INCLUDE_FILES[@]}" "${EXCLUDE_DIRS[@]}" "${EXCLUDE_FILES[@]}" "$ROOT" 2>/dev/null \
        | grep -vE "(slug|class|icon|heroicon|namespace|use\s+[A-Z]|@route|@param|@return|@var|->trans|__\(|trans\()" \
        | head -200 || true)
    if [ -n "$raw_c" ]; then
        echo
        echo "R1.C high-entropy literals (review manually — many false positives):"
        echo "$raw_c" | head -30
        c_count=$(echo "$raw_c" | wc -l | tr -d ' ')
        findings=$((findings + c_count))
        stages="${stages}C"
    fi
fi

#####################################################################
# Footer
#####################################################################
echo
[ -z "$stages" ] && stages="none"
exit_code=0
[ "$findings" -gt 0 ] && exit_code=1
echo "SUMMARY findings=${findings} stages=${stages} exit=${exit_code}"
exit "$exit_code"
