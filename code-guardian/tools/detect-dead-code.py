#!/usr/bin/env python3
"""
detect-dead-code.py — Code Guardian liveness-evidence aggregator (report-only)

Mechanically gathers EVIDENCE for whether a symbol is reachable; it never
deletes, rewrites, or otherwise mutates a source file. The governing axiom is
asymmetric: ANY reference proves a symbol LIVE, but the ABSENCE of references
never proves it dead (string-resolved routes, Blade/Vue components, Eloquent
magic, DI containers, migrations and webhooks all reach code the static graph
cannot see). So the tool reports a graded verdict and the human decides.

Dependency-free on purpose — a built-in regex symbol extractor (shared verbatim
with detect-symbol-loss.py) plus whole-word grep across every text file, and the
`git` CLI for the diff. No ctags, no AST library.

Two modes:
    # Self-slop gate (BUILD MODE): own additions in the working-tree diff that
    # nothing references yet, plus debug leftovers on the added lines.
    detect-dead-code.py --diff-slop [--ref HEAD] [path ...]

    # Liveness classifier (CLEANUP MODE, opt-in): classify pre-existing symbols.
    detect-dead-code.py --liveness NAME [NAME ...] [--root .]

Exit codes:
    0  no actionable findings
    1  >=1 finding (REMOVABLE / DEBUG-LEFTOVER, or any VERIFIED-DEAD-PRIVATE)
    2  usage / environment error

Output ends with a SUMMARY line for paste-as-Verified-by:
    SUMMARY findings=N live=L asserted=A verified=V exit=E
"""

import argparse
import os
import re
import subprocess
import sys

# ----------------------------------------------------------------------
# Language inference by extension (mirrors detect-symbol-loss.py)
# ----------------------------------------------------------------------
EXT_LANG = {
    ".php": "php", ".py": "py", ".js": "js", ".ts": "js", ".tsx": "js",
    ".jsx": "js", ".vue": "js", ".mjs": "js", ".cjs": "js",
    ".rb": "rb", ".go": "go", ".java": "java", ".kt": "java", ".cs": "java",
}
CODE_EXTS = tuple(EXT_LANG.keys())

# JS-family extensions: a non-exported function/class here is closed-world
# (it can never be imported), exactly like a PHP `private` member.
JS_EXTS = frozenset(e for e, lang in EXT_LANG.items() if lang == "js")

# All text files a reference could live in (code + templates + data + docs).
# `.env*` is matched by filename below, not by extension.
TEXT_EXTS = CODE_EXTS + (
    ".blade.php", ".html", ".twig",
    ".json", ".yaml", ".yml",
    ".sql", ".md",
)

# ----------------------------------------------------------------------
# Default exclude pattern (copied from detect-clones.py)
# ----------------------------------------------------------------------
DEFAULT_EXCLUDE = (
    r"(?:^|/)(vendor|node_modules|\.git|storage|public/build|dist|build|"
    r"bower_components|\.idea|\.vscode|coverage|tests/(?:_data|fixtures))"
    r"(?:/|$)"
)


def _default_exclude():
    return re.compile(DEFAULT_EXCLUDE)


# ----------------------------------------------------------------------
# Symbol extraction — regex heads, dependency-free (verbatim from
# detect-symbol-loss.py). Each pattern captures (name, params); class-like
# heads capture name only.
# ----------------------------------------------------------------------
DEF_PATTERNS = [
    (re.compile(r"\b(?:function|def|fn)\s+(\w+)\s*\(([^)]*)\)"), "func"),
    (re.compile(r"\bfunc\s+(?:\([^)]*\)\s*)?(\w+)\s*\(([^)]*)\)"), "func"),
    (re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?"
                r"(?:function\b\s*)?\(([^)]*)\)\s*(?::[^=>{]+)?=>"), "func"),
    (re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?"
                r"function\b\s*\(([^)]*)\)"), "func"),
    (re.compile(r"\b(?:public|private|protected|internal|static|final|"
                r"override|virtual|async)\s+[\w<>\[\],\s\.]+?\s+(\w+)\s*"
                r"\(([^)]*)\)\s*(?:\{|=>|throws|where\b)"), "method"),
    (re.compile(r"\b(?:class|interface|trait|struct|enum)\s+(\w+)"), "type"),
]

