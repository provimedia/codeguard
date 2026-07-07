# Vendor `llm-council` into the codeguard repo — Design

**Date:** 2026-07-08 · **Status:** Approved (Option: install-only-if-missing) · **Scope:** 3 files

## Problem

`code-guardian` invokes the `llm-council` skill at three judgment points (DEBUG Phase 3
gate, DEBUG two-failure escalation, BUILD Pre-Flight 1e Blast-Radius gate). The council
lived only at `~/.claude/skills/llm-council/` on the author's machine — users installing
codeguard from this repo did not get it, so all three Council Gates silently degraded.

## Decision

Ship the council with the repo and install it automatically:

1. **`llm-council/SKILL.md`** — verbatim vendored copy (SHA `c17c053c…`), top-level
   sibling of `code-guardian/`. Pure vendor, zero content edits.
2. **`install.sh`** — replaces the old warn-only check with a real companion install:
   - council **absent** → copy bundled copy in, verify `name: llm-council` marker
   - council **present** (dir or symlink) → leave untouched (user may have customized it)
   - `--force` → overwrite with bundled copy
   - `--dry-run` → report intent, write nothing
   - new source sanity check: `llm-council/SKILL.md` must exist in the repo
3. **`README.md`** — council reframed from "recommended companion, skipped silently if
   absent" to "bundled & auto-installed"; layout tree, prerequisite line, installer
   bullets, companion table updated.

## Rejected alternatives

- **Backup + always replace:** keeps versions in lockstep but clobbers user
  customizations on every run — wrong default for a *companion* skill.
- **Merging council content into code-guardian/SKILL.md:** breaks the separate-skill
  invocation contract (`invoke the llm-council skill`) and bloats the always-loaded body.

## Out of scope (reported, not fixed)

The vendored council SKILL.md has a pre-existing internal contradiction: step 5 says
"Do NOT generate an HTML report" while the closing notes say "The visual report
matters… Make the HTML output clean." Shipped verbatim; fix upstream separately.

## Verification (all Verified-by command output, 2026-07-08)

- `diff` + `shasum`: vendored copy identical to source (c17c053c…)
- `bash -n install.sh`: syntax OK
- Throwaway-HOME matrix: fresh install lands both skills · pre-existing custom council
  preserved byte-identical · `--force` overwrites to bundled SHA · `--dry-run` creates nothing
- `detect-secrets.sh llm-council` → `SUMMARY findings=0 exit=0`
- `detect-symbol-loss.py --git` → `SUMMARY findings=0 lost=0 changed=0 moved=0 exit=0`
