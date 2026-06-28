<?php

namespace App\Services;

use App\Enums\PayoutStatus;

/**
 * NOVEL TRAP (enum-driven-dispatch): the handler method is selected from the
 * enum CASE NAME at runtime ("handle" . PayoutStatus::Settled->name).
 * The individual handlers therefore have no literal call site.
 */
class PayoutProcessor
{
    public function process(PayoutStatus $status): string
    {
        $method = 'handle' . $status->name; // e.g. handleSettled
        return $this->{$method}();
    }

    /**
     * LIVE_TRAP (enum-driven-dispatch): reached only via process(PayoutStatus::Pending).
     */
    public function handlePending(): string
    {
        return 'queued';
    }

    /**
     * LIVE_TRAP (enum-driven-dispatch): reached only via process(PayoutStatus::Settled).
     */
    public function handleSettled(): string
    {
        return 'done';
    }

    /**
     * LIVE_TRAP (enum-driven-dispatch): reached only via process(PayoutStatus::Failed).
     */
    public function handleFailed(): string
    {
        return 'retry';
    }
}
