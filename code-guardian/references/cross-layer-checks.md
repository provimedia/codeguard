# Cross-Layer Checks — Full Reflex Catalog

> Loaded on demand from SKILL.md (see "Reference Files"). Every reflex below was distilled from a real shipped bug ("Born from"). Apply the ones whose trigger matches the diff; each requires command-output proof, not code reading.

These catch bugs that live BETWEEN components — not inside any single file, but in the handshake between them.

### Cross-Layer Data Contracts
When one layer produces data and another layer consumes it, verify both sides agree.

**Producer → Consumer mismatches** (all silent — no error, just missing data):
- Key rename mid-pipeline: producer emits `status`, consumer reads `success` → null
- Computed/derived property not opted into the serializer (accessor, virtual attribute, getter, lazy field) → absent from payload, consumer reads undefined
- Hardcoded path under a subdirectory / reverse-proxy install bypasses the base-URL helper → resolves to wrong base, 404 only in the non-root deployment
- 64-bit integer ID (BIGINT / int64) emitted as a JSON number > 2^53 → any float64-backed parser (JS, most JSON libs) rounds to nearest double and adjacent IDs collide silently → serialize large integers as strings at the response boundary

**How to check (READING is not enough):**
1. Trace the data from where it's CREATED to where it's READ.
2. **Dump the actual serialized payload** — hit the endpoint, parse the response, prove every consumed key is non-null on the bug path.
3. Verify key names AND shape (array vs object, nested depth, null possibility) match at every hop.

This is the #1 source of silent bugs. Structural-match audits ("producer returns X, consumer reads X") pass while the runtime payload is `{X: undefined}` — dump, don't read.

### Return Type Completeness
When a function has conditional branches (if/else, early returns, error paths), verify ALL branches return a compatible type.

Common traps:
- Main path returns ResponseObject, error path returns redirect() → different types
- Happy path returns {data: [...]}, edge case returns null → consumer crashes
- Normal flow returns rendered page, self-redirect returns different response type

### Interface Boundary Verification
When new code calls existing services/functions, read the ACTUAL signature — verify parameter count, types, order, return type, and optional defaults all match what you assume.

### ORM/Model Verification
When code references DB fields, verify against BOTH the Model AND the live DB:
- Are mass-assigned fields in the whitelist ($fillable, attr_accessible, etc.)?
- Are type casts correct? Wrong cast = wrong type at runtime.
- Do relationship definitions match the actual FK columns in the DB?
- Is the table name explicitly set if the model name doesn't follow convention?

### Single-Use Resource Consumption (token / coupon / one-time action replay)
Whenever a DB row represents a single-use resource (password-reset token, email-verify token, magic-login code, one-time coupon, invite link, idempotency key, consumed webhook), the consumption MUST be enforced by an **atomic conditional UPDATE** whose `rowCount()` is checked BEFORE any follow-on side effect:

```sql
UPDATE t SET consumed_at = NOW(6)
 WHERE id = :id AND consumed_at IS NULL AND expires_at > NOW(6)
```
Then in code: only if `$stmt->rowCount() === 1` proceed to change the password / grant access / apply the coupon. Otherwise reject as `already_used`.

**Anti-pattern**: `SELECT consumed_at IS NULL → BEGIN → UPDATE users ... → UPDATE resets SET consumed_at = NOW() WHERE id = :id → COMMIT`. Two concurrent replays both pass the SELECT gate, both enter their own transaction, both UPDATE the user row, second silently overwrites first. Wrapping in a transaction does NOT fix it — transactions serialize writes to the same row but do NOT turn a prior read into a lock. `SELECT ... FOR UPDATE` works ONLY if the consumed-flag is re-checked AFTER the lock; the conditional-UPDATE + rowCount gate is simpler and less error-prone.

**Audit reflex**: for every diff that touches a row with `consumed_at` / `used_at` / `redeemed_at` / `verified_at` / `processed_at` / `is_consumed`, grep the diff for `SELECT` followed by `UPDATE` on the same row — if the UPDATE lacks `WHERE ... AND <flag> IS NULL` OR the code doesn't check `rowCount() === 1` before the side effect, FAIL. Verified-by: a concurrent-replay script (`seq 1 20 | xargs -P20 -I{} curl ...`) should show exactly 1 success and 19 `already_used`.

**Timestamp sub-reflex**: expiry / window checks MUST be evaluated in SQL (`WHERE expires_at > NOW(6)`) or via typed `DateTimeImmutable` comparison. Never compare two datetime strings lexicographically — MySQL may return `DATETIME(6)` with or without fractional seconds depending on how the row was inserted, and lex-compare of 19-char vs 26-char strings silently reorders around second boundaries. Same reflex INBOUND: caller-supplied datetime params (body / query / cursor) MUST be strict-parsed with `DateTimeImmutable::createFromFormat('!Y-m-d H:i:s', $in, $tz)` and rejected on failure BEFORE SQL bind — raw string bind against `DATETIME(6)` silently coerces malformed input to NULL (empty result, no error), drops TZ suffixes, and triggers implicit `CONVERT` on the indexed column.

### Auth Enforcement Parity Across Entry Points
When a service/domain method is invoked from MORE THAN ONE entry point — web route, CLI command, queue/background worker, scheduled task, admin panel, internal API, webhook handler — the authorization gate MUST be equivalent at every entry point, OR the gate must live INSIDE the service and not at the edge.

Auth-at-the-edge (middleware/policy on the route) is safe ONLY while the service has exactly one caller. The moment a second entry point appears, the route-level gate is bypassed by design — middleware does not run for background workers or CLI invocations.

**Audit reflex** — for every service method touched in the diff, run the consumer grep from BUILD Step 1d and for EACH caller answer out loud:

1. **What auth check guards this entry point?** Name the middleware / policy / gate / inline check.
2. **Is the check equivalent to every OTHER entry point's check?** A route gated by a policy (checks verified / not-banned / has-quota) is NOT equivalent to an admin route checking only an admin flag, and NOT equivalent to a CLI or queue caller with no gate.
3. **If the gates differ, does the difference match intent?** An admin override that explicitly bypasses one invariant is acceptable IF documented AND the non-admin paths still enforce the others.

**The fix is almost always the same**: push the authorization check INTO the service (it throws on failure regardless of caller). Edge-auth then becomes defense-in-depth, not the only line.

### Session Lifecycle at Auth Boundaries (fixation, privilege upgrade, cookie drift)
Authentication is an IDENTITY TRANSITION: the caller arrives as anonymous (or some other identity) and leaves as an authenticated principal. Every identity transition MUST rotate the session identifier AND re-assert the session cookie attributes — or the pre-transition session ID remains valid post-transition and whoever planted it is now logged in as the victim.

Distinct from Auth Enforcement Parity (who-can-call a service across entry points): this reflex covers the identity-rebinding STEP itself.

**Three failure modes:**

1. **Session fixation** — login succeeds, principal is written into the existing session (`$_SESSION['user_id'] = ...`) WITHOUT first rotating the session ID. If the runtime accepts attacker-supplied session IDs (PHP with `session.use_strict_mode = 0`, hand-rolled cookie stores, any session system that mints on first touch without a server-side allowlist), an attacker who planted a session cookie on the victim now holds a valid authenticated session. Fix: rotate the session ID immediately after credentials verify and BEFORE writing the principal (e.g. PHP `session_regenerate_id(true)`).
2. **Privilege upgrade without rotation** — same bug class at a different boundary: a logged-in user becomes admin / enters sudo / completes 2FA step-up. If the session ID is not rotated at the upgrade, a pre-upgrade token captured at a lower trust level now grants the higher trust level. Rotate on every trust-level change, not just at initial login.
3. **Cookie attribute drift** — setting cookie params (remember-me lifetime, `Secure`, `HttpOnly`, `SameSite`, `Domain`) AFTER the session has already started silently does NOT apply to the already-issued cookie for the current request. Correct order: set params → rotate session ID → write principal → send response. **Attribute-compatibility rule**: `SameSite=None` without `Secure` is rejected by every modern browser (Chrome/Edge/Firefox drop the Set-Cookie entirely, no error surfaced server-side) — the pair is load-bearing, not independent. **CORS credentialed-request rule**: `Access-Control-Allow-Origin: *` combined with `Access-Control-Allow-Credentials: true` is invalid per the Fetch standard and browsers silently reject the response; credentialed cross-origin requests require reflecting the exact Origin against an allowlist AND `Vary: Origin`.

