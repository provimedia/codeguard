<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

/**
 * Real model so the unused `use App\Models\Comment;` in PostController is an
 * honest dead-import (resolves to a real class) rather than a broken reference.
 */
class Comment extends Model
{
    protected $fillable = ['post_id', 'body'];

    public function post()
    {
        return $this->belongsTo(Post::class);
    }
}
