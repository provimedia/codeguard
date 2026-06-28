<?php

namespace App\Slop;

/**
 * Simulated AI-agent output. Everything here is slop the agent "helpfully"
 * added in a diff. None of it is wired into the app.
 */
class AgentHelpers
{
    /**
     * SLOP (unused-helper): the agent added this helper but nothing calls it.
     * Zero references -> REMOVABLE.
     */
    public static function formatMoneyAgent(int $cents): string
    {
        // Divide the cents by one hundred to get euros.
        $euros = $cents / 100; // SLOP (redundant-comment): the comment just restates the line.
        return number_format($euros, 2) . ' EUR';
    }

    /**
     * SLOP (reimplementation): re-implements initials logic that ALREADY exists
     * in App\Services\AvatarService::initialsOf / ContactService::initialsOf.
     * Same knowledge, rewritten by the agent (a reimplementation is a rewrite,
     * not a verbatim clone) -> REMOVABLE (call the existing helper instead).
     */
    public static function makeInitials(string $name): string
    {
        $initials = '';
        foreach (explode(' ', $name) as $word) {
            if ($word !== '') {
                $initials .= strtoupper($word[0]);
            }
        }
        return substr($initials, 0, 2);
    }

    public static function debugDump(array $data): void
    {
        // SLOP (debug-leftover): print_r debug statement left in the diff.
        print_r($data);
    }
}
