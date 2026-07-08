# Code Guardian v12 — Update-Anleitung

Dieses Paket aktualisiert den Code-Guardian-Skill für Claude Code auf **v12**,
installiert den gebündelten **llm-council**-Companion mit und richtet die
**Hooks jetzt automatisch** ein — inklusive des neuen DECISION GATE.

## Was ist neu seit v10

### v11 — Cleanup & Anti-Slop
- **Self-Slop Sweep (always-on):** Jede Code-Änderung räumt den eigenen
  AI-Slop des Diffs automatisch weg (ungenutzte eigene Symbole/Imports,
  Debug-Reste, redundante Kommentare).
- **CLEANUP MODE (opt-in, report-only):** Klassifiziert bestehenden toten /
  verwaisten / redundanten Code (LIVE / ASSERTED-DEAD / VERIFIED-DEAD-PRIVATE)
  — **löscht nie selbst**; jedes positive Signal beweist LIVE.
- Neues Tool `detect-dead-code.py` (report-only Liveness-Aggregator).

### v12 — Decision Gate
- **Keine Optionsfrage mehr ohne Empfehlung:** Bevor Claude euch eine
  A/B/C-Frage stellt, MUSS es eine begründete Empfehlung erarbeiten
  (T1-Rubrik: Langlebigkeit · Architektur-Sauberkeit · Reversibilität ·
  Folgekosten · Best Practice; Tie-Break: langfristig schlägt kurzfristig).
  Bei großer Tragweite eskaliert es auf parallele Advokaten (T2) oder den
  LLM-Council (T3). **Empfohlene Option steht immer an erster Stelle mit
  „(Empfohlen)" — entschieden wird nie autonom, ihr entscheidet.**
- **Deterministische Durchsetzung:** Der neue Hook `decision-gate-check.sh`
  blockt jede unmarkierte Optionsfrage, bevor sie euch erreicht; Claude muss
  sie mit Empfehlung neu stellen.
- **llm-council liegt jetzt im Paket** und wird automatisch mitinstalliert
  (nur wenn noch keiner vorhanden ist — ein eigener/angepasster Council wird
  nie überschrieben).

## Schritt 1 — Installieren (EIN Befehl, macht alles)

```bash
unzip code-guardian-v12-update.zip -d code-guardian-v12 && cd code-guardian-v12
./install.sh
```

Der Installer erledigt jetzt ALLES selbst:

1. Backup der bestehenden Skill-Installation nach
   `~/.claude/skill-backups/code-guardian.backup.<timestamp>/`
2. Skill v12 nach `~/.claude/skills/code-guardian/`
3. `llm-council` nach `~/.claude/skills/llm-council/` (nur falls fehlt)
4. Die 3 Hooks nach `~/.claude/hooks/` (werden bei Updates überschrieben):
   - `code-guardian-prompt-check.sh` — Skill-Reminder bei Code-/Bug-Prompts
   - `code-guardian-reminder.sh` — Audit-Reminder nach jedem Write/Edit
   - `decision-gate-check.sh` — **NEU:** blockt Optionsfragen ohne Empfehlung
5. **Automatische Registrierung in `~/.claude/settings.json`** — idempotenter
   Merge: vorher Backup (`settings.json.backup-code-guardian.<timestamp>`),
   nur die 3 eigenen Einträge werden ergänzt (falls nicht schon vorhanden),
   alles andere in der Datei bleibt unangetastet. Das manuelle
   JSON-Editieren aus der v10-Anleitung entfällt.

`./install.sh --force` überschreibt ohne Backup (auch einen vorhandenen
llm-council). `./install.sh --dry-run` zeigt nur, was passieren würde.

## Schritt 2 — Claude Code NEU STARTEN (wichtig!)

Hooks werden nur beim **Session-Start** eingelesen. Eine laufende Session
übernimmt sie NICHT — auch nicht per `/clear` oder Skill-Reload.

```
claude beenden → neu starten → /hooks eintippen
```

Unter `/hooks` müssen erscheinen:
- `UserPromptSubmit` → `code-guardian-prompt-check.sh`
- `PostToolUse` (Write|Edit) → `code-guardian-reminder.sh`
- `PreToolUse` (AskUserQuestion) → `decision-gate-check.sh`

## Schritt 3 — Verifizieren

```bash
grep -m1 "Code Guardian (v12)" ~/.claude/skills/code-guardian/SKILL.md   # → Treffer
ls ~/.claude/skills/code-guardian/references/   # → 8 .md-Dateien (inkl. decision-gate.md, cleanup-mode.md)
ls ~/.claude/skills/code-guardian/tools/        # → 5 Skripte (inkl. detect-dead-code.py)
ls ~/.claude/skills/llm-council/SKILL.md        # → vorhanden
ls -l ~/.claude/hooks/decision-gate-check.sh    # → -rwxr-xr-x

# Hook-Funktionstest (muss eine deny-JSON-Zeile ausgeben):
echo '{"tool_input":{"questions":[{"question":"A oder B?","options":[{"label":"A"},{"label":"B"}]}]}}' \
  | ~/.claude/hooks/decision-gate-check.sh
```

Der Installer prüft die v12-Marker selbst und meldet
`v12 markers + symbol-loss + dead-code + decision gates detected`.

## Voraussetzungen

- **jq** — Pflicht für die Hooks: `which jq || brew install jq`
  (fehlt jq, blocken die Hooks NICHTS — sie schalten sich still ab, fail-open)
- **Python 3** — für die Tools und die settings.json-Registrierung:
  `python3 --version`

## Rollback

- Skill: Backup-Ordner aus `~/.claude/skill-backups/code-guardian.backup.<timestamp>/`
  zurück nach `~/.claude/skills/code-guardian/` kopieren.
- Hooks/Settings: `~/.claude/settings.json.backup-code-guardian.<timestamp>`
  zurückkopieren; Hook-Skripte in `~/.claude/hooks/` ggf. löschen.

Stand: 08.07.2026 · Fragen an Alex
