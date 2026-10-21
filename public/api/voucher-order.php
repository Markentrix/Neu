<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';
require __DIR__ . '/../../app/vouchers.php';

// PayPal-Order für einen Gutschein anlegen. Betrag wird serverseitig geprüft.
require_method('POST');
if (!paypal_enabled()) json_fail('Online-Gutscheine sind derzeit nicht verfügbar.', 503);
if (rate_limited('voucher-order', 20, 3600)) json_fail('Zu viele Versuche. Bitte später erneut probieren.', 429);
$amount = voucher_amount_ok(json_in()['amount'] ?? null);
$v = cfg()['vouchers'];
if ($amount === null) json_fail("Bitte einen Betrag zwischen {$v['min']} und {$v['max']} € wählen.");

try {
    $id = paypal_create_order((float)$amount, "GS-{$amount}", cfg()['salon']['name'] . " Gutschein über {$amount} €");
    json_out(['id' => $id]);
} catch (Throwable $e) {
    error_log((string)$e);
    json_fail('PayPal-Zahlung konnte nicht gestartet werden.', 502);
}
