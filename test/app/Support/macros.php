<?php

use Illuminate\Support\Str;

/**
 * Macro registration file (loaded by a service provider). Registers a runtime
 * method on Str. After this, Str::slugifyTitle('...') works even though
 * "slugifyTitle" is not a declared method anywhere -> the closure body is the
 * real implementation and is invoked only via the macro name.
 */

Str::macro('slugifyTitle', function (string $title): string {
    // NOVEL TRAP (str-macro): live code reachable only as Str::slugifyTitle(...).
    $slug = strtolower(trim($title));
    $slug = preg_replace('/[^a-z0-9]+/', '-', $slug) ?? '';
    return trim($slug, '-');
});
