<?php

namespace App\Providers;

use App\Models\Post;
use App\Observers\PostObserver;
use App\Rules\IbanRule;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        // Wires the observer CLASS (methods are still convention-dispatched).
        Post::observe(PostObserver::class);

        // Wires the IBAN rule by STRING keyword. The closure references
        // IbanRule::validate via a callable array, not a literal call.
        Validator::extend('iban', [IbanRule::class, 'validate']);

        // Load runtime Str macros (registers Str::slugifyTitle).
        require __DIR__ . '/../Support/macros.php';
    }
}
