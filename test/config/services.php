<?php

/**
 * Container / service wiring. PaymentGateway is bound here ONLY via class-string
 * (both the ::class form and a plain FQ string). It is never imported or
 * instantiated directly in source -> DI-config class-string trap.
 */

return [
    'payments' => [
        // class-string binding (resolved by the container)
        'driver' => \App\Services\PaymentGateway::class,
        // legacy plain-string form of the same class
        'fallback' => 'App\\Services\\PaymentGateway',
        'currency' => 'EUR',
    ],

    'partner' => [
        'base_url' => 'https://api.partner.example.com/v2',
    ],
];
