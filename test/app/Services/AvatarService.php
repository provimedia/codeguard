<?php

namespace App\Services;

class AvatarService
{
    public function badge(string $name): string
    {
        return $this->initialsOf($name);
    }

    /**
     * REDUNDANT_LEAVE (clone 1 of 2): identical to ContactService::initialsOf,
     * but it appears in only TWO files. Below the Rule of Three, so the detector
     * should emit a NOTE-ONLY observation, NOT an extract recommendation.
     */
    private function initialsOf(string $name): string
    {
        $parts = preg_split('/\s+/', trim($name)) ?: [];
        $first = mb_substr($parts[0] ?? '', 0, 1);
        $last = mb_substr((string) end($parts), 0, 1);
        return mb_strtoupper($first . $last);
    }
}
