<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';
require __DIR__ . '/../../app/vouchers.php';

// Salon-Verwaltung: Login, Termine ansehen, Zeiten blockieren, Termine absagen.
admin_session();
$method = $_SERVER['REQUEST_METHOD'];
$action = (string)($_GET['action'] ?? '');

if ($action === 'login' && $method === 'POST') {
    if (rate_limited('admin-login', 8, 900)) json_fail('Zu viele Anmeldeversuche. Bitte 15 Minuten warten.', 429);
    $hash = cfg()['local']['adminPasswordHash'] ?? '';
    $pw = (string)(json_in()['password'] ?? '');
    if (!$hash || !password_verify($pw, $hash)) json_fail('Passwort falsch.', 401);
    session_regenerate_id(true);
    $_SESSION['admin'] = true;
    $_SESSION['admin_until'] = time() + 8 * 3600;
    json_out(['ok' => true, 'csrf' => csrf_token()]);
}

if ($action === 'logout') {
    $_SESSION = [];
    session_destroy();
    json_out(['ok' => true]);
}

if (!is_admin()) json_fail('Nicht angemeldet.', 401);
if ($method !== 'GET' && !hash_equals(csrf_token(), (string)($_SERVER['HTTP_X_CSRF_TOKEN'] ?? ''))) json_fail('Sitzung abgelaufen – bitte neu laden.', 403);

// ---------- Gutscheine ----------
if ($action === 'vouchers' && $method === 'GET') {
    $q = strtoupper(trim((string)($_GET['q'] ?? '')));
    if ($q !== '') {
        $st = db()->prepare('SELECT * FROM vouchers WHERE code LIKE ? OR upper(buyer_name) LIKE ? OR upper(recipient) LIKE ? ORDER BY created_at DESC LIMIT 50');
        $like = '%' . $q . '%';
        $st->execute([$like, $like, $like]);
    } else {
        $st = db()->query('SELECT * FROM vouchers ORDER BY created_at DESC LIMIT 50');
    }
    $rows = $st->fetchAll();
    $red = db()->prepare('SELECT amount, note, created_at FROM voucher_redemptions WHERE voucher_id = ? ORDER BY created_at');
    foreach ($rows as &$r) {
        unset($r['dl_token']);
        $red->execute([$r['id']]);
        $r['redemptions'] = $red->fetchAll();
        $r['expired'] = $r['valid_until'] < today();
    }
    json_out(['vouchers' => $rows, 'csrf' => csrf_token()]);
}

if ($action === 'redeem' && $method === 'POST') {
    $in = json_in();
    $amount = round((float)($in['amount'] ?? 0), 2);
    if ($amount <= 0) json_fail('Bitte einen Betrag eingeben.');
    $pdo = db();
    $pdo->exec('BEGIN IMMEDIATE');
    $v = voucher_find((string)($in['code'] ?? ''));
    if (!$v) { $pdo->exec('ROLLBACK'); json_fail('Gutschein nicht gefunden.', 404); }
    if ($v['status'] === 'redeemed') { $pdo->exec('ROLLBACK'); json_fail('Dieser Gutschein ist bereits vollständig eingelöst.', 409); }
    if ($v['status'] !== 'active') { $pdo->exec('ROLLBACK'); json_fail('Dieser Gutschein ist nicht mehr gültig.', 409); }
    if ($amount > (float)$v['balance'] + 0.001) { $pdo->exec('ROLLBACK'); json_fail('Der Betrag ist höher als das Restguthaben (' . euro((float)$v['balance'], true) . ').', 409); }
    $pdo->prepare('INSERT INTO voucher_redemptions (voucher_id, amount, note, created_at) VALUES (?, ?, ?, ?)')
        ->execute([$v['id'], $amount, clean_text($in['note'] ?? '', 120), date('c')]);
    $balance = round((float)$v['balance'] - $amount, 2);
    $pdo->prepare('UPDATE vouchers SET balance = ?, status = ? WHERE id = ?')->execute([$balance, $balance <= 0 ? 'redeemed' : 'active', $v['id']]);
    $pdo->exec('COMMIT');
    json_out(['ok' => true, 'balance' => $balance]);
}

