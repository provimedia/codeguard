# Code Guardian

A mandatory audit skill for [Claude Code](https://claude.com/claude-code) that prevents bugs by enforcing plan-time, build-time, and debug-time reflexes. Born from real bugs that escaped audits in production — every rule is backed by a concrete incident citation in `SKILL.md`.

- **Version:** v7.1 (Council Edition)
- **Platform:** macOS / Linux
- **Languages:** English + German trigger phrases

---

## What Code Guardian Enforces

### PLAN MODE (v5)

Six plan-time reflexes that review a spec or plan *before* code is written:

| ID | Rule |
|----|------|
| P1 | Cross-Layer Trace for every new field (DB → Model → Serializer → Transport → Client) |
| P2 | Scale Verification (cursor / lazy / get based on row count) |
| P3 | Secrets Hygiene (header-based auth, never URL key params) |
| P4 | `config:cache` Safety (`config()` not `env()` outside config files) |
| P5 | Pattern Source Quality Check (audit inherited code before copying) |
| P6 | WIP Staging Discipline (hunk-level `git add` on branches with WIP) |

### BUILD MODE (v4 + v6 + v7.1)

- **Pre-flight:** scope, schema check, dependency impact, three redundancy pre-searches (secret/constant, function/class, template/view), and (v7.1) the **Blast-Radius Council Gate** — proactive analog of DEBUG Phase 3's council, fires only when ALL of: ≥ 5 consumers + non-additive change + sparse test coverage + non-trivial reversal
- **Audit layers** after every code change: Correctness, Logic, Efficiency, **Redundancy**, Security
- Every claim backed by command output (`Verified-by:` line)

### Redundancy Layer (v6 — new)

Five reflexes, each driven by a helper script in `code-guardian/tools/`. Every reflex emits a `SUMMARY findings=… exit=…` footer that becomes the `Verified-by:` proof. "I checked, looks clean" is forbidden.

| ID | Reflex                                            | Helper script               |
|----|---------------------------------------------------|------------------------------|
| R1 | Hardcoded secrets / credential duplication        | `tools/detect-secrets.sh`    |
| R2 | Cross-file code clones (function/method bodies)   | `tools/detect-clones.py`     |
| R3 | Cross-file template/view clones                   | `tools/detect-clones.py`     |
| R4 | Config / constant leakage outside config layer    | `tools/detect-config-leaks.sh` |
| R5 | Duplicate query / fetch shapes                    | `tools/detect-clones.py`     |

### DEBUG MODE (with v7 Council Gate)

- Phase 1: Collect (no fix, no suggestion)
- Phase 2: Root cause (not symptom)
- Phase 3: Two paths (minimal + structural) — **Council Gate fires when paths materially diverge**
- Phase 4: Validate before touching code
- Phase 5: Implement + verify
- Escalation: two failed root-cause fixes → **Council unconditionally** before STOP

### v7 / v7.1 LLM Council Integration

The [`llm-council`](https://github.com/) skill is consulted at the skill's three genuine judgment points — and nowhere else:

| Gate | Mode | Trigger | Gating |
|------|------|---------|--------|
| Phase 3 Path A/B | DEBUG (reactive) | Bug fix paths materially diverge | OR-of-4 (any condition fires) |
| Escalation | DEBUG (reactive) | Two root-cause fixes have failed | Unconditional |
| Blast-Radius (v7.1) | BUILD Pre-Flight (proactive) | High-impact non-additive change | **AND-of-4** (all must fire) |

The reactive gates are looser; the proactive gate is strict by design — a live bug is concrete evidence of stakes, a pre-flight change is not, and the cost of council fatigue is real. The council is a *decision aid*, never a verification substitute. Verification proof still comes from the helper scripts and Cross-Layer Checks.

### Cleanup & Anti-Slop (v11)

Two safety-separated capabilities for keeping the codebase clean — split by risk, with the boundary being the git diff:

- **Self-Slop Sweep** (always-on, BUILD MODE audit Layer 6, diff-only): every code change auto-strips the AI-slop *this change itself* introduced — unused symbols/imports you just added, debug leftovers (`var_dump`/`dd`/`console.log`/`print`), redundant comments, single-use abstractions. Mechanical slop is removed; semantic slop (reimplementation, redundant comments) is flagged for reuse-grep / judgment. It only ever touches your own just-written, zero-reference additions.
- **CLEANUP MODE** (opt-in, **report-only** — never deletes): on an explicit request ("clean up", "räum auf", "dead code", "redundant"), classifies pre-existing dead/orphaned/redundant code as **LIVE / ASSERTED-DEAD / VERIFIED-DEAD-PRIVATE** under a liveness-veto gate, and reports it for your decision. **It never deletes productive code.**

The governing law: **any single positive signal (a reference, a route/template/DI/DB-dispatch/config hit) proves LIVE and vetoes removal; absence of references never proves dead.** Only closed-world symbols (PHP `private`, Python `_name`, non-exported JS/TS) with zero references and no framework keep-alive flag can ever reach VERIFIED-DEAD-PRIVATE — and even then the skill only *recommends*; the human deletes. Validated against a 30-trap adversarial fixture in `test/`: **0 productive-code symbols flagged deletable (CRITICAL_FP=0)**.

The new helper `tools/detect-dead-code.py` is a dependency-free, report-only liveness-evidence aggregator — it classifies, it never mutates a source file.

---

## Repository Layout

```
.
├── install.sh                     ← automated installer (macOS + Linux)
├── README.md                      ← this file
├── code-guardian/
│   ├── SKILL.md                   ← the skill definition (~1110 lines)
│   └── tools/
│       ├── detect-secrets.sh      ← R1 hardcoded-secret scanner
│       ├── detect-clones.py       ← R2/R3/R5 cross-file clone detector (Rule-of-Three guard)
│       ├── detect-config-leaks.sh ← R4 env()/getenv() leakage scanner
│       ├── detect-symbol-loss.py  ← post-change silent-symbol-loss gate
│       └── detect-dead-code.py    ← v11 report-only liveness aggregator (Self-Slop + CLEANUP MODE)
└── llm-council/
    └── SKILL.md                   ← bundled companion — powers the Council Gates
```

---

## Installation

**Prerequisite:** Claude Code installed on the target machine. The `llm-council` companion skill is **bundled** in this repo and installed automatically, so the Council Gates work out of the box — no separate download. If you already have your own `llm-council`, the installer leaves it untouched (see below).

```bash
git clone https://github.com/provimedia/codeguard.git
cd codeguard
./install.sh
```

The installer will:

- Create `~/.claude/skills/` if it does not exist
- Back up any existing `code-guardian` install to `~/.claude/skills/code-guardian.backup.YYYYMMDD-HHMMSS`
- Copy `SKILL.md` and `tools/` into `~/.claude/skills/code-guardian/`
- Set executable bits on the helper scripts
- Verify that v5 + v6 + v7 + v7.1 markers are present
- Install the bundled `llm-council` companion into `~/.claude/skills/llm-council/` **only if it is not already present** (an existing council is left untouched unless `--force` is passed)
- Print next steps

### Installer options

```bash
./install.sh             # Normal install with backup
./install.sh --force     # Overwrite existing without backup
./install.sh --dry-run   # Preview without writing anything
./install.sh --help      # Show usage
```

---

## Post-Install Verification

1. Open Claude Code: `claude`
2. Type `/help` and look for **code-guardian** in the skills list.
   Alternatively, start any task that matches a trigger phrase (EN or DE) —
   *"add", "create", "fix", "refactor", "aendere", "erstelle", "baue"* …
   — and watch for the skill to auto-activate.
3. Confirm all version markers are loaded:

   ```bash
   grep -E "PLAN MODE \(v5|v6 Redundancy Rules|v7 Council Rules|v7\.1 Proactive Council Rules" \
       ~/.claude/skills/code-guardian/SKILL.md
   ```

   Should return **4 matches**.

4. Confirm the helper scripts are executable:

   ```bash
   ls -l ~/.claude/skills/code-guardian/tools/
   ```

   All three files should be `-rwxr-xr-x`.

---

## Uninstall

```bash
rm -rf ~/.claude/skills/code-guardian
```

Restore a previous backup:

```bash
mv ~/.claude/skills/code-guardian.backup.YYYYMMDD-HHMMSS \
   ~/.claude/skills/code-guardian
```

---

## Integration with Superpowers Skills

Code Guardian is designed to **compose** with Anthropic's superpowers skills, not replace them:

| Superpowers skill                         | Code Guardian role                                          |
|-------------------------------------------|-------------------------------------------------------------|
| `superpowers:brainstorming`               | PLAN MODE reviews the output spec before a plan is written  |
| `superpowers:writing-plans`               | PLAN MODE reviews the final plan before dispatch            |
| `superpowers:subagent-driven-development` | BUILD MODE runs in each subagent's post-impl audit          |
| `superpowers:systematic-debugging`        | DEBUG MODE drives the hypothesis-verification loop          |
| `llm-council` (bundled companion)         | DEBUG Phase 3 Council Gate + Escalation council + BUILD 1e  |

Run both systems at the same time — they reinforce each other. When they conflict, user instructions always win.

---

## Recommended Companion Settings

Add to `~/.claude/settings.json` to fire an audit reminder after every `Write` / `Edit`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "echo 'Code Guardian reminder: run 5-layer audit before next step'"
      }]
    }]
  }
}
```

Optional — the skill self-activates via its frontmatter triggers regardless.

---

## Version History

- **v11** (2026-06) — Cleanup & Anti-Slop. Always-on **Self-Slop Sweep** (BUILD audit Layer 6, diff-only) strips the agent's own AI-slop; opt-in **CLEANUP MODE** (report-only) classifies pre-existing dead/orphaned/redundant code (LIVE / ASSERTED-DEAD / VERIFIED-DEAD-PRIVATE) under a liveness-veto gate and never deletes productive code. New `tools/detect-dead-code.py` (report-only liveness aggregator) + Rule-of-Three guard in `detect-clones.py`. Validated against a 30-trap adversarial fixture (`test/`): CRITICAL_FP=0. *(Note: this history skips v8–v10.1, documented in `code-guardian/references/design-rationale.md`; the sections above still describe v7.1 and predate them.)*
- **v7.1** (2026-05) — Blast-Radius Council Gate added to BUILD MODE Pre-Flight (step 1e). Proactive analog of DEBUG Phase 3's reactive gate. Strictly AND-of-4 gated (≥ 5 consumers + non-additive change + sparse test coverage + non-trivial reversal) to avoid council fatigue on routine pre-flights. Catches architectural divergence at build-time, orders of magnitude cheaper than catching it after a regression ships.
- **v7** (2026-05) — LLM Council integration. Council Gate in DEBUG Phase 3 (gated, 4 conditions) and unconditional council in Escalation after two failed root-cause fixes. Council is a decision aid, not a verification substitute. Heavy expansion of Cross-Layer Checks (auth parity, session lifecycle, HTTP cacheability, log hygiene, CRLF injection, CSRF-on-GET, index coercion, charset drift, deep-offset pagination, cache invalidation coverage, TOCTOU / idempotency, SSRF). Security reflex covers JWT `alg=none`, unserialize / LFI / command-injection / XXE sinks, rate-limit key scope, IPv6 /64 masking.
- **v6** (2026-05) — Redundancy audit layer with five reflexes (R1–R5) and three helper scripts shipped in `tools/`. Pre-flight 1c expanded into three pre-searches (secret/constant, function/class, template/view).
- **v5** (2026-04) — Plan Mode added. Six plan-time reflexes (P1–P6) born from a real Product-Helpful-Text feature session: cross-layer trace, scale verification, secrets hygiene, `config:cache` safety, pattern-source quality, WIP staging discipline.
- **v4** — Verification-not-assertion rules. Hunt-and-replace mandatory. Layout-link → route existence check. Eloquent accessors need `$appends`.
- **v3 and earlier** — Pre-flight schema check, dependency impact analysis, audit structure, debug mode with two-path fix proposals.

---

## Updates

To upgrade to a newer version, pull the latest from this repo and re-run `./install.sh` — the backup flow preserves your previous install.

```bash
git pull
./install.sh
```

---

## License

See the repository for license information. Issues and pull requests welcome.
