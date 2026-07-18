<?php
/** Cronjob: verwaiste Lock-Dateien aelter 6h entfernen (taeglich) */
foreach (glob(__DIR__ . '/*.lock') as $lock) {
    if (filemtime($lock) < time() - 6 * 3600) { @unlink($lock); }
}
