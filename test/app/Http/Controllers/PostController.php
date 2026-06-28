<?php

namespace App\Http\Controllers;

use App\Models\Post;
use App\Models\User;
use App\Models\Comment; // DEAD (php-unused-import): Comment is never referenced in this file.

class PostController extends Controller
{
    /**
     * LIVE_TRAP (route-string-at): registered as 'PostController@index' (legacy string form)
     * in routes/web.php. No static call site exists for this method.
     * Exercises the live scope User::active() so scopeActive is genuinely reachable.
     */
    public function index()
    {
        $authors = User::active()->withTrashedAdmins()->get();
        $posts = Post::published()->get();

        return view('posts.index', compact('posts', 'authors'));
    }

    /**
     * LIVE_TRAP (route-class-array): registered as [PostController::class, 'show']
     * in routes/web.php. Reached only through the router, never called in code.
     */
    public function show(int $id)
    {
        $post = Post::published()->findOrFail($id);
        // Touch the magic accessor so $post->excerpt is genuinely consumed somewhere.
        $preview = $post->excerpt;

        return view('posts.show', [
            'post' => $post,
            'preview' => $preview,
        ]);
    }

    /**
     * Normal internal helper, called by show()/index() indirectly through the
     * builder. Present as realistic noise (NOT an oracle case).
     */
    private function buildCacheKey(int $id): string
    {
        return 'post:' . $id . ':v2';
    }

    /**
     * DEAD (php-private-method): an old ranking filter that nothing calls.
     * Unique name, zero references anywhere in the fixture. Safe to delete.
     */
    private function deprecatedScoreFilter(array $scores): array
    {
        return array_filter($scores, fn ($s) => $s > 0);
    }
}
