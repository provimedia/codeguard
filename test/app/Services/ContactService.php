<?php

namespace App\Services;

class ContactService
{
    public function shortLabel(string $name): string
    {
        return $this->initialsOf($name);
    }

    /**
     * REDUNDANT_LEAVE (clone 2 of 2): the second (and last) copy. Two copies
     * only -> NOTE-ONLY, not EXTRACT-CANDIDATE.
     */
    private function initialsOf(string $name): string
    {
        $parts = preg_split('/\s+/', trim($name)) ?: [];
        $first = mb_substr($parts[0] ?? '', 0, 1);
        $last = mb_substr((string) end($parts), 0, 1);
        return mb_strtoupper($first . $last);
    }
}
