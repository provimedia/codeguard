# Code Guardian

A mandatory audit skill for [Claude Code](https://claude.com/claude-code) that prevents bugs by enforcing plan-time, build-time, and debug-time reflexes. Born from real bugs that escaped audits in production — every rule is backed by a concrete incident citation in `SKILL.md`.

- **Version:** v5 (Plan-Mode Edition)
- **Platform:** macOS / Linux
- **Languages:** English + German trigger phrases

---

## What Code Guardian Enforces

### PLAN MODE (v5 — new)

Six plan-time reflexes that review a spec or plan *before* code is written:

| ID | Rule |
|----|------|
| P1 | Cross-Layer Trace for every new field (DB → Model → Controller → View) |
| P2 | Scale Verification (cursor / lazy / get based on row count) |
| P3 | Secrets Hygiene (header-based auth, never URL key params) |
| P4 | `config:cache` Safety (`config()` not `env()` outside config files) |
| P5 | Pattern Source Quality Check (audit inherited code before copying) |
| P6 | WIP Staging Discipline (hunk-level `git add` on branches with WIP) |

### BUILD MODE (v4)

- **Pre-flight:** scope, schema check, dependency impact
- **7-point audit** after every code change
- Every claim backed by command output (`Verified-by:` line)

### DEBUG MODE

- Cross-page dependency trace
- Root cause vs. symptom separation
- Two-path fix proposals (minimal + structural)

---

## Repository Layout

```
.
├── install.sh                  ← automated installer (macOS + Linux)
├── README.md                   ← this file
└── code-guardian/
    └── SKILL.md                ← the skill definition (~715 lines)
```

---

## Installation

**Prerequisite:** Claude Code installed on the target machine.

```bash
git clone https://github.com/provimedia/codeguard.git
cd codeguard
./install.sh
```

The installer will:

- Create `~/.claude/skills/` if it does not exist
- Back up any existing `code-guardian` install to `~/.claude/skills/code-guardian.backup.YYYYMMDD-HHMMSS`
- Copy the new `SKILL.md` into `~/.claude/skills/code-guardian/`
- Verify that v5 plan-time reflexes are present
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
3. Confirm v5 plan-time reflexes are loaded:

   ```bash
   grep "PLAN MODE (v5" ~/.claude/skills/code-guardian/SKILL.md
   ```

   Should return **1 match**.

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

Code Guardian v5 is designed to **compose** with Anthropic's superpowers skills, not replace them:

| Superpowers skill                  | Code Guardian role                                          |
|------------------------------------|-------------------------------------------------------------|
| `superpowers:brainstorming`        | PLAN MODE reviews the output spec before a plan is written  |
| `superpowers:writing-plans`        | PLAN MODE reviews the final plan before dispatch            |
| `superpowers:subagent-driven-development` | BUILD MODE runs in each subagent's post-impl audit     |
| `superpowers:systematic-debugging` | DEBUG MODE drives the hypothesis-verification loop          |

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
        "command": "echo 'Code Guardian reminder: run 7-point audit before next step'"
      }]
    }]
  }
}
```

Optional — the skill self-activates via its frontmatter triggers regardless.

---

## Version History

- **v5** (2026-04-15) — Plan Mode added. Six plan-time reflexes (P1–P6) born from the Product Helpful Text feature session: cross-layer trace at plan-time, scale verification, secrets hygiene, `config:cache` safety, pattern-source quality, WIP staging discipline.
- **v4** — Verification-not-assertion rules. Hunt-and-replace mandatory. Layout-link → route existence check. Eloquent accessors need `$appends`.
- **v3 and earlier** — Pre-flight schema check, dependency impact analysis, 7-point audit structure, debug mode with two-path fix proposals.

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
