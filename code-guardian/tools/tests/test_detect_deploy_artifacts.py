#!/usr/bin/env python3
"""Tests for detect-deploy-artifacts.py.

Dual-mode: collected by pytest (`pytest -v`) OR run standalone with bare
asserts (`python3 test_detect_deploy_artifacts.py`) when pytest is unavailable.
"""

import hashlib
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

# Load the hyphenated module by path (cannot `import detect-deploy-artifacts`).
_HERE = pathlib.Path(__file__).resolve()
_TOOL = _HERE.parents[1] / "detect-deploy-artifacts.py"
_spec = importlib.util.spec_from_file_location("dda", _TOOL)
dda = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dda)


# ----------------------------------------------------------------------
# classify_path — the four classes over the locked catalog
# ----------------------------------------------------------------------
def test_app_code_is_deploy():
    assert dda.classify_path("app/Http/Controllers/HomeController.php")[0] == "DEPLOY"
    assert dda.classify_path("public/index.php")[0] == "DEPLOY"
    assert dda.classify_path("resources/views/home.blade.php")[0] == "DEPLOY"
    assert dda.classify_path("database/migrations/2026_01_01_create_users.php")[0] == "DEPLOY"
    assert dda.classify_path("vendor/autoload.php")[0] == "DEPLOY"


def test_env_is_server_only_but_example_deploys():
    assert dda.classify_path(".env")[0] == "SERVER-ONLY"
    assert dda.classify_path(".env.production")[0] == "SERVER-ONLY"
    assert dda.classify_path(".env.example")[0] == "DEPLOY"
    assert dda.classify_path(".env.dist")[0] == "DEPLOY"


def test_server_only_catalog():
    assert dda.classify_path("storage/logs/laravel.log")[0] == "SERVER-ONLY"
    assert dda.classify_path("certs/server.key")[0] == "SERVER-ONLY"
    assert dda.classify_path("ssl/chain.pem")[0] == "SERVER-ONLY"
    assert dda.classify_path("data/app.sqlite")[0] == "SERVER-ONLY"
    assert dda.classify_path("uploads/kunde/foto.jpg")[0] == "SERVER-ONLY"
    assert dda.classify_path(".ssh/id_rsa")[0] == "SERVER-ONLY"


def test_never_high_catalog():
    for p in [
        "tests/Feature/LoginTest.php",
        "test/unit/x_test.go",
        "__tests__/app.test.js",
        "docs/architecture.md",
        ".git/config",
        ".github/workflows/ci.yml",
        "dump.sql",
        "backup-2026.tar.gz",
        "db.dump",
        "index.php.bak",
        "phpunit.xml",
        "phpunit.xml.dist",
        ".audit-log.md",
        ".code-guardian-deploy-report.md",
        ".code-guardian-deploy.yml",
        ".claude/settings.json",
        "__pycache__/x.pyc",
        ".pytest_cache/CACHEDIR.TAG",
        "error.log",
        "cypress/e2e/spec.cy.js",
        "playwright/tests/a.spec.ts",
    ]:
        cls, risk, _reason = dda.classify_path(p)
        assert cls == "NEVER", p
        assert risk == "high", p


def test_never_low_catalog():
    for p in [
        ".DS_Store",
        "img/.DS_Store",
        ".idea/workspace.xml",
        ".vscode/launch.json",
        ".editorconfig",
        ".eslintrc.json",
        "docker-compose.yml",
        "Dockerfile",
        "Makefile",
        "vite.config.js",
        "README.md",
        ".gitignore",
        ".gitattributes",
        "index.php.swp",
        "Thumbs.db",
        "phpstan.neon",
    ]:
        cls, risk, _reason = dda.classify_path(p)
        assert cls == "NEVER", p
        assert risk == "low", p


def test_review_catalog():
    assert dda.classify_path("node_modules/left-pad/index.js")[0] == "REVIEW"
    assert dda.classify_path("database/seeders/DemoSeeder.php")[0] == "REVIEW"
    assert dda.classify_path("seeds/users.php")[0] == "REVIEW"


def test_nested_md_in_app_is_low_never_not_docs():
    # *.md outside docs/ is junk-on-server but low risk
    cls, risk, _ = dda.classify_path("app/NOTES.md")
    assert cls == "NEVER" and risk == "low"


# ----------------------------------------------------------------------
# rsync --itemize-changes line parsing
# ----------------------------------------------------------------------
def test_itemize_prefix_stripped():
    assert dda.parse_list_line(">f+++++++++ app/Models/User.php") == "app/Models/User.php"
    assert dda.parse_list_line("cd+++++++++ tests/") == "tests/"
    assert dda.parse_list_line("<f.st...... public/index.php") == "public/index.php"
    assert dda.parse_list_line("*deleting   old/gone.php") is None
    assert dda.parse_list_line("deleting old/gone.php") is None


def test_itemize_prefix_stripped_short_format():
    # rsync 2.6.x / macOS openrsync emit 9-char prefixes (found live 2026-07-08)
    assert dda.parse_list_line(">f....... .env") == ".env"
    assert dda.parse_list_line(">f....... tests/Feature/LoginTest.php") == "tests/Feature/LoginTest.php"
    assert dda.parse_list_line("cd+++++++ database/seeders/") == "database/seeders/"


