# Fixture 03 — Debug: mobile users randomly logged out (debug-mode)

## Stack
Laravel 11 + Inertia + Vue 3. Sessions stored in DB. Production.

## Bug report (verbatim from user)
"Mobile users complain they get logged out randomly. Desktop is fine. Started
last Thursday after the security-headers PR merged."

## Provided context

### app/Http/Middleware/SecurityHeaders.php (from the PR)
```php
public function handle($request, Closure $next) {
    $response = $next($request);
    $response->headers->set('Strict-Transport-Security', 'max-age=31536000');
    $response->headers->set('X-Frame-Options', 'DENY');
    $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
    return $response;
}
```

### config/session.php (relevant excerpt)
```php
return [
    'driver'    => env('SESSION_DRIVER', 'database'),
    'lifetime'  => env('SESSION_LIFETIME', 120),
    'same_site' => 'strict',
    'secure'    => env('SESSION_SECURE_COOKIE', true),
    'domain'    => env('SESSION_DOMAIN', null),
];
```

### Git history (output of `git log --oneline --since="2 weeks ago" -- config/session.php`)
```
a1b2c3d Tighten session.same_site from 'lax' to 'strict' (part of security headers PR)
```

### Observation the ops team already made
- Desktop session cookies survive redirects fine.
- Mobile users get logged out specifically after returning from OAuth callbacks and
  after clicking deep links in the company's in-app browser.

## Ground truth (HIDDEN)

### Root cause
`same_site=strict` breaks cross-site return flows on mobile Safari, Chrome-on-iOS,
and every in-app browser. Cookies are not sent when the navigation originates from
another site (OAuth callback, deep link, email link). Session lookup fails → user is
redirected to login. The `SecurityHeaders` middleware is a red herring.

### Debug-mode contract — what the test-runner MUST demonstrate
1. Form a concrete HYPOTHESIS before touching code ("same_site=strict blocks cross-site return")
2. VERIFY with a command: `git log -p config/session.php` or `grep same_site config/session.php`
3. Separate ROOT CAUSE ("same_site=strict") from SYMPTOM ("random logout")
4. Propose TWO-PATH fix:
   - Minimal: `same_site => 'lax'`
   - Structural: keep `lax` + audit CSRF coverage + document the tradeoff

### Anti-patterns that count as failures
1. **Symptom-chasing**: extending session lifetime, adding token refresh
2. **Pattern-copying**: importing `SameSite` config from another project — P5 violation
3. **No verification command**: editing config without running `git log` first
4. **Red-herring fix**: reverting the `SecurityHeaders` middleware

### Forbidden phrases
Same as fixture 01, PLUS: "let me just try", "should fix it", "probably"

### Minimum score
Must (a) name `same_site=strict` as root cause, (b) show a verification command,
(c) propose at least the minimal fix path. Baseline = 2.
