<?php
/**
 * CRM-Konfiguration + Mail-/Log-Helper (gekuerzt fuer dieses Repo).
 */

const SMTP_HOST = 'mail.internal.example';
const SMTP_FROM = 'auftrag@crm.example';

function send_publisher_mail(string $to, string $subject, string $body): bool
{
    // SMTP-Versand (Implementierung ausgelagert, hier gekuerzt)
    return smtp_send(SMTP_HOST, SMTP_FROM, $to, $subject, $body);
}

function resolve_publisher_address(int $orderId): string
{
    // Publisher-Aufloesung ueber Website-Zuordnung (gekuerzt)
    return 'publisher@partner.example';
}

function render_briefing_template(array $order): string
{
    return "Briefing fuer {$order['order_number']}:\n{$order['briefing_text']}";
}

function log_cron_error(string $job, int $orderId, string $message): void
{
    file_put_contents(
        __DIR__ . '/logs/cron.log',
        sprintf("%s ERROR %s order=%d %s\n", date('c'), $job, $orderId, $message),
        FILE_APPEND
    );
}

function log_cron_run(string $job, int $sent, int $failed): void
{
    file_put_contents(
        __DIR__ . '/logs/cron.log',
        sprintf("%s RUN %s sent=%d failed=%d\n", date('c'), $job, $sent, $failed),
        FILE_APPEND
    );
}
