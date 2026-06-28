<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;

/**
 * LIVE_TRAP (artisan-command): a CLI entry point. The framework discovers it by
 * scanning the Commands directory; `php artisan inventory:sync` runs handle().
 * There is no PHP call site for handle() or for this class name anywhere -> a
 * naive scanner reports it dead, but it is a real, invokable command.
 */
class SyncInventoryCommand extends Command
{
    protected $signature = 'inventory:sync {--full}';

    protected $description = 'Synchronise inventory from the partner feed';

    // config duplication: same partner endpoint as PaymentGateway + InvoiceMailer.
    private const PARTNER_API = 'https://api.partner.example.com/v2';

    /**
     * LIVE_TRAP (artisan-command): invoked by the console kernel, never by code.
     */
    public function handle(): int
    {
        $feed = self::PARTNER_API . '/inventory';
        $this->info('Syncing from ' . $feed);

        return self::SUCCESS;
    }
}