def test_plain_path_passthrough_and_noise_skipped():
    assert dda.parse_list_line("app/Models/User.php") == "app/Models/User.php"
    assert dda.parse_list_line("") is None
    assert dda.parse_list_line("sending incremental file list") is None
    assert dda.parse_list_line("sent 1,234 bytes  received 56 bytes") is None
    assert dda.parse_list_line("total size is 9,999  speedup is 42.00") is None


# ----------------------------------------------------------------------
# config: YAML-lite overrides
# ----------------------------------------------------------------------
def test_config_extra_and_allow():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = os.path.join(tmp, ".code-guardian-deploy.yml")
        with open(cfg, "w") as fh:
            fh.write(
                "docroot_url: https://example.org\n"
                "ssh: prod-alias\n"
                "extra_never:\n"
                "  - internal-notes/\n"
                "extra_server_only:\n"
                "  - shared/\n"
                "allow:\n"
                "  - 'docs/api-public/: served intentionally as /docs'\n"
            )
        conf = dda.load_config(cfg)
        assert conf["docroot_url"] == "https://example.org"
        assert conf["ssh"] == "prod-alias"
        cls = dda.classify_path("internal-notes/plan.txt", conf)
        assert cls[0] == "NEVER"
        assert dda.classify_path("shared/uploads/a.jpg", conf)[0] == "SERVER-ONLY"
        allowed = dda.classify_path("docs/api-public/index.html", conf)
        assert allowed[0] == "ALLOWED"


# ----------------------------------------------------------------------
# CLI integration
# ----------------------------------------------------------------------
def _run(args, cwd=None, stdin=None):
    return subprocess.run(
        [sys.executable, str(_TOOL)] + args,
        input=stdin,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)


def test_cli_list_mode_traps_exit_1():
    with tempfile.TemporaryDirectory() as tmp:
        lst = os.path.join(tmp, "transfer.txt")
        with open(lst, "w") as fh:
            fh.write(">f+++++++++ app/Models/User.php\n")
            fh.write(">f+++++++++ tests/Feature/LoginTest.php\n")
            fh.write(">f+++++++++ .env\n")
            fh.write(">f+++++++++ .git/config\n")
            fh.write("*deleting   old/gone.php\n")
        r = _run(["--list", lst])
        assert r.returncode == 1, r.stdout + r.stderr
        assert "tests/" in r.stdout  # dir findings are grouped, not per-file
        assert ".env" in r.stdout
        assert ".git/" in r.stdout
        assert "old/gone.php" not in r.stdout
        assert "app/Models/User.php" not in r.stdout  # DEPLOY is silent
        assert "SUMMARY " in r.stdout and "exit=1" in r.stdout


def test_cli_list_mode_clean_exit_0():
    with tempfile.TemporaryDirectory() as tmp:
        lst = os.path.join(tmp, "transfer.txt")
        with open(lst, "w") as fh:
            fh.write("app/Models/User.php\npublic/index.php\n")
        r = _run(["--list", lst])
        assert r.returncode == 0, r.stdout + r.stderr
        assert "deploy=2" in r.stdout and "never=0" in r.stdout


def test_cli_list_stdin():
    r = _run(["--list", "-"], stdin=">f+++++++++ dump.sql\n")
    assert r.returncode == 1
    assert "dump.sql" in r.stdout


def test_cli_root_inventory_on_repo_fixture():
    fixture = _HERE.parents[3] / "test" / "deploy" / "project"
    if not fixture.is_dir():  # installed copy ships without the repo fixture
        return
    r = _run(["--root", str(fixture)])
    assert r.returncode == 1, r.stdout
    out = r.stdout
    # planted traps must be represented
    for needle in ["tests/", "docs/", "dump.sql", "backup-2026.tar.gz",
                   ".DS_Store", ".audit-log.md", "phpunit.xml", ".github/"]:
        assert needle in out, "missed trap: %s" % needle
    # SERVER-ONLY plants
    assert ".env" in out and "storage/" in out and "server.key" in out
    # clean app files stay silent
    for clean in ["HomeController.php", "index.php", "home.blade.php",
                  "create_users", "autoload.php", ".env.example"]:
        assert clean not in out, "false positive: %s" % clean


def test_cli_usage_errors_exit_2():
    assert _run([]).returncode == 2
    assert _run(["--root", "/nonexistent-dir-xyz"]).returncode == 2
    assert _run(["--list", "/nonexistent-file-xyz.txt"]).returncode == 2


def test_tool_never_mutates_scanned_tree():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "dump.sql")
        with open(f, "w") as fh:
            fh.write("SELECT 1;\n")
        before = hashlib.sha256(open(f, "rb").read()).hexdigest()
        _run(["--root", tmp])
        after = hashlib.sha256(open(f, "rb").read()).hexdigest()
        assert before == after
        assert sorted(os.listdir(tmp)) == ["dump.sql"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("OK — %d tests passed (standalone mode)" % len(fns))
