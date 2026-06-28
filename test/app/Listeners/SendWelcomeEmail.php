<?php

namespace App\Listeners;

use App\Events\UserRegistered;

/**
 * LIVE_TRAP (event-listener): auto-discovered. Laravel's event discovery maps
 * the type-hinted handle(UserRegistered $event) to the UserRegistered event.
 * No EventServiceProvider $listen array entry and no manual ->listen() call
 * reference this class -> looks dead, is fully wired by convention.
 */
class SendWelcomeEmail
{
    /**
     * LIVE_TRAP (event-listener): invoked by the event dispatcher only.
     */
    public function handle(UserRegistered $event): void
    {
        // pretend to queue a welcome mail for $event->user
    }
}
