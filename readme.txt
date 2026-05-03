========================================================================
  Code Guardian Skill — v6 (Redundancy-Reflex Edition)
  Claude Code installation package
========================================================================

WHAT IS THIS
------------
Code Guardian is a mandatory audit skill for Claude Code that prevents
bugs by enforcing:

  • REDUNDANCY reflexes (v6 — NEW)
      R1 Hardcoded Secrets / Credential Duplication
         (known-prefix scan: AIza, sk-, AKIA, ghp_, JWT, Slack/Discord
          webhooks, private-key blocks; same-secret-in-2+-files detector)
      R2 Cross-File Code Clones (function-body hash, normalized)
      R3 Cross-File Template/Markup Clones (HTML/Blade/Vue blocks ≥ 200ch)
      R4 Config-as-Code Leaks (URL/email/absolute-path duplicated 2+ files)
      R5 Cross-File Query Clones (Eloquent chain / SQL fragment)
      Pre-Flight 1c expanded into 1c.1/1c.2/1c.3 (secret/function/template
      pre-search) — prevents duplicates BEFORE the first edit, not after.
      Three helper scripts ship in code-guardian/tools/.

  • PLAN-TIME reflexes (v5)
      P1 Cross-Layer Trace for every new field (DB → Model → Controller → Vue)
      P2 Scale Verification (cursor/lazy/get based on row count)
      P3 Secrets Hygiene (header-based auth, never URL key params)
      P4 config:cache Safety (config() not env() outside config files)
      P5 Pattern Source Quality Check (audit inherited code before copying)
      P6 WIP Staging Discipline (hunk-level git add on branches with WIP)

  • BUILD-TIME reflexes (v4)
      Pre-flight: scope, schema check, dependency impact
      Audit: 7-point verification after every code change
      All checks backed by command output ("Verified-by:" line)

  • DEBUG-TIME reflexes
      Cross-page dependency trace
      Root cause vs symptom separation
      Two-path fix proposals (minimal + structural)

Born from real bugs that escaped audits in production. Each rule has
a concrete real-bug citation in the SKILL.md file.


PACKAGE CONTENTS
----------------
code-guardian-skill-v6.zip
├── install.sh                  ← automated installer (macOS + Linux)
├── readme.txt                  ← this file
└── code-guardian/
    ├── SKILL.md                ← the skill definition (~1080 lines)
    └── tools/                  ← v6 helper scripts (R1-R5 reflexes)
        ├── detect-secrets.sh           ← R1: known-prefix + dup-secret scan
        ├── detect-clones.py            ← R2/R3/R5: cross-file clone hashing
        └── detect-config-leaks.sh      ← R4: duplicated URL/email/path

The helper scripts are zero-dependency (POSIX bash + Python 3 stdlib).
Each emits a SUMMARY footer line that the skill paste as "Verified-by"
proof in the audit report. Exit code = 1 on findings, 0 if clean.


INSTALLATION
------------

