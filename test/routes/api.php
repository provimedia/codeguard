<?php

use App\Http\Controllers\WebhookController;
use Illuminate\Support\Facades\Route;

/*
 * Only the WebhookController::handle entry point is routed. The individual
 * handle<Event>() methods are dispatched from inside handle() by string -> they
 * have no route and no static call site.
 */
Route::post('/webhooks/partner', [WebhookController::class, 'handle']);
