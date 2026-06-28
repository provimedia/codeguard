<?php

namespace App\Http\Sanitizers;

/**
 * Cleans user-submitted FORM input. The body below is textually identical to
 * QuerySanitizer::clean, but it encodes DIFFERENT knowledge: form-field
 * validation rules. It will change when the *form* rules change (e.g. trimming
 * policy for free-text fields). Merging it with the query sanitizer would
 * couple two things that change for different reasons.
 */
class FormSanitizer
{
    /**
     * REDUNDANT_COINCIDENTAL (1 of 2): do NOT extract/merge with QuerySanitizer.
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
