#!/usr/bin/env python3
"""
detect-deploy-artifacts.py — Code Guardian DEPLOY GATE classifier (report-only)

Classifies every path that would travel to (or already lives on) an external
server into the four DEPLOY GATE classes:

    DEPLOY          app code/assets/migrations — belongs on the server (silent)
    SERVER-ONLY     never transfer, MUST exist server-side, never delete
                    (prod .env, storage/, uploads, certs, live sqlite DBs)
    NEVER[high|low] neither transfer nor tolerate on the server
                    (tests, docs, dumps, VCS/CI, audit artifacts | IDE/OS junk)
    REVIEW          context-dependent — the agent decides with evidence
                    (node_modules for SSR, seeders)

The catalogs below are DATA tables (pattern + reason), never branching logic —
the Generalization law applied to this tool itself. Project-specific reality
goes into `.code-guardian-deploy.yml` (extra patterns, documented exceptions),
not into this file.

Report-only like every Code Guardian tool: it never mutates a file.

Modes:
    # Inventory a source tree (drive the D1/D2 exclude check)
    detect-deploy-artifacts.py --root <dir> [--config <yml>]

    # Classify a transfer list — rsync --dry-run --itemize-changes output,
    # plain path lists, or `-` for stdin (THE D1 ground truth)
    detect-deploy-artifacts.py --list <file|-> [--config <yml>]

Exit codes:
    0  only DEPLOY (and ALLOWED) paths
    1  >=1 SERVER-ONLY / NEVER / REVIEW finding
    2  usage / environment error

Output ends with a SUMMARY line for paste-as-Verified-by:
    SUMMARY deploy=N server-only=N never=N review=N allowed=N exit=E
"""

import argparse
import fnmatch
import os
import re
import sys

# ----------------------------------------------------------------------
# Catalogs — DATA, not code. Order of evaluation:
#   ALLOW (config) > DEPLOY-exceptions > SERVER-ONLY > NEVER[high] >
#   NEVER[low] > REVIEW > DEPLOY (default)
# "dir" entries match a path SEGMENT; "glob" entries match the BASENAME;
# "rootglob" entries match root-level paths only (no '/' in the path).
# ----------------------------------------------------------------------

# Files that LOOK like a sensitive pattern but are safe repo content.
DEPLOY_EXCEPTIONS = [
    ("glob", ".env.example", "template without real credentials"),
    ("glob", ".env.dist", "template without real credentials"),
]

SERVER_ONLY_PATTERNS = [
    ("glob", ".env*", "production credentials live server-side only"),
    ("dir", "storage", "runtime state (logs/cache/sessions) is server-owned"),
    ("dir", "uploads", "user uploads are server-owned data"),
    ("dir", ".ssh", "server key material"),
    ("glob", "*.sqlite", "live database file"),
    ("glob", "*.sqlite3", "live database file"),
    ("glob", "*.pem", "TLS/key material is provisioned server-side"),
    ("glob", "*.key", "TLS/key material is provisioned server-side"),
    ("glob", "*.crt", "TLS material is provisioned server-side"),
    ("glob", "id_rsa*", "SSH key material"),
]