# words that are never real symbol names even if a head pattern matches them
KEYWORD_NAMES = {
    "if", "for", "foreach", "while", "switch", "catch", "return", "echo",
    "print", "function", "def", "fn", "func", "class", "new", "and", "or",
    "in", "is", "as", "use", "match", "do",
}


def _norm_sig(params):
    p = re.sub(r"\s+", "", params)
    p = re.sub(r"=[^,]*", "", p)      # drop default values
    return p


def extract_symbols(text):
    """Return {name: set(normalised-signatures)} for all definitions in text."""
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


def extract_added_symbols(before_text, after_text):
    """Symbols defined in `after` but not in `before` -> {name: set(sigs)}."""
    before = extract_symbols(before_text)
    after = extract_symbols(after_text)
    return {n: after[n] for n in after if n not in before}


def _def_positions(text, name):
    """Start offsets of `name` where it is a *definition* head (dedup'd by
    name-token position, so overlapping patterns are not double-counted)."""
    pos = set()
    for pat, _kind in DEF_PATTERNS:
        for m in pat.finditer(text):
            if m.group(1) == name:
                pos.add(m.start(1))
    return pos


# ----------------------------------------------------------------------
# I/O helpers (read_file / git_show / git_changed_files from detect-symbol-loss)
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
        return ""  # not in ref => newly added file
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


