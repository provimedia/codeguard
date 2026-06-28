<?php

namespace App\Rules;

/**
 * NOVEL TRAP (validator-extend-string-rule): the validate() method is wired to
 * the validation rule keyword "iban" via Validator::extend('iban', [IbanRule::class, 'validate'])
 * in AppServiceProvider. Form requests then reference it purely as the string
 * 'iban' in their rules() array. validate() therefore has no literal call site.
 */
class IbanRule
{
    /**
     * LIVE_TRAP (validator-extend-string-rule): invoked by the validator when a
     * field uses the 'iban' rule string.
     */
    public function validate(string $attribute, mixed $value, array $parameters): bool
    {
        $iban = strtoupper(preg_replace('/\s+/', '', (string) $value) ?? '');
        return (bool) preg_match('/^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$/', $iban);
    }
}