NEVER_PATTERNS_HIGH = [
    ("dir", "tests", "test code never runs in production"),
    ("dir", "test", "test code never runs in production"),
    ("dir", "__tests__", "test code never runs in production"),
    ("dir", "spec", "test code never runs in production"),
    ("dir", "specs", "test code never runs in production"),
    ("dir", "cypress", "e2e tooling never runs in production"),
    ("dir", "playwright", "e2e tooling never runs in production"),
    ("dir", "docs", "internal documentation leaks architecture/infra detail"),
    ("dir", "doc", "internal documentation leaks architecture/infra detail"),
    ("dir", ".git", "full VCS history incl. every secret ever committed"),
    ("dir", ".github", "CI config leaks infra detail"),
    ("dir", ".gitlab", "CI config leaks infra detail"),
    ("dir", ".claude", "agent config/session data"),
    ("dir", "__pycache__", "build cache"),
    ("dir", ".pytest_cache", "test cache"),
    ("glob", ".gitlab-ci.yml", "CI config leaks infra detail"),
    ("glob", "*.sql", "database dump — direct data leak"),
    ("glob", "*.dump", "database dump — direct data leak"),
    ("glob", "*.bak", "editor/backup copy bypasses the interpreter (served raw)"),
    ("glob", "*.orig", "merge artifact bypasses the interpreter (served raw)"),
    ("glob", "phpunit.xml*", "test config maps the codebase"),
    ("glob", ".phpunit.result.cache", "test cache"),
    ("glob", ".audit-log.md", "Code Guardian audit trail is internal"),
    ("glob", ".code-guardian-*", "Code Guardian working files are internal"),
    ("glob", "*.log", "logs leak stack traces, paths, tokens"),
    ("glob", "*backup*.tar.gz", "backup archive — direct data leak"),
    ("glob", "*backup*.zip", "backup archive — direct data leak"),
    ("rootglob", "*.tar.gz", "root-level archive is almost always a backup/export"),
    ("rootglob", "*.tgz", "root-level archive is almost always a backup/export"),
    ("rootglob", "*.zip", "root-level archive is almost always a backup/export"),
]

NEVER_PATTERNS_LOW = [
    ("glob", ".DS_Store", "OS junk"),
    ("glob", "Thumbs.db", "OS junk"),
    ("dir", ".idea", "IDE config"),
    ("dir", ".vscode", "IDE config"),
    ("glob", ".editorconfig", "dev tooling, unused at runtime"),
    ("glob", ".eslintrc*", "dev tooling, unused at runtime"),
    ("glob", ".prettierrc*", "dev tooling, unused at runtime"),
    ("glob", "phpstan.neon*", "dev tooling, unused at runtime"),
    ("glob", "psalm.xml", "dev tooling, unused at runtime"),
    ("glob", ".php-cs-fixer*", "dev tooling, unused at runtime"),
    ("glob", "jest.config.*", "test config, unused at runtime"),
    ("glob", "vitest.config.*", "test config, unused at runtime"),
    ("glob", "cypress.config.*", "test config, unused at runtime"),
    ("glob", "docker-compose*", "container config, unused on a file-transfer deploy"),
    ("glob", "Dockerfile*", "container config, unused on a file-transfer deploy"),
    ("glob", "Makefile", "build tooling, unused at runtime"),
    ("glob", "webpack.mix.js", "build config, unused at runtime"),
    ("glob", "vite.config.*", "build config, unused at runtime"),
    ("glob", "*.md", "documentation, unused at runtime"),
    ("glob", ".gitignore", "VCS metadata, unused at runtime"),
    ("glob", ".gitattributes", "VCS metadata, unused at runtime"),
    ("glob", "*.swp", "editor swap file"),
]

REVIEW_PATTERNS = [
    ("dir", "node_modules", "needed only for SSR/node runtime — verify per project"),
    ("dir", "seeders", "prod seeding is project policy — verify per project"),
    ("dir", "seeds", "prod seeding is project policy — verify per project"),
]

# rsync noise lines that are not paths (dry-run / stats output)
_RSYNC_NOISE_PREFIXES = (
    "sending incremental file list", "receiving incremental file list",
    "building file list", "created directory", "sent ", "total size",
    "deleting ", "*deleting",
)
_ITEMIZE_RE = re.compile(r"^[<>ch.*][fdLDSg][.+?cstTpoguaxn]{9}\s+(.+)$")


