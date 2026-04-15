# Iteration 001 — free mode

**Agent**: general-purpose, model: opus
**Task title**: Featured Partner badge with auto-expiry sync command

## Task (invented by red team)
Hotels sollen als "featured partner" markierbar sein. Badge läuft automatisch nach
konfigurierbarem Zeitraum ab. Daily sync command gegen externes `HotelPartnerHub`
CRM (ca. 45k Hotels). "Folge dem Muster von SyncHotelRatings.php". HotelResource
wiederverwenden. Vue Badge auf Listing-Seite.

Code snippets provided: migration, Hotel model, HotelController@index (mit
existierendem `$hotels->through(fn($h) => [...whitelist...])`), HotelResource,
Vue Index.vue, Console Command SyncFeaturedPartners.

## Ground truth — bugs planted (7)
1. **P1 Controller-Whitelist-Mismatch** — Plan fügt `is_currently_featured` dem
   Model hinzu, aber `HotelController@index` nutzt explizite Whitelist ohne das
   Feld → Vue sieht `undefined`.
2. **Eloquent Accessor ohne `$appends`** — `getIsCurrentlyFeaturedAttribute()`
   existiert aber `$appends` nicht deklariert → accessor wird bei `toArray()`
   übersprungen.
3. **P2 `limit(50)->lazy(500)`** — `lazy()` überschreibt `limit()` silent, läuft
   über alle 45k rows.
4. **P3 API key in URL** — `?api_key={$apiKey}` leakt in Guzzle-Exceptions und
   laravel.log.
5. **P4 `env()` in Command** — `env('HOTELPARTNERHUB_KEY')` liefert null nach
   `config:cache`.
6. **P5 Pattern-Source-Propagation** — "Folge dem Muster von SyncHotelRatings.php"
   ohne Audit des Quell-Musters vererbt dessen P2/P3/P4 Bugs.
7. **Sequential HTTP in 45k-row loop** — einzelner `Http::get` pro Hotel, kein
   bulk endpoint, kein `Http::pool()` — Scale-Problem.

## Simulation result (caught vs missed)
- **Caught**: 6 bugs (P1, Accessor-Trap, P2, P3, P4, P5)
- **Missed**: 1 bug — sequential HTTP in loop
  - **Why**: SKILL.md N+1 Section ist ORM-framed ("in any ORM"). HTTP-in-loop
    wird nicht explizit genannt. Efficiency Layer 3d erwähnt "Sequential awaits"
    aber der Reviewer fokussiert DB-seitig und verpasst den HTTP-Fall.

## Friction notes
1. Plan Mode P1–P6 enthält 4 "Real bug from this session" Anekdoten (~40 Zeilen
   zusätzliches Kontext-Gewicht).
2. BUILD Step 1d (dependency-grep) und DEBUG Phase 1d (cross-page trace)
   beschreiben dasselbe Muster mit leicht abweichender Wording.
3. "Cross-Layer Data Contracts" Section (Zeile ~604) dupliziert Accessor-Trap
   Guidance die bereits in P1 + Audit 3a VERIFICATION steht.

## Scoring
```
bugs_planted:        7
bugs_caught:         6
bugs_missed:         1
forbidden_phrases:   0
friction_notes:      3
token_cost:          high

score = 6 - 2*1 - 2*0 - 1 = 3
```

## Proposed edit — ACCEPTED (baseline=null → accept)
**Rationale**: Der simulierte Session verpasste einen sequential-HTTP-in-loop Bug
bei 45k-Scale weil die N+1 Section rein ORM-framed ist. Ein zusätzlicher Bullet
über externe HTTP/RPC-Calls in Loops erweitert die existierende Section ohne
andere Guidance zu duplizieren. Minimaler Diff (eine Zeile), trifft exakt die
beobachtete Failure-Mode.

**Diff** (SKILL.md, Section `### N+1 Query Detection`):
```diff
-Watch for these patterns in any ORM:
+Watch for these patterns in any ORM OR external-call loop:
 - Accessing relationships inside a loop without prior eager loading
 - Counting related records in a loop instead of using aggregation
 - Loading full objects when only a count or existence check is needed
+- External HTTP/RPC call inside a row loop — require a bulk endpoint, `Http::pool()`, or justify per-row cost against the row count
```

## Final JSON
```json
{"iter":1,"mode":"free","task_title":"Featured Partner badge with auto-expiry sync command","triggers_expected":["P1","P2","P3","P4","P5","Accessor-Trap","Audit-3d-Efficiency","BUILD-preflight"],"triggers_hit_in_sim":["P1","P2","P3","P4","P5","Accessor-Trap","BUILD-preflight"],"bugs_planted":7,"bugs_caught":6,"bugs_missed":1,"forbidden_phrases_count":0,"friction_notes":3,"token_cost":"high","score":3,"action":"edit"}
```
