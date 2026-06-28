<?php

namespace App\Services;

/**
 * Package-style service: this is the public surface of a (pretend) reusable
 * billing package. Its public methods are part of the published API and are
 * consumed by DOWNSTREAM applications, not from within this fixture.
 */
class InvoiceMailer
{
    // config duplication: same support email appears in 3 files.
    private const SUPPORT_EMAIL = 'billing@example.com';
    // config duplication: same partner endpoint appears in 3 files.
    private const PARTNER_API = 'https://api.partner.example.com/v2';

    /**
     * LIVE_TRAP (public-api-export): public, documented, semver-protected entry
     * point. Zero internal callers in this fixture -> a naive scanner flags it,
     * but deleting it is a breaking change for external consumers.
     * NOTE: public symbol -> oracle expects ASSERTED-DEAD (not VERIFIED-DEAD-PRIVATE).
     */
    public function send(string $to, array $invoice): bool
    {
        $payload = [
            'reply_to' => self::SUPPORT_EMAIL,
            'sync_url' => self::PARTNER_API . '/invoices',
            'to' => $to,
            'invoice' => $invoice,
        ];

        return ! empty($payload['to']);
    }

    /**
     * DEAD (php-private-method): an internal draft formatter that was never
     * called by send() (or anything else). Truly removable.
     */
    private function formatLegacyHeader(array $invoice): string
    {
        return '#' . ($invoice['number'] ?? '0');
    }
}
