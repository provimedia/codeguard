<?php
function brancheFuer(string $host): string
{
    // Generic: the mapping lives in the database, not in control flow.
    $row = DB::table('domain_branchen')->where('host', $host)->first();
    return $row ? $row->branche : 'unbekannt';
}
