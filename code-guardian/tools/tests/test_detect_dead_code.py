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
