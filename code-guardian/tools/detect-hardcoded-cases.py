#!/usr/bin/env python3
"""
detect-hardcoded-cases.py — Code Guardian example-hardcoding detector (report-only)

Finds the overfitting anti-pattern: literal example values (domains, URLs,
emails, dates, IDs handed in via --examples) that ended up as CONTROL-FLOW
constants — `if ($domain === 'domain1.de')`, `case 'domain1.de':`, a regex
matching exactly the example, or a lookup array keyed by example values —
where the requirement was universal ("every industry", "any domain").
The governing law: an example in the requirement is DATA, never CODE.

Design bias: few false positives beat completeness. A literal is only flagged
when it sits in a DECISION context (if/elif/elseif/switch/case/match/ternary,
comparison / membership / regex-match calls) or as a LOOKUP KEY mapping the
literal to behavior. Plain data usage (config values, log lines, seeder rows)
is not a finding. Config, test, spec, and fixture paths are ignored entirely.

Escape hatch: a line (or one of the 3 lines above it) carrying
`INTENTIONAL-SPECIAL-CASE: <reason>` is counted as intentional, never flagged —
a legitimate business rule for one specific value stays possible, but visible.

Report-only like every Code Guardian tool: it never mutates a file.

Modes:
    # Scan a tree (CLEANUP-style or fixture validation)
    detect-hardcoded-cases.py --root <dir> [--examples a,b] [--exclude REGEX]

    # Scan explicit files
    detect-hardcoded-cases.py --files f1 f2 [--examples a,b]

    # Diff mode (BUILD Self-Slop Sweep): only lines ADDED vs. ref
    detect-hardcoded-cases.py --git [--ref HEAD] [--examples a,b]

Exit codes:
    0  no findings
    1  >=1 finding
    2  usage / environment error

Output ends with a SUMMARY line for paste-as-Verified-by:
    SUMMARY findings=N intentional=I files-scanned=F exit=E
"""

import argparse
import os
import re
import subprocess
import sys

MARKER = "INTENTIONAL-SPECIAL-CASE"
MARKER_LOOKBACK = 3  # marker may sit up to 3 lines above the special-cased line

CODE_EXTS = {
    ".php", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue",
    ".py", ".rb", ".go", ".java", ".kt", ".cs", ".sh", ".bash", ".swift",
}

# Paths that are DATA by definition — never a generalization finding.
# Matched against the path RELATIVE to the scan root (or repo root in --git).
IGNORE_PATH_RE = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs|fixtures?|config|docs?|examples?)(/|$)"
    r"|(^|/)(test_[^/]*|conftest\.py|settings[^/]*|\.env[^/]*)$"
    r"|[._](test|spec)\.[a-z]+$"
    r"|\.config\.[a-z]+$",
    re.IGNORECASE,
)

# A line is a DECISION context when it branches or compares.
DECISION_RE = re.compile(
    r"(^|[^\w$])(if|elif|elseif|else\s+if|switch|case|match|when|unless)\s*[\s(:]"
    r"|===?|!==?|<>"
    r"|\bin_array\s*\(|\.includes\s*\(|\.startsWith\s*\(|\.endsWith\s*\("
    r"|\bstr_contains\s*\(|\bstr_starts_with\s*\(|\bstr_ends_with\s*\(|\bstrpos\s*\("
    r"|\bpreg_match\s*\(|\bre\.(match|search|fullmatch)\s*\(|\.test\s*\(",
    re.IGNORECASE,
)

COMMENT_RE = re.compile(r"^\s*(#|//|\*|/\*|--|<!--)")

# Business TLDs only — an allowlist keeps `file.py`, `obj.prop` etc. unmatched.
_TLDS = (
    "de|com|net|org|io|ai|co|eu|at|ch|info|biz|shop|online|store|dev|app|cloud"
    "|me|tv|uk|us|fr|it|nl|es|pl|se|dk|cz|hu|gr|pt|fi|no|be|ie"
)
LITERAL_CLASSES = [
    ("url",    re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)),
    ("email",  re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}", re.IGNORECASE)),
    ("domain", re.compile(
        r"(?<![\w@.-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:%s)(?![\w-])" % _TLDS,
        re.IGNORECASE)),
    ("date",   re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\.\d{1,2}\.\d{4}\b")),
]


def is_ignored_path(relpath):
    """Config/test/spec/fixture paths and non-code extensions are DATA — skip."""
    rp = relpath.replace(os.sep, "/")
    if os.path.splitext(rp)[1].lower() not in CODE_EXTS:
        return True
    return bool(IGNORE_PATH_RE.search(rp))


def normalize(line):
    """Un-escape regex-literal dots so /domain1\\.de/ matches the domain class."""
    return line.replace("\\.", ".")


def suspicious_literals(line):
    """Return deduped [(class, literal)] found in the line, masking overlaps
    so an email does not additionally report its domain part."""
    norm = normalize(line)
    found, masked = [], []
    for cls, rx in LITERAL_CLASSES:
        for m in rx.finditer(norm):
            if any(m.start() < e and m.end() > s for s, e in masked):
                continue
            masked.append((m.start(), m.end()))
            found.append((cls, m.group(0)))
    return found


