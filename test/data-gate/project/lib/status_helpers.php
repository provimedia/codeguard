<?php
/** Status-Konstanten + Label-Helper fuer Auftragsansichten */
const ORDER_STATUSES = ['new', 'confirmed', 'online', 'done', 'cancelled'];

function status_label(string $status): string
{
    return [
        'new' => 'Neu',
        'confirmed' => 'Bestaetigt',
        'online' => 'Online',
        'done' => 'Fertig',
        'cancelled' => 'Storniert',
    ][$status] ?? $status;
}
