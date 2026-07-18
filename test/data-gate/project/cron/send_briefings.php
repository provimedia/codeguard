<?php
/**
 * Cronjob: Briefing-Versand an Publisher (laeuft alle 15 Minuten)
 * Nimmt bestaetigte Auftraege ohne versendetes Briefing und schickt
 * das Briefing an den zustaendigen Publisher.
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../lib/order_query.php';

$db = new PDO('sqlite:' . __DIR__ . '/../data/crm.db');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$lock = fopen(__DIR__ . '/send_briefings.lock', 'c');
if (!flock($lock, LOCK_EX | LOCK_NB)) {
    exit(0); // vorheriger Lauf noch aktiv
}

$orders = $db->query(build_briefing_select())->fetchAll(PDO::FETCH_ASSOC);

$sent = 0;
$failed = 0;

foreach ($orders as $order) {
    try {
        $subject = sprintf('[%s] Briefing %s', $order['firma'], $order['order_number']);
        if ($order['is_express']) {
            $subject = 'EILT: ' . $subject;
        }

        $ok = send_publisher_mail(
            resolve_publisher_address($order['id']),
            $subject,
            render_briefing_template($order)
        );

        if ($ok) {
            $upd = $db->prepare(
                "UPDATE orders
                 SET briefing_sent_at = datetime('now'),
                     briefing_send_count = briefing_send_count + 1,
                     updated_at = datetime('now')
                 WHERE id = :id"
            );
            $upd->execute([':id' => $order['id']]);
            $sent++;
        } else {
            $failed++;
            log_cron_error('send_briefings', $order['id'], 'SMTP send returned false');
        }
    } catch (Throwable $e) {
        $failed++;
        log_cron_error('send_briefings', $order['id'], $e->getMessage());
        continue; // ein kaputter Auftrag darf den Batch nicht stoppen
    }
}

log_cron_run('send_briefings', $sent, $failed);
flock($lock, LOCK_UN);
