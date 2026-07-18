<?php
/** Cronjob: Rechnungs-Sync mit Buchhaltungssystem (stuendlich) */
require_once __DIR__ . '/../config.php';
$db = new PDO('sqlite:' . __DIR__ . '/../data/crm.db');
$rows = $db->query("SELECT id, invoice_id FROM orders WHERE status = 'done' AND invoiced_at IS NULL AND deleted_at IS NULL")->fetchAll(PDO::FETCH_ASSOC);
foreach ($rows as $o) {
    // Uebergabe an Rechnungs-API (gekuerzt)
}
