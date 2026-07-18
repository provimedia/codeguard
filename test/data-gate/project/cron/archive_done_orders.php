<?php
/** Cronjob: abgeschlossene Auftraege aelter 12 Monate archivieren (monatlich) */
require_once __DIR__ . '/../config.php';
$db = new PDO('sqlite:' . __DIR__ . '/../data/crm.db');
$db->exec("UPDATE orders SET internal_notes = COALESCE(internal_notes,'') || ' [archiv-kandidat]' WHERE status = 'done' AND julianday('now') - julianday(status_changed_at) > 365");
