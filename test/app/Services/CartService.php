<?php

namespace App\Services;

class CartService
{
    private array $lines = [];

    public function addLine(int $netCents, float $vatRate): void
    {
        $this->lines[] = $this->grossFromNet($netCents, $vatRate);
    }

    public function total(): int
    {
        return array_sum($this->lines);
    }

    /**
     * REDUNDANT_EXTRACT (clone 1 of 3): identical VAT gross calculation,
     * byte-for-byte duplicated in OrderService and QuoteService. Same business
     * knowledge ("how we compute gross from net") in 3 files -> Rule of Three
     * says EXTRACT to a shared helper.
     */
    private function grossFromNet(int $netCents, float $vatRate): int
    {
        $factor = 1.0 + ($vatRate / 100.0);
        $gross = (int) round($netCents * $factor);
        return $gross;
    }
}
