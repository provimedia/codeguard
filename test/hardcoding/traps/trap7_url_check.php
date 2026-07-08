<?php
function isPartnerCallback(string $url): bool
{
    if (str_contains($url, 'https://domain1.de/api')) {
        return true;
    }
    return false;
}
