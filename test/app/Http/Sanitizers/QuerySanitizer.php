<?php

namespace App\Http\Sanitizers;

/**
 * Cleans URL QUERY parameters. The body is byte-for-byte identical to
 * FormSanitizer::clean purely by coincidence: a generic "drop nulls, trim
 * strings" loop. But this one encodes URL-parsing knowledge and will change for
 * different reasons (e.g. URL-decoding, array-bracket params). Coincidental
 * duplication -> NOTE-ONLY at most, never an extract target.
 */
class QuerySanitizer
{
    /**
     * REDUNDANT_COINCIDENTAL (2 of 2): identical text, different knowledge.
     */
    public function clean(array $items): array
    {
        $result = [];
        foreach ($items as $key => $value) {
            if ($value === null) {
                continue;
            }
            $result[$key] = trim((string) $value);
        }
        return $result;
    }
}
