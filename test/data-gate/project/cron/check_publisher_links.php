<?php
/** Cronjob: Live-Links auf Erreichbarkeit pruefen (woechentlich) */
require_once __DIR__ . '/../config.php';
$db = new PDO('sqlite:' . __DIR__ . '/../data/crm.db');
$rows = $db->query("SELECT id, published_url FROM orders WHERE status = 'online' AND published_url IS NOT NULL")->fetchAll(PDO::FETCH_ASSOC);
foreach ($rows as $o) {
    // HTTP-HEAD-Check mit Retry, Offline-Todo bei 404 (gekuerzt)
}
