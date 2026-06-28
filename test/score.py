#!/usr/bin/env python3
"""
score.py -- ground-truth scorer for the dead-code / AI-slop / redundancy detector.

Runs the detector tools against this fixture and prints a scorecard across four
sections:

  1. LIVENESS  (DEAD + LIVE_TRAP)  -> detect-dead-code.py --liveness <symbol>
  2. SLOP      (git-diff additions) -> detect-dead-code.py --diff-slop
  3. REDUNDANCY (cross-file clones) -> detect-clones.py --kind code ...
  4. SCORECARD + final verdict

THE CRITICAL SAFETY PROPERTY
----------------------------
No LIVE_TRAP may EVER be classified VERIFIED-DEAD-PRIVATE. That classification
authorizes deletion; doing it to a live trap = deleting productive code =
CRITICAL FAILURE. The run FAILS (exit 1) if CRITICAL_FP > 0.

GRACEFUL DEGRADATION
--------------------
The detector tools may not exist yet. If detect-dead-code.py is absent, the
liveness + slop sections are skipped and the script exits 0 (so the harness can
still be validated). Use `--self-test` to exercise all matrix math with an inline
MOCK classifier (no tools required); that mode also proves the harness DETECTS a
critical false positive.

Usage:
  python3 score.py              # real run against the detector tools
  python3 score.py --self-test  # offline self-test with mock classifications
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE  # the fixture root == directory containing this script (test/)
TOOLS = os.path.normpath(os.path.join(HERE, "..", "code-guardian", "tools"))
DEAD_TOOL = os.path.join(TOOLS, "detect-dead-code.py")
CLONE_TOOL = os.path.join(TOOLS, "detect-clones.py")
CONFIG_TOOL = os.path.join(TOOLS, "detect-config-leaks.sh")
ORACLE = os.path.join(ROOT, "oracle.json")

# Classification vocabulary the harness recognizes in tool output.
LIVENESS_TOKENS = ["VERIFIED-DEAD-PRIVATE", "ASSERTED-DEAD", "LIVE"]
SLOP_TOKENS = ["DEBUG-LEFTOVER", "REMOVABLE"]
CLONE_TOKENS = ["EXTRACT-CANDIDATE", "NOTE-ONLY"]

TP_THRESHOLD = 0.70  # >= 70% of the VERIFIABLE SUBSET must be VERIFIED-DEAD-PRIVATE

# WHY this exclude: the detector greps the WHOLE --root for references, but test/
# also holds the scoring scaffolding. oracle.json is literally the answer key (it
# names every symbol under test), and score.py / README.md / slop/ are harness, not
# project-under-test code. Scanning them makes a genuinely-dead private symbol look
# LIVE purely because the answer key mentions its name. Drop them so we measure the
# project, not the test. (Real LIVE_TRAP cross-references live in
# app/routes/config/resources/database/tests — never in these meta-files — so this
# cannot manufacture a CRITICAL_FP.)
LIVENESS_EXCLUDE = r"(^|/)(oracle\.json|score\.py|README\.md)$|(^|/)slop/"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def load_oracle():
    with open(ORACLE, encoding="utf-8") as fh:
        return json.load(fh)


def extract_token(text, tokens):
    """Return the first token (by the given priority order) found in text."""
    for tok in tokens:
        if tok in text:
            return tok
    return None


def run_tool(cmd, cwd=None, timeout=120):
    try:
        res = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return (res.stdout or "") + "\n" + (res.stderr or "")
    except Exception as exc:  # pragma: no cover - defensive
        return f"__TOOL_ERROR__ {exc}"


def trunc(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


# --------------------------------------------------------------------------- #
# 1. LIVENESS  (DEAD + LIVE_TRAP)
# --------------------------------------------------------------------------- #
def score_liveness(entries, classify):
    """classify(entry) -> (token, is_private_bool).

    DEAD entries are split into measurement CHANNELS via the oracle "channel" field:

      * liveness -- a named function/class/method whose reachability the
                    --liveness graph can legitimately judge.
      * linter   -- an unused *import* / unused *local var* / *unreachable* tail.
                    These are NOT named-symbol questions; --liveness (which
                    classifies definitions) cannot answer them. They belong to a
                    linter or the --diff-slop channel. Reported informationally,
                    EXCLUDED from the recall gate.

    Inside the liveness channel we isolate the VERIFIABLE SUBSET = closed-world
    symbols only (private, or non-exported JS/TS), read straight from the tool's
    own `private=` evidence. A public/exported DEAD symbol that lands
    ASSERTED-DEAD is SAFE by design (open-world: external importers are
    unprovable), NOT a miss — so it is reported but not gated.
    """
    rows = []
    verifiable = []   # (entry, cls): closed-world liveness DEAD -> gated subset
    open_world = []   # (entry, cls): open-world liveness DEAD   -> SAFE, ungated
    linter = []       # (entry, cls): linter-channel DEAD        -> out of scope
    tp = 0
    critical_fp = safe = 0
    trap_total = 0
    for e in entries:
        if e["kind"] not in ("DEAD", "LIVE_TRAP"):
            continue
        if not e.get("liveness_query", True):
            continue
        cls, is_private = classify(e)
        if e["kind"] == "DEAD":
            channel = e.get("channel", "liveness")
            if channel == "linter":
                linter.append((e, cls))
                outcome = "OUT-OF-SCOPE"
            elif is_private:               # closed-world -> verifiable subset
                verifiable.append((e, cls))
                if cls == "VERIFIED-DEAD-PRIVATE":
                    outcome = "TP"
                    tp += 1
                else:
                    outcome = "MISS"
            else:                          # open-world -> SAFE, un-verifiable
                open_world.append((e, cls))
                outcome = "SAFE-OPEN-WORLD"
        else:  # LIVE_TRAP
            trap_total += 1
            if cls == "VERIFIED-DEAD-PRIVATE":
                outcome = "CRITICAL_FP"
                critical_fp += 1
            else:
                outcome = "SAFE"
                safe += 1
        rows.append((e["id"], e["kind"], e["symbol"], cls, outcome))
    return {
        "rows": rows,
        "verifiable": verifiable,
        "open_world": open_world,
        "linter": linter,
        "tp": tp,
        "verifiable_total": len(verifiable),
        "critical_fp": critical_fp,
        "safe": safe,
        "trap_total": trap_total,
        "dead_total": len(verifiable) + len(open_world) + len(linter),
    }


def real_liveness_classifier(entry):
    """Return (classification, is_private) from the detector's own output.

    The `--exclude` drops the answer key (see LIVENESS_EXCLUDE) so a dead private
    symbol is no longer kept 'LIVE' by oracle.json naming it. `private=` is the
    tool's own closed-world signal and decides verifiable-subset membership.
    """
    out = run_tool(["python3", DEAD_TOOL, "--liveness", entry["symbol"],
                    "--root", ROOT, "--exclude", LIVENESS_EXCLUDE])
    cls = extract_token(out, LIVENESS_TOKENS) or "UNKNOWN"
    m = re.search(r"\bprivate=(y|n)\b", out)
    is_private = bool(m and m.group(1) == "y")
    return cls, is_private


def mock_liveness_classifier(entry):
    # Inline MOCK: green path. DEAD -> verified removable; LIVE_TRAP -> kept.
    if entry["kind"] == "DEAD":
        return "VERIFIED-DEAD-PRIVATE", True
    if "ASSERTED-DEAD" in entry.get("expect_ok", []):
        return "ASSERTED-DEAD", False  # e.g. the public-api export
    return "LIVE", False


def print_liveness(res, show_all=False):
    print("\n=== 1. LIVENESS (DEAD + LIVE_TRAP) ===")
    print(f"  {'OUTCOME':<16} {'KIND':<10} {'SYMBOL':<28} CLASSIFICATION")
    print(f"  {'-'*16} {'-'*10} {'-'*28} {'-'*22}")
    for (oid, kind, sym, cls, outcome) in res["rows"]:
        # Always surface misses + criticals; sample the rest unless show_all.
        flag = outcome in ("MISS", "CRITICAL_FP")
        if show_all or flag:
            mark = "!!" if outcome == "CRITICAL_FP" else ("xx" if outcome == "MISS" else "  ")
            print(f"  {mark}{outcome:<14} {kind:<10} {trunc(sym,28):<28} {cls}")

    # ---- transparent DEAD breakdown: nothing hidden ----
    print("\n  --- DEAD breakdown (transparent; all channels shown) ---")
    print(f"  total DEAD entries:                          {res['dead_total']}")
    print(f"  [GATED] verifiable subset (closed-world):    {res['verifiable_total']}"
          f"   (private / non-exported JS-TS)")
    print(f"          -> VERIFIED-DEAD-PRIVATE (true pos):  {res['tp']}/{res['verifiable_total']}")
    for (e, cls) in res["verifiable"]:
        m = "ok" if cls == "VERIFIED-DEAD-PRIVATE" else "xx"
        print(f"             [{m}] {e['symbol']:<24} got={cls}  ({e['category']})")

    print(f"  [UNGATED] open-world liveness DEAD:          {len(res['open_world'])}"
          f"   (public/exported -> un-verifiable by design)")
    for (e, cls) in res["open_world"]:
        print(f"             SAFE  {e['symbol']:<24} got={cls}  ({e['category']})")
    if res["open_world"]:
        print("             note: SAFE — the only textual reference is the dead")
        print("             import line itself; proving an import unused is a linter")
        print("             question, and LIVE/ASSERTED never authorizes deletion.")

    print(f"  [INFO] linter-channel DEAD (out of scope):   {len(res['linter'])}"
          f"   (unused import / local var / unreachable)")
    for (e, cls) in res["linter"]:
        print(f"             ----  {e['symbol']:<24} got={cls}  ({e['category']})")
    if res["linter"]:
        print("             note: NOT a named-symbol liveness question; --liveness")
        print("             cannot answer it. Belongs to a linter / --diff-slop.")

    print(
        f"\n  LIVE_TRAP: {res['safe']}/{res['trap_total']} SAFE, "
        f"{res['critical_fp']} CRITICAL_FP (productive-code deletions)"
    )


# --------------------------------------------------------------------------- #
# 2. SLOP  (reproduced as a git diff)
# --------------------------------------------------------------------------- #
def build_slop_repo():
    """Copy the fixture WITHOUT slop/ as a baseline commit, then drop the slop/
    additions into the working tree. Returns the repo path (caller cleans up)."""
    tmp = tempfile.mkdtemp(prefix="slop-fixture-")
    repo = os.path.join(tmp, "repo")

    def ignore(dirname, names):
        skip = set()
        for n in names:
            if n in (".git", "slop"):
                skip.add(n)
        return skip

    shutil.copytree(ROOT, repo, ignore=ignore)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "baseline (no slop)"], cwd=repo, check=True
    )
    # Lay down the working-tree slop additions (the simulated agent diff).
    shutil.copytree(os.path.join(ROOT, "slop"), os.path.join(repo, "slop"))
    # Intent-to-add so the brand-new files are visible to `git diff`.
    subprocess.run(["git", "add", "-N", "slop"], cwd=repo, check=True)
    return tmp, repo


def score_slop(entries, classify):
    """classify(entry, blob) -> True if the slop case was flagged
    REMOVABLE/DEBUG-LEFTOVER."""
    slop_entries = [e for e in entries if e["kind"] == "SLOP"]
    rows = []
    hits = 0
    for e in slop_entries:
        ok = classify(e)
        rows.append((e["id"], e["file"], e["symbol"], e["expect"], ok))
        if ok:
            hits += 1
    return {"rows": rows, "hits": hits, "total": len(slop_entries)}


def make_real_slop_classifier(blob):
    """Per-line matcher: a slop case counts as flagged only if a line carrying a
    REMOVABLE/DEBUG-LEFTOVER label actually references that case's marker/symbol."""
    lines = blob.splitlines()

    def classify(entry):
        if "__TOOL_ERROR__" in blob:
            return False
        needle = entry["symbol"].rstrip("(")  # "var_dump(" -> "var_dump"
        cat = entry["category"]
        for ln in lines:
            if extract_token(ln, SLOP_TOKENS) is None:
                continue
            if cat == "leftover-todo-placeholder":
                if "TODO" in ln or "PLACEHOLDER" in ln:
                    return True
            elif needle and needle in ln:
                return True
        return False

    return classify


