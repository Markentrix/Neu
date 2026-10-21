<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';
require __DIR__ . '/../../app/vouchers.php';

// Gutschein nach PayPal-Zahlung ausstellen und per E-Mail verschicken.
require_method('POST');
$in = json_in();
if (rate_limited('voucher', 10, 3600)) json_fail('Zu viele Versuche.', 429);

$amount = voucher_amount_ok($in['amount'] ?? null);
$buyerName = clean_text($in['buyerName'] ?? '', 80);
$buyerEmail = mb_strtolower(clean_text($in['buyerEmail'] ?? '', 254));
$recipient = clean_text($in['recipient'] ?? '', 60);
$message = clean_text($in['message'] ?? '', 200);
$orderId = (string)($in['orderId'] ?? '');

if ($amount === null) json_fail('Ungültiger Betrag.');
if (mb_strlen($buyerName) < 2) json_fail('Bitte geben Sie Ihren Namen an.');
if (!filter_var($buyerEmail, FILTER_VALIDATE_EMAIL)) json_fail('Bitte geben Sie eine gültige E-Mail-Adresse an.');
if (($in['consent'] ?? false) !== true) json_fail('Bitte stimmen Sie der Datenverarbeitung zu.');
if (!paypal_enabled() || !preg_match('/^[A-Z0-9]{10,40}$/', $orderId)) json_fail('PayPal-Zahlung fehlt.');

try {
    $cap = paypal_capture($orderId);
} catch (Throwable $e) {
    error_log((string)$e);
    json_fail('Die PayPal-Zahlung konnte nicht abgeschlossen werden. Es wurde nichts abgebucht.', 402);
}
$valid = $cap['status'] === 'COMPLETED' && $cap['currency'] === 'EUR'
    && abs($cap['amount'] - $amount) < 0.005 && $cap['reference'] === "GS-{$amount}";
if (!$valid) {
    if ($cap['captureId']) { try { paypal_refund($cap['captureId']); } catch (Throwable $e) { error_log((string)$e); } }
    json_fail('Die Zahlung passte nicht zum Gutschein und wurde erstattet.', 402);
}

$v = [
    'id' => uuid(), 'amount' => $amount, 'balance' => $amount,
    'buyer_name' => $buyerName, 'buyer_email' => $buyerEmail,
    'recipient' => $recipient ?: null, 'message' => $message ?: null,
    'paypal_order' => $orderId, 'paypal_capture' => $cap['captureId'],
    'dl_token' => bin2hex(random_bytes(16)), 'valid_until' => voucher_valid_until(), 'created_at' => date('c'),
];
for ($i = 0; ; $i++) {
    $v['code'] = voucher_code();
    try {
        db()->prepare('INSERT INTO vouchers (id, code, amount, balance, buyer_name, buyer_email, recipient, message, paypal_order, paypal_capture, dl_token, valid_until, created_at)
            VALUES (:id, :code, :amount, :balance, :buyer_name, :buyer_email, :recipient, :message, :paypal_order, :paypal_capture, :dl_token, :valid_until, :created_at)')
            ->execute($v);
        break;
    } catch (PDOException $e) {
        if ($i < 3 && str_contains($e->getMessage(), 'vouchers.code')) continue; // Code-Kollision: neuer Versuch
        error_log((string)$e);
        try { paypal_refund($cap['captureId']); } catch (Throwable $e2) { error_log((string)$e2); }
        json_fail('Der Gutschein konnte nicht gespeichert werden. Ihre Zahlung wurde erstattet.', 500);
    }
}

$mailed = voucher_send($v);
json_out(['ok' => true, 'voucher' => [
    'code' => $v['code'], 'amount' => $amount, 'validUntil' => $v['valid_until'], 'mailed' => $mailed,
    'pdf' => '/gutschein-pdf?c=' . rawurlencode($v['code']) . '&t=' . $v['dl_token'],
]], 201);
