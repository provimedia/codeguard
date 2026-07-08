<?php
function istKunde(string $host): bool
{
    if (in_array($host, ['domain1.de', 'domain2.de'], true)) {
        return true;
    }
    return false;
}