def git_added_lines(ref, path):
    """Return [(new_line_no, content)] for every '+' line in `git diff ref -- path`."""
    out = subprocess.run(
        ["git", "diff", ref, "--", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if out.returncode != 0:
        return []
    added = []
    newno = 0
    for ln in out.stdout.decode("utf-8", "replace").splitlines():
        if ln.startswith("@@"):
            m = re.search(r"\+(\d+)", ln)
            newno = int(m.group(1)) if m else 0
            continue
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln.startswith("+"):
            added.append((newno, ln[1:]))
            newno += 1
        elif ln.startswith("-"):
            continue
        else:  # context line advances the new-file counter
            newno += 1
    return added


# ----------------------------------------------------------------------
# Small text utilities
# ----------------------------------------------------------------------
def _line_at(text, idx):
    start = text.rfind("\n", 0, idx) + 1
    end = text.find("\n", idx)
    if end < 0:
        end = len(text)
    return text[start:end]


def _ext_of(path):
    return os.path.splitext(path)[1].lower()


def _is_text_file(filename):
    if filename.startswith(".env"):
        return True
    return any(filename.endswith(e) for e in TEXT_EXTS)


def _iter_text_files(root, exclude_re):
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if not exclude_re.search(
                os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/"))
        ]
        for f in filenames:
            if not _is_text_file(f):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if exclude_re.search(rel):
                continue
            yield full, rel


def _kebab(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _under_tests(rel):
    return re.search(r"(^|/)tests?/", rel) is not None


# ----------------------------------------------------------------------
# Reference counting
# ----------------------------------------------------------------------
def count_refs(name, root, exclude_re):
    """Whole-word `\\bname\\b` occurrences across every text file under root,
    minus the definition occurrences. Absence (0) never proves dead."""
    word = re.compile(r"\b" + re.escape(name) + r"\b")
    total = 0
    defs = 0
    for full, _rel in _iter_text_files(root, exclude_re):
        text = read_file(full)
        if text is None:
            continue
        total += len(word.findall(text))
        defs += len(_def_positions(text, name))
    return total - defs


# ----------------------------------------------------------------------
# Definition site lookup (privacy / def-file)
# ----------------------------------------------------------------------
def _is_private(def_line, name, ext):
    if re.search(r"\bprivate\b", def_line):
        return True
    if ext == ".py" and re.search(r"\bdef\s+_\w", def_line):
        return True
    if name.startswith("_"):
        return True
    return False


def _js_is_exported(text, def_line, name):
    """True if a JS/TS symbol `name` is exported from its module — i.e. an
    external importer could reach it (open-world). Checks the inline `export`
    on the def line plus the four out-of-line export forms in the whole file."""
    # inline:  export function/class/const NAME ...  (export before the symbol)
    name_pos = def_line.find(name)
    before = def_line[:name_pos] if name_pos >= 0 else def_line
    if re.search(r"\bexport\b", before):
        return True
    n = re.escape(name)
    # named:   export { ... NAME ... }
    if re.search(r"export\s*\{[^}]*\b" + n + r"\b", text):
        return True
    # default: export default NAME
    if re.search(r"export\s+default\s+" + n + r"\b", text):
        return True
    # CommonJS: module.exports ... NAME   /   exports.NAME
    if re.search(r"module\.exports\b.*\b" + n + r"\b", text):
        return True
    if re.search(r"\bexports\." + n + r"\b", text):
        return True
    return False


def find_definition(name, root, exclude_re):
    """Return (def_file_rel | None, is_private, def_line) for the first
    definition of `name` found under root."""
    for full, rel in _iter_text_files(root, exclude_re):
        text = read_file(full)
        if text is None:
            continue
        for pat, _kind in DEF_PATTERNS:
            for m in pat.finditer(text):
                if m.group(1) == name:
                    line = _line_at(text, m.start(1))
                    ext = _ext_of(rel)
                    if ext in JS_EXTS:
                        # Non-exported JS/TS module-locals are closed-world
                        # (cannot be imported); any export => open-world.
                        is_private = not _js_is_exported(text, line, name)
                    else:
                        is_private = _is_private(line, name, ext)
                    return rel, is_private, line
    return None, False, ""


# ----------------------------------------------------------------------
# Framework false-positive flags — each is a keep-alive veto
# ----------------------------------------------------------------------
RELATION_RE = re.compile(
    r"->\s*(hasMany|hasOne|belongsToMany|belongsTo|morphToMany|morphedByMany|"
    r"morphTo|morphMany|morphOne|hasManyThrough|hasOneThrough)\s*\(")

_ENTRYPOINT_NAME_RE = re.compile(r"(Job|Listener|Observer|Webhook|Command|Subscriber)$")
_ENTRYPOINT_FILE_RE = re.compile(r"(Job|Listener|Observer|Webhook|Command|Subscriber)")


def fp_flags_for(name, root, def_file, exclude_re):
    """Compute the set of framework keep-alive vetoes for `name`."""
    flags = set()
    word = re.compile(r"\b" + re.escape(name) + r"\b")

    # magic by name shape (Eloquent scope / accessor)
    if re.match(r"scope[A-Z]", name) or re.match(r"(get|set)[A-Za-z0-9_]*Attribute$", name):
        flags.add("magic")
    # entrypoint by name shape
    if _ENTRYPOINT_NAME_RE.search(name):
        flags.add("entrypoint")

    # def-file-derived flags
    if def_file:
        dfl = def_file.lower()
        base = os.path.basename(def_file)
        if dfl.startswith("app/console") or "/app/console/" in "/" + dfl:
            flags.add("entrypoint")
        if _ENTRYPOINT_FILE_RE.search(base):
            flags.add("entrypoint")
        dtext = read_file(os.path.join(os.path.abspath(root), def_file))
        if dtext:
            mdef = re.search(r"function\s+" + re.escape(name) + r"\s*\(", dtext)
            if mdef and RELATION_RE.search(dtext[mdef.end():mdef.end() + 200]):
                flags.add("magic")  # relation-like public method

    # template forms for blade_vue
    kebab = _kebab(name)
    pascal = name[:1].upper() + name[1:]
    tmpl_pat = re.compile(
        r"<x-" + re.escape(kebab) + r"\b"
        r"|<" + re.escape(pascal) + r"[\s/>]"
        r"|<" + re.escape(kebab) + r"[-\s/>]")
    name_class = re.compile(r"\b" + re.escape(name) + r"::class\b")
    name_str = re.compile(r"['\"]" + re.escape(name) + r"['\"]")

    refs_tests = 0
    refs_other = 0
    for full, rel in _iter_text_files(root, exclude_re):
        text = read_file(full)
        if text is None:
            continue
        low = rel.lower()
        if rel.endswith((".blade.php", ".vue", ".html", ".twig")) and tmpl_pat.search(text):
            flags.add("blade_vue")
        positions = [m.start() for m in word.finditer(text)]
        if not positions:
            continue
        # route
        if low.startswith("routes/") or "/routes/" in "/" + low:
            flags.add("route")
        else:
            for p in positions:
                ln = _line_at(text, p)
                if "Route::" in ln or "->name(" in ln:
                    flags.add("route")
                    break
        # di_config
        if low.startswith("config/") or "/config/" in "/" + low \
                or rel.endswith((".json", ".yaml", ".yml")):
            if name_class.search(text) or name_str.search(text):
                flags.add("di_config")
        # db_dispatch
        if "database/migrations" in low or "database/seeders" in low \
                or rel.endswith(".sql"):
            flags.add("db_dispatch")
        # test_only ref accounting (non-definition occurrences)
        nondef = len(positions) - len(_def_positions(text, name))
        if nondef > 0:
            if _under_tests(rel):
                refs_tests += nondef
            else:
                refs_other += nondef

    if refs_tests > 0 and refs_other == 0:
        flags.add("test_only")
    return flags


# ----------------------------------------------------------------------
# Liveness verdict (pure decision table)
# ----------------------------------------------------------------------
def classify_symbol(name, refs, fp_flags, is_private):
    """Liveness verdict. ANY reference => LIVE (veto). Absence never proves dead."""
    if refs > 0:
        return "LIVE"
    if fp_flags:
        return "ASSERTED-DEAD"          # framework-reachable; keep, investigate
    if is_private:
        return "VERIFIED-DEAD-PRIVATE"  # closed-world, no caller => human may delete
    return "ASSERTED-DEAD"              # public/open-world: needs deprecation cycle first


# ----------------------------------------------------------------------
# --diff-slop: own unused additions + debug leftovers
# ----------------------------------------------------------------------
def _slop_entrypoint(name, def_file, def_line):
    """True if an added symbol looks like an intended entry point => REVIEW,
    not REMOVABLE."""
    dfl = (def_file or "").lower()
    base = os.path.basename(def_file or "")
    if dfl.startswith("routes/") or "/routes/" in "/" + dfl:
        return True
    if "Route::" in def_line or "->name(" in def_line:
        return True
    if "controller" in dfl or re.search(r"Controller", base):
        return True
    if dfl.startswith("app/console") or "/app/console/" in "/" + dfl:
        return True
    if re.search(r"(Command|Job|Listener|Observer)", base):
        return True
    if re.search(r"(Command|Job|Listener|Observer|Webhook|Subscriber)$", name):
        return True
    if (def_file or "").endswith(".vue") or "/components/" in "/" + dfl:
        return True
    if re.search(r"\bexport\b", def_line):
        return True
    return False


DEBUG_PATTERNS = [
    ("var_dump", re.compile(r"var_dump\s*\(")),
    ("dd", re.compile(r"\bdd\s*\(")),
    ("dump", re.compile(r"\bdump\s*\(")),
    ("console.log", re.compile(r"console\s*\.\s*log\s*\(")),
    ("print_r", re.compile(r"\bprint_r\s*\(")),
    ("print", re.compile(r"\bprint\s*\(")),
    ("marker", re.compile(r"\b(TODO|FIXME|XXX|PLACEHOLDER)\b|\bexample\b", re.I)),
]


def _debug_hit(line):
    for label, pat in DEBUG_PATTERNS:
        if pat.search(line):
            return label
    return None


def _find_def_line(text, name):
    for pat, _kind in DEF_PATTERNS:
        for m in pat.finditer(text):
            if m.group(1) == name:
                return _line_at(text, m.start(1))
    return ""


def report_slop(removable, review, live_added, debug):
    paths = sorted(set([p for p, _ in removable]
                       + [p for p, _ in review]
                       + [p for p, _, _, _ in debug]))
    for path in paths:
        print("## %s" % path)
        for p, n in removable:
            if p == path:
                print("  REMOVABLE       %s()  — added this change · 0 refs · "
                      "not an entry point → strip it" % n)
        for p, n in review:
            if p == path:
                print("  REVIEW          %s()  — added · 0 refs · entry-point-like → "
                      "verify it is actually wired" % n)
        for p, ln, lbl, content in debug:
            if p == path:
                print("  DEBUG-LEFTOVER  %s:%d :: %s  — %s" % (p, ln, lbl, content[:80]))
        print()

    if live_added:
        print("# live own-additions (referenced — fine):")
        for p, n in live_added:
            print("  LIVE            %s()  (%s)" % (n, p))
        print()

    findings = len(removable) + len(debug)
    live = len(live_added)
    asserted = len(review)
    verified = len(removable)
    exit_code = 1 if findings else 0
    print("SUMMARY findings=%d live=%d asserted=%d verified=%d exit=%d"
          % (findings, live, asserted, verified, exit_code))
    return exit_code


def run_diff_slop(ref, paths, exclude_re):
    paths = paths or git_changed_files(ref)
    if paths is None:
        print("error: not a git repo or bad --ref: %s" % ref, file=sys.stderr)
        return 2
    paths = [p for p in paths if p.endswith(CODE_EXTS)]

    removable, review, live_added, debug = [], [], [], []
    for path in paths:
        before = git_show(ref, path)
        if before is None:
            return 2
        after = read_file(path) if os.path.exists(path) else ""
        if after is None:
            after = ""
        added = extract_added_symbols(before, after)
        for name in sorted(added):
            refs = count_refs(name, ".", exclude_re)
            if refs > 0:
                live_added.append((path, name))
                continue
            def_line = _find_def_line(after, name)
            if _slop_entrypoint(name, path, def_line):
                review.append((path, name))
            else:
                removable.append((path, name))
        for lineno, content in git_added_lines(ref, path):
            hit = _debug_hit(content)
            if hit:
                debug.append((path, lineno, hit, content.strip()))

    return report_slop(removable, review, live_added, debug)


# ----------------------------------------------------------------------
# --liveness: classify pre-existing symbols
# ----------------------------------------------------------------------
def report_liveness(rows):
    live = asserted = verified = 0
    for name, cls, refs, fp, priv in rows:
        fpstr = ",".join(sorted(fp)) if fp else "-"
        print("%s  class=%s  refs=%d  fp=%s  private=%s"
              % (name, cls, refs, fpstr, "y" if priv else "n"))
        if cls == "LIVE":
            live += 1
        elif cls == "VERIFIED-DEAD-PRIVATE":
            verified += 1
        else:
            asserted += 1
    findings = verified
    exit_code = 1 if findings else 0
    print("SUMMARY findings=%d live=%d asserted=%d verified=%d exit=%d"
          % (findings, live, asserted, verified, exit_code))
    return exit_code


def run_liveness(names, root, exclude_re):
    if not os.path.isdir(root):
        print("error: --root not a directory: %s" % root, file=sys.stderr)
        return 2
    rows = []
    for name in names:
        refs = count_refs(name, root, exclude_re)
        def_file, is_priv, _line = find_definition(name, root, exclude_re)
        fp = fp_flags_for(name, root, def_file, exclude_re)
        cls = classify_symbol(name, refs, fp, is_priv)
        rows.append((name, cls, refs, fp, is_priv))
    return report_liveness(rows)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main(argv):
    ap = argparse.ArgumentParser(
        description="Report-only liveness-evidence aggregator (never mutates files)")
    ap.add_argument("--diff-slop", action="store_true", dest="diff_slop",
                    help="flag own unused additions + debug leftovers vs --ref")
    ap.add_argument("--liveness", nargs="+", metavar="NAME",
                    help="classify each pre-existing symbol's liveness")
    ap.add_argument("--ref", default="HEAD",
                    help="diff-slop mode: before-image ref (default HEAD)")
    ap.add_argument("--root", default=".",
                    help="liveness mode: tree to grep for references (default .)")
    ap.add_argument("--exclude", default=DEFAULT_EXCLUDE,
                    help="path-relative regex of files/dirs to skip "
                         "(default: vendor/node_modules/etc.)")
    ap.add_argument("paths", nargs="*",
                    help="diff-slop mode: limit to these paths (default: all changed)")
    args = ap.parse_args(argv)

    if args.diff_slop and args.liveness:
        print("error: choose one mode: --diff-slop or --liveness", file=sys.stderr)
        return 2

    try:
        exclude_re = re.compile(args.exclude)
    except re.error as e:
        print("error: bad --exclude regex: %s" % e, file=sys.stderr)
        return 2

    if args.diff_slop:
        return run_diff_slop(args.ref, args.paths, exclude_re)
    if args.liveness:
        return run_liveness(args.liveness, args.root, exclude_re)
    print("error: choose a mode: --diff-slop or --liveness NAME ...", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
