<?php

namespace App\Slop;

/**
 * Simulated agent diff with debug leftovers and a placeholder block.
 */
class PaymentProcessor
{
    public function process(array $payload): array
    {
        var_dump($payload); // SLOP (debug-leftover): var_dump left in.

        $amount = (int) ($payload['amount'] ?? 0);

        if ($amount <= 0) {
            dd('invalid amount', $payload); // SLOP (debug-leftover): dd() left in.
        }

        // TODO: PLACEHOLDER -- wire this up to the real gateway later.
        // example: $gateway->charge($amount, $payload['token']);
        // SLOP (todo-block): leftover TODO/PLACEHOLDER/example scaffold.

        return ['status' => 'ok', 'amount' => $amount];
    }
}
