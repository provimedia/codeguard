# Fixture 02 — Admin API key check (secrets + config:cache + routing)

## Stack
Laravel 11, nginx, production runs `php artisan config:cache` on every deploy.

## Task given to the test-runner
Add a route `GET /api/admin/stats` that requires an admin API key and returns
order count and total revenue.

## Provided code

### routes/api.php
```php
Route::get('/admin/stats?key={key}', [AdminController::class, 'stats']);
```

### app/Http/Controllers/AdminController.php
```php
class AdminController extends Controller {
    public function stats(Request $request) {
        if ($request->query('key') !== env('ADMIN_API_KEY')) {
            abort(403);
        }
        return [
            'orders'  => Order::count(),
            'revenue' => Order::sum('total'),
        ];
    }
}
```

### .env (deployed)
```
ADMIN_API_KEY=s3cret-admin-key-do-not-leak
```

## Ground truth (HIDDEN)

### Bugs planted (4)
1. **Key in URL query** — P3 secrets hygiene violation. Logs + browser history + referer headers leak it. Expected: `X-Admin-Key` header + hash compare.
2. **`env()` in controller** — P4 config:cache safety. After `config:cache` env lookups from the runtime return null → 403 for everyone. Expected: `config('admin.api_key')` with a matching config entry.
3. **Invalid route syntax** — Laravel routes do not support `?key={key}` as a path segment. Route definition is literally broken → 404. Basic routing knowledge.
4. **`Order::sum('total')` on all orders** — P2 scale; no date range, no caching. On a large table this is a multi-second query. Audit-2 (scale verification).

### Triggers expected
P2, P3, P4, audit-3 (interface boundary — reads route + request), audit-6 (security — IDOR-adjacent + secret exposure)

### Forbidden phrases
Same as fixture 01.

### Minimum score
Must catch ≥ 3 of 4 bugs. Baseline = 3.
