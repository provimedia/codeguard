# CRM Datenbank — Kern-Schema (Stand: 2025-11)

> Kurzreferenz der für die Auftragsbearbeitung relevanten Spalten.

## Tabelle `orders`

| Spalte | Typ | Bedeutung |
|---|---|---|
| id | INTEGER | PK |
| order_number | TEXT | Format `<kunde>_<lfd>` |
| customer_id | INTEGER | FK → customers.id |
| status | TEXT | `new` → `confirmed` → `online` → `done` (Storno: `cancelled`) |
| status_changed_at | TEXT | letzter Statuswechsel |
| created_at | TEXT | Anlage |
| briefing_sent_at | TEXT | Zeitpunkt Briefing-Versand an Publisher (NULL = noch nicht versendet) |
| briefing_send_count | INTEGER | Anzahl Versände |
| text_delivered_at | TEXT | Text vom Publisher geliefert |
| published_at | TEXT | Link live |
| invoiced_at | TEXT | Rechnung gestellt |
| deleted_at | TEXT | Soft-Delete |

## Tabelle `customers`

| Spalte | Typ | Bedeutung |
|---|---|---|
| id | INTEGER | PK |
| firma | TEXT | Firmenname |
| email | TEXT | Rechnungs-/Kontakt-Mail |

## Verarbeitungs-Pipeline

1. Auftrag angelegt (`new`) → bestätigt (`confirmed`)
2. Cronjob versendet Briefing an Publisher (`briefing_sent_at` gesetzt)
3. Publisher liefert Text (`text_delivered_at`)
4. Link geht live (`published_at`, Status `online`)
