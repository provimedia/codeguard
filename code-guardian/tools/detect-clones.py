#!/usr/bin/env python3
"""
detect-clones.py — Code Guardian Reflex R2 (code) / R3 (html) / R5 (sql)

Find cross-file duplication via normalized-block hashing.

Usage:
    detect-clones.py --root <dir> --kind code|html|sql
                     [--min-locs N] [--min-chars N] [--lines N]
                     [--cross-file-only] [--exclude REGEX] [--json]

Exit codes:
    0  no findings
    1  at least one clone group meets the criteria
    2  usage error

Output ends with a SUMMARY line for paste-as-Verified-by.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

# ----------------------------------------------------------------------
# File extension whitelist per kind
# ----------------------------------------------------------------------
EXT_BY_KIND = {
    "code": (".php", ".py", ".js", ".ts", ".tsx", ".jsx", ".vue",
             ".rb", ".go", ".java", ".kt", ".cs"),
    "html": (".blade.php", ".vue", ".tsx", ".jsx", ".html", ".twig",
             ".latte", ".erb"),
    "sql":  (".php", ".py", ".js", ".ts", ".rb", ".go", ".java", ".kt",
             ".cs", ".sql"),
}

# ----------------------------------------------------------------------
# Default exclude pattern (project-irrelevant or framework noise)
# ----------------------------------------------------------------------
DEFAULT_EXCLUDE = (
    r"(?:^|/)(vendor|node_modules|\.git|storage|public/build|dist|build|"
    r"bower_components|\.idea|\.vscode|coverage|tests/(?:_data|fixtures))"
    r"(?:/|$)"
)


# ----------------------------------------------------------------------
# Normalization
# ----------------------------------------------------------------------
def normalize_code(snippet: str) -> str:
    """Strip whitespace, replace string literals with '?', $vars with $?."""
    s = re.sub(r'"(?:[^"\\]|\\.)*"', '"?"', snippet)
    s = re.sub(r"'(?:[^'\\]|\\.)*'", "'?'", s)
    s = re.sub(r"\$[A-Za-z_]\w*", "$?", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_html(snippet: str) -> str:
    """Collapse whitespace; lowercase tag names; strip class/id attribute values."""
    s = re.sub(r"\s+", " ", snippet).strip()
    s = re.sub(r"<\s*(/?)([A-Za-z][A-Za-z0-9-]*)",
               lambda m: "<" + m.group(1) + m.group(2).lower(), s)
    s = re.sub(r"\s(class|id)\s*=\s*\"[^\"]*\"", "", s)
    s = re.sub(r"\s(class|id)\s*=\s*'[^']*'", "", s)
    return s


def normalize_sql(snippet: str) -> str:
    """Replace bind values, normalize quotes, lowercase keywords."""
    s = re.sub(r'"(?:[^"\\]|\\.)*"', "'?'", snippet)
    s = re.sub(r"'(?:[^'\\]|\\.)*'", "'?'", s)
    s = re.sub(r"\b\d+\b", "?", s)
    s = re.sub(r"\$[A-Za-z_]\w*", "$?", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Lowercase only common SQL keywords for stable hashing.
    for kw in ("SELECT", "FROM", "WHERE", "AND", "OR", "JOIN", "INNER",
               "LEFT", "RIGHT", "OUTER", "ORDER BY", "GROUP BY", "LIMIT",
               "OFFSET", "INSERT INTO", "UPDATE", "DELETE FROM", "VALUES",
               "ON", "AS"):
        s = re.sub(r"\b" + kw + r"\b", kw.lower(), s, flags=re.IGNORECASE)
    return s


# ----------------------------------------------------------------------
# Block extractors
# ----------------------------------------------------------------------
FUNC_HEAD_RE = re.compile(
    r"\b(?:function|def|fn)\s+(\w+)\s*\([^)]*\)[^{:]*[{:]"
    r"|\b(\w+)\s*[:=]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>)\s*\{",
    re.MULTILINE,
)


def extract_code_blocks(text, lines_n=5):
    """Yield (symbol, line_no, snippet) for each function body."""
    for m in FUNC_HEAD_RE.finditer(text):
        name = m.group(1) or m.group(2) or "<anon>"
        start = m.end()
        # Walk braces
        depth = 1
        i = start
        body_lines, used_chars = [], 0
        while i < len(text) and depth > 0 and len(body_lines) < lines_n + 3:
            line_end = text.find("\n", i)
            if line_end < 0:
                break
            line = text[i:line_end].strip()
            for c in text[i:line_end]:
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
            if (line and not line.startswith("//") and not line.startswith("*")
                    and not line.startswith("#")):
                body_lines.append(line)
                used_chars += len(line)
                if len(body_lines) >= lines_n:
                    break
            if depth == 0:
                break
            i = line_end + 1
        if len(body_lines) >= 3:
            line_no = text[:m.start()].count("\n") + 1
            yield (name, line_no, "\n".join(body_lines[:lines_n]))


HTML_BLOCK_RE = re.compile(
    r"<(header|footer|nav|section|form|aside|main|article)\b[^>]*>(.*?)</\1>",
    re.S | re.I,
)


def extract_html_blocks(text, min_chars=200):
    """Yield (tag, line_no, snippet) for each semantic block."""
    for m in HTML_BLOCK_RE.finditer(text):
        inner = m.group(0)
        if len(re.sub(r"\s+", "", inner)) < min_chars:
            continue
        line_no = text[:m.start()].count("\n") + 1
        yield (m.group(1).lower(), line_no, inner)


SQL_PATTERNS = [
    re.compile(
        r"\b([A-Z][A-Za-z0-9_]*)::where\([^;]{15,400}?"
        r"(?:->\s*(?:where|orderBy|orderByDesc|select|with|join|leftJoin|"
        r"whereNull|whereNotNull|whereHas|withCount)\([^;]{0,300}?\))*"
        r"\s*->\s*(?:get|first|firstOrFail|paginate|count|exists|find|sum|avg|max|min)\(\s*[^;]{0,80}?\)",
        re.S,
    ),
    re.compile(
        r"\bDB::(?:table|select|raw|statement|update|insert|delete)\([^;]{15,500}?\)",
        re.S,
    ),
    re.compile(
        r"\b(?:SELECT|select)\s+[\w\*,\s\.]+\s+(?:FROM|from)\s+\w+"
        r"(?:\s+(?:WHERE|where)\s+[^;'\"\n]{1,300})?",
        re.S,
    ),
]


def extract_sql_blocks(text):
    """Yield (label, line_no, snippet) for each SQL/Eloquent fragment."""
    for pat in SQL_PATTERNS:
        for m in pat.finditer(text):
            snippet = m.group(0)
            if len(snippet) < 25:
                continue
            line_no = text[:m.start()].count("\n") + 1
            yield ("query", line_no, snippet)


# ----------------------------------------------------------------------
# Walking
# ----------------------------------------------------------------------
def matches_ext(filename, exts):
    return any(filename.endswith(e) for e in exts)


def iter_files(root, kind, exclude_re):
    exts = EXT_BY_KIND[kind]
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        # filter dirs in-place for performance
        dirnames[:] = [
            d for d in dirnames
            if not exclude_re.search(os.path.relpath(os.path.join(dirpath, d), root))
        ]
        for f in filenames:
            if not matches_ext(f, exts):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            if exclude_re.search(rel):
                continue
            yield full, rel


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main(argv):
    ap = argparse.ArgumentParser(description="Cross-file clone detector")
    ap.add_argument("--root", required=True)
    ap.add_argument("--kind", required=True, choices=("code", "html", "sql"))
    ap.add_argument("--min-locs", type=int, default=2,
                    help="minimum occurrences to flag (default 2)")
    ap.add_argument("--min-chars", type=int, default=200,
                    help="for kind=html: minimum block length (default 200)")
    ap.add_argument("--lines", type=int, default=5,
                    help="for kind=code: leading body lines hashed (default 5)")
    ap.add_argument("--cross-file-only", action="store_true",
                    help="ignore clone groups confined to a single file")
    ap.add_argument("--exclude", default=DEFAULT_EXCLUDE,
                    help="path-relative regex to exclude")
    ap.add_argument("--json", action="store_true",
                    help="emit JSON Lines instead of human format")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        print(f"error: --root not a directory: {args.root}", file=sys.stderr)
        return 2

    try:
        exclude_re = re.compile(args.exclude)
    except re.error as e:
        print(f"error: bad --exclude regex: {e}", file=sys.stderr)
        return 2

    if args.kind == "code":
        extractor = lambda t: extract_code_blocks(t, lines_n=args.lines)
        normalize = normalize_code
    elif args.kind == "html":
        extractor = lambda t: extract_html_blocks(t, min_chars=args.min_chars)
        normalize = normalize_html
    else:
        extractor = extract_sql_blocks
        normalize = normalize_sql

    # sig -> [(rel_path, line_no, symbol, snippet_preview), ...]
    groups = defaultdict(list)

    for full, rel in iter_files(args.root, args.kind, exclude_re):
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for symbol, line_no, snippet in extractor(text):
            norm = normalize(snippet)
            if len(norm) < 30:
                continue
            sig = hashlib.md5(norm.encode("utf-8")).hexdigest()[:8]
            preview = norm[:120]
            groups[sig].append((rel, line_no, symbol, preview))

    # Filter groups
    flagged = []
    for sig, locs in groups.items():
        if len(locs) < args.min_locs:
            continue
        if args.cross_file_only:
            distinct_files = {l[0] for l in locs}
            if len(distinct_files) < 2:
                continue
        flagged.append((sig, locs))

    flagged.sort(key=lambda g: -len(g[1]))

    findings = len(flagged)
    if args.json:
        for sig, locs in flagged:
            obj = {
                "kind": args.kind,
                "hash": sig,
                "count": len(locs),
                "files": sorted({l[0] for l in locs}),
                "locations": [
                    {"file": rel, "line": ln, "symbol": sym}
                    for rel, ln, sym, _ in locs
                ],
                "preview": locs[0][3],
            }
            print(json.dumps(obj))
    else:
        kind_label = {"code": "R2", "html": "R3", "sql": "R5"}[args.kind]
        for sig, locs in flagged:
            distinct_files = sorted({l[0] for l in locs})
            print(f"{kind_label}.{args.kind} clone-group "
                  f"hash={sig} locs={len(locs)} files={len(distinct_files)}")
            for rel, ln, sym, _ in locs[:10]:
                print(f"  {rel}:{ln} :: {sym}")
            if len(locs) > 10:
                print(f"  ... +{len(locs) - 10} more")
            print(f"  --- normalized snippet (first 120 chars):")
            print(f"      {locs[0][3]}")
            print()

    exit_code = 0 if findings == 0 else 1
    print(f"SUMMARY findings={findings} kind={args.kind} exit={exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
