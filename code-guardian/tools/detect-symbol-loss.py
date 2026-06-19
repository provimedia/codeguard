#!/usr/bin/env python3
"""
detect-symbol-loss.py — Code Guardian post-change reflex: silent-symbol-loss gate

Mechanically answers ONE question across an edit: "did a function / method /
class disappear or change its signature without me meaning it to?"  It reports
FACTS (removed / signature-changed / moved symbols); the model reconciles them
against the 1d LEDGER of *intended* changes — anything not in the LEDGER is a
finding. It does NOT judge behaviour: a symbol whose body was rewritten but
whose name+signature are unchanged is invisible here (that is what tests are
for).

Dependency-free on purpose — uses a built-in regex symbol extractor, never an
external ctags (Apple/BSD ctags rejects --output-format). universal-ctags, if
present, is not required.

Two modes:
    # pairwise (testable, and usable against any backup copy):
    detect-symbol-loss.py --before OLD --after NEW [--lang php|js|py|...]

    # git (default for the audit): before-image = git show <ref>:<path>,
    # after-image = working tree, over every changed file:
    detect-symbol-loss.py --git [--ref HEAD] [path ...]

Exit codes:
    0  no symbols lost or signature-changed
    1  at least one symbol lost or signature-changed (findings>0)
    2  usage / environment error

Output ends with a SUMMARY line for paste-as-Verified-by:
    SUMMARY findings=N lost=L changed=C moved=M exit=E
"""

import argparse
import os
import re
import subprocess
import sys

# ----------------------------------------------------------------------
# Language inference by extension (mirrors detect-clones.py "code" kind)
# ----------------------------------------------------------------------
EXT_LANG = {
    ".php": "php", ".py": "py", ".js": "js", ".ts": "js", ".tsx": "js",
    ".jsx": "js", ".vue": "js", ".mjs": "js", ".cjs": "js",
    ".rb": "rb", ".go": "go", ".java": "java", ".kt": "java", ".cs": "java",
}
CODE_EXTS = tuple(EXT_LANG.keys())


# ----------------------------------------------------------------------
# Symbol extraction — regex heads, dependency-free.
# Each pattern captures (name, params). Class-like heads capture name only.
# `[^)]*` spans newlines (char classes match \n in Python) so multi-line
# signatures are handled. Patterns deliberately require a defining keyword or
# a visibility modifier to keep call-sites from masquerading as definitions.
# ----------------------------------------------------------------------
DEF_PATTERNS = [
    # function foo(...) / php+js method "public function foo(...)" / python-ish
    (re.compile(r"\b(?:function|def|fn)\s+(\w+)\s*\(([^)]*)\)"), "func"),
    # go: func (recv) Name(...) / func Name(...)
    (re.compile(r"\bfunc\s+(?:\([^)]*\)\s*)?(\w+)\s*\(([^)]*)\)"), "func"),
    # js/ts arrow- or function-expression assigned to a binding
    (re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?"
                r"(?:function\b\s*)?\(([^)]*)\)\s*(?::[^=>{]+)?=>"), "func"),
    (re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?"
                r"function\b\s*\(([^)]*)\)"), "func"),
    # java/c#/ts class methods: a visibility/modifier keyword then `name(params)`
    (re.compile(r"\b(?:public|private|protected|internal|static|final|"
                r"override|virtual|async)\s+[\w<>\[\],\s\.]+?\s+(\w+)\s*"
                r"\(([^)]*)\)\s*(?:\{|=>|throws|where\b)"), "method"),
    # type declarations (no params)
    (re.compile(r"\b(?:class|interface|trait|struct|enum)\s+(\w+)"), "type"),
]

# words that are never real symbol names even if a head pattern matches them
KEYWORD_NAMES = {
    "if", "for", "foreach", "while", "switch", "catch", "return", "echo",
    "print", "function", "def", "fn", "func", "class", "new", "and", "or",
    "in", "is", "as", "use", "match", "do",
}


def _norm_sig(params):
    """Normalise a parameter list to a comparable contract string.

    Collapses whitespace and strips default values (`= ...`) so that a
    cosmetic default tweak is not flagged, but param add / remove / reorder is.
    """
    p = re.sub(r"\s+", "", params)
    p = re.sub(r"=[^,]*", "", p)      # drop default values
    return p


def extract_symbols(text):
    """Return {name: set(normalised-signatures)} for all definitions in text.

    A name maps to the set of distinct signatures it is defined with (handles
    overloads). Class-like symbols use the sentinel signature '<type>'.
    """
    symbols = {}
    for pat, kind in DEF_PATTERNS:
        for m in pat.finditer(text):
            name = m.group(1)
            if not name or name in KEYWORD_NAMES:
                continue
            if kind == "type":
                sig = "<type>"
            else:
                sig = _norm_sig(m.group(2) if m.lastindex and m.lastindex >= 2 else "")
            symbols.setdefault(name, set()).add(sig)
    return symbols


