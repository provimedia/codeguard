<?php
/** Cronjob: SEO-Metriken der Publisher-Domains aktualisieren (naechtlich) */
require_once __DIR__ . '/../config.php';
// API-Batch: DR/Traffic je Domain, Backoff bei 429 (gekuerzt)