**Audit reflex** — for every assignment into session state that follows a successful credential / MFA / role check in the diff:
1. **Is the session ID rotated between credential-verify and principal-write?** Name the rotation call and its `delete_old_session` argument. Missing → BLOCKED.
2. **Does the runtime reject unknown session IDs?** (`session.use_strict_mode` or equivalent.) If off, rotation is the ONLY defence — no excuses.
3. **If cookie params changed, did the change happen BEFORE the rotation call?** Post-rotation param changes apply only to the NEXT session.
4. **Is the OLD session server-side storage actually destroyed?** `session_regenerate_id(false)` leaves the old session file readable by whoever has the old ID — pass `true`.

**Verification (command output):**
```bash
# 1. Pre-login session cookie:
curl -c jar -b jar -s -o /dev/null -D - https://app/login | grep -i '^set-cookie'
# 2. POST credentials re-using the same cookie jar:
curl -c jar -b jar -s -o /dev/null -D - -d 'email=a&password=b' https://app/login | grep -i '^set-cookie'
# 3. The Set-Cookie session-ID value from step 2 MUST differ from step 1.
#    Same value → no rotation → session fixation present.
```

### HTTP Response Cacheability for Authenticated Pages (shared-proxy cross-user disclosure)
Any HTTP response whose body depends on caller identity (session cookie, bearer token, API key) is a **per-user** response. Most runtimes emit NO `Cache-Control` by default, and RFC 7234 lets shared caches (reverse proxies, CDNs, corporate forward-proxies, browser bfcache) apply a heuristic freshness lifetime to any 200 OK lacking explicit directives. The cache key is typically `(method, host, path)` — the session cookie is NOT part of the key unless `Vary: Cookie` is present. Result: user A's account statement is stored under `/statement.php` and served verbatim to user B hitting the same URL within the heuristic TTL.

Distinct from "sensitive fields in responses" (WHAT is in the body): this reflex covers WHO ELSE can receive the same body via cache replay.

**Required headers on every authenticated response** (sent BEFORE any body output):
```
Cache-Control: private, no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
Vary: Cookie
```
`private` alone is insufficient — a misconfigured proxy that ignores `private` still honors `no-store`. `Vary: Cookie` is the belt to `no-store`'s braces.

