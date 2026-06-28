<?php

namespace App\Services;

class OrderService
{
    public function lineGross(int $netCents, float $vatRate): int
    {
        return $this->grossFromNet($netCents, $vatRate);
    }

    /**
     * REDUNDANT_EXTRACT (clone 2 of 3): byte-for-byte identical to the same
     * helper in CartService and QuoteService.
     */
    private function grossFromNet(int $netCents, float $vatRate): int
    {
        $factor = 1.0 + ($vatRate / 100.0);
        $gross = (int) round($netCents * $factor);
        return $gross;
    }
}