Prerequisite: Claude Code is already installed on the target machine.
             (https://claude.com/claude-code)

1. Copy the ZIP file to the target machine. Any location works —
   ~/Downloads, ~/Desktop, /tmp, etc.

2. Unzip:

      unzip code-guardian-skill-v5.zip
      cd code-guardian-package

3. Run the installer:

      ./install.sh

   The installer will:
     • Create ~/.claude/skills/ if it doesn't exist
     • Back up any existing code-guardian installation to
       ~/.claude/skills/code-guardian.backup.YYYYMMDD-HHMMSS
     • Copy the new SKILL.md into ~/.claude/skills/code-guardian/
     • Make tools/*.sh and tools/*.py executable
     • Verify the v5 plan-time reflexes are present
     • Verify the v6 redundancy reflexes (R1-R5) are present
     • Print next steps

   Prerequisites for the v6 helper scripts:
     • bash (any version, including macOS 3.2)
     • python3 (any 3.x; uses stdlib only — no pip install needed)
     • grep, awk, sed, sort, uniq (POSIX core utils)
   No npm, no composer, no pip, no homebrew packages required.

4. Installer options:

      ./install.sh             # Normal install with backup
      ./install.sh --force     # Overwrite existing without backup
      ./install.sh --dry-run   # Preview what would happen
      ./install.sh --help      # Show usage


POST-INSTALL VERIFICATION
-------------------------

1. Open Claude Code:

      claude

2. Type /help and look for code-guardian in the skills list.

   OR — start any task that matches a trigger phrase (German or English):
   "add", "create", "fix", "refactor", "aendere", "erstelle", "baue"...
   and watch for the skill to auto-activate.

3. Verify v5 plan-time reflexes are loaded:

      grep "PLAN MODE (v5" ~/.claude/skills/code-guardian/SKILL.md

   Should return 1 match.

4. Verify v6 redundancy reflexes are loaded:

      grep "v6 Redundancy Rules" ~/.claude/skills/code-guardian/SKILL.md
      ls -1 ~/.claude/skills/code-guardian/tools/

   First should return 1 match. ls should print:
      detect-clones.py
      detect-config-leaks.sh
      detect-secrets.sh

5. Smoke-test the helper scripts against any code repository:

      bash ~/.claude/skills/code-guardian/tools/detect-secrets.sh /path/to/repo
      bash ~/.claude/skills/code-guardian/tools/detect-config-leaks.sh /path/to/repo
      python3 ~/.claude/skills/code-guardian/tools/detect-clones.py \
              --root /path/to/repo --kind code --cross-file-only

   Each should end with a "SUMMARY findings=N ... exit=0|1" line.


UNINSTALL
---------

      rm -rf ~/.claude/skills/code-guardian

If you want to restore a backup:

      mv ~/.claude/skills/code-guardian.backup.YYYYMMDD-HHMMSS \
         ~/.claude/skills/code-guardian


INTEGRATION WITH SUPERPOWERS SKILLS
-----------------------------------
Code Guardian v5 is designed to compose with Anthropic's superpowers
skills, not replace them:

  superpowers:brainstorming     → Code Guardian PLAN MODE reviews
                                   the output spec before plan is written
  superpowers:writing-plans     → Code Guardian PLAN MODE reviews
                                   the final plan before dispatch
  superpowers:subagent-driven-  → Code Guardian BUILD MODE runs in every
    development                   subagent's post-implementation audit
  superpowers:systematic-       → Code Guardian DEBUG MODE drives the
    debugging                     hypothesis-verification loop

Both systems should be active at the same time — they reinforce each
other. When they conflict, user instructions always win.


RECOMMENDED COMPANION SETTINGS
------------------------------
Add to ~/.claude/settings.json to make Code Guardian audit reminders
fire automatically after Write/Edit tool calls:

      {
        "hooks": {
          "PostToolUse": [{
            "matcher": "Write|Edit",
            "hooks": [{
              "type": "command",
              "command": "echo '🛡️  Code Guardian reminder: run 7-point audit before next step'"
            }]
          }]
        }
      }

(Optional — the skill self-activates via its frontmatter triggers regardless.)


SUPPORT / UPDATES
-----------------
This skill is maintained manually. Updates are delivered as new ZIP
packages with incremented version numbers in the filename (e.g.,
code-guardian-skill-v6.zip).

To upgrade: just re-run ./install.sh from the new ZIP — the backup
flow ensures the old version is preserved.


VERSION HISTORY
---------------
v6 (2026-05-03) — Redundancy reflex layer added. Five reflexes
                  (R1-R5) replace the previous one-line Redundancy
                  spot-check: hardcoded-secret duplication detection,
                  cross-file code-clone hashing, template-block
                  duplication, config-leak (URL/email/path) detection,
                  cross-file Eloquent/SQL clone hashing. Pre-Flight 1c
                  expanded to 1c.1/1c.2/1c.3 (secret/function/template
                  pre-search). Three helper scripts ship in tools/,
                  zero-dependency, each emitting a SUMMARY footer for
                  paste-as-Verified-by. Born from real bugs: hardcoded
                  Gemini API key duplicated across 4 files, sitemap
                  generation logic duplicated controller↔command,
                  validation Eloquent chains duplicated across
                  controllers (security divergence risk).

v5 (2026-04-15) — Plan Mode added. Six plan-time reflexes (P1-P6)
                  born from Product Helpful Text feature session:
                  cross-layer trace at plan-time, scale verification,
                  secrets hygiene, config:cache safety, pattern source
                  quality, WIP staging discipline.

v4 (prior)      — Verification-not-assertion rules. Hunt-and-replace
                  mandatory. Layout-link → route existence check.
                  Eloquent accessors need $appends.

v3 and earlier  — Pre-flight schema check, dependency impact analysis,
                  7-point audit structure, debug mode with two-path
                  fix proposals.

========================================================================
