<?php
/** Cronjob: Watchdog — gelieferte Texte ohne Veroeffentlichung nach 14 Tagen melden */
require_once __DIR__ . '/../config.php';
$db = new PDO('sqlite:' . __DIR__ . '/../data/crm.db');
$rows = $db->query("SELECT id, order_number FROM orders WHERE text_delivered_at IS NOT NULL AND published_at IS NULL AND deleted_at IS NULL AND julianday('now') - julianday(text_delivered_at) > 14")->fetchAll(PDO::FETCH_ASSOC);
foreach ($rows as $o) {
    log_cron_error('publish_watchdog', $o['id'], 'Text geliefert, aber seit >14 Tagen nicht veroeffentlicht');
}
