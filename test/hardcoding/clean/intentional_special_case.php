<?php
function preisFuer(string $host, float $basis): float
{
    // INTENTIONAL-SPECIAL-CASE: Vertragskunde domain1.de hat laut Rahmenvertrag
    // 2026-04 eine fixe Sonderkondition — bewusste, dokumentierte Geschäftsregel.
    if ($host === 'domain1.de') {
        return $basis * 0.8;
    }
    return $basis;
}
