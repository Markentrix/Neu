<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';

// Zustand des Buchungsdienstes für die Überwachung (deploy/monitor.sh).
// Gibt nur Ja/Nein-Werte heraus, keine Daten.
header('X-Robots-Tag: noindex');
$checks = [];
$local = cfg()['local'];
$dataDir = dirname($local['databasePath'] ?? __DIR__ . '/../../app/data/x');

try {
    db()->query('SELECT 1')->fetchColumn();
    $checks['database'] = is_writable($dataDir);
} catch (Throwable $e) {
    $checks['database'] = false;
}
$checks['disk'] = (@disk_free_space($dataDir) ?: 0) > 200 * 1024 * 1024;
$checks['config'] = !empty($local['siteUrl']) && !empty($local['adminPasswordHash']);
$checks['mail_configured'] = !empty($local['mail']['from']) && (!empty($local['mail']['smtp']['host']) || function_exists('mail'));
try {
    $st = db()->prepare('SELECT COUNT(*) FROM mail_failures WHERE at > ?');
    $st->execute([time() - 3600]);
    $checks['mail_ok_last_hour'] = (int)$st->fetchColumn() === 0;
} catch (Throwable $e) {
    $checks['mail_ok_last_hour'] = false;
}
$beat = (int)@file_get_contents($dataDir . '/cron-heartbeat');
$checks['cron'] = $beat > time() - 2 * 3600;

$ok = !in_array(false, $checks, true);
json_out(['ok' => $ok, 'checks' => $checks, 'time' => date('c')], $ok ? 200 : 503);
