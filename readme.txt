========================================================================
  Code Guardian Skill — v5 (Plan-Mode Edition)
  Claude Code installation package
========================================================================

WHAT IS THIS
------------
Code Guardian is a mandatory audit skill for Claude Code that prevents
bugs by enforcing:

  • PLAN-TIME reflexes (v5 — NEW)
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
code-guardian-skill-v5.zip
├── install.sh                  ← automated installer (macOS + Linux)
├── readme.txt                  ← this file
└── code-guardian/
    └── SKILL.md                ← the skill definition (~715 lines)


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
     • Verify the v5 plan-time reflexes are present
     • Print next steps

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
