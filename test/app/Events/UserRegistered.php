<?php

namespace App\Events;

use App\Models\User;

/**
 * Plain event object so the listener's type-hint resolves to a real class.
 */
class UserRegistered
{
    public function __construct(public User $user)
    {
    }
}
