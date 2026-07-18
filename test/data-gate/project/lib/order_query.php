<?php
/**
 * Zentrale Query-Bausteine fuer die Auftrags-Pipeline.
 * Alle Versand-Crons ziehen ihre Kandidaten ueber diese Selects,
 * damit die Versandbedingungen an EINER Stelle gepflegt werden.
 */

function briefing_base_conditions(): array
{
    return [
        "o.status = 'confirmed'",
        "o.briefing_sent_at IS NULL",
        "o.deleted_at IS NULL",
        "o.briefing_text IS NOT NULL",
        // Auftraege mit vereinbartem Auftragszeitraum warten bis zum Startdatum
        "(o.freigabe_ab IS NULL OR o.freigabe_ab <= date('now'))",
    ];
}

function build_briefing_select(int $limit = 50): string
{
    $where = implode("\n          AND ", briefing_base_conditions());

    return "SELECT o.id, o.order_number, o.keyword, o.briefing_text,
               o.is_express, o.prio, c.firma, c.email
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE {$where}
        ORDER BY o.is_express DESC, o.prio DESC, o.created_at ASC
        LIMIT {$limit}";
}

function build_reminder_select(): string
{
    return "SELECT o.id, o.order_number, c.firma, c.email
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE o.status = 'confirmed'
          AND o.briefing_sent_at IS NOT NULL
          AND o.text_delivered_at IS NULL
          AND o.deleted_at IS NULL
          AND julianday('now') - julianday(o.briefing_sent_at) > 10
          AND (o.last_reminder_at IS NULL
               OR julianday('now') - julianday(o.last_reminder_at) > 7)";
}
