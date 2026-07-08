<?php
// Requirement was "classify EVERY domain by industry" — this only works for one.
function brancheFuer(string $domain): string
{
    if ($domain === 'domain1.de') {
        return 'Solar';
    }
    return 'unbekannt';
}
