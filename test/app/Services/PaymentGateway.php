<?php

namespace App\Services;

/**
 * LIVE_TRAP (di-config-classstring): this class is never `new`-ed or imported
 * by any other PHP file. It is resolved by the container only because
 * config/services.php references it as a class-string
 * (\App\Services\PaymentGateway::class) AND as a plain string key.
 */
class PaymentGateway
{
    // REDUNDANT_COINCIDENTAL/config: hardcoded partner endpoint (also in InvoiceMailer + SyncInventoryCommand).
    private const PARTNER_API = 'https://api.partner.example.com/v2';

    public function __construct(private array $config = [])
    {
    }

    /**
     * LIVE_TRAP (di-config-classstring): the container resolves this class and
     * calls charge(); there is no static `->charge(` call site in the fixture.
     */
    public function charge(int $cents, string $token): array
    {
        $endpoint = self::PARTNER_API . '/charges';

        return [
            'endpoint' => $endpoint,
            'amount' => $cents,
            'token' => $token,
            'status' => 'authorized',
        ];
    }
}
