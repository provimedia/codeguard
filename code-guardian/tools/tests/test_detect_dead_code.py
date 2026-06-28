#!/usr/bin/env python3
"""Tests for detect-dead-code.py.

Dual-mode: collected by pytest (`pytest -v`) OR run standalone with bare
asserts (`python3 test_detect_dead_code.py`) when pytest is unavailable.
"""

import contextlib
import importlib.util
import io
import os
import pathlib
import subprocess
import tempfile

# Load the hyphenated module by path (cannot `import detect-dead-code`).
_HERE = pathlib.Path(__file__).resolve()
_spec = importlib.util.spec_from_file_location(
    "ddc", _HERE.parents[1] / "detect-dead-code.py")
ddc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ddc)


# ----------------------------------------------------------------------
# classify_symbol — the decision table (pure, no I/O)
# ----------------------------------------------------------------------
def test_any_reference_is_live():
    assert ddc.classify_symbol("foo", 3, set(), True) == "LIVE"


def test_zero_refs_with_fp_flag_is_asserted_dead():
    assert ddc.classify_symbol("scopeActive", 0, {"magic"}, False) == "ASSERTED-DEAD"


def test_zero_refs_private_no_flags_is_verified_dead_private():
    assert ddc.classify_symbol("helperX", 0, set(), True) == "VERIFIED-DEAD-PRIVATE"


def test_zero_refs_public_no_flags_is_asserted_dead():
    assert ddc.classify_symbol("publicApi", 0, set(), False) == "ASSERTED-DEAD"


# ----------------------------------------------------------------------
# Integration helpers
# ----------------------------------------------------------------------
def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@contextlib.contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


# ----------------------------------------------------------------------
# --diff-slop on a temp git repo
# ----------------------------------------------------------------------
def test_diff_slop_flags_orphan_and_debug_leftover():
    with tempfile.TemporaryDirectory() as d:
        _git(["init"], d)
        _git(["config", "user.email", "t@t.t"], d)
        _git(["config", "user.name", "tester"], d)
        f = pathlib.Path(d) / "app.js"
        f.write_text("function used(){}\nused();\n")
        _git(["add", "-A"], d)
        _git(["commit", "-m", "init"], d)
        # working-tree change: an unreferenced helper + a debug leftover
        f.write_text("function used(){}\nused();\n"
                     "function orphanHelper(){}\nconsole.log('x');\n")
        buf = io.StringIO()
        with _chdir(d), contextlib.redirect_stdout(buf):
            rc = ddc.main(["--diff-slop"])
        out = buf.getvalue()
        assert "orphanHelper" in out and "REMOVABLE" in out, out
        assert "DEBUG-LEFTOVER" in out, out
        assert rc == 1, out


# ----------------------------------------------------------------------
# --liveness on a tiny temp tree
# ----------------------------------------------------------------------
def test_liveness_private_dead_live_and_magic():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "models").mkdir()
        (root / "models" / "User.php").write_text(
            "<?php\nclass User {\n"
            "    private function deadOne() { return 1; }\n"
            "    public function scopeActive($q) { return $q; }\n"
            "    public function liveOne() { return 2; }\n"
            "}\n")
        (root / "service.php").write_text(
            "<?php\n$u = new User();\n$u->liveOne();\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ddc.main(["--liveness", "deadOne", "liveOne", "scopeActive",
                           "--root", str(root)])
        out = buf.getvalue()
        rows = {}
        for ln in out.splitlines():
            if "class=" in ln and not ln.startswith("SUMMARY"):
                rows[ln.split()[0]] = ln
        assert "VERIFIED-DEAD-PRIVATE" in rows["deadOne"], out
        assert "class=LIVE" in rows["liveOne"], out
        assert "ASSERTED-DEAD" in rows["scopeActive"], out
        # the VERIFIED-DEAD-PRIVATE candidate is an actionable finding
        assert rc == 1, out


# ----------------------------------------------------------------------
# --exclude is threaded through EVERY scan (count_refs / find_definition /
# fp_flags_for). A symbol mentioned only in an excluded file must NOT keep
# the symbol alive (no stray ref, no di_config keep-alive flag).
# ----------------------------------------------------------------------
def test_exclude_option_is_threaded_through_every_scan():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "app").mkdir()
        (root / "app" / "Foo.php").write_text(
            "<?php\nclass Foo {\n"
            "    private function deadX() { return 1; }\n"
            "}\n")
        # bare string mention in a data manifest — not a live code reference
        (root / "manifest.json").write_text('{\n  "symbol": "deadX"\n}\n')

        # Without --exclude the json mention flips deadX away from VERIFIED
        # (either via a stray ref or the di_config keep-alive flag).
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ddc.main(["--liveness", "deadX", "--root", str(root)])
        out_no = buf.getvalue()
        assert "VERIFIED-DEAD-PRIVATE" not in out_no, out_no

        # With --exclude on the manifest, deadX is closed-world dead.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ddc.main(["--liveness", "deadX", "--root", str(root),
                      "--exclude", r"manifest\.json"])
        out_ex = buf.getvalue()
        assert "VERIFIED-DEAD-PRIVATE" in out_ex, out_ex