def mock_slop_classifier(entry):
    # Inline MOCK: the detector flagged each case with its expected label.
    return entry["expect"] in (SLOP_TOKENS + ["REMOVABLE", "DEBUG-LEFTOVER"])


def print_slop(res, note=None):
    print("\n=== 2. SLOP (git-diff additions) ===")
    if note:
        print(f"  {note}")
    for (oid, f, sym, expect, ok) in res["rows"]:
        mark = "ok" if ok else "xx"
        print(f"  [{mark}] {trunc(oid,30):<30} {expect:<14} {trunc(f,28)}")
    print(f"\n  SLOP flagged: {res['hits']}/{res['total']}")


# --------------------------------------------------------------------------- #
# 3. REDUNDANCY  (cross-file clones)
# --------------------------------------------------------------------------- #
def score_redundancy(entries, classify):
    red = [e for e in entries if e["kind"].startswith("REDUNDANT")]
    rows = []
    ok_count = 0
    coincidental_safe = True
    for e in red:
        verdict = classify(e)  # observed label or None
        expect = e["expect"]
        if expect == "EXTRACT-CANDIDATE":
            passed = verdict == "EXTRACT-CANDIDATE"
        else:  # NOTE-ONLY (incl. COINCIDENTAL) -> must NOT be an extract target
            passed = verdict in (None, "NOTE-ONLY")
        if e["kind"] == "REDUNDANT_COINCIDENTAL" and verdict == "EXTRACT-CANDIDATE":
            coincidental_safe = False
        rows.append((e["id"], e["kind"], expect, verdict, passed))
        if passed:
            ok_count += 1
    return {
        "rows": rows,
        "ok": ok_count,
        "total": len(red),
        "coincidental_safe": coincidental_safe,
    }


