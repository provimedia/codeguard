# Code Guardian v16.1 — Update-Anleitung

Dieses Paket aktualisiert den Code-Guardian-Skill für Claude Code auf **v16**,
installiert die gebündelten Companion-Skills **llm-council** und **senior-dev**
mit und richtet die **Hooks automatisch** ein — inklusive DECISION GATE und
DEPLOY GATE. Neu in v16: der **Senior Dev Companion** (`senior-dev`) — er lädt
bei jeder Eingabe zuerst und sorgt für Task-Intake plus einen durchgehenden
Senior-Mindset.

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

### v13 — Generalization Gate (Anti-Hardcoding)

- **Beispiele aus der Anforderung sind DATEN, niemals CODE:** Wenn die
  Anforderung universell ist („für jede Branche") und Beispielwerte nennt
  (domain1.de, ein Datum), darf keiner davon als `if`/`switch`/Regex/
  Lookup-Konstante enden — Claude muss den generischen Mechanismus bauen
  (Klassifikator/Parser/DB/KI-Analyse). Zwei Pflicht-Tests: Löschtest und
  Zweitbeispiel-Test.
- **Neues Tool `detect-hardcoded-cases.py`** (report-only): findet Domains/
  URLs/E-Mails/Datumswerte (+ per `--examples` übergebene Werte) in
  Entscheidungs-Kontexten; Config-/Test-/Fixture-Dateien sind ausgenommen.
- **Ehrliche Ausnahme:** echte Einzelfall-Geschäftsregeln brauchen den Marker
  `INTENTIONAL-SPECIAL-CASE: <Grund>` — sichtbar statt eingeschmuggelt.
- Verdrahtet in PLAN MODE (neuer Reflex P7), BUILD-Audit (Logic-Layer) und
  den always-on Self-Slop Sweep (diff-only).

### v14 — Deploy Gate (Deploy-Hygiene)

- **Nichts geht ungeprüft auf einen Server:** Vor JEDEM Deploy (deploy.sh,
  rsync/scp/sftp auf einen Remote, ftp, git push auf prod/live) klassifiziert
  Claude die komplette Transferliste in 4 Klassen:
  **DEPLOY** (App-Code) · **SERVER-ONLY** (nie übertragen, muss aber auf dem
  Server existieren — Prod-`.env`, `storage/`, Uploads, Zertifikate; wird auch
  NIE gelöscht) · **NEVER-ON-SERVER** (weder übertragen noch dulden — Tests,
  Docs, `*.sql`-Dumps, `.git`, CI/IDE-Dateien, Audit-Logs) · **REVIEW**
  (projektabhängig, z. B. `node_modules/`).
- **Altlasten werden entfernt:** Nach dem Deploy prüft Claude den Server
  (HTTP-Probes auf `/.env`, `/phpunit.xml`, Dumps usw. + SSH-find, wo möglich).
  Funde werden als klassifizierte Löschliste vorgelegt — **ihr gebt EINMAL
  frei**, Claude löscht und verifiziert per Re-Probe. Eine per HTTP erreichbare
  `.env` wird NIE gelöscht, sondern die Webserver-Config gefixt.
- **Excludes dauerhaft:** Fixes landen committed im Deploy-Mechanismus
  (deploy.sh-Excludes / `.deployignore`), nie als Einmal-Filter.
- **Neues Tool `detect-deploy-artifacts.py`** (report-only) + projektspezifische
  `.code-guardian-deploy.yml` (Zusatz-Patterns, begründete `allow:`-Ausnahmen).
- **Deterministische Durchsetzung:** Der neue Hook `deploy-gate-check.sh`
  blockt jedes Deploy-Kommando, solange kein frischer Gate-Report
  (`.code-guardian-deploy-report.md`, `DEPLOY GATE: APPROVED`, < 30 min)
  existiert. rsync `--dry-run`, lokales rsync und git push auf normale
  Remotes bleiben frei.

### v15 — Data Gate (Vollbild vor Daten-Verdikten)

- **Kein Daten-Verdikt mehr aus dem Teilbild:** Bevor Claude Datensätze als
  „verwaist / hängen geblieben / nie bearbeitet / inkonsistent" einstuft — oder
  auf Basis interpretierter DB-Daten fixt, migriert, bereinigt oder berichtet —
  MUSS das Vollbild stehen: **V1** Live-Schema-Inventar JEDER beteiligten
  Tabelle (Introspection, nie Doku/Gedächtnis) plus ein FK-Hop (Historie-/Log-/
  Queue-/Schedule-Tabellen), alle zustandstragenden Spalten markiert
  (Aufschub-Daten wie `deadline_ab`/`freigabe_ab`, Gültigkeitsfenster, Flags,
  Soft-Delete) · **V2** `SELECT *` auf die konkreten Zeilen (nie eine
  handverlesene Spaltenliste) + Vergleich mit einer gesunden Geschwister-Zeile ·
  **V3** das ECHTE Prädikat des Verarbeiters (Cron/Job/Trigger) gegen die
  Zeilen testen — ein vorgegebenes Kriterium (Ticket, Meeting, veraltete Doku)
  ist Hypothese, nie Prädikat · **V4** die harmlose Erklärung („legitimer
  Wartezustand") ist IMMER Kandidat und stirbt nur durch Beleg.
- **Anlass:** echter Fehlbefund — Aufträge wurden als „verwaist" gemeldet, weil
  die Wartespalte `deadline_ab` dem Analysten unbekannt war. Das Gesetz:
  **Abwesenheit von Aktivität beweist nie kaputte Daten.**
- **Verbindlicher Output:** Jedes Daten-Verdikt trägt den „Vollbild-Block"
  (geprüfte Tabellen · ausgeschlossene Zustandsspalten · gedumpte Zeilen ·
  getestetes Prädikat · Verdikt `DEFECT | INTENDED STATE | MIXED |
  INSUFFICIENT PICTURE`). Ohne Block ist das Verdikt nicht berichtsfähig;
  ohne Bild heißt es ehrlich `INSUFFICIENT PICTURE` statt raten.
- Neu: `references/data-gate.md`; DEBUG MODE verdrahtet (Phase 1e +
  Pflicht-Kandidat in Phase 2). **Kein neuer Hook** — ein Verdikt ist Prosa,
  kein Tool-Call; der Pflicht-Block selbst ist die Durchsetzung.

### v16 — Senior Dev Companion

- **Task-Intake bei JEDER Eingabe:** Der `UserPromptSubmit`-Hook
  (`code-guardian-prompt-check.sh`) feuert jetzt nicht mehr nur bei
  Code-/Bug-Prompts, sondern bei jedem Prompt und lässt zuerst den neuen
  Companion-Skill **`senior-dev`** laden. Der übernimmt die Anfrage als
  Senior-Fullstack-Entwickler: Triage in **question / trivial / normal /
  large**, die Intake-Tiefe skaliert mit der Klasse (Frage: keine Prüfung,
  trivial: 3 Kernchecks, groß/riskant: volles Senior-Protokoll plus
  `superpowers:brainstorming` → `writing-plans` → PLAN MODE); erst danach
  wird in code-guardian bzw. superpowers geroutet.
- **Der Senior-Fragenkatalog (`references/senior-card.md`, §A–§E):** §A
  Intake, §B Architektur & Design, §C beim Coden, §D Meta-Blick, §E
  Abschluss — per Einzeiler in PLAN-, BUILD- und DEBUG-Mode verankert, damit
  die Fragen während der ganzen Aufgabe aktiv bleiben, nicht nur am Anfang.
- **§D-Heartbeat:** `code-guardian-reminder.sh` injiziert jetzt bei jedem
  3. gezählten Code-Edit rotierend eine der §D-Meta-Fragen — ein
  deterministischer Reflex, der nicht vom Modell-Ermessen abhängt und auch
  eine Context-Kompaktierung übersteht.
- **Rule-of-Three-Skill-Vorschlag:** Jede angenommene Aufgabe wird in
  `.task-journal.md` protokolliert (Typ-Tag, Triage-Klasse, Ein-Zeiler-Ziel).
  Taucht derselbe Typ-Tag zum 2.–3. Mal auf, schlägt der Skill vor, dafür
  einen eigenen Skill zu bauen — Empfehlung + 1-Klick-Freigabe, nie autonom
  gebaut.
- `install.sh` installiert `senior-dev` gebündelt wie `llm-council` — aber
  anders als `llm-council` (nur installiert, wenn noch keiner vorhanden ist)
  wird `senior-dev` bei jedem Update immer mit dem Paket aktualisiert.

### v16.1 — Plan-Mode-Schleuse

Bei Triage-Klasse **large/unclear/risky** ruft `senior-dev` vor jeder Analyse
`EnterPlanMode` auf: Die komplette Analyse- und Planungsphase läuft hart
read-only (das Harness blockiert Edits), `ExitPlanMode` legt den fertigen Plan
zur Freigabe vor — gebaut wird erst nach dem Freigabe-Klick des Entwicklers.
Trivial-/Normal-Aufgaben durchlaufen die Schleuse bewusst nicht.

## Schritt 1 — Installieren (EIN Befehl, macht alles)

```bash
unzip code-guardian-v16.1-update.zip -d code-guardian-v16.1 && cd code-guardian-v16.1
./install.sh
```

Der Installer erledigt jetzt ALLES selbst:

1. Backup der bestehenden Skill-Installation nach
   `~/.claude/skill-backups/code-guardian.backup.<timestamp>/`
2. Skill v16 nach `~/.claude/skills/code-guardian/`
3. `llm-council` nach `~/.claude/skills/llm-council/` (nur falls fehlt) und
   `senior-dev` nach `~/.claude/skills/senior-dev/` (**NEU**, wird bei jedem
   Update immer mit installiert)
4. Die 4 Hooks nach `~/.claude/hooks/` (werden bei Updates überschrieben):
   - `code-guardian-prompt-check.sh` — Skill-Reminder bei Code-/Bug-Prompts
   - `code-guardian-reminder.sh` — Audit-Reminder nach jedem Write/Edit
   - `decision-gate-check.sh` — blockt Optionsfragen ohne Empfehlung
   - `deploy-gate-check.sh` — **NEU:** blockt Deploy-Kommandos ohne frischen
     Gate-Report
5. **Automatische Registrierung in `~/.claude/settings.json`** — idempotenter
   Merge: vorher Backup (`settings.json.backup-code-guardian.<timestamp>`),
   nur die 4 eigenen Einträge werden ergänzt (falls nicht schon vorhanden),
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
- `PreToolUse` (Bash) → `deploy-gate-check.sh`

## Schritt 3 — Verifizieren

```bash
grep -m1 "Code Guardian (v16)" ~/.claude/skills/code-guardian/SKILL.md   # → Treffer
grep -m1 "DATA GATE" ~/.claude/skills/code-guardian/SKILL.md             # → Treffer
ls ~/.claude/skills/code-guardian/references/   # → 11 .md-Dateien (inkl. data-gate.md)
ls ~/.claude/skills/code-guardian/tools/        # → 7 Skripte (inkl. detect-deploy-artifacts.py)
ls ~/.claude/skills/llm-council/SKILL.md        # → vorhanden
grep -m1 "name: senior-dev" ~/.claude/skills/senior-dev/SKILL.md         # → Treffer
ls -l ~/.claude/hooks/deploy-gate-check.sh      # → -rwxr-xr-x

# Hook-Funktionstest DECISION GATE (muss eine deny-JSON-Zeile ausgeben):
echo '{"tool_input":{"questions":[{"question":"A oder B?","options":[{"label":"A"},{"label":"B"}]}]}}' \
  | ~/.claude/hooks/decision-gate-check.sh

# Hook-Funktionstest DEPLOY GATE (muss eine deny-JSON-Zeile ausgeben):
echo '{"tool_input":{"command":"rsync -avz ./ user@server.de:/var/www/html/"}}' \
  | ~/.claude/hooks/deploy-gate-check.sh
```

Der Installer prüft die v16-Marker selbst und meldet
`v16 markers + senior-dev anchor + symbol-loss + dead-code + decision + generalization + deploy + data gates detected`.

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

Stand: 19.07.2026 (v16.1) · Fragen an Alex
