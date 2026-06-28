<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;

class Post extends Model
{
    protected $fillable = ['title', 'slug', 'body', 'status', 'author_id'];

    /**
     * LIVE_TRAP (eloquent-scope): reached only via Post::published().
     */
    public function scopePublished(Builder $query): Builder
    {
        return $query->where('status', 'published');
    }

    public function author()
    {
        return $this->belongsTo(User::class, 'author_id');
    }

    /**
     * LIVE_TRAP (eloquent-accessor): consumed as $post->excerpt in Blade.
     */
    public function getExcerptAttribute(): string
    {
        return mb_substr(strip_tags($this->body), 0, 140);
    }
}
