#!/usr/bin/env python3
"""Tests for detect-hardcoded-cases.py.

Dual-mode: collected by pytest (`pytest -v`) OR run standalone with bare
asserts (`python3 test_detect_hardcoded_cases.py`) when pytest is unavailable.
"""

import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

# Load the hyphenated module by path (cannot `import detect-hardcoded-cases`).
_HERE = pathlib.Path(__file__).resolve()
_TOOL = _HERE.parents[1] / "detect-hardcoded-cases.py"
_spec = importlib.util.spec_from_file_location("dhc", _TOOL)
dhc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dhc)


# ----------------------------------------------------------------------
# suspicious_literals — literal classes
# ----------------------------------------------------------------------
def test_domain_literal_found():
    assert ("domain", "domain1.de") in dhc.suspicious_literals("x == 'domain1.de'")


def test_escaped_regex_domain_found():
    lits = dhc.suspicious_literals(r"if (/domain1\.de/.test(host)) {")
    assert ("domain", "domain1.de") in lits


def test_email_masks_its_domain():
    lits = dhc.suspicious_literals("if (email === 'ceo@domain1.de')")
    assert ("email", "ceo@domain1.de") in lits
    assert ("domain", "domain1.de") not in lits


def test_url_and_date_found():
    assert dhc.suspicious_literals("if u == 'https://domain1.de/api':")[0][0] == "url"
    assert ("date", "2026-07-08") in dhc.suspicious_literals("if d == '2026-07-08':")


def test_file_py_is_not_a_domain():
    assert dhc.suspicious_literals("import detect.foo, os.path") == []


# ----------------------------------------------------------------------
# decision / lookup context
# ----------------------------------------------------------------------
def test_if_comparison_is_decision():
    assert dhc.is_decision_context("if ($domain === 'domain1.de') {")


def test_case_is_decision():
    assert dhc.is_decision_context("    case 'domain1.de':")


def test_plain_log_line_is_not_decision():
    assert not dhc.is_decision_context("logger.info('sync fertig')")


def test_lookup_key_php_and_python():
    assert dhc.is_lookup_key("'domain1.de' => 'solar',", "domain1.de")
    assert dhc.is_lookup_key("    'domain1.de': 'solar',", "domain1.de")
    assert not dhc.is_lookup_key("$url = 'domain1.de';", "domain1.de")


# ----------------------------------------------------------------------
# line_findings — marker, comments, examples
# ----------------------------------------------------------------------
def test_marker_suppresses_finding_and_counts_intentional():
    prev = ["// INTENTIONAL-SPECIAL-CASE: contract customer\n"]
    findings, intentional = dhc.line_findings(
        "if ($host === 'domain1.de') {", prev, [])
    assert findings == [] and intentional == 1


def test_comment_line_is_never_a_finding():
    findings, _ = dhc.line_findings("// fall for domain1.de == special", [], [])
    assert findings == []


def test_example_literal_flagged_anywhere_in_code():
    findings, _ = dhc.line_findings("$x = handle('Branche X');", [], ["Branche X"])
    assert ("example", "Branche X") in findings


def test_data_context_domain_not_flagged_without_examples():
    findings, _ = dhc.line_findings("$base = 'https://domain1.de';", [], [])
    assert findings == []


# ----------------------------------------------------------------------
# is_ignored_path — config/tests/fixtures/extensions
# ----------------------------------------------------------------------
def test_ignored_paths():
    assert dhc.is_ignored_path("config/services.php")
    assert dhc.is_ignored_path("test_branch_classifier.py")
    assert dhc.is_ignored_path("app/Foo.spec.ts")
    assert dhc.is_ignored_path("fixtures/domains.php")
    assert dhc.is_ignored_path("data.json")
    assert not dhc.is_ignored_path("app/Services/Classifier.php")


# ----------------------------------------------------------------------
# Integration: CLI on a self-contained temp fixture + the repo fixture
# ----------------------------------------------------------------------
def _run(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(_TOOL)] + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)


def test_cli_temp_fixture_trap_and_clean():
    with tempfile.TemporaryDirectory() as tmp:
        trap = os.path.join(tmp, "hardcoded.php")
        with open(trap, "w") as fh:
            fh.write("<?php\nif ($d === 'domain1.de') { return 'solar'; }\n")
        clean = os.path.join(tmp, "generic.php")
        with open(clean, "w") as fh:
            fh.write("<?php\n$b = DB::table('map')->where('host', $h)->value('b');\n")
        r = _run(["--root", tmp])
        assert r.returncode == 1, r.stdout
        assert "hardcoded.php" in r.stdout and "generic.php" not in r.stdout
        assert "SUMMARY findings=1" in r.stdout


def test_cli_repo_fixture_oracle():
    fixture = _HERE.parents[3] / "test" / "hardcoding"
    if not fixture.is_dir():  # installed copy ships without the repo fixture
        return
    traps = _run(["--root", str(fixture / "traps")])
    assert traps.returncode == 1
    for n in range(1, 10):  # every trap file must be represented
        assert ("trap%d" % n) in traps.stdout, "trap%d missed!" % n
    clean = _run(["--root", str(fixture / "clean")])
    assert clean.returncode == 0
    assert "findings=0" in clean.stdout


def test_cli_exit_2_on_bad_root():
    assert _run(["--root", "/nonexistent-dir-xyz"]).returncode == 2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("OK — %d tests passed (standalone mode)" % len(fns))
