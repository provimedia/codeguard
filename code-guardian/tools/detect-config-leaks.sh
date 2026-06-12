#!/usr/bin/env bash
#
# detect-config-leaks.sh — Code Guardian Reflex R4
# -------------------------------------------------
# Find duplicated absolute identifiers (URL / email / filesystem path)
# that should live in config files, not be hardcoded in 2+ source files.
#
# Usage:
#   detect-config-leaks.sh <root-dir> [--min-locs N] [--exclude REGEX]
#
# Exit codes:
#   0 — no duplicates
#   1 — at least one duplicate identifier
#   2 — usage error
#
# Output ends with a SUMMARY line.

set -u

ROOT="${1:-}"
MIN_LOCS=2
EXTRA_EXCLUDE=""
shift || true
while [ "$#" -gt 0 ]; do
    case "$1" in
        --min-locs) MIN_LOCS="$2"; shift 2 ;;
        --exclude)  EXTRA_EXCLUDE="$2"; shift 2 ;;
        -h|--help)  sed -n '2,18p' "$0"; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [ -z "$ROOT" ] || [ ! -d "$ROOT" ]; then
    echo "usage: $0 <root-dir> [--min-locs N] [--exclude REGEX]" >&2
    exit 2
fi

EXCLUDE_DIRS=(
    --exclude-dir=vendor
    --exclude-dir=node_modules
    --exclude-dir=.git
    --exclude-dir=storage
    --exclude-dir=public
    --exclude-dir=dist
    --exclude-dir=build
    --exclude-dir=tests
)
INCLUDE_FILES=(
    --include='*.php'
    --include='*.js'
    --include='*.ts'
    --include='*.tsx'
    --include='*.jsx'
    --include='*.vue'
    --include='*.py'
    --include='*.rb'
)
EXCLUDE_FILES=(
    --exclude='*.lock'
    --exclude='*.min.*'
    --exclude='*.map'
    --exclude='*.svg'
)

# Note: seeders/factories often legitimately list URLs (customer demo data).
# We exclude them by default.
DEFAULT_PATH_EXCLUDE='database/(seeders|factories)|tests/'
ALL_PATH_EXCLUDE="$DEFAULT_PATH_EXCLUDE"
[ -n "$EXTRA_EXCLUDE" ] && ALL_PATH_EXCLUDE="${ALL_PATH_EXCLUDE}|${EXTRA_EXCLUDE}"

# Allowlists are matched against the LITERAL only (column 1, not the
# whole `literal\tfile` line). Each pattern is anchored with ^...$
# implicitly inside awk's match against $1.
URL_ALLOW='^https?://(www\.)?(schema\.org|w3\.org|example\.(com|org|net)|github\.com|gravatar\.com|placehold\.(it|co)|via\.placeholder\.com|localhost([:/].*)?)(/.*)?$'
# Email allowlist — match the LITERAL only.
# Covers: example/test/localhost domains, hyphen-test subdomains
# (e.g. *-test.de), test-prefixed locals, .test TLD, and the "@email.<tld>"
# placeholder convention used in localized form templates
# (your@email.com, votre@email.fr, ihre@email.de, uw@email.nl, etc.).
EMAIL_ALLOW='^([a-z0-9._-]+@(example\.(com|org|net)|domain\.tld|test\.(com|local)|localhost)|.+@email\.[a-z]{2,4}|.+-test\..+|test@.+|.*@.+\.test)$'
PATH_ALLOW='^(/var/(www|html|task|log)|/Users/[^/]+|/home/[^/]+|/opt|/tmp)/?$'

findings=0
stages=""

scan_kind() {
    local label="$1" pattern="$2" allow_re="$3"
    # grep -roEn produces "file:line:literal". Reformat to "literal\tfile",
    # filter excluded paths, drop allowlisted literals, then group by literal.
    local raw
    raw=$(grep -roEn "$pattern" "${INCLUDE_FILES[@]}" "${EXCLUDE_DIRS[@]}" "${EXCLUDE_FILES[@]}" "$ROOT" 2>/dev/null \
          | grep -vE "$ALL_PATH_EXCLUDE" \
          | awk -F: '{
                file=$1
                body=$0
                sub(/^[^:]+:[^:]+:/, "", body)
                printf "%s\t%s\n", body, file
            }' \
          | sort -u)

    [ -z "$raw" ] && return 0

    # Allowlist filter — applied to column 1 (the literal) only
    if [ -n "$allow_re" ]; then
        raw=$(printf '%s\n' "$raw" | awk -F'\t' -v re="$allow_re" '$1 !~ re {print}')
    fi
    [ -z "$raw" ] && return 0

    # Group by literal, emit groups with distinct-file-count >= MIN_LOCS
    local dup_block
    dup_block=$(printf '%s\n' "$raw" | awk -F'\t' -v m="$MIN_LOCS" '
        { c[$1]++ }
        END { for (k in c) if (c[k] >= m) print c[k] "\t" k }
    ' | sort -rn)

    [ -z "$dup_block" ] && return 0

    echo "R4.${label} duplicate $label (≥${MIN_LOCS} files):"
    while IFS=$'\t' read -r cnt literal; do
        [ -z "$literal" ] && continue
        echo "  ${cnt}× ${literal}"
        findings=$((findings + 1))
    done <<< "$dup_block"
    stages="${stages}${label:0:1}"
    echo
}

# Stage U — URLs
scan_kind "URL" 'https?://[A-Za-z0-9._/?=&%+-]{4,}' "$URL_ALLOW"

# Stage E — emails
scan_kind "EMAIL" '[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,12}' "$EMAIL_ALLOW"

# Stage P — absolute filesystem paths
scan_kind "PATH" '(/var/[A-Za-z0-9._/-]+|/Users/[A-Za-z0-9._/-]+|/home/[A-Za-z0-9._/-]+|/opt/[A-Za-z0-9._/-]+|[A-Z]:\\\\[A-Za-z0-9._\\-]+)' "$PATH_ALLOW"

[ -z "$stages" ] && stages="none"
exit_code=0
[ "$findings" -gt 0 ] && exit_code=1
echo "SUMMARY findings=${findings} stages=${stages} exit=${exit_code}"
exit "$exit_code"
