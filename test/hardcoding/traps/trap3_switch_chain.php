<?php
function branche(string $domain): string
{
    switch ($domain) {
        case 'domain1.de':
            return 'Solar';
        case 'domain2.de':
            return 'Krypto';
        default:
            return 'unbekannt';
    }
}