**Audit reflex** — for every route/page/endpoint in the diff that reads session state or returns user-scoped data:
1. **What `Cache-Control` does the response emit?** Default / absent → BLOCKED.
2. **Is `Vary: Cookie` (or `Vary: Authorization` for token auth) set?** Absent → BLOCKED.
3. **Auth-failure redirects** (302s) are cacheable too — same headers on the redirect response.
4. **Browser bfcache**: on logout, does the sensitive page still render from bfcache? `no-store` is the only directive that reliably evicts bfcache.
5. **Defense-in-depth headers** when the body reflects any user-controlled content (XSS sink present or possible): `Content-Security-Policy` (strict `default-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'`, no `unsafe-inline`), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` (or `same-origin`), `Permissions-Policy` locking down unused features. Absent → BLOCKED — escaping at the sink is the first line; CSP is the second and they are NOT interchangeable.

**Verification (command output):**
```bash
curl -b jar -s -o /dev/null -D - https://app/statement | grep -iE '^(cache-control|pragma|expires|vary):'
# Must include: Cache-Control: private, no-store... AND Vary: Cookie. Absent → FAIL.
```

### Error-Path Log Content Hygiene (PII / secrets in logs)
Logs are a secondary data store — whatever lands in them inherits the weakest access control on ANY surface the log reaches (file permissions, backups, log-aggregator retention, SaaS vendor access, support screen-shares). An error-path logger serializing opaque blobs is a secret-leak with a timer. Distinct from P3 (secrets in URLs) and from "sensitive fields in responses" (body content): this covers the LOG sink.

**Forbidden log payloads** — never serialize wholesale into log lines:

| Blob                              | Why it leaks                                                      |
|-----------------------------------|-------------------------------------------------------------------|
| `$_REQUEST` / `$_POST` / `$_GET`  | Arbitrary caller fields: passwords, card numbers, reset tokens    |
| `$_SERVER` / `getallheaders()`    | `Authorization`, `Cookie`, `X-Api-Key`, any custom auth header    |
| `$_ENV` / `getenv()` dump         | Every boot-time secret: DB password, webhook signing key, etc.    |
| Full row from `SELECT *`          | `password_hash`, `api_token_hash`, MFA secret, PII columns        |
| Raw request body                  | On PII/PAN/credential endpoints, the body IS the secret           |
| Stack trace with local variables  | Many runtimes bind SQL params and locals in the trace             |

**Audit reflex** — for every log/write call in the diff (error handler, `catch` block, `error_log`, `file_put_contents` to a log path, SIEM hook), answer three questions:

1. **Allowlist or blob?** Payload must be an explicit allowlist of named, non-secret fields (`['user_id' => $id, 'event_id' => $eventId, 'error_class' => get_class($e)]`), never an opaque blob. Blob → BLOCKED.
2. **Can an UNAUTHENTICATED caller reach this log line?** Pre-auth error paths (bad signature, bad CSRF, bad nonce) let an attacker deliberately trip the path with chosen content — log injection as a reflection primitive.
3. **Does the row fetched for the log contain columns the logger doesn't need?** `SELECT *` feeding an exception path = latent password_hash leak. Project columns at the query.

Also: append-only log writes without an exclusive lock interleave under concurrency and corrupt downstream parsers — use a logger library that locks per write.

### HTTP Header-Value Injection (CRLF + quoted-string breakout)
Any user-controlled string flowing into a response header value is a header-injection sink — even when the runtime claims to reject CRLF. Three ways past the default defence:

1. **Quoted-string breakout**: `Content-Disposition`, `Link`, `WWW-Authenticate` use quoted sub-parameters (`filename="..."`, `rel="..."`). A raw `"` closes the string and lets the attacker inject extra params (`; filename*=UTF-8''evil.html`) — the CRLF filter does NOT filter `"`.
2. **Bare `\r` / `\x00`**: some runtimes and FastCGI bridges block the `\r\n` pair but pass a lone `\r` or NUL byte; downstream proxies may still split on them.
3. **Non-ASCII in ASCII-only fields**: RFC 7230 requires header values to be VCHAR+SP+HTAB. Non-ASCII in `Content-Disposition filename=` without the RFC 5987 `filename*=UTF-8''` encoded form is silently mangled by proxies → cross-browser filename inconsistency that can mask extension-sniffing attacks.

Distinct from XSS (HTML body escaping) and P3 (secrets in URLs): this covers data flowing into `header()` / `setcookie()` / `Location:` / template header pushes.

**Audit reflex** — for every `header(` / `setcookie(` / equivalent in the diff, trace the value to its source and answer:
1. **Is any part user-controlled?** DB columns count if ANY user endpoint ever writes them (grep the write path).
2. **Strictly filtered to the header's grammar?** For `filename=`: ASCII printable minus `"` and `\`, non-ASCII via `filename*=UTF-8''` percent-encoding. For `Location:`: a URL allowlist, not just a CRLF strip. For `Set-Cookie` value: token grammar only.
3. **Validation at WRITE time or READ time?** Write-time reject (at rename/upload) is correct; read-time filtering is defence-in-depth. "We wrote it ourselves" is wrong if ANY path lets a user shape the column.

Verify: `curl -D -` on the endpoint after injecting a quote-breakout payload at write time; response MUST contain exactly one `Content-Disposition` parameter with no raw `"`, `\r`, `\n`, `\x00`, or non-ASCII outside `filename*=`.

### HTTP Verb Safety for State-Changing Requests (CSRF-on-GET)
RFC 7231 marks GET/HEAD as **safe** and every mainstream CSRF middleware exempts them from token checks. A `GET` route that mutates state (INSERT/UPDATE/DELETE, mail, counter, external POST) is therefore a cross-site write primitive: `<img src="https://app/action">` fires it with the victim's cookie (zero-click, no JS). Link prefetchers, email-link scanners, and IM link previews also pre-fetch every URL in reach — tripping state-changing GETs before the user sees the message. Distinct from Session Lifecycle, Open Redirect, Header-Value Injection, and Cacheability: this covers the VERB vs SIDE-EFFECT mismatch.

**Audit reflex** — for every route declaration in the diff:
1. **Does the handler mutate persistent state or call a side-effecting external API?** Grep the handler body for `UPDATE` / `INSERT` / `DELETE` / `save` / `update` / `delete` / mail send / queue dispatch / external POST. Any match → the route MUST be POST/PUT/PATCH/DELETE, never GET or HEAD.
2. **Is the verb actually enforced?** A route reachable via a "match any method" / "match get+post" form inherits the GET exemption. Enumerate the registered verbs with the router's introspection command — do NOT read the route file.

**Not a valid defence**: requiring authentication. The victim IS authenticated — that's the whole point of CSRF. Ownership checks also do NOT mitigate: the attacker targets the victim's own row via the victim's own session.

**Valid remediations**: change the verb to POST and require a CSRF token; for email "one-click unsubscribe" RFC 8058 supports `List-Unsubscribe-Post` directly. OR bind the action to a signed, single-use, time-limited token in the URL itself (HMAC of `user_id + action + expiry`, consumed via the Single-Use Resource Consumption reflex; note this trades CSRF risk for URL-leakage risk — P3 applies).

### Frontend Reactivity Traps
These cause bugs that no linter catches:
- **Destructured reactive state**: Extracting values from reactive objects into plain variables loses reactivity. Always use computed/derived state.
- **Non-reactive async data**: Data fetched via polling or async calls that updates UI must be stored in reactive containers.
- **Stale closures**: Event handlers or watchers that capture a value at creation time instead of reading current state.

### N+1 Query Detection
Watch for these patterns in any ORM OR external-call loop:
- Accessing relationships inside a loop without prior eager loading
- Counting related records in a loop instead of using aggregation
- Loading full objects when only a count or existence check is needed
- External HTTP/RPC call inside a row loop — require a bulk endpoint, a parallel-request primitive (concurrent fan-out), or justify per-row cost against the row count

### Composite Index Column-Order (leading-column rule)
"Column X appears in an index" is NOT the same as "a query on X can use that index". A composite index `(A, B, C)` is a B-tree keyed on A first, then B within each A, then C within each (A,B). The engine can only seek the tree for predicates that include the LEADING column — `WHERE A = ?`, `WHERE A = ? AND B = ?`, `WHERE A = ? AND B > ?`. A bare `WHERE B = ?` or `WHERE C = ?` cannot seek and degrades to a full scan. (Skip-scan exists in some engines but is narrow and planner-dependent — never assume it.)

Distinct from "missing index": the index exists, the queried column appears in it, a schema-reading audit ticks the box, and the query still full-scans at 10M+ rows.

**Audit reflex** — for every `WHERE col = ?` / `WHERE col IN (...)` / `ORDER BY col` / `GROUP BY col` in the diff, do NOT stop at "col is listed in some index". Answer two questions out loud:

1. **Is `col` the LEADING key_part of an index, OR does the same query constrain every earlier key_part to an equality?** If neither, no index is usable — name the leading-matching index, or add one.
2. **Range-before-equality trap.** An index `(created_at, user_id)` used for `WHERE user_id = ? AND created_at > ?` can only seek the range on `created_at`; the later equality becomes a filter, not a seek. Put equality columns FIRST and range columns LAST.

**Verification (command output, not schema reading):**
```sql
EXPLAIN SELECT COUNT(*) FROM <t> WHERE <col> = ?;
-- `key`  column: must name an index whose FIRST key_part is <col> (or earlier key_parts all equality-constrained by this query).
-- `type` column: must be ref / eq_ref / range / const — NOT `ALL` and NOT `index`.
-- `rows` column: bounded (small multiple of result set), NOT ≈ table row count.
```

**Failure signature**: `key: idx_user_status_created`, `type: ALL`, `rows: 17834221` on `WHERE status = ?` — the planner considered the composite and declined it because `user_id` is leading and unconstrained. Schema reading would have said "status is in an index"; EXPLAIN proves it isn't usable.

### Implicit Coercion Defeating Indexes (type & collation mismatch)
"The column is indexed" is NOT the same as "a query comparing this column can use the index". If the planner must implicitly convert EITHER side of a comparison to match the OTHER side's type or collation, the index on the converted side becomes unusable — the engine wraps it in an implicit `CONVERT(col USING ...)` or `CAST(col AS ...)` and that expression is not sargable. Schema-reading audits tick the box ("`idx_x` exists"); `EXPLAIN` shows `type: ALL` at production row counts.

Distinct from column-order: here the index IS the leading key_part and there's no range-before-equality problem — the coercion alone kills the seek.

**Three common sources:**
1. **Type mismatch**: `WHERE bigint_col = '42'` (string literal against BIGINT) or `WHERE varchar_col = 42` (int literal against VARCHAR). Always bind parameters with the correct type; never interpolate a numeric ID as a string.
2. **Collation mismatch on JOIN**: two tables with different column collations (common after a partial utf8mb4 migration — one table still `utf8_general_ci`). `JOIN ON a.col = b.col` forces a per-row `CONVERT(... USING ...)` on one side → full scan even though both columns are individually indexed.
3. **Charset mismatch on literal/connection**: connection charset ≠ column charset forces conversion on every comparison.

**Audit reflex** — for every `WHERE col = ?`, `JOIN ON a.x = b.y`, or `IN (...)` in the diff on a string column:
1. **Does the bound/literal type EXACTLY match the column type?**
2. **For JOINs on string columns: do BOTH sides share charset AND collation?** Check `information_schema.COLUMNS.CHARACTER_SET_NAME` and `COLLATION_NAME` for both columns — column-level settings override the table default.

**Verification (command output):**
```sql
EXPLAIN <query>;
-- key / type / rows must indicate a real seek, AND Extra must NOT mention CONVERT/CAST wrapping an indexed column.

SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE() AND (TABLE_NAME, COLUMN_NAME) IN (('t1','col'), ('t2','col'));
-- Both rows MUST match on CHARACTER_SET_NAME AND COLLATION_NAME.
```

### Client-Connection Charset Drift (READ-path data corruption, not index cost)
Implicit Coercion above covers charset mismatch as an INDEX-usability problem. The same missing DSN parameter also CORRUPTS read-path DATA silently — and looks nothing like the index case, so the index reflex doesn't trip. Every DB driver negotiates a client-side charset for results delivery; if the DSN (`mysql:host=...;dbname=...;charset=utf8mb4`) or equivalent is missing, the server falls back to `character_set_results` from its config — on legacy/distro defaults that's often `latin1`. `utf8mb4` columns are then TRANSCODED on delivery: emoji, CJK, curly quotes, en/em dash become `?` or invalid-UTF-8 byte sequences.

**Three silent failure modes riding one DSN bug:**
1. **`json_encode` returns `false`** (JSON_ERROR_UTF8) on non-UTF-8 bytes; unchecked, `echo json_encode($rows)` emits literal `"false"` at HTTP 200 with no log.
2. **Silent data loss on round-trip** — read transcodes to `?`, write stores `?`, original is gone with no error.
3. **Index lookups by string value miss rows** — `WHERE name = :emoji` binds the transcoded `?` and matches zero rows; looks like "user not found", not a charset bug.

**Audit reflex** — for every DB driver connect in the diff:
1. Is the client charset named explicitly in the DSN or connect options? Absent → BLOCKED. `SET NAMES` via init-command is belt-and-braces, not a substitute (it runs after handshake).
2. Does the named charset match the storage charset of every column the connection reads? Use the `information_schema.COLUMNS` query above — `utf8mb4` columns with a 3-byte client silently degrade supplementary-plane codepoints.
3. Response `Content-Type` carries `charset=utf-8`? A JSON endpoint without it is sniffed wrong by legacy middleboxes; pair the DSN check with the outbound header check.
4. Is the serializer return value checked? `json_encode` returning `false` without a log entry is how `HTTP 200 body="false"` reaches production.

**Verify**: `SHOW SESSION VARIABLES LIKE 'character_set_%'` — all three of `client` / `connection` / `results` must be `utf8mb4`. Then `curl -sD -` the endpoint with a row containing an emoji; body must be valid JSON starting with `[` or `{`, and `Content-Type` must contain `charset=utf-8`.

### Deep-Offset Pagination (LIMIT/OFFSET at depth)
`LIMIT N OFFSET M` is **O(N+M)**, NOT O(N). The engine walks M+N rows through the chosen index, discards the first M, returns the tail. Under a narrowing predicate (`WHERE user_id = ?` → ~10k rows) the cost is invisible. On a large unpartitioned table with no filter it degrades catastrophically — page 1000 of a 50/page feed touches 50,050 index rows; page 100,000 touches 5M. Each slow request also pins a DB connection, so deep-offset is both latency and pool-exhaustion.

**Audit reflex** — for every `LIMIT ? OFFSET ?` in the diff, answer three questions out loud:

1. **What narrows the scan BEFORE the OFFSET?** Name the WHERE predicate and prove an index covers it AND bounds the filtered set to a small multiple of page size. No narrowing WHERE → unbounded.
2. **Is the filtered set itself bounded?** If unbounded (global firehose, audit log, telemetry, append-only table without retention), OFFSET is NOT acceptable — use keyset pagination: `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT N`. Cost stays O(N) regardless of depth. **Tie-breaker is load-bearing, not cosmetic:** a cursor on `created_at` alone is NOT keyset — rows sharing the boundary timestamp are SKIPPED (strict `<`) or DUPLICATED (`<=`), and ms/sub-second precision makes ties routine under fan-out inserts. The `id` (or any unique monotonic column) in the tuple is what makes the ordering total; same applies to `ORDER BY score DESC` / `ORDER BY updated_at DESC` / any non-unique sort — always pair with a unique tiebreaker in BOTH the `ORDER BY` and the `WHERE` tuple.
3. **Is the `page` parameter capped?** `?page=999999999` on a large table forces a walk of the entire index — a one-request DoS. Clamp `page` like you clamp `per_page`.

**Verification** (command output, not code reading):
```sql
EXPLAIN SELECT id FROM <t> WHERE <pred> ORDER BY <col> DESC LIMIT 50 OFFSET 500000;
-- `rows` must NOT be ≈ 500050. If it is, the query is O(offset) and FAILS.
```

**Copy-paste trap**: a safe OFFSET paginator over a narrow predicate is often copy-pasted into a global-firehose variant by dropping the WHERE — identical shape, runtime cost differs by 4+ orders of magnitude. "Follow the existing pagination pattern" is safe ONLY if the new call site keeps the source's narrowing predicate; LIMIT/OFFSET shape alone is never what makes a paginator safe on a large table.

### Cache Invalidation Coverage
Every cached read is a promise that EVERY mutation to the backing data also invalidates the cache entry. A cache without invalidation is a bug with a timer.

**The check (VERIFIED, not asserted):** for every cache key this change introduces or reads, grep EVERY write path to the backing table — request handlers, scheduled tasks, background workers, inline increments, raw SQL, ad-hoc scripts — and prove each one invalidates (or tag-flushes) the same key. Audit reflex: name 0 unguarded mutation paths out loud before the check passes.

Also check the inverse direction: a background process that mutates the DB outside the request cycle must STILL invalidate. Shared cache is global; stale reads do not self-heal.

**Row mutation → list/aggregate cache drift.** Invalidation must reach DERIVED cache entries that EMBED the mutated row without being keyed by it: list pages, feeds, search result pages, leaderboards, `COUNT(*)` rollups, homepage modules, first-page CDN objects. A write to `post:123` that only flushes `cache[post:123]` leaves `cache[posts:list:page1]` holding the stale row 123 for the full TTL — and list endpoints are typically the higher-traffic path, so the stale-read surface is strictly LARGER than the row-keyed one. Same trap for aggregates: updating one `orders` row flushes `cache[order:987]` but not `cache[dashboard:revenue:today]`. Audit reflex: for every cache WRITE in the diff, ask "what OTHER cache keys encode rows from this table?" — grep the cache-get call sites for every key prefix reading the same table and prove each is tag-flushed, versioned (read key includes a generation counter bumped on every write), OR has a TTL short enough to bound the inconsistency. "I flushed the row key" is not enough.

### Concurrency / TOCTOU on Counters and Quotas
Any `check-then-act` pattern on a counter (`uses_left`, `stock`, `seats_remaining`, `credits`) is a race unless the check and the mutation happen in ONE atomic step — a conditional `UPDATE` with affected-row check, a row-level lock inside a transaction (`SELECT ... FOR UPDATE`), or an equivalent CAS primitive. Reading from a cache and then decrementing is ALWAYS wrong: the cache value is already stale relative to concurrent writers.

```sql
-- WRONG: read-then-write leaks a race window
SELECT uses_left FROM promo WHERE id = ?;        -- both concurrent requests see 1
UPDATE promo SET uses_left = 0 WHERE id = ?;      -- both reach here, quota oversubscribed

-- RIGHT: atomic conditional decrement, check affected rows
UPDATE promo SET uses_left = uses_left - 1 WHERE id = ? AND uses_left > 0;
-- PHP then checks PDOStatement::rowCount(); 0 = race lost, reject.
```

Audit reflex: for every counter mutation in the diff, name the atomicity mechanism out loud or reject the change. Same reflex for business-key uniqueness (invoice number, slug, SKU, external reference, tenant-scoped sequence): SELECT-MAX / SELECT-by-key followed by INSERT is a race unless a `UNIQUE` index on the key catches the collision AND the handler catches the duplicate-key error and retries — the SELECT alone proves nothing, both concurrent callers see the same max and both INSERT. Wrapping in a transaction does NOT help: under InnoDB REPEATABLE READ the SELECT is a consistent snapshot and the INSERT has nothing to collide with at the row level.

**`SELECT ... FOR UPDATE` without a transaction is a no-op.** Under autocommit (PDO MySQL default and most driver defaults), each statement is its own transaction — the row lock acquired by `FOR UPDATE` is released the instant the SELECT finishes, BEFORE the follow-up UPDATE runs. The code READS as locked-then-updated but executes as unlocked. Verification: grep every `FOR UPDATE` in the diff and prove a `BEGIN`/`START TRANSACTION` opens before it AND a `COMMIT` closes after the UPDATE. Missing either → the lock is decorative. Same failure applies to advisory locks (`GET_LOCK`) released at session end when the connection is returned to a pool mid-request.

**The inverse: a transaction without `FOR UPDATE` does NOT lock the rows it reads.** Under InnoDB REPEATABLE READ (default), a bare `SELECT` inside `BEGIN`/`COMMIT` is a *consistent snapshot read* — concurrent writers are invisible. Two callers can both read the same starting value, both compute `new = old - amount` from the same basis, and both UPDATE; the second commit is a lost update and any predicate checked against the snapshot (`if (new < limit) throw`) is also defeated. Distinct from counter TOCTOU above — this is multiple real rows inside an explicit transaction where the reviewer sees `BEGIN/COMMIT` and wrongly reads it as a lock. Fixes: (a) every row later UPDATEd is read with `SELECT ... FOR UPDATE` in the same transaction, OR (b) the entire mutation is one atomic conditional UPDATE whose WHERE re-asserts the business predicate and whose `rowCount()` is checked. Audit reflex: for every `beginTransaction` in the diff, name each row read-then-updated and prove either option. Verification: a two-connection race script must show the second committer's final value reflecting BOTH mutations.

**Lock ordering for multi-row locks.** Once `FOR UPDATE` is added on N rows, the next latent bug is deadlock from inconsistent acquisition order: `transfer(A,B)` locks A→B, `transfer(B,A)` locks B→A, they meet in the middle. Acquire locks in a globally consistent order — sort IDs ascending and `SELECT ... WHERE id IN (?, ?) ORDER BY id FOR UPDATE`, or issue each `FOR UPDATE` in sorted order. Verify by running the two-connection race with argument order swapped and confirming no `ERROR 1213 Deadlock found`.

### Queue/Task Idempotency (at-least-once by contract)
Virtually every queue/task runner is at-least-once by contract: a worker crash between side-effect and ack re-runs the SAME payload. Every job that sends mail, charges money, increments a counter, writes a file, or calls an external API needs a dedup key checked-and-set in one transaction (e.g. a `UNIQUE` index on `(aggregate_id, operation_id)`) OR must be provably pure. Unguarded side-effects inside a retry-eligible handler = duplicate side-effect on every retry. Audit reflex: for every enqueued job type in the diff, name the idempotency key or justify purity.

**Same reflex for HTTP client retry middleware.** Any outbound client configured to auto-retry on network error / 5xx / timeout is at-least-once on the egress path: a connection reset AFTER the remote accepted the write re-sends the same body on the next attempt and the remote executes it twice. Non-idempotent verbs (POST / PATCH / non-conditional PUT / DELETE) under such middleware MUST send a caller-generated `Idempotency-Key` header (UUIDv4 or hash of `aggregate_id + operation_id`) that the remote dedupes on, OR the retry policy MUST exclude non-idempotent verbs. A `timeout` is NOT a failure signal — the remote may have committed and only the response was lost; retrying on timeout without a dedup key is indistinguishable from retrying on a confirmed error. Audit reflex: for every HTTP client construction in the diff, name the retry policy AND the verbs it applies to; any non-idempotent verb in the retry set without an idempotency-key header → BLOCKED.

### Multi-Step Side-Effect Atomicity (saga / compensation)
A single handler that performs 2+ side-effects — even without concurrency or retries — is a saga. If any step after the first throws and nothing undoes the earlier steps, the system is left in a partial state no error log reconciles: customer charged with no order row, file written with no DB record, email referencing a row that doesn't exist.

Distinct from Queue Idempotency (same payload across retries) and TOCTOU (concurrent races). This is ONE request, sequential steps, partial-commit window between them.

**Audit reflex** — for every handler in the diff with 2+ side-effects (local write, external API, payment, file write, email, queue dispatch, cache mutation), enumerate steps IN ORDER and for each transition answer out loud: **"If step N+1 throws, what automatically undoes step N?"** If the answer is "nothing" for any transition, the handler is broken.

Three acceptable remediations:
1. **Single atomic boundary** — all steps inside ONE DB transaction, zero external side-effects inside. Only works when every step is a local DB write.
2. **External-last ordering** — reorder so the irreversible external step (payment, email, third-party POST) runs AFTER all local writes commit. A throw on the external step still fails the request, but local state stays consistent and retriable. Usually the minimal fix.
3. **Explicit compensation** — wrap each external step in a try/catch whose catch calls the documented undo (refund, reversal, delete). The compensation itself must be idempotent and logged.

**Anti-pattern**: `local decrement → external charge → INSERT order` — if the INSERT throws (unique-index conflict, lock timeout, disk full), the customer is charged with no order row and no refund. Fix: INSERT with `status='pending'` FIRST, then charge, then UPDATE to `status='paid'`. The confirmation email moves AFTER commit.

Verification: for each handler in the diff, mark each step as L (local) or X (external), point at the L step that must come LAST. If the last step is X and irreversible, the audit is BLOCKED until compensation or reordering is added.

### Error-Path Resource Cleanup (finally-block discipline)
Distinct from Multi-Step Side-Effect Atomicity (which covers UNDO ordering between 2+ side-effects). This reflex covers SINGLE resources whose lifetime must span every exit path — happy return, early return, AND every throw reachable from the acquire. A release call that sits on the happy path AFTER the work leaks the resource on every non-happy exit.

PDO's transaction state is the most dangerous case: PHP does NOT auto-rollback on exception, so a throw between `beginTransaction()` and `commit()` leaves the connection with an open transaction. When the connection returns to a pool or long-running worker, the next unrelated query runs inside the stale transaction and either auto-commits partial writes or is silently rolled back by the next `beginTransaction()`.

**Resources that leak on throw unless released in `finally` (or a catch that releases before re-throwing):**

| Resource                          | Release call                                              |
|-----------------------------------|-----------------------------------------------------------|
| PDO transaction                   | `$pdo->rollBack()` in catch, `commit()` only on success   |
| File handle (`fopen`, `tmpfile`)  | `fclose`                                                  |
| Advisory lock (`GET_LOCK`, `flock`) | `RELEASE_LOCK` / `flock(LOCK_UN)`                       |
| Temp file / directory             | `unlink` / `rmdir`                                        |
| Process / pipe (`proc_open`)      | `proc_close` + close stdin/out/err                        |
| External keep-alive connection    | framework-specific close                                  |

**Audit reflex** — for every resource-acquiring call in the diff, draw the function's exit graph (happy return, early return, every throw reachable from the acquire — INCLUDING throws inside library calls that consume the resource) and answer out loud for EACH exit: **"Is the release call reached on this exit?"** The only safe answer on all exits simultaneously is `try { ... } finally { release(); }` wrapping the acquire, OR a catch that releases before re-throwing.

**PDO-transaction canonical fix:**
```php
$pdo->beginTransaction();
try {
    $stmt->execute([...]);
    $pdo->commit();
} catch (\Throwable $e) {
    if ($pdo->inTransaction()) { $pdo->rollBack(); }
    throw $e;
}
```
(The `inTransaction()` guard prevents masking the original exception when an implicit commit — e.g. DDL in MySQL — already closed the transaction.)

### Long-Running Data Backfill Shape (undo log, resumability, replica lag)
One-shot data migrations and backfill commands fail in three ways that no query-correctness reflex catches. Distinct from P2 (READ streaming), from deep-offset pagination (LIMIT/OFFSET shape), and from queue idempotency (retry of the same payload). This reflex is about the OPERATIONAL shape of a handler that mutates N million rows in one run.

**Three failure modes:**

1. **Single-statement UPDATE / undo log blow-up.** `UPDATE t SET col = expr WHERE ...` on 10M rows runs in ONE transaction whether you asked for one or not. InnoDB must keep the entire pre-image in the undo log until commit — `innodb_log_file_size` cannot absorb it and the transaction either aborts or locks the table for minutes. Fix: chunked keyset loop, 1k–5k rows per chunk, each chunk in its own short transaction. Same trap applies to `DELETE ... WHERE` and to `INSERT ... SELECT` over large source sets.
2. **No resumability.** The command runs under `nohup`, the box reboots at row 7M, the operator restarts — and unless progress is persisted (checkpoint table OR the WHERE is naturally idempotent: `WHERE col IS NULL AND id > ?`), the restart re-processes finished rows or starts from zero.
3. **Replica lag / write-rate unbounded.** A tight loop of chunk UPDATEs generates binlog faster than an async replica can apply it. No sleep between chunks, no watch on `Seconds_Behind_Master`, and the replica falls behind SLA invisibly — the primary looks fine, the command finishes on time, and read-replica-backed endpoints serve stale data for hours.

**Audit reflex** — for every long-running mutation command / migration / backfill in the diff, answer out loud:
1. **Chunk size + commit per chunk?** Name the chunk size and prove each chunk commits before the next begins. Single unbounded UPDATE → BLOCKED.
2. **Resume key?** Name the column the WHERE advances on AND prove finished rows are excluded (self-excluding predicate like `WHERE col IS NULL`, or a checkpoint row updated transactionally with the chunk).
3. **Throttle?** Name the sleep-between-chunks AND the replication-lag check (polling `SHOW REPLICA STATUS` or equivalent). Missing → BLOCKED unless the job explicitly documents "primary-only / no replicas / maintenance window covers any lag".

**Verification** (command output, not code reading):
```sql
SHOW PROCESSLIST;               -- backfill MUST appear as many short UPDATEs, not one long one
SHOW ENGINE INNODB STATUS\G    -- 'History list length' must not grow unbounded
SHOW REPLICA STATUS\G          -- Seconds_Behind_Master stays within SLA while the job runs
```

### Input Size & Complexity Limits (DoS budget)
Every untrusted input has three dimensions — **bytes**, **cardinality**, and **complexity** — and ALL three need an explicit cap BEFORE the input reaches code that allocates memory or CPU proportional to it. An uncapped input is a DoS vector with a timer.

Audit reflex — for every new endpoint, webhook, file parser, or upload handler in the diff, name the cap out loud per dimension OR reject the change:

| Dimension           | Vector                                   | Required cap                                                                              |
|---------------------|------------------------------------------|-------------------------------------------------------------------------------------------|
| Raw bytes           | JSON body, multipart upload, webhook     | Web-server body limit + per-route override; reject before parsing                         |
| Array length        | `items: [...]`, bulk-create, ID lists    | `count($arr) <= N` validated BEFORE iteration. **SQL follow-up** when the array becomes an `IN (...)` list: HTTP cap alone is insufficient. Past `eq_range_index_dive_limit` (MySQL default 200) the planner stops per-value dive and may bail to `type: ALL`; each distinct arity is also a new prepared-statement plan-cache entry. EXPLAIN at the CAP value (not at 3), confirm `type: range` and `rows ≈ list size`, and chunk the IN list into fixed-size batches OR join against a temp/VALUES table for a single cached plan shape. |
| Nested depth        | User JSON / YAML / XML                   | Decode with explicit `$depth` (default is often 512, too deep for recursion)              |
| Decompression ratio | gzip / zip upload, `Content-Encoding`    | Stream-decode with max output bytes; reject ratio > ~100x (zip bomb)                      |
| Regex input size    | Server-side text validation              | Length cap BEFORE the regex; reject patterns with nested quantifiers (catastrophic backtracking like `(a+)+$`) |
| Page size           | `?per_page=`, `?limit=`                  | Clamp server-side to a hard max (`min($n, 100)`); NEVER trust client                      |
| Pixel area          | Image upload, thumbnail generation       | Reject width*height > N BEFORE decode; image bombs allocate on decode, not on read        |
| String length       | Any text field persisted to a sized column (`VARCHAR(N)`, `CHAR(N)`, `TINYTEXT`) | PHP-side `mb_strlen($s) <= N` BEFORE the INSERT/UPDATE. Under non-strict sql_mode (`@@sql_mode` does NOT contain `STRICT_TRANS_TABLES`) MySQL SILENTLY truncates oversize strings — statement returns success, `rowCount()==1`, stored value is cut. Verify: `SELECT @@sql_mode` AND `information_schema.COLUMNS.CHARACTER_MAXIMUM_LENGTH`; if non-strict, every bound string must be length-capped in app code. Under utf8mb4, `CHARACTER_MAXIMUM_LENGTH` is in characters but a 4-byte emoji still counts as 1 — use `mb_strlen` with the right encoding. |

**Two silent failure modes:** (1) OOM under load — cap "works" at p50 because the average payload is tiny, p99.9 takes the worker down and the stack trace points at the allocator, not the missing cap. (2) CPU lock — a regex with nested quantifiers on a 50KB string hangs the worker for minutes with no error, no log, just a queue that stops draining.

Verification: for each new input-accepting endpoint in the diff, produce command output showing behavior at 2x the documented cap — expect 413/422, NOT 500 / OOM / hang.

### Timezone / Date-Boundary Sanity
Any code that computes a day-boundary string ("yesterday", "today", "this month") OR compares it to a SQL `DATE(col)` / `CURDATE()` has THREE timezones in play: the PHP process TZ, the DB session TZ, and — if rows are owned by an entity with its own TZ column (tenant, user, venue, subscription) — that entity's TZ. If all three are not explicitly named and aligned, the boundary is wrong at least once per day and twice per DST transition.

Audit reflex — for every `date()`, `strtotime()`, `DateTime`, `DATE(col)`, `CURDATE()`, `NOW()`, or `BETWEEN` over datetimes in the diff:
- Name the TZ of the producer (PHP default vs explicit `new DateTimeZone(...)`).
- Name the TZ of the consumer (DB session `@@time_zone`, or the entity's TZ column).
- Prove they match, OR that the comparison uses `CONVERT_TZ(col, @@session.time_zone, ?)` with the entity TZ bound as a parameter.
- For recurring-event generation or "N days from now" math, verify DST: spring-forward and fall-back make `+1 day` non-equivalent to `+86400 seconds`.
- Store timestamps as UTC (or a single fixed zone) in the DB; do day-grouping in the READER's TZ, not the server's.

Silent failure mode: for a same-TZ developer the code works every day in local testing, and breaks only for users in other zones near midnight — invisible until a support ticket from a far-away customer.

### Open Redirect via Untrusted Return-To URL (`?next=`, `?redirect=`, `?returnTo=`)
Any endpoint that reads a URL/path from caller input and emits `Location:` (meta-refresh or `window.location = ...` count too) is an open-redirect primitive unless the target is allowlisted BEFORE the header is sent. `?next=//evil.com/fake-login` bounces the post-login victim to an attacker clone for credential re-entry. Distinct from P3 and Session Lifecycle: this covers the DESTINATION of a caller-controlled redirect.

**Four payload shapes that bypass naive checks** (all defeated by `parse_url` + host-component equality, NOT by string prefix / regex):

1. **Protocol-relative** `//evil.com/x` — `starts_with('/')` passes; `Location:` resolves off-host.
2. **Backslash normalization** `/\evil.com` — some browsers/proxies rewrite to `//evil.com`, defeats `^/[^/]`.
3. **Empty-scheme with host** `//evil.com/x` — scheme is null but `parse_url(..., PHP_URL_HOST)` is NOT null; assert host null OR equals app host.
4. **Userinfo** `https://app.example.com@evil.com/x` — substring match on app host passes; actual host is `evil.com`.

**Audit reflex** — for every `Location:` / `redirect($var)` / `location.href = ...` in the diff where the target is derived from request input:
1. **Allowlist mechanism**: a fixed enum of route names, or `parse_url` host-component equality check against the app host. Regex on raw string → BLOCKED (fails at least one trap above).
2. **Prove the empty-host path**: demonstrate `parse_url($next, PHP_URL_HOST)` returns `null` on the accepted form AND the attacker host on each trap form.
3. **End-to-end run**: hit the endpoint with each trap payload and follow `Location`; final hop MUST stay on the app host.
4. **Scheme allowlist**: only null (relative) or `http`/`https` with host === app host. Reject `javascript:`, `data:`, `vbscript:`, `file:` — they may be inert in `Location:` but the same helper is often reused for `<a href>` or `<meta refresh>` where they DO execute.

**Companion reflex — Path Traversal via Filesystem READ.** The same normalization-bypass shape applies to any `readfile` / `fopen` / `file_get_contents` / `include` / `require` / `SplFileObject` sink where ANY segment of the resolved path is derived from request input OR from a DB column that ANY write path has ever shaped from user input (the column is user-controlled for audit purposes, even if the write form is long gone). Distinct from upload WRITE-path validation (extension allowlist AND magic-byte sniff via `finfo_file($tmp, FILEINFO_MIME_TYPE)` — NEVER `$_FILES['type']`, which is caller-supplied and forgeable; store under a randomly generated basename OUTSIDE the webroot and serve through a handler that emits `Content-Disposition: attachment` + `X-Content-Type-Options: nosniff`, so a forged `.jpg.php` cannot be executed by the web server): this covers the READ sink. Bypass payloads that defeat naive defences: `../../../etc/passwd` (raw concat), absolute `/etc/passwd` (collapsed `//base`), NUL byte `safe.pdf\x00../../etc/passwd` (suffix-check bypass on legacy bridges), symlink-in-base pointing out-of-base (defeats string-prefix check on INPUT but caught by `realpath()` on RESOLVED path). Required defence: `$base = realpath('/var/app/storage/x')` → `$full = realpath($base . '/' . $input)` → reject unless `$full !== false && str_starts_with($full . DIRECTORY_SEPARATOR, $base . DIRECTORY_SEPARATOR)`. `basename()` alone is NOT sufficient. An ownership check (`row.user_id === session.user_id`) does NOT mitigate — the attacker owns their own row. Verify: plant a row with `pdf_path = '../../../../etc/passwd'`, hit the endpoint, expect 404 with empty body (NOT 200 with `root:x:0:0:`).

**Companion reflex — SSRF via server-side URL fetch.** Any `file_get_contents` / `curl_exec` / `fopen` / HTTP-client call whose URL is derived from caller input is an SSRF primitive — scheme allowlist (`http`/`https` only; reject `file://`, `gopher://`, `phar://`, `dict://`, `ftp://`) AND resolve the host to an IP (`gethostbynamel` / `dns_get_record`) and reject RFC1918, loopback, `169.254.0.0/16` (cloud metadata IMDS), `0.0.0.0/8`, and IPv6 ULA/link-local BEFORE the fetch; disable follow-redirects or re-validate every hop (`CURLOPT_FOLLOWLOCATION=false`), and defeat DNS-rebinding by fetching via the resolved IP with `CURLOPT_RESOLVE` (or re-check the post-resolve IP before read). An ownership check does NOT mitigate — the attacker targets THEIR OWN row with a URL pointing at `http://169.254.169.254/latest/meta-data/iam/security-credentials/`.

### NULL Semantics in Aggregation
Aggregate functions treat NULL inconsistently — the wrong choice silently produces the wrong number with no error. Distinct from the P2 aggregate trap (SCAN COST): this reflex is about CORRECTNESS.

**Four traps:**

1. **`COUNT(col)` vs `COUNT(*)`** — `COUNT(col)` (and `COUNT(DISTINCT col)`) ignore rows where `col IS NULL`. A nullable column is NEVER the right thing to `COUNT(DISTINCT ...)` when the intent is "how many distinct entities" — count the primary key instead: `COUNT(DISTINCT u.id)`.
2. **`SUM` / `AVG` over empty set returns NULL, not 0** — downstream arithmetic silently becomes NULL in loose-typed code and throws in strict-typed code. Wrap with `COALESCE(SUM(col), 0)` at the query boundary.
3. **`AVG(col)` ignores NULL rows in BOTH numerator and denominator** — `AVG(rating)` over 100 rows where 60 are NULL returns the average of 40, not `sum/100`. If intent is "unrated = 0", use `SUM(COALESCE(rating, 0)) / COUNT(*)`.
4. **`LEFT JOIN` silently degrades to `INNER JOIN`** — `LEFT JOIN p ON p.fk = u.id WHERE p.status = 'X'` is INNER in disguise: the WHERE filters out NULL rows the LEFT JOIN produced. Keep LEFT semantics by moving the predicate into the ON clause.

**Audit reflex** — for every `COUNT`/`SUM`/`AVG`/`MIN`/`MAX` in the diff, check if the aggregated column is nullable (use `IS_NULLABLE` from the Pre-Flight schema introspection); if yes, say out loud whether NULL-exclusion is intended. For every LEFT JOIN, grep the WHERE for references to the right-side table — any match means the LEFT has degraded to INNER; confirm intent or move the predicate into ON.

### State-Transition Side-Effect Fan-Out (every writer of a state must fire its side-effects)
*v8 — born from a 20-commit state-machine audit where the most frequent fault was "side-effect wired into one setter, other setters write the same state raw".*

When a status/state value acquires a side-effect — a mail, notification, hook, companion-column write, a spawned workflow/job — OR an existing transition's side-effect changes, then EVERY code path that puts a row into that state MUST fire the side-effect identically. A side-effect wired into ONE setter while other setters write the same state raw is silent drift: the row reaches the state, the side-effect never fires, nothing errors.

This is the single most recurring fault family in state-machine codebases ("N-path consistency drift"). The setters are rarely one function: a CRUD module typically mutates the same status from a single-update handler, an edit handler, a bulk handler, AND ad-hoc raw `UPDATE`s.

**Audit reflex** — for the state value touched in the diff, enumerate ALL writers, not just the one you edited:
```bash
grep -rn "status_id\s*=\s*<V>\|'status_id'\s*=>\s*<V>\|set_status(.*<V>\|->status\s*=\s*<V>" --include=*.php .
grep -rn "update_order_status\|edit_order\|bulk_status_change" --include=*.php .   # named setter paths
```
For EACH writer, confirm out loud it fires the side-effect (or routes through the shared setter that does). A raw `UPDATE ... SET status = <V>` that bypasses the shared setter is the failure signature → BLOCKED until it fires the side-effect too. The side-effect is often "set status AND set a companion flag the consumer also filters on" — see the next reflex.

Born from: a status→approval-mail wired into only 1 of 3 setters (30 orders stuck, no mail ever sent); a `draengel_relevant` flag flipped on for a status while a raw-UPDATE writer of that status never received the workflow-sync hook (latent dunning gap).

### Producer/Consumer State Liveness & Companion-Column Coupling
A row's *actionable* state is often a COMBINATION of columns (`status` + `flag` + `date`). Two silent killers:

1. **Liveness** — at least one consumer (cron query, releaser, worker) must have a WHERE that can SELECT the exact combination the producer writes. A state no consumer's WHERE matches is a permanently-stuck row: it sits forever, no error, until a human notices.
2. **Companion-column coupling** — if any consumer filters on `status AND flag` together, then EVERY producer of that status must set the flag in the SAME operation. Set the status, forget the companion flag → a row the consumer skips.

**Audit reflex** — for every `(status, flag, date)` combination the diff can produce, grep the consumers and read their WHERE clauses:
```bash
grep -rn "WHERE.*status\|status_id\s*=\|->where(" --include=*.php app/cronjobs app/class | grep -i "<flag>\|<status>"
```
- Name the consumer query that advances/picks up the produced state. If none can select it → BLOCKED (stuck-state).
- Prove the producer sets every column the consumer's WHERE requires. Producer sets `status=X`, consumer filters `status=X AND flag=1`, producer never sets `flag=1` → BLOCKED.

Born from: an approval path that set `status=55` but not `publisher_mail_pending=1` while the mail-sender filters `pending=1` → orders approved but never mailed (one due to release the next day); and a `(status=55, date IS NULL, month=X)` state no releaser cron could ever select.

### DB-Driven Dispatch Awareness ("dead code" & reachability need a DATA check, not just grep)
When behavior is dispatched from DB rows — `workflow_steps.template_id`, route/menu tables, a handler/plugin registry, feature-flag rows — a source grep CANNOT prove an artifact is dead, reachable, or safe to remove. The dispatch target lives in data, not in the tree.

**Audit reflex** — before calling a template/handler/branch "dead code", deleting it, or relabeling it:
1. Grep the source for hardcoded references (necessary, not sufficient).
2. Query EVERY dispatch table that can point to it, read-only:
```bash
php -r "require 'config.php'; \$c=new mysqli(\$dbhost,\$dbuser,\$dbpass,\$dbname);
  print_r(\$c->query(\"SELECT * FROM <dispatch_table> WHERE <id_col> = <ID>\")->fetch_all());"
```
"0 grep hits" + an unchecked dispatch table = an unproven claim. If the artifact carries sensitive content (prices, invoice numbers, PII), an unverified "dead" label is a latent data-leak, not just dead weight.

Born from: a mail template called "dead code" and partially edited, still containing customer VK-price + invoice number, while dunning dispatch is driven by `draengel_workflow_steps.email_template_id` — grep could not prove it unreachable.

### DB Trigger-Change Integrity
Triggers are code that lives in the database and is NOT captured by a code deploy. Any `DROP/CREATE TRIGGER` or trigger-body edit gets a four-point check:

1. **Column existence** — every `OLD.col`/`NEW.col` referenced MUST exist in `information_schema.COLUMNS`. A reference to a missing column makes `CREATE TRIGGER` fail outright → BLOCKED.
2. **Coverage intent** — an audit/sync trigger that tracks a SUBSET of the table's columns silently loses the forensic/replication trail for the untracked ones. Audited-column set should equal the table's columns OR the omission must be deliberate and documented.
3. **Error-handler logging** — the trigger's `DECLARE ... HANDLER FOR SQLEXCEPTION` (or equivalent) must LOG the failure (e.g. to a failures table), never silently swallow. A swallowed trigger error is an invisible data-integrity hole.
4. **Live-applied proof** — trigger DDL ships outside the code deploy. Verify it was actually applied:
```sql
SHOW CREATE TRIGGER <name>;   -- body must contain the new column blocks
SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_NAME='<t>' AND COLUMN_NAME IN (<referenced cols>);
```

Born from: an audit trigger recreated to track 4 newly-added pause columns — correct only because the author hand-verified all four points; nothing in the audit forced it.

### Direct-Fetch Endpoint Bootstrap (the endpoint must actually run)
Any new `fetch()`/XHR/AJAX call to a server file must resolve to an endpoint that bootstraps its OWN runtime. A file reached by RELATIVE PATH that relies on `session`, a DB connection, or config being injected by a front-controller/router will 401, 500, or fatal when hit directly — because the front-controller never ran.

**Audit reflex** — for every new fetch/XHR target in the diff:
1. Determine whether the URL goes THROUGH the front controller/router (e.g. `index.php?module=…&ajax=1`) or hits the file DIRECTLY (`./templates/x/handler.php`).
2. If direct, grep the target file for its bootstrap — session start, config require, DB-connection creation. If it relies on injected globals it does not create itself → unreachable as called.

**Verification (command output, NOT code reading, NOT a unit test):** actually hit the endpoint and confirm the intended response:
```bash
curl -s -X POST -b "session=..." "<resolved-url>" --data "<representative payload>"   # or execute the handler standalone
# Must return the intended JSON/HTML — NOT {"success":false,"message":"…not authorized"} / 401 / 500.
```
Tests that only assert "the method exists" / "POST-only is enforced" pass while the endpoint is 401-dead — they are NOT a substitute for one real over-HTTP (or standalone-execution) hit.

Born from: a "mark as indexed" button whose `fetch` hit a handler file directly; the file never called `session_start()`/`require config.php`, so it returned `{"success":false,"message":"Nicht autorisiert"}` for EVERY user — the feature shipped completely non-functional while its unit tests were green.

### Batch-Loop Throw-Safety (one bad row must not kill the batch)
A `throw`/assert/uncaught-exception newly added INSIDE a loop that processes a batch of independent rows (a cron queue, a mailing run, an import) aborts EVERY remaining row the moment one row trips it — unless the throw is caught per-iteration or the loop sits under a continue-on-error handler.

**Audit reflex** — for every new `throw`/assert/`die`/uncaught path in the diff, check whether it is inside a `foreach`/`while` over a work-set. If yes, prove one of: (a) a per-iteration `try/catch` that logs+continues; (b) an outer handler the loop resumes from; or (c) a documented intentional fail-fast. A bare throw at loop-body depth → NEEDS-FIX (latent batch-abort), even if currently unreachable — guards drift into reachability over time.

Born from: a Patrick-account assert added to several publisher senders; in two of them (a deadline cron and the index-monitor cron) the assert sat in an unprotected `foreach`, so a single bad row would have aborted the whole nightly batch — latent only because an upstream resolver currently excludes the triggering value.

### Coverage-Claim & Guard-Branch Verification (extends v4 Hunt-and-Replace)
Two claims that audits wave through but that hide bugs:

1. **"System-wide / all X / 100% coverage"** must be backed by a sweep whose PATTERN-SET *and* SCOPE (id-range, file-set, language variants) EQUAL what the requirement implies — not a subset of patterns over a subset of ids. Self-asserted coverage with no matching sweep is forbidden (same spirit as Hunt-and-Replace rule B). A regex-driven data migration in particular must enumerate every language/label variant (DE+EN, "Kunde"/"Client"/"Support:", every salutation) OR be gated by a post-run full-table pattern sweep before "done":
```bash
for p in '<P1>' '<P2>' ... ; do echo "== $p =="; <query/grep over the FULL scope> ; done
# Result must be empty for every Pi across the full range — not just the ids you remembered.
```
2. **A guard added "for all callers/senders" must sit on the branch that consumes UNTRUSTED / client-supplied input**, not only the server-side fallback branch. A check that runs only when the value is empty — while a client can supply the value directly and skip it — is not a guard. For every new guard, trace BOTH the fallback branch and the client-supplied branch and prove the guard covers the one the caller controls.

Born from: a "system-wide" template cleanup whose sweep checked 5 patterns over template ids 4–11 while the requirement said "all templates" — a publisher template outside that range still shipped the forbidden salutation; and an account guard that ran only on the empty-`account_id` fallback while the client-supplied `account_id` branch reached the send unchecked.

### Data-Repair (Heilung) Script Discipline
One-shot data fixes are code and get the same rigor:

1. **Committed & reproducible** — a live data fix must be committed as an idempotent, re-runnable script (dry-run default + explicit `--execute` gate + pre-state snapshot), never applied as an uncommitted ad-hoc `UPDATE`. An uncommitted live mutation is irreproducible from the repo and invisible to the next auditor.
2. **Selector ⊇ code-fix predicate** — when a heilung accompanies a code-fix, its selector must cover the FULL post-state of the bug: every companion column the code-fix sets, AND states produced by EARLIER heilung runs. A selector narrower than the code-fix predicate leaves a residual cohort unhealed and invisible.

**Audit reflex** — for every data-repair in the diff: confirm it is a committed script (not a described live UPDATE); diff its WHERE against the code-fix's condition and against prior heilung selectors in the same bug lineage; the heilung selector must be a superset. Verify the residual count is 0 after the run (`SELECT COUNT(*) … WHERE <full bug post-state>`).

Born from: a salutation fix applied as an uncommitted live UPDATE (only a pre-snapshot in the repo); and a heilung that set `status=55` but not the companion `publisher_mail_pending` flag, while the final sweep selected `status=12` only — leaving four `status=55, pending=0` orders permanently unswept, one due to release the next day.

### Router-Param Rename → Orphan-Link Sweep (extends Layout-Link → Route)
Renaming a query parameter that a router/`switch` dispatches on (`?action=` → `?view=`) is SILENT: old links still resolve to a valid PATH, fall through to the dispatcher's `default` branch, and render the WRONG view — no 404, no error, no log. Distinct from Layout-Link→Route (which checks the path/route exists): here the path is fine, only the dispatch key changed.

**Audit reflex** — on any rename of a parameter a router/switch branches on, grep the ENTIRE repo (server + client JS + templates) for the OLD `param=` token:
```bash
grep -rn "[?&]<oldparam>=" --include=*.php --include=*.js --include=*.html . | grep -v <backup/excludes>
# every hit is a silent mis-route. Result must be empty, OR each remaining bare-param link must intentionally target the default branch.
```

Born from: a todos module router switched from `?action=` to `?view=`; four caller links still used `action=` and silently rendered the list instead of the create/detail form — caught only by author diligence, not by any reflex.

---