if ($action === 'resend' && $method === 'POST') {
    $v = voucher_find((string)(json_in()['code'] ?? ''));
    if (!$v) json_fail('Gutschein nicht gefunden.', 404);
    json_out(['ok' => voucher_send($v, false)]);
}

if ($method === 'GET') {
    $from = (string)($_GET['from'] ?? today());
    $days = max(1, min(31, (int)($_GET['days'] ?? 7)));
    if (!valid_date($from)) json_fail('Ungültiges Datum.');
    $st = db()->prepare('SELECT * FROM entries WHERE date >= ? AND date <= ? ORDER BY date, start_min');
    $st->execute([$from, add_days($from, $days - 1)]);
    $rows = array_map(function ($r) {
        unset($r['cancel_token']);
        $r['time'] = to_time((int)$r['start_min']);
        $r['services'] = json_decode($r['services'], true) ?: [];
        return $r;
    }, $st->fetchAll());
    json_out(['entries' => $rows, 'csrf' => csrf_token()]);
}

if ($method === 'POST') {
    // Zeitraum blockieren (Pause, Telefon-Termin, Urlaub …)
    $in = json_in();
    $start = to_minutes($in['time'] ?? null);
    $duration = (int)($in['duration'] ?? 0);
    if (!valid_date($in['date'] ?? null) || $start === null || $duration < 5 || $duration > 720) json_fail('Ungültige Angaben.');
    $id = uuid();
    db()->prepare("INSERT INTO entries (id, type, status, date, start_min, duration, name, note, created_at) VALUES (?, 'block', 'confirmed', ?, ?, ?, ?, ?, ?)")
        ->execute([$id, $in['date'], $start, $duration, clean_text($in['name'] ?? '', 80), clean_text($in['note'] ?? '', 200), date('c')]);
    json_out(['ok' => true, 'id' => $id], 201);
}

if ($method === 'DELETE') {
    $id = (string)($_GET['id'] ?? '');
    $st = db()->prepare('SELECT * FROM entries WHERE id = ?');
    $st->execute([$id]);
    $entry = $st->fetch();
    if (!$entry) json_fail('Nicht gefunden.', 404);
    if ($entry['type'] === 'block') {
        db()->prepare('DELETE FROM entries WHERE id = ?')->execute([$id]);
        json_out(['ok' => true]);
    }
    $refunded = (int)$entry['refunded'];
    if (($_GET['refund'] ?? '') === '1' && $entry['paypal_capture'] && !$refunded) {
        try {
            paypal_refund($entry['paypal_capture']);
            $refunded = 1;
        } catch (Throwable $e) {
            error_log((string)$e);
            json_fail('Erstattung fehlgeschlagen – bitte im PayPal-Konto prüfen.', 502);
        }
    }
    db()->prepare("UPDATE entries SET status = 'cancelled', cancelled_at = ?, cancelled_by = 'salon', refunded = ? WHERE id = ?")
        ->execute([date('c'), $refunded, $id]);
    if (($_GET['notify'] ?? '') === '1') {
        send_mail($entry['email'], 'Ihr Termin bei ' . cfg()['salon']['name'] . ' wurde abgesagt',
            '<p>Hallo ' . e($entry['name']) . ',</p><p>leider müssen wir Ihren Termin am ' . e(german_date($entry['date'])) . ' um ' . to_time((int)$entry['start_min'])
            . ' Uhr absagen. ' . ($refunded ? 'Ihre Zahlung wird vollständig erstattet. ' : '')
            . 'Bitte buchen Sie einen neuen Termin online oder rufen Sie uns an: ' . e(cfg()['salon']['phoneDisplay']) . '.</p>');
    }
    json_out(['ok' => true]);
}

json_fail('Methode nicht erlaubt.', 405);
