<?php
/** Cronjob: Publisher-Erinnerungen bei ueberfaelligen Textlieferungen (taeglich 06:00) */
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../lib/order_query.php';
$db = new PDO('sqlite:' . __DIR__ . '/../data/crm.db');
$rows = $db->query(build_reminder_select())->fetchAll(PDO::FETCH_ASSOC);
foreach ($rows as $o) {
    $ok = send_publisher_mail(resolve_publisher_address($o['id']), 'Erinnerung: Text ' . $o['order_number'], 'Bitte Textlieferung pruefen.');
    if ($ok) {
        $db->prepare("UPDATE orders SET last_reminder_at = datetime('now') WHERE id = :id")->execute([':id' => $o['id']]);
    }
}
