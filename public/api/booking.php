<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';

require_method('POST');
$in = json_in();
if (!empty($in['website'])) json_out(['ok' => true]); // Honeypot: Bots stillschweigend ignorieren
if (rate_limited('booking', 10, 3600)) json_fail('Zu viele Buchungsversuche. Bitte rufen Sie uns an.', 429);

$customer = [
    'name'  => clean_text($in['name'] ?? '', 80),
    'phone' => clean_text($in['phone'] ?? '', 25),
    'email' => mb_strtolower(clean_text($in['email'] ?? '', 254)),
    'note'  => clean_text($in['note'] ?? '', 500),
];
if (mb_strlen($customer['name']) < 2) json_fail('Bitte geben Sie Ihren Namen an.');
if (!preg_match('/^[+()\d\s\/-]{6,25}$/', $customer['phone'])) json_fail('Bitte geben Sie eine gültige Telefonnummer an.');
if (!filter_var($customer['email'], FILTER_VALIDATE_EMAIL)) json_fail('Bitte geben Sie eine gültige E-Mail-Adresse an.');
if (($in['consent'] ?? false) !== true) json_fail('Bitte stimmen Sie der Datenverarbeitung zu.');

$check = check_slot($in);
if (isset($check['error'])) json_fail($check['error'], $check['status']);
$summary = $check['summary'];
$date = $in['date'];
$time = $in['time'];

$payment = ['method' => 'onsite', 'amount' => 0.0, 'order' => null, 'capture' => null];
if (($in['payment'] ?? '') === 'paypal') {
    $orderId = (string)($in['orderId'] ?? '');
    if (!paypal_enabled() || !preg_match('/^[A-Z0-9]{10,40}$/', $orderId)) json_fail('PayPal-Zahlung fehlt.');
    try {
        $cap = paypal_capture($orderId);
    } catch (Throwable $e) {
        error_log((string)$e);
        json_fail('Die PayPal-Zahlung konnte nicht abgeschlossen werden. Es wurde nichts abgebucht.', 402);
    }
    $valid = $cap['status'] === 'COMPLETED' && $cap['currency'] === 'EUR'
        && abs($cap['amount'] - $summary['payNow']) < 0.005
        && $cap['reference'] === "{$date} {$time}";
    if (!$valid) {
        if ($cap['captureId']) { try { paypal_refund($cap['captureId']); } catch (Throwable $e) { error_log((string)$e); } }
        json_fail('Die Zahlung passte nicht zur Buchung und wurde erstattet.', 402);
    }
    $payment = ['method' => 'paypal', 'amount' => $cap['amount'], 'order' => $orderId, 'capture' => $cap['captureId']];
}

// Erneut prüfen und speichern – in einer exklusiven Transaktion gegen Doppelbuchungen
$pdo = db();
$id = uuid();
$token = rtrim(strtr(base64_encode(random_bytes(18)), '+/', '-_'), '=');
$pdo->exec('BEGIN IMMEDIATE');
try {
    if (!in_array($time, free_slots($date, $summary['duration'], busy_ranges($date)), true)) {
        $pdo->exec('ROLLBACK');
        if ($payment['capture']) {
            try { paypal_refund($payment['capture']); } catch (Throwable $e) { error_log((string)$e); }
            json_fail('Der Termin wurde während der Zahlung vergeben. Ihre Zahlung wurde vollständig erstattet.', 409);
        }
        json_fail('Dieser Termin ist leider nicht mehr frei. Bitte wählen Sie eine andere Uhrzeit.', 409);
    }
    $services = array_map(fn($s) => ['id' => $s['id'], 'name' => $s['fullName'], 'price' => $s['price'], 'from' => $s['from'] || $s['consult']], $summary['items']);
    $pdo->prepare('INSERT INTO entries (id, type, status, date, start_min, duration, services, price_estimate, name, phone, email, note,
        pay_method, pay_amount, paypal_order, paypal_capture, cancel_token, created_at, review_optin, followup_optin)
        VALUES (?, \'booking\', \'confirmed\', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        ->execute([$id, $date, to_minutes($time), $summary['duration'], json_encode($services, JSON_UNESCAPED_UNICODE), $summary['price'],
            $customer['name'], $customer['phone'], $customer['email'], $customer['note'],
            $payment['method'], $payment['amount'], $payment['order'], $payment['capture'], $token, date('c'),
            ($in['reviewOptin'] ?? false) === true && !empty(cfg()['salon']['reviewUrl']) ? 1 : 0,
            ($in['followupOptin'] ?? false) === true ? 1 : 0]);
    $pdo->exec('COMMIT');
} catch (Throwable $e) {
    if ($pdo->inTransaction()) $pdo->exec('ROLLBACK');
    error_log((string)$e);
    if ($payment['capture']) { try { paypal_refund($payment['capture']); } catch (Throwable $e2) { error_log((string)$e2); } }
    json_fail('Die Buchung konnte nicht gespeichert werden. Bitte rufen Sie uns an.', 500);
}

// Bestätigungen
$s = cfg()['salon'];
$cancelUrl = site_url('/termin-stornieren?id=' . rawurlencode($id) . '&t=' . $token);
$list = implode('', array_map(fn($x) => '<li>' . e($x['name']) . ' – ' . ($x['from'] ? ($x['price'] > 0 ? 'ab ' . euro((float)$x['price']) : 'nach Beratung') : euro((float)$x['price'])) . '</li>', $services));
$paid = $payment['amount'] > 0 ? '<p>Online bezahlt (PayPal): <strong>' . euro($payment['amount'], true) . '</strong></p>' : '<p>Zahlung vor Ort (bar oder Karte).</p>';
$when = german_date($date) . ", {$time} Uhr";

send_mail($customer['email'], "Terminbestätigung {$s['name']} – {$when}",
    '<p>Hallo ' . e($customer['name']) . ',</p><p>vielen Dank für Ihre Buchung! Wir freuen uns auf Sie am <strong>' . e($when) . '</strong>.</p>'
    . "<ul>{$list}</ul>{$paid}"
    . '<p>' . e("{$s['name']} · {$s['street']} · {$s['zip']} {$s['city']}-{$s['district']} · Tel. {$s['phoneDisplay']}") . '</p>'
    . '<p>Termin verhindert? Bis ' . cfg()['booking']['freeCancelHours'] . ' Stunden vorher kostenfrei <a href="' . e($cancelUrl) . '">online stornieren</a>.</p>');

send_mail(cfg()['local']['mail']['salonEmail'] ?? null, "Neue Buchung: {$when} – {$customer['name']}",
    '<p><strong>' . e($customer['name']) . '</strong> · ' . e($customer['phone']) . ' · ' . e($customer['email']) . '</p>'
    . "<ul>{$list}</ul>{$paid}<p>Dauer: {$summary['duration']} Min.</p><p>Notiz: " . (e($customer['note']) ?: '–') . '</p>',
    $customer['email']);

json_out(['ok' => true, 'booking' => [
    'date' => $date, 'time' => $time, 'duration' => $summary['duration'],
    'services' => $services, 'paid' => $payment['amount'],
]], 201);