def make_real_clone_classifier(blob):
    def classify(entry):
        if "__TOOL_ERROR__" in blob:
            return None
        sym = entry["symbol"]
        if sym not in blob:
            return None
        # Heuristic: find the symbol's mention, look at the nearest clone token.
        idx = blob.find(sym)
        window = blob[max(0, idx - 400): idx + 400]
        return extract_token(window, CLONE_TOKENS)
    return classify


def make_real_redundancy_classifier(clone_blob, config_blob):
    """Route each redundancy entry to the right tool: code clones go to
    detect-clones.py; config-duplication (duplicated URLs/emails) goes to
    detect-config-leaks.sh."""
    clone_cls = make_real_clone_classifier(clone_blob)

    def classify(entry):
        if entry.get("category") == "config-duplication":
            if not config_blob or "__TOOL_ERROR__" in config_blob:
                return None
            # config-leaks flags a duplicated literal -> treat as extract target.
            return "EXTRACT-CANDIDATE" if entry["symbol"] in config_blob else None
        return clone_cls(entry)

    return classify


def mock_clone_classifier(entry):
    # Inline MOCK: the detector labelled each clone group as the oracle expects.
    return entry["expect"]


def print_redundancy(res, note=None):
    print("\n=== 3. REDUNDANCY (cross-file clones) ===")
    if note:
        print(f"  {note}")
    for (oid, kind, expect, verdict, passed) in res["rows"]:
        mark = "ok" if passed else "xx"
        print(
            f"  [{mark}] {trunc(oid,32):<32} expect={expect:<16} got={verdict}"
        )
    cs = "OK" if res["coincidental_safe"] else "VIOLATED"
    print(f"\n  Redundancy correct: {res['ok']}/{res['total']}  "
          f"| COINCIDENTAL-not-merged: {cs}")


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def final_verdict(liveness, skipped=False):
    print("\n" + "=" * 60)
    if skipped:
        print("CRITICAL_FP=0  (absolute safety gate, primary)")
        print("RESULT: SKIPPED (detect-dead-code.py not found)")
        return 0
    cfp = liveness["critical_fp"]
    subset = liveness["verifiable_total"]
    recall = (liveness["tp"] / subset) if subset else 0.0
    # PRIMARY, ABSOLUTE gate: a single LIVE_TRAP -> VERIFIED-DEAD-PRIVATE is a
    # productive-code deletion and FAILS the run regardless of recall.
    print(f"CRITICAL_FP={cfp}  (LIVE_TRAP -> VERIFIED-DEAD-PRIVATE; absolute gate, must be 0)")
    print(f"verifiable-subset recall: {liveness['tp']}/{subset} = {recall:.0%} "
          f"(threshold {TP_THRESHOLD:.0%}; closed-world liveness DEAD only)")
    safety_ok = (cfp == 0)
    recall_ok = (recall >= TP_THRESHOLD)
    passed = safety_ok and recall_ok
    if not safety_ok:
        print("  -> FAIL is forced by CRITICAL_FP > 0 (safety), independent of recall.")
    print(f"RESULT: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def run_self_test(entries):
    print("################  SELF-TEST (inline MOCK classifier)  ################")

    liveness = score_liveness(entries, mock_liveness_classifier)
    print_liveness(liveness)

    slop = score_slop(entries, mock_slop_classifier)
    print_slop(slop, note="(mock: every slop case flagged with its expected label)")

    redundancy = score_redundancy(entries, mock_clone_classifier)
    print_redundancy(redundancy, note="(mock: every clone group labelled as oracle expects)")

    code = final_verdict(liveness)

    # Internal sanity: prove the matrix DETECTS a critical false positive.
    print("\n--- internal check: critical-FP detection ---")

    def evil_classifier(entry):
        # Flip exactly one LIVE_TRAP into a deletion authorization.
        if entry["id"] == "trap-eloquent-scope-active":
            return "VERIFIED-DEAD-PRIVATE", True
        return mock_liveness_classifier(entry)

    evil = score_liveness(entries, evil_classifier)
    assert evil["critical_fp"] == 1, "harness failed to detect a critical FP!"
    print("  injected 1 LIVE_TRAP->VERIFIED-DEAD-PRIVATE; harness counted "
          f"CRITICAL_FP={evil['critical_fp']} -> detection OK")

    # And the green path must itself be clean + passing.
    assert liveness["critical_fp"] == 0, "mock green path should have 0 CRITICAL_FP"
    assert code == 0, "mock green path should PASS"
    assert slop["hits"] == slop["total"], "mock slop should flag all"
    assert redundancy["ok"] == redundancy["total"], "mock redundancy should match all"
    assert redundancy["coincidental_safe"], "coincidental must not be an extract target"
    print("  self-test assertions passed.")
    return 0


def run_real(entries):
    dead_present = os.path.isfile(DEAD_TOOL)
    clone_present = os.path.isfile(CLONE_TOOL)
    print("################  REAL RUN  ################")
    print(f"  detect-dead-code.py: {'found' if dead_present else 'NOT FOUND'}")
    print(f"  detect-clones.py:    {'found' if clone_present else 'NOT FOUND'}")

    # ---- redundancy can run independently of the dead-code tool ----
    if clone_present:
        clone_blob = run_tool([
            "python3", CLONE_TOOL, "--root", ROOT, "--kind", "code",
            "--cross-file-only", "--extract-threshold", "3",
        ])
        config_blob = None
        if os.path.isfile(CONFIG_TOOL):
            config_blob = run_tool(["bash", CONFIG_TOOL, ROOT])
        classify = make_real_redundancy_classifier(clone_blob, config_blob)
        redundancy = score_redundancy(entries, classify)
        note = None if config_blob is not None else \
            "(config-duplication routed to detect-config-leaks.sh, which was not found)"
        print_redundancy(redundancy, note=note)
    else:
        print("\n=== 3. REDUNDANCY ===\n  detect-clones.py not found -- redundancy scoring skipped")

    if not dead_present:
        # graceful degrade: liveness is the gated matrix; skip + exit 0.
        print("\ndetect-dead-code.py not found -- liveness + slop scoring skipped")
        return final_verdict(None, skipped=True)

    # ---- liveness ----
    liveness = score_liveness(entries, real_liveness_classifier)
    print_liveness(liveness, show_all=False)

    # ---- slop (git-diff harness) ----
    if shutil.which("git"):
        tmp = None
        try:
            tmp, repo = build_slop_repo()
            blob = run_tool(["python3", DEAD_TOOL, "--diff-slop"], cwd=repo)
            slop = score_slop(entries, make_real_slop_classifier(blob))
            print_slop(slop)
        except Exception as exc:
            print(f"\n=== 2. SLOP ===\n  slop harness error: {exc} (non-gating)")
        finally:
            if tmp and os.path.isdir(tmp):
                shutil.rmtree(tmp, ignore_errors=True)
    else:
        print("\n=== 2. SLOP ===\n  git not found -- slop scoring skipped")

    return final_verdict(liveness)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="run offline with an inline mock classifier (no tools)")
    args = ap.parse_args()

    if not os.path.isfile(ORACLE):
        print(f"oracle not found: {ORACLE}", file=sys.stderr)
        return 2
    entries = load_oracle()
    print(f"loaded {len(entries)} oracle entries from {os.path.relpath(ORACLE, ROOT)}")

    if args.self_test:
        return run_self_test(entries)
    return run_real(entries)


if __name__ == "__main__":
    sys.exit(main())