def load_config(path):
    """Minimal YAML-lite reader: `key: value` scalars and `- item` lists.

    Recognized keys: docroot_url, ssh (scalars); extra_never,
    extra_server_only, allow (lists; allow items are 'pattern: reason').
    No PyYAML — the tool suite stays dependency-free.
    """
    conf = {"docroot_url": None, "ssh": None,
            "extra_never": [], "extra_server_only": [], "allow": []}
    current = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            if not line.startswith((" ", "\t", "-")):
                key, _, val = line.partition(":")
                key, val = key.strip(), val.strip()
                if key in ("extra_never", "extra_server_only", "allow"):
                    current = key
                elif key in conf:
                    conf[key] = val or None
                    current = None
                else:
                    current = None
            elif line.strip().startswith("- ") and current:
                item = line.strip()[2:].strip().strip("'\"")
                if current == "allow":
                    pattern, _, reason = item.partition(":")
                    conf["allow"].append((pattern.strip(), reason.strip() or "allowed"))
                else:
                    conf[current].append(item)
    return conf


def _segment_match(path, name):
    """True if `name` equals any directory segment of `path`."""
    return name in path.split("/")[:-1] or path.rstrip("/").split("/")[-1] == name and path.endswith("/")


def _match_entry(path, kind, pattern):
    base = path.rstrip("/").split("/")[-1]
    if kind == "dir":
        return pattern in path.split("/")[:-1] or (path.endswith("/") and base == pattern)
    if kind == "glob":
        return fnmatch.fnmatch(base, pattern)
    if kind == "rootglob":
        return "/" not in path.rstrip("/") and fnmatch.fnmatch(base, pattern)
    return False


def _display_for(path, kind, pattern):
    """Grouping display: a dir match reports the dir once, not every file."""
    if kind == "dir":
        segs = path.split("/")
        if pattern in segs:
            return "/".join(segs[: segs.index(pattern) + 1]) + "/"
    return path


def _config_pattern_match(path, pattern):
    """Config entries: 'dir/' prefixes-or-segments, otherwise fnmatch on path."""
    if pattern.endswith("/"):
        p = pattern.rstrip("/")
        return path.startswith(pattern) or ("/" + p + "/") in ("/" + path)
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(
        path.rstrip("/").split("/")[-1], pattern)


def _norm(path):
    path = path.replace(os.sep, "/")
    while path.startswith("./"):  # NOT lstrip("./") — that eats a leading dot of '.env'
        path = path[2:]
    return path


def _classify(path, conf=None):
    """Full classification: (CLASS, risk, reason, matched_kind, matched_pattern)."""
    path = _norm(path)
    if conf:
        for pattern, reason in conf.get("allow", []):
            if _config_pattern_match(path, pattern):
                return ("ALLOWED", "", reason, "config", pattern)
        for pattern in conf.get("extra_server_only", []):
            if _config_pattern_match(path, pattern):
                return ("SERVER-ONLY", "", "project config: extra_server_only",
                        "config", pattern)
        for pattern in conf.get("extra_never", []):
            if _config_pattern_match(path, pattern):
                return ("NEVER", "high", "project config: extra_never",
                        "config", pattern)
    for kind, pattern, reason in DEPLOY_EXCEPTIONS:
        if _match_entry(path, kind, pattern):
            return ("DEPLOY", "", reason, kind, pattern)
    for kind, pattern, reason in SERVER_ONLY_PATTERNS:
        if _match_entry(path, kind, pattern):
            return ("SERVER-ONLY", "", reason, kind, pattern)
    for table, risk in ((NEVER_PATTERNS_HIGH, "high"), (NEVER_PATTERNS_LOW, "low")):
        for kind, pattern, reason in table:
            if _match_entry(path, kind, pattern):
                return ("NEVER", risk, reason, kind, pattern)
    for kind, pattern, reason in REVIEW_PATTERNS:
        if _match_entry(path, kind, pattern):
            return ("REVIEW", "", reason, kind, pattern)
    return ("DEPLOY", "", "", "", "")


