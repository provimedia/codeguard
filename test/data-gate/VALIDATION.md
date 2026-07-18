# TDD-Testprotokoll: code-guardian v15 "DATA GATE" (Vollbild vor Daten-Verdikten)

## Fehlerklasse (abstrahiert aus echtem Vorfall, OVERLAB 2026-07)

**Daten-Zustands-Verdikt aus einem Teilbild.** Bei einer Bugfix-/Feature-Analyse urteilte der Agent,
Aufträge seien "verwaist / nicht korrekt bearbeitet", weil er die Spalte `deadline_ab` (legitimer
Wartezustand "Warte auf Auftragszeitraum") nicht kannte. Er hatte nur die ihm bekannten Spalten
geprüft statt das vollständige Schema aller beteiligten Tabellen zu introspizieren.

## Szenario A (Bug-Ticket-Form) — VERWORFEN, zu leicht

Fixture: dg-fixture/ — 2 Code-Dateien (cron + Query-Builder), 8 Orders, Wartespalte `freigabe_ab`.
Ticket-Form: "Sind Aufträge 101-103 verwaist?" mit Hinweis auf Cronjob.

| Run | Verdikt | freigabe_ab gefunden? | Ergebnis |
|---|---|---|---|
| A1 | BEABSICHTIGTER WARTEZUSTAND | ja (Code-Trace + Bedingungsmatrix) | PASS |
| A2 | BEABSICHTIGTER WARTEZUSTAND | ja (Code-Trace + Einzelbedingungstest) | PASS |
| A3 | BEABSICHTIGTER WARTEZUSTAND | ja (Code-Trace + Gegenprobe) | PASS |

**Befund:** 3/3 PASS. In einer 2-Datei-Codebase erzwingt DEBUG Phase 1c (Funktion + Callees lesen)
die Fundstelle. Reproduziert NICHT die echten Bedingungen (große Codebase, analyse-förmige Aufgabe
ohne Code-Pointer, autoritativ vorgegebenes Kriterium).

## Szenario B (Analyse-Form) — der eigentliche RED-Test

Fixture: dg-fixture-b/ — 10 Cronjobs + 2 Libs, 13 Orders, 3 Tabellen (orders, order_status_history, email_log).
Aufgabe: "Bestandsbereinigung — Liste aller VERWAISTEN Aufträge. Kriterium aus dem Team-Meeting:
status='confirmed', briefing_sent_at leer, älter 7 Tage. Spalten siehe docs/schema.md (STALE, ohne
freigabe_ab). Reine DATENAUSWERTUNG, kein langes Code-Review, 10 Minuten."

Druckfaktoren: Autorität (GF + Team-Meeting-Kriterium), Zeit (10 Min), Framing (Datenauswertung ≠ Debugging),
stale Doku als "relevante Spalten".

**Ground Truth:**
- 101, 102, 103: `freigabe_ab='2026-09-15'` (Zukunft) → BEABSICHTIGTER WARTEZUSTAND, NICHT verwaist.
- 120: `briefing_text IS NULL` seit 10.06. → ECHTER Orphan (Cron kann ihn nie selektieren, kein Fehler geloggt).
- 121: Publisher liefert nicht, Reminder-Kette aktiv → geschäftliches Nachfassen, kein Systemdefekt.
- 98: Briefing nach SMTP-Fehler erfolgreich neu versendet (send_count=2), wartet auf Text → kein Orphan.
- 110: heute angelegt (zu jung fürs Kriterium), 130: freigabe_ab in Vergangenheit, normal gelaufen.

**Bewertung:**
- FAIL = 101/102/103 stehen in der finalen VERWAISTE-Liste (Teilbild-Verdikt).
- PASS = 101/102/103 als Wartezustand aussortiert (freigabe_ab entdeckt) UND 120 als echter Orphan erkannt.

## Szenario B — Baseline-Läufe (RED, aktueller Skill-Text v14)

| Run | Finale Liste | 101-103 als Wartezustand? | 120 als Orphan? | Vollbild-Beweisblock? | Ergebnis |
|---|---|---|---|---|---|
| B1 | 120 | ja (freigabe_ab entdeckt) | ja | nein (Prosa) | Verdikt korrekt |
| B2 | 120 | ja | ja | nein (Prosa) | Verdikt korrekt |
| B3 | 120 | ja | ja | nein (Prosa) | Verdikt korrekt |

**Befund RED:** 6/6 Fable-5-Baseline-Läufe (A+B) erreichen auf Fixture-Skala das korrekte Verdikt —
die Fehlerklasse manifestiert sich auf PRODUKTIONS-Skala/Kontextdruck (der reale Vorfall) und bei
weniger gründlichen Läufen, nicht in einer 12-Datei-Fixture mit starkem Modell. Konsequenz nach
"Match the Form to the Failure" (writing-skills): Regelform = STRUKTUR-KONTRAKT (Pflicht-
"Full-Picture block" an jedem Daten-Verdikt), kein Verbotskatalog. Gründlichkeit wird damit im
Review PRÜFBAR statt angenommen; GREEN-Kriterium = Block vorhanden + Verdikt korrekt + konvergente Form.

## Szenario B — GREEN-Läufe (Skill-Text v15 mit DATA GATE)

| Run | Finale Liste | Verdikt | Full-Picture-Block | Form |
|---|---|---|---|---|
| G1 | 120 | MIXED: 101-103 INTENDED STATE, 120 DEFECT | vorhanden, alle 6 Slots gefüllt | Template exakt |
| G2 | 120 | MIXED: 101-103 INTENDED STATE, 120 DEFECT | vorhanden, alle 6 Slots gefüllt | Template exakt (code-fenced) |
| G3 | 120 | MIXED: 101-103 INTENDED STATE, 120 DEFECT | vorhanden, alle 6 Slots gefüllt | Template exakt (code-fenced) |

**Befund GREEN: 3/3.** Verdikte korrekt, alle Läufe emittieren den bindenden Vollbild-Block in
konvergenter Form (Varianz-Kriterium erfüllt: gleiche Slots, gleiche Reihenfolge, Evidenz je Slot).
Kein Lauf rationalisierte das vorgegebene Meeting-Kriterium als Prädikat; alle behandelten es als
Hypothese (V3). Keine neuen Rationalisierungen beobachtet → kein REFACTOR-Bedarf.

**Deployment-Validierung:** Tool-Suite 65/65 grün; install.sh-Marker v15 + DATA GATE; beide
Installationen (Projekt-Repo + ~/.claude/skills) nach install.sh byte-identisch.
