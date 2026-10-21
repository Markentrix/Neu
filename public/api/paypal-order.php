<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';

// Legt eine PayPal-Order an. Der Betrag wird ausschließlich serverseitig berechnet.
require_method('POST');
if (!paypal_enabled()) json_fail('PayPal ist derzeit nicht verfügbar.', 503);
if (rate_limited('paypal-order', 20, 3600)) json_fail('Zu viele Versuche. Bitte später erneut probieren.', 429);

$in = json_in();
$check = check_slot($in);
if (isset($check['error'])) json_fail($check['error'], $check['status']);
$summary = $check['summary'];
if ($summary['payNow'] <= 0) json_fail('Für diese Auswahl ist keine Online-Zahlung nötig.');

try {
    $names = implode(', ', array_column($summary['items'], 'fullName'));
    $id = paypal_create_order($summary['payNow'], "{$in['date']} {$in['time']}", cfg()['salon']['name'] . " {$in['date']} {$in['time']}: {$names}");
    json_out(['id' => $id]);
} catch (Throwable $e) {
    error_log((string)$e);
    json_fail('PayPal-Zahlung konnte nicht gestartet werden.', 502);
}
