# Generalization Gate trap fixture (v13)

Validates `tools/detect-hardcoded-cases.py` — the example-hardcoding detector.

## Oracle

- `traps/` — **9 files, EVERY file must produce ≥1 FINDING** (exit=1):
  literal-if (php), example-regex (js), switch chain (php), lookup array (py),
  hard date (py), email-if (js), URL check (php), elseif ladder (ts), in_array (php).
- `clean/` — **0 findings** (exit=0): generic classifier (py, the mechanism the
  requirement actually asked for), `config/services.php` (ignored path), a
  `test_*.py` file (ignored), an `INTENTIONAL-SPECIAL-CASE` marker file
  (suppressed, counted as `intentional=`), a DB lookup (no literal), a JSON
  data file (ignored extension).

## Run

```bash
python3 code-guardian/tools/detect-hardcoded-cases.py --root test/hardcoding/traps   # exit=1, all 9 traps
python3 code-guardian/tools/detect-hardcoded-cases.py --root test/hardcoding/clean   # exit=0, findings=0
```

Success criterion (mirrors the v11 fixture discipline): **CRITICAL_FP=0** — no
clean case may ever be flagged; low false positives beat completeness.
