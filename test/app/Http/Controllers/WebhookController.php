<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Str;

/**
 * NOVEL TRAP (webhook-string-dispatch): incoming webhooks are routed to a
 * handler method whose name is *built from the payload's event type string*.
 * e.g. event "invoice.paid" -> handleInvoicePaid(). No static call site exists
 * for the individual handlers; they are reachable only via the runtime string.
 */
class WebhookController extends Controller
{
    public function handle(Request $request)
    {
        $type = (string) $request->input('type', '');          // e.g. "invoice.paid"
        $method = 'handle' . Str::studly(str_replace('.', '_', $type));

        if (method_exists($this, $method)) {
            return $this->{$method}($request->input('data', []));
        }

        return response('ignored', 202);
    }

    /**
     * LIVE_TRAP (webhook-string-dispatch): reached only as $this->{'handleInvoicePaid'}().
     */
    protected function handleInvoicePaid(array $data)
    {
        return response('invoice recorded', 200);
    }

    /**
     * LIVE_TRAP (webhook-string-dispatch): reached only as $this->{'handleChargeRefunded'}().
     */
    protected function handleChargeRefunded(array $data)
    {
        return response('refund recorded', 200);
    }
}
