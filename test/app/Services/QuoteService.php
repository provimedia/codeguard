<?php

namespace App\Services;

class QuoteService
{
    public function estimate(int $netCents, float $vatRate): int
    {
        return $this->grossFromNet($netCents, $vatRate);
    }

    /**
     * REDUNDANT_EXTRACT (clone 3 of 3): the third byte-for-byte copy. Three
     * copies of the same knowledge -> detector should recommend EXTRACT-CANDIDATE.
     */
    private function grossFromNet(int $netCents, float $vatRate): int
    {
        $factor = 1.0 + ($vatRate / 100.0);
        $gross = (int) round($netCents * $factor);
        return $gross;
    }
}
