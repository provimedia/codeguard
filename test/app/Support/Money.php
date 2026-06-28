<?php

namespace App\Support;

use BadMethodCallException;

/**
 * NOVEL TRAP (magic-__call-routing): a value object whose currency formatters
 * are dispatched through __call. Calling $money->eur() / $money->usd() routes
 * into renderIn('EUR') / renderIn('USD'). The per-currency render methods are
 * reachable only through this magic routing -> a naive scanner sees the helper
 * methods as never called.
 */
class Money
{
    public function __construct(private int $cents)
    {
    }

    public static function of(int $cents): self
    {
        return new self($cents);
    }

    /**
     * Magic router: $money->eur(), $money->usd(), ... -> renderEur()/renderUsd().
     */
    public function __call(string $name, array $args): string
    {
        $method = 'render' . ucfirst($name);
        if (method_exists($this, $method)) {
            return $this->{$method}();
        }
        throw new BadMethodCallException($name);
    }

    /**
     * LIVE_TRAP (magic-__call-routing): reached only via $money->eur().
     */
    protected function renderEur(): string
    {
        return number_format($this->cents / 100, 2, ',', '.') . ' €';
    }

    /**
     * LIVE_TRAP (magic-__call-routing): reached only via $money->usd().
     */
    protected function renderUsd(): string
    {
        return '$' . number_format($this->cents / 100, 2, '.', ',');
    }
}
