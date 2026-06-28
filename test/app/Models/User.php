<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;

/**
 * Account holder. Most of the magic surface here (scopes, accessors)
 * is reached only through Eloquent's __call / __get indirection.
 */
class User extends Model
{
    protected $fillable = ['first_name', 'last_name', 'email', 'status'];

    /**
     * LIVE_TRAP (eloquent-scope): reached only via User::active() / $query->active().
     * A naive static scan sees zero direct call sites for "scopeActive".
     */
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('status', 'active');
    }

    /**
     * LIVE_TRAP (eloquent-scope): reached via ->withTrashedAdmins() chained on a query.
     */
    public function scopeWithTrashedAdmins(Builder $query): Builder
    {
        return $query->where('role', 'admin')->withTrashed();
    }

    /**
     * LIVE_TRAP (eloquent-accessor): consumed as $user->full_name (magic __get).
     */
    public function getFullNameAttribute(): string
    {
        return trim($this->first_name . ' ' . $this->last_name);
    }

    /**
     * LIVE_TRAP (eloquent-accessor): consumed as $user->initials in a Blade view.
     */
    public function getInitialsAttribute(): string
    {
        $f = mb_substr($this->first_name, 0, 1);
        $l = mb_substr($this->last_name, 0, 1);
        return mb_strtoupper($f . $l);
    }

    /**
     * Normal, internally-referenced helper (NOT a trap): called by getInitialsAttribute? No -
     * actually called by ReportBuilder. Present to add realistic noise.
     */
    public function displayEmail(): string
    {
        return strtolower($this->email);
    }

    /**
     * DEAD (php-private-method): zero references anywhere in the fixture.
     * Legacy flag migration that was never wired up. Safe to delete.
     */
    private function normalizeLegacyFlags(array $flags): array
    {
        $out = [];
        foreach ($flags as $k => $v) {
            $out[strtolower($k)] = (bool) $v;
        }
        return $out;
    }
}