def is_decision_context(line):
    return bool(DECISION_RE.search(line))


def is_lookup_key(line, literal):
    """True when the literal is an array/dict KEY mapping it to behavior:
    'domain1.de' => …   or   'domain1.de': …"""
    rx = re.compile(r"['\"]" + re.escape(literal) + r"['\"]\s*(=>|:)")
    return bool(rx.search(normalize(line)))


def line_findings(line, prev_lines, examples):
    """Pure per-line classifier. prev_lines = up to MARKER_LOOKBACK preceding
    lines (for the marker). Returns (findings, intentional_count)."""
    context = "".join(prev_lines) + line
    if MARKER in context:
        # A decision on a suspicious literal under the marker is intentional.
        if (is_decision_context(line) and suspicious_literals(line)) or any(
            is_lookup_key(line, lit) for _, lit in suspicious_literals(line)
        ):
            return [], 1
        return [], 0
    if COMMENT_RE.match(line):
        return [], 0

    findings = []
    lits = suspicious_literals(line)
    decision = is_decision_context(line)
    for cls, lit in lits:
        if decision or is_lookup_key(line, lit):
            findings.append((cls, lit))
    # Explicit requirement examples are hard-flagged in ANY code context —
    # the example belongs in data/config, not in the source at all.
    norm = normalize(line).lower()
    for ex in examples:
        if ex and ex.lower() in norm and not any(l.lower() == ex.lower() for _, l in findings):
            findings.append(("example", ex))
    return findings, 0


def scan_lines(relpath, numbered_lines, examples):
    """numbered_lines: iterable of (lineno, text). Returns (findings, intentional)."""
    findings, intentional = [], 0
    window = []
    for lineno, text in numbered_lines:
        f, i = line_findings(text, window, examples)
        intentional += i
        for cls, lit in f:
            findings.append((relpath, lineno, cls, lit, text.strip()[:120]))
        window.append(text)
        if len(window) > MARKER_LOOKBACK:
            window.pop(0)
    return findings, intentional


def scan_file(path, relpath, examples):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        print("warn: cannot read %s: %s" % (path, exc), file=sys.stderr)
        return [], 0
    return scan_lines(relpath, enumerate(lines, 1), examples)


def iter_tree(root, exclude_re):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "vendor"}]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if exclude_re and exclude_re.search(rel.replace(os.sep, "/")):
                continue
            if is_ignored_path(rel):
                continue
            yield full, rel


def added_lines_from_git(ref):
    """Yield (relpath, lineno, text) for every line ADDED vs. ref."""
    try:
        out = subprocess.run(
            ["git", "diff", "--unified=0", ref],
            check=True, stdout=subprocess.PIPE, text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print("error: git diff failed: %s" % exc, file=sys.stderr)
        sys.exit(2)
    relpath, lineno = None, 0
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            relpath = raw[6:]
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            lineno = int(m.group(1)) if m else 0
        elif raw.startswith("+") and not raw.startswith("+++") and relpath:
            yield relpath, lineno, raw[1:] + "\n"
            lineno += 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Example-hardcoding detector (report-only)")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--root", help="directory tree to scan")
    mode.add_argument("--files", nargs="+", help="explicit files to scan")
    mode.add_argument("--git", action="store_true", help="scan only lines added vs --ref")
    ap.add_argument("--ref", default="HEAD", help="git ref for --git (default HEAD)")
    ap.add_argument("--examples", default="",
                    help="comma-separated example literals from the requirement")
    ap.add_argument("--exclude", default="", help="extra path-exclude regex (relative)")
    args = ap.parse_args(argv)

    examples = [e.strip() for e in args.examples.split(",") if e.strip()]
    exclude_re = re.compile(args.exclude) if args.exclude else None

    findings, intentional, files_scanned = [], 0, 0

    if args.git:
        per_file = {}
        for rel, lineno, text in added_lines_from_git(args.ref):
            if is_ignored_path(rel) or (exclude_re and exclude_re.search(rel)):
                continue
            per_file.setdefault(rel, []).append((lineno, text))
        for rel, numbered in per_file.items():
            files_scanned += 1
            f, i = scan_lines(rel, numbered, examples)
            findings.extend(f)
            intentional += i
    elif args.root:
        if not os.path.isdir(args.root):
            print("error: not a directory: %s" % args.root, file=sys.stderr)
            return 2
        for full, rel in iter_tree(args.root, exclude_re):
            files_scanned += 1
            f, i = scan_file(full, rel, examples)
            findings.extend(f)
            intentional += i
    else:
        for path in args.files:
            if not os.path.isfile(path):
                print("error: not a file: %s" % path, file=sys.stderr)
                return 2
            if is_ignored_path(path):
                continue
            files_scanned += 1
            f, i = scan_file(path, path, examples)
            findings.extend(f)
            intentional += i

    for rel, lineno, cls, lit, ctx in findings:
        print("FINDING %s:%d [%s] literal='%s' | %s" % (rel, lineno, cls, lit, ctx))

    exit_code = 1 if findings else 0
    print("SUMMARY findings=%d intentional=%d files-scanned=%d exit=%d"
          % (len(findings), intentional, files_scanned, exit_code))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
