import subprocess, sys, pathlib, tempfile
TOOL = pathlib.Path(__file__).resolve().parents[1] / "detect-clones.py"
def _run(root):
    return subprocess.run([sys.executable, str(TOOL), "--root", root, "--kind", "code",
                           "--cross-file-only"], capture_output=True, text=True)
def test_two_site_clone_is_note_only_three_is_extract_candidate():
    d = tempfile.mkdtemp()
    body = "function f(){\n  const a = compute(1);\n  const b = compute(2);\n  return a+b;\n}\n"
    for i in range(2):
        (pathlib.Path(d)/f"f{i}.js").write_text(body.replace("f(", f"f{i}("))
    out2 = _run(d).stdout
    assert "NOTE-ONLY" in out2 and "EXTRACT-CANDIDATE" not in out2
    (pathlib.Path(d)/"f2.js").write_text(body.replace("f(", "f2("))
    out3 = _run(d).stdout
    assert "EXTRACT-CANDIDATE" in out3
    assert "wrong abstraction" in out3.lower()


if __name__ == "__main__":
    # Standalone runner so the test validates without pytest (not installed in CI here).
    test_two_site_clone_is_note_only_three_is_extract_candidate()
    print("PASS")