def test_bad_exclude_regex_exits_2():
    buf = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        rc = ddc.main(["--liveness", "x", "--exclude", "([unterminated"])
    assert rc == 2, (buf.getvalue(), err.getvalue())
    assert "bad --exclude regex" in err.getvalue(), err.getvalue()


# ----------------------------------------------------------------------
# JS/TS module-locals are closed-world ONLY when not exported.
#   not exported + 0 refs  -> VERIFIED-DEAD-PRIVATE  (cannot be imported)
#   exported   + 0 refs  -> ASSERTED-DEAD          (external importers possible)
# ----------------------------------------------------------------------
def test_js_nonexport_is_closed_world_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "util.js").write_text("function debounce(){ return 1; }\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ddc.main(["--liveness", "debounce", "--root", str(root)])
        out = buf.getvalue()
        assert "VERIFIED-DEAD-PRIVATE" in out, out
        assert rc == 1, out


def test_js_export_stays_open_world_asserted():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "util.js").write_text("export function debounce(){ return 1; }\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ddc.main(["--liveness", "debounce", "--root", str(root)])
        out = buf.getvalue()
        assert "ASSERTED-DEAD" in out, out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out
        assert rc == 0, out


# ----------------------------------------------------------------------
# Liveness integration helper: parse "NAME class=... fp=... def=..." rows.
# ----------------------------------------------------------------------
def _liveness_rows(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ddc.main(args)
    out = buf.getvalue()
    rows = {}
    for ln in out.splitlines():
        if "class=" in ln and not ln.startswith("SUMMARY"):
            rows[ln.split()[0]] = ln
    return rows, out, rc


# ----------------------------------------------------------------------
# FIX 1 — leading-underscore privacy is Python-only.
# A PHP `public function _normalize()` is open-world, never closed-world.
# ----------------------------------------------------------------------
def test_php_leading_underscore_is_not_private():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "Helper.php").write_text(
            "<?php\nclass Helper {\n"
            "    public function _normalize() { return 1; }\n"
            "}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "_normalize", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["_normalize"], out
        assert "private=n" in rows["_normalize"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_python_leading_underscore_stays_private():
    # The same name in a .py file IS private (recall preserved for Python).
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "helper.py").write_text(
            "class Helper:\n    def _normalize(self):\n        return 1\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "_normalize", "--root", str(root)])
        assert "VERIFIED-DEAD-PRIVATE" in rows["_normalize"], out
        assert "private=y" in rows["_normalize"], out


# ----------------------------------------------------------------------
# FIX 2 — dynamic dispatch inside the definition's own file vetoes VERIFIED.
# ----------------------------------------------------------------------
def test_dynamic_dispatch_in_def_file_blocks_verified_php():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "Exporter.php").write_text(
            "<?php\nclass Exporter {\n"
            "    private function handleExport() { return 1; }\n"
            "    public function run($method) { return $this->{$method}(); }\n"
            "}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "handleExport", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["handleExport"], out
        assert "dynamic" in rows["handleExport"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_getattr_in_def_file_blocks_verified_py():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "legacy.py").write_text(
            "class Legacy:\n"
            "    def _legacy(self):\n"
            "        return 1\n"
            "    def dispatch(self, name):\n"
            "        return getattr(self, name)()\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "_legacy", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["_legacy"], out
        assert "dynamic" in rows["_legacy"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


# ----------------------------------------------------------------------
# FIX 2 (precision refinement) — the dynamic-marker scan must see CODE, not
# prose. A marker that appears ONLY in a comment or string literal must NOT
# fire the `dynamic` keep-alive flag (that would needlessly lose recall on a
# genuinely-dead private). Dispatch is code; a docblock mentioning __call is not.
# ----------------------------------------------------------------------
def test_dynamic_marker_in_comment_does_not_block_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "Model.php").write_text(
            "<?php\nclass Model {\n"
            "    /**\n"
            "     * reached only through Eloquent's __call / __get indirection.\n"
            "     */\n"
            "    private function legacyThing() { return 1; }\n"
            "    public function used() { return 2; }\n"
            "}\n")
        (root / "caller.php").write_text("<?php\n$m = new Model();\n$m->used();\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "legacyThing", "--root", str(root)])
        assert "VERIFIED-DEAD-PRIVATE" in rows["legacyThing"], out
        assert "dynamic" not in rows["legacyThing"], out


def test_dynamic_marker_in_real_code_still_blocks_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "Handler.php").write_text(
            "<?php\nclass Handler {\n"
            "    private function handle() { return 1; }\n"
            "    public function run($method) { return $this->{$method}(); }\n"
            "}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "handle", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["handle"], out
        assert "dynamic" in rows["handle"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_dynamic_marker_in_string_literal_does_not_block_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "Logger.php").write_text(
            "<?php\nclass Logger {\n"
            "    private function deadLog() { return 1; }\n"
            "    public function note() {\n"
            "        $log = \"calls call_user_func sometimes\";\n"
            "        return $log;\n"
            "    }\n"
            "}\n")
        (root / "caller.php").write_text("<?php\n$l = new Logger();\n$l->note();\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "deadLog", "--root", str(root)])
        assert "VERIFIED-DEAD-PRIVATE" in rows["deadLog"], out
        assert "dynamic" not in rows["deadLog"], out


# ----------------------------------------------------------------------
# FIX 3 — modern Laravel Attribute accessors are Eloquent magic.
# ----------------------------------------------------------------------
def test_laravel_attribute_accessor_is_magic():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "User.php").write_text(
            "<?php\nclass User extends Model {\n"
            "    protected function fullName(): Attribute\n"
            "    { return Attribute::make(get: fn() => 1); }\n"
            "}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "fullName", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["fullName"], out
        assert "magic" in rows["fullName"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


# ----------------------------------------------------------------------
# FIX 5 — per-flag VERIFIED block + def-file reporting + name-collision veto.
# ----------------------------------------------------------------------
def test_each_flag_blocks_verified_pure():
    # ANY framework keep-alive flag (incl. the new dynamic/ambiguous) on a
    # private, 0-ref symbol must NEVER verify it dead.
    for flag in ("route", "blade_vue", "di_config", "db_dispatch", "test_only",
                 "magic", "entrypoint", "dynamic", "ambiguous"):
        assert ddc.classify_symbol("x", 0, {flag}, True) == "ASSERTED-DEAD", flag


def test_route_flag_blocks_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "routes").mkdir()
        (root / "routes" / "web.php").write_text(
            "<?php\nclass Web {\n    private function deadRoute() { return 1; }\n}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "deadRoute", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["deadRoute"], out
        assert "route" in rows["deadRoute"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_db_dispatch_flag_blocks_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "database" / "migrations").mkdir(parents=True)
        (root / "database" / "migrations" / "x.php").write_text(
            "<?php\nclass Mig {\n    private function deadMig() { return 1; }\n}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "deadMig", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["deadMig"], out
        assert "db_dispatch" in rows["deadMig"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_blade_vue_flag_blocks_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "app").mkdir()
        (root / "views").mkdir()
        (root / "app" / "View.php").write_text(
            "<?php\nclass V {\n    private function widgetBox() { return 1; }\n}\n")
        (root / "views" / "x.blade.php").write_text("<div><x-widget-box /></div>\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "widgetBox", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["widgetBox"], out
        assert "blade_vue" in rows["widgetBox"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_di_config_flag_detected_and_not_verified():
    # A config-string reference fires di_config AND counts as a ref (-> LIVE);
    # either way the symbol is kept, never VERIFIED.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "app").mkdir()
        (root / "config").mkdir()
        (root / "app" / "Service.php").write_text(
            "<?php\nclass Service {\n    private function buildClient() { return 1; }\n}\n")
        (root / "config" / "services.php").write_text(
            "<?php\nreturn ['client' => 'buildClient'];\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "buildClient", "--root", str(root)])
        assert "di_config" in rows["buildClient"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_test_only_flag_detected_and_not_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "app").mkdir()
        (root / "tests").mkdir()
        (root / "app" / "Foo.php").write_text(
            "<?php\nclass Foo {\n    private function helperT() { return 1; }\n}\n")
        (root / "tests" / "FooTest.php").write_text(
            "<?php\n$f = new Foo();\n$f->helperT();\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "helperT", "--root", str(root)])
        assert "test_only" in rows["helperT"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_two_def_sites_same_name_blocks_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "a").mkdir()
        (root / "b").mkdir()
        (root / "a" / "Foo.php").write_text(
            "<?php\nclass Foo {\n    private function dup() { return 1; }\n}\n")
        (root / "b" / "Bar.php").write_text(
            "<?php\nclass Bar {\n    private function dup() { return 2; }\n}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "dup", "--root", str(root)])
        assert "ASSERTED-DEAD" in rows["dup"], out
        assert "ambiguous" in rows["dup"], out
        assert "VERIFIED-DEAD-PRIVATE" not in out, out


def test_liveness_reports_def_file():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "Foo.php").write_text(
            "<?php\nclass Foo {\n    private function onlyHere() { return 1; }\n}\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "onlyHere", "--root", str(root)])
        assert "def=Foo.php" in rows["onlyHere"], out


# ----------------------------------------------------------------------
# FIX 4 — --diff-slop debug detection is precise (no example/print noise).
# ----------------------------------------------------------------------
def test_diff_slop_debug_patterns_are_precise():
    with tempfile.TemporaryDirectory() as d:
        _git(["init"], d)
        _git(["config", "user.email", "t@t.t"], d)
        _git(["config", "user.name", "tester"], d)
        mail = pathlib.Path(d) / "mail.php"
        out_py = pathlib.Path(d) / "out.py"
        dbg = pathlib.Path(d) / "dbg.php"
        js = pathlib.Path(d) / "app.js"
        mail.write_text("<?php\n$c = [];\n")
        out_py.write_text("x = 1\n")
        dbg.write_text("<?php\n$y = 1;\n")
        js.write_text("const a = 1;\n")
        _git(["add", "-A"], d)
        _git(["commit", "-m", "init"], d)
        # added lines: an example email + a bare print (both NOT debug),
        # plus a var_dump + a console.log (both ARE debug).
        mail.write_text("<?php\n$c = [];\n$c['from'] = 'noreply@example.com';\n")
        out_py.write_text("x = 1\nprint(\"done\")\n")
        dbg.write_text("<?php\n$y = 1;\nvar_dump($y);\n")
        js.write_text("const a = 1;\nconsole.log(a);\n")
        buf = io.StringIO()
        with _chdir(d), contextlib.redirect_stdout(buf):
            rc = ddc.main(["--diff-slop"])
        out = buf.getvalue()
        debug_lines = [l for l in out.splitlines() if "DEBUG-LEFTOVER" in l]
        joined = "\n".join(debug_lines)
        assert "var_dump" in joined, out
        assert "console" in joined, out
        assert "example.com" not in joined, out
        assert "done" not in joined, out


# ----------------------------------------------------------------------
# FIX 7 — Python entry points (bare main / __main__ guard) are REVIEW.
# ----------------------------------------------------------------------
def test_diff_slop_bare_main_is_review():
    with tempfile.TemporaryDirectory() as d:
        _git(["init"], d)
        _git(["config", "user.email", "t@t.t"], d)
        _git(["config", "user.name", "tester"], d)
        f = pathlib.Path(d) / "cli.py"
        f.write_text("x = 1\n")
        _git(["add", "-A"], d)
        _git(["commit", "-m", "init"], d)
        f.write_text("x = 1\ndef main():\n    return 1\n")
        buf = io.StringIO()
        with _chdir(d), contextlib.redirect_stdout(buf):
            rc = ddc.main(["--diff-slop"])
        out = buf.getvalue()
        assert "REVIEW" in out and "main" in out, out
        assert "REMOVABLE" not in out, out


def test_diff_slop_dunder_main_guard_makes_additions_review():
    with tempfile.TemporaryDirectory() as d:
        _git(["init"], d)
        _git(["config", "user.email", "t@t.t"], d)
        _git(["config", "user.name", "tester"], d)
        f = pathlib.Path(d) / "tool.py"
        f.write_text("x = 1\n")
        _git(["add", "-A"], d)
        _git(["commit", "-m", "init"], d)
        f.write_text("x = 1\ndef helperZ():\n    return 1\n\n"
                     "if __name__ == '__main__':\n    pass\n")
        buf = io.StringIO()
        with _chdir(d), contextlib.redirect_stdout(buf):
            rc = ddc.main(["--diff-slop"])
        out = buf.getvalue()
        assert "REVIEW" in out and "helperZ" in out, out
        assert "REMOVABLE" not in out, out


# ----------------------------------------------------------------------
# Recall guard — a genuinely-dead private is STILL VERIFIED after hardening.
# ----------------------------------------------------------------------
def test_genuinely_dead_private_still_verified():
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "app").mkdir()
        (root / "app" / "Foo.php").write_text(
            "<?php\nclass Foo {\n"
            "    private function trulyDead() { return 1; }\n"
            "    public function used() { return 2; }\n"
            "}\n")
        (root / "caller.php").write_text("<?php\n$f = new Foo();\n$f->used();\n")
        rows, out, rc = _liveness_rows(
            ["--liveness", "trulyDead", "--root", str(root)])
        assert "VERIFIED-DEAD-PRIVATE" in rows["trulyDead"], out
        assert "fp=-" in rows["trulyDead"], out
        assert rc == 1, out


# ----------------------------------------------------------------------
# Standalone runner (used when pytest is unavailable)
# ----------------------------------------------------------------------
def _main():
    funcs = [(k, v) for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in funcs:
        try:
            fn()
            print("PASS  %s" % name)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL  %s -> %r" % (name, e))
    print("\n%d passed, %d failed" % (len(funcs) - failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(_main())
