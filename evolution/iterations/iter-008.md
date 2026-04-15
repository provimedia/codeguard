# Iteration 008 — free mode (v2, manually rejected)

**Agent**: general-purpose, model: opus
**Task title**: Profile avatar + company logo + bulk import attachments upload

## Task
6 snippets covering three upload flows: user avatar (`storage/app/public/avatars/`),
company logo (`public/logos/` — web-served RCE landing), bulk import attachments
(`storage/app/imports/{id}/`), plus a download endpoint.

## Bugs planted (6)
1. Path traversal via `getClientOriginalName()` → `storeAs()`
2. No `mimes:`/`mimetypes:` allow-list → `.php` uploadable
3. Upload target in `public_path()` → directly web-served → RCE
4. `dirname()/basename()` ordering bug → traversal survives
5. IDOR on download endpoint (`findOrFail($fileId)` without parent scope)
6. No rate limiting on avatar endpoint

## Simulation outcome
- **Caught (1)**: IDOR only
- **Missed (5)**: all file-upload specific bugs (last known gap from iter-5)

## Scoring (diagnostic)
```
planted: 6, caught: 1, missed: 5
forbidden: 0, friction: 2
score = 1 - 2*5 - 0 - 0 = -9
```

## ⚠ PROPOSED EDIT — MANUALLY REJECTED

The subagent proposed a ~40-line new sub-section **"File Upload Sanitization"**
with 3 rules + WRONG/RIGHT code blocks + verification-grep recipes, ALL deeply
Laravel-specific: `storeAs`, `storage_path`, `public_path`, `$request->file`,
`mimes:`, `mimetypes:`, `Str::uuid()`, `->extension()`.

**User directive (mid-iteration)**:
> Für mich ist wichtig das der Skill so optimiert ist das er allgemein für jedes
> Projekt funktioniert, ich brauche keine 1000 Spezialfälle die nie vorkommen, es
> geht im wesentlichen um eine Optimierung.

The proposed edit violates this principle on multiple axes:
- Framework-locked (Laravel Blade + Request API + Storage facade)
- 40+ lines for one Laravel bug family
- Would not apply to any Rails / Django / Node / Go project
- SKILL.md is meant to work across stacks — accumulating per-framework recipes
  makes it longer without making it more broadly useful

**Decision**: reject, noop this iteration. Going forward, iterations should
prefer TIGHTENING / GENERALIZING / REMOVING over ADDING.

## Gate decision: **NOOP** (manual rejection on generality grounds)
consecutive_noops: 0 → 1

## Note on prior iters 1–7 under new directive
- iter-1 (N+1 external HTTP): principle is general, examples (`Http::pool()`) are Laravel — could be tightened
- iter-2/3 (P3 webhook + token): principles general, examples Laravel-flavored
- iter-7 (Cache / TOCTOU / Queue Idempotency): principles general and VALUABLE,
  but examples (`Cache::remember`, `PromoCode::`, `ShouldQueue`, `Mail::to`) are
  Laravel-specific. Should be retrofitted to framework-agnostic wording in a
  future iteration.

## Final JSON
```json
{"iter":8,"mode":"free","score":-9,"baseline":11,"action":"noop","reason":"proposed_edit Laravel-specific, rejected per user directive (generality principle)","bugs_planted":6,"bugs_caught":1,"bugs_missed":5,"friction_notes":2,"token_cost":"medium"}
```
