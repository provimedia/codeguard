<?php

namespace App\Observers;

use App\Models\Post;

/**
 * Registered via Post::observe(PostObserver::class) in AppServiceProvider. The
 * CLASS is referenced there, but the individual hook METHODS (created/updated)
 * are invoked by Eloquent purely by naming convention -> classic looks-dead.
 */
class PostObserver
{
    /**
     * LIVE_TRAP (observer): fired by Eloquent after a Post is created. No code
     * ever calls ->created( ) directly.
     */
    public function created(Post $post): void
    {
        // warm a cache, etc.
    }

    /**
     * LIVE_TRAP (observer): fired by Eloquent after a Post is updated.
     */
    public function updated(Post $post): void
    {
        // bust a cache, etc.
    }
}