def classify_path(path, conf=None):
    """Return (CLASS, risk, reason) for a repo-relative path.

    CLASS ∈ DEPLOY | SERVER-ONLY | NEVER | REVIEW | ALLOWED;
    risk is 'high'/'low' for NEVER, '' otherwise.
    """
    cls, risk, reason, _kind, _pattern = _classify(path, conf)
    return (cls, risk, reason)


def parse_list_line(line):
    """Extract the path from a transfer-list line; None for noise lines.

    Accepts rsync --itemize-changes lines, plain path lists, and skips
    rsync chatter and `deleting` entries (removals are not transfers).
    """
    line = line.strip()
    if not line:
        return None
    for prefix in _RSYNC_NOISE_PREFIXES:
        if line.startswith(prefix):
            return None
    m = _ITEMIZE_RE.match(line)
    if m:
        return m.group(1).strip()
    return line


def _grouped_findings(paths, conf):
    """Classify paths; return (counts, ordered {(cls,risk,display,reason): n})."""
    counts = {"DEPLOY": 0, "SERVER-ONLY": 0, "NEVER": 0, "REVIEW": 0, "ALLOWED": 0}
    groups = {}
    for path in paths:
        cls, risk, reason, kind, pattern = _classify(path, conf)
        counts[cls] += 1
        if cls == "DEPLOY":
            continue  # DEPLOY is the silent default
        display = _display_for(_norm(path), kind, pattern)
        key = (cls, risk, display, reason)
        groups[key] = groups.get(key, 0) + 1
    return counts, groups


def _emit(counts, groups):
    order = {"SERVER-ONLY": 0, "NEVER": 1, "REVIEW": 2, "ALLOWED": 3}
    risk_order = {"high": 0, "low": 1, "": 0}
    for (cls, risk, display, reason), n in sorted(
            groups.items(), key=lambda kv: (order[kv[0][0]], risk_order[kv[0][1]], kv[0][2])):
        label = "NEVER[%s]" % risk if cls == "NEVER" else cls
        suffix = " (%d files)" % n if n > 1 else ""
        print("%s %s — %s%s" % (label, display, reason, suffix))
    findings = counts["SERVER-ONLY"] + counts["NEVER"] + counts["REVIEW"]
    code = 1 if findings else 0
    print("SUMMARY deploy=%d server-only=%d never=%d review=%d allowed=%d exit=%d"
          % (counts["DEPLOY"], counts["SERVER-ONLY"], counts["NEVER"],
             counts["REVIEW"], counts["ALLOWED"], code))
    return code


def main():
    ap = argparse.ArgumentParser(
        description="Code Guardian DEPLOY GATE classifier (report-only)")
    ap.add_argument("--root", help="inventory a source tree")
    ap.add_argument("--list", dest="list_file",
                    help="classify a transfer list (file or - for stdin)")
    ap.add_argument("--config", help=".code-guardian-deploy.yml overrides")
    args = ap.parse_args()

    if not args.root and not args.list_file:
        ap.print_usage(sys.stderr)
        return 2
    conf = None
    if args.config:
        if not os.path.isfile(args.config):
            print("config not found: %s" % args.config, file=sys.stderr)
            return 2
        conf = load_config(args.config)

    paths = []
    if args.list_file:
        if args.list_file == "-":
            lines = sys.stdin.read().splitlines()
        else:
            if not os.path.isfile(args.list_file):
                print("list file not found: %s" % args.list_file, file=sys.stderr)
                return 2
            with open(args.list_file, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        for line in lines:
            path = parse_list_line(line)
            if path:
                paths.append(path)
    else:
        if not os.path.isdir(args.root):
            print("root not found: %s" % args.root, file=sys.stderr)
            return 2
        for dirpath, dirnames, filenames in os.walk(args.root):
            for fname in filenames:
                full = os.path.join(dirpath, fname)
                paths.append(os.path.relpath(full, args.root))

    counts, groups = _grouped_findings(paths, conf)
    return _emit(counts, groups)


if __name__ == "__main__":
    sys.exit(main())
