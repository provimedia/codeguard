<?php

namespace App\Slop;

/**
 * SLOP (single-use-abstraction): an interface with exactly ONE implementation
 * and exactly ONE caller. The agent introduced premature indirection; the
 * interface earns nothing and should be inlined -> REMOVABLE abstraction.
 */
interface Notifier
{
    public function notify(string $message): void;
}

class EmailNotifier implements Notifier
{
    public function notify(string $message): void
    {
        // send an email...
    }
}

class SignupService
{
    public function __construct(private Notifier $notifier)
    {
    }

    public function register(string $email): void
    {
        $this->notifier->notify('welcome ' . $email);
    }
}