# ----------------------------------------------------------------------
# Diff of two symbol tables
# ----------------------------------------------------------------------
def diff_symbols(before, after):
    """Return (lost, changed) for one before/after symbol table pair.

    lost    = [name, ...]                 present before, gone after
    changed = [(name, old_sigs, new_sigs)] same name, different signature set
    """
    lost = sorted(set(before) - set(after))
    changed = []
    for name in sorted(set(before) & set(after)):
        if before[name] != after[name]:
            # a type that stays a type is not a signature change
            if before[name] == {"<type>"} and after[name] == {"<type>"}:
                continue
            changed.append((name, before[name], after[name]))
    return lost, changed


# ----------------------------------------------------------------------
# I/O helpers
# ----------------------------------------------------------------------
def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError as e:
        print("error: cannot read %s: %s" % (path, e), file=sys.stderr)
        return None


def git_show(ref, path):
    """Before-image from git; '' if the path did not exist at ref (new file)."""
    try:
        out = subprocess.run(
            ["git", "show", "%s:%s" % (ref, path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as e:
        print("error: git unavailable: %s" % e, file=sys.stderr)
        return None
    if out.returncode != 0:
        return ""  # not in ref => newly added file, nothing to lose
    return out.stdout.decode("utf-8", errors="replace")


def git_changed_files(ref):
    out = subprocess.run(
        ["git", "diff", "--name-only", ref],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if out.returncode != 0:
        return None
    files = [l for l in out.stdout.decode("utf-8", "replace").splitlines() if l]
    return [f for f in files if f.endswith(CODE_EXTS)]


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------
def report_and_exit(per_file, moved):
    """per_file: list of (path, lost[list], changed[list]). moved: set(names)."""
    lost_total = changed_total = 0
    for path, lost, changed in per_file:
        real_lost = [n for n in lost if n not in moved]
        if not real_lost and not changed:
            continue
        print("## %s" % path)
        for name in real_lost:
            print("  LOST     %s()  — defined before, absent after" % name)
            lost_total += 1
        for name, old, new in changed:
            print("  CHANGED  %s(%s)  ->  %s(%s)"
                  % (name, " | ".join(sorted(old)), name, " | ".join(sorted(new))))
            changed_total += 1
        print()

    if moved:
        print("# moved (lost here, re-defined in another changed file — likely fine):")
        for name in sorted(moved):
            print("  MOVED    %s()" % name)
        print()

    findings = lost_total + changed_total
    exit_code = 1 if findings else 0
    print("SUMMARY findings=%d lost=%d changed=%d moved=%d exit=%d"
          % (findings, lost_total, changed_total, len(moved), exit_code))
    return exit_code


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main(argv):
    ap = argparse.ArgumentParser(
        description="Detect silently lost / signature-changed symbols across an edit")
    ap.add_argument("--before", help="pairwise mode: old version of a file")
    ap.add_argument("--after", help="pairwise mode: new version of a file")
    ap.add_argument("--git", action="store_true",
                    help="git mode: compare working tree against --ref")
    ap.add_argument("--ref", default="HEAD",
                    help="git mode: before-image ref (default HEAD)")
    ap.add_argument("paths", nargs="*",
                    help="git mode: limit to these paths (default: all changed)")
    args = ap.parse_args(argv)

    if args.before or args.after:
        if not (args.before and args.after):
            print("error: --before and --after must be given together",
                  file=sys.stderr)
            return 2
        bt = read_file(args.before)
        at = read_file(args.after)
        if bt is None or at is None:
            return 2
        lost, changed = diff_symbols(extract_symbols(bt), extract_symbols(at))
        return report_and_exit([(args.after, lost, changed)], set())

    if not args.git:
        print("error: choose a mode: --before/--after or --git", file=sys.stderr)
        return 2

    paths = args.paths or git_changed_files(args.ref)
    if paths is None:
        print("error: not a git repo or bad --ref: %s" % args.ref, file=sys.stderr)
        return 2
    paths = [p for p in paths if p.endswith(CODE_EXTS)]
    if not paths:
        print("SUMMARY findings=0 lost=0 changed=0 moved=0 exit=0")
        return 0

    per_file = []
    all_lost = {}   # name -> path it was lost from
    all_added = set()
    for path in paths:
        before_text = git_show(args.ref, path)
        if before_text is None:
            return 2
        after_text = read_file(path) if os.path.exists(path) else ""
        if after_text is None:
            after_text = ""
        before = extract_symbols(before_text)
        after = extract_symbols(after_text)
        lost, changed = diff_symbols(before, after)
        per_file.append((path, lost, changed))
        for n in lost:
            all_lost.setdefault(n, path)
        all_added.update(set(after) - set(before))

    # a symbol lost from one file but newly defined in another changed file = moved
    moved = {n for n in all_lost if n in all_added}
    return report_and_exit(per_file, moved)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
