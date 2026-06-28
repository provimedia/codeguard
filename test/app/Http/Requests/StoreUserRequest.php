<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreUserRequest extends FormRequest
{
    /**
     * The 'iban' string here is the ONLY thing that keeps IbanRule::validate
     * alive (the rule keyword was registered via Validator::extend).
     */
    public function rules(): array
    {
        return [
            'email' => 'required|email',
            'payout_iban' => 'required|iban',
        ];
    }
}
