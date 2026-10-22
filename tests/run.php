<?php
declare(strict_types=1);

// Testsuite für Website und Buchungsdienst – nur PHP nötig:
//   php tests/run.php
// Arbeitet mit eigener Test-Datenbank in einem Temp-Ordner; echte Termine bleiben unberührt.
// Exit-Code 0 = alles in Ordnung (deploy/update.sh bricht sonst ab).

if (PHP_SAPI !== 'cli') exit(1);
$root = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/ajtest-' . bin2hex(random_bytes(4));
mkdir($tmp . '/data', 0777, true);
$port = random_int(20000, 40000);
$base = "http://127.0.0.1:{$port}";
$password = 'test-passwort-' . bin2hex(random_bytes(3));

file_put_contents("{$tmp}/config.local.php", '<?php return ' . var_export([
    'siteUrl' => $base,
    'adminPasswordHash' => password_hash($password, PASSWORD_DEFAULT),
    'paypal' => ['env' => 'sandbox', 'clientId' => '', 'clientSecret' => ''],
    'mail' => ['from' => '', 'salonEmail' => ''],
    'alertEmail' => '',
    'databasePath' => "{$tmp}/data/bookings.sqlite",
], true) . ';');
putenv("AJ_LOCAL_CONFIG={$tmp}/config.local.php");

require $root . '/app/lib.php';
require $root . '/app/vouchers.php';

// ---------- Mini-Testrahmen ----------
$passed = 0;
$failed = [];
function check(string $name, bool $ok, string $detail = ''): void
{
    global $passed, $failed;
    if ($ok) {
        $passed++;
        echo "  ✓ {$name}\n";
    } else {
        $failed[] = $name;
        echo "  ✗ {$name}" . ($detail !== '' ? " – {$detail}" : '') . "\n";
    }
}
function section(string $t): void { echo "\n{$t}\n"; }

$cookies = '';
function http(string $method, string $path, ?array $json = null, array $headers = []): array
{
    global $base, $cookies;
    $h = array_merge(['Content-Type: application/json'], $headers, $cookies ? ["Cookie: {$cookies}"] : []);
    $ctx = stream_context_create(['http' => [
        'method' => $method, 'header' => implode("\r\n", $h), 'ignore_errors' => true, 'timeout' => 20,
        'follow_location' => 0, 'content' => $json === null ? '' : json_encode($json),
    ]]);
    $body = @file_get_contents($base . $path, false, $ctx);
    $status = 0;
    $type = '';
    foreach ($http_response_header ?? [] as $line) {
        if (preg_match('#^HTTP/\S+ (\d+)#', $line, $m)) $status = (int)$m[1];
        if (stripos($line, 'Content-Type:') === 0) $type = trim(substr($line, 13));
        if (stripos($line, 'Set-Cookie:') === 0 && preg_match('/^Set-Cookie:\s*([^;]+)/i', $line, $m)) $cookies = $m[1];
    }
    return [$status, $body === false ? '' : $body, json_decode((string)$body, true), $type];
}

// ---------- 1. Logik ohne Server ----------
section('Öffnungszeiten, Feiertage, Preise');
$h = holidays(2026);
check('Karfreitag 2026 = 03.04.', isset($h['2026-04-03']));
check('Pfingstmontag 2026 = 25.05.', isset($h['2026-05-25']));
check('Reformationstag (Niedersachsen)', isset($h['2026-10-31']));
check('Sonntag geschlossen', opening_for('2026-11-01') === null);
check('Montag geschlossen', opening_for('2026-11-02') === null);
check('Dienstag 10–18 Uhr', opening_for('2026-11-03') === [600, 1080]);
check('Samstag 10–14 Uhr', opening_for('2026-11-07') === [600, 840]);
$sum = summarize(['h-schnitt', 'h-bart']);
check('Herrenschnitt + Bart = 65 € / 55 Min.', $sum && $sum['price'] == 65.0 && $sum['duration'] === 55);
check('Balayage: Anzahlung 50 €', summarize(['f-balayage'])['payNow'] == 50.0);
check('Unbekannte Leistung wird abgelehnt', summarize(['gibts-nicht']) === null);
check('Mehr als 5 Leistungen werden abgelehnt', summarize(['d-wsf-kurz', 'h-bart', 'f-glossing', 'b-zupfen', 'b-faerben', 'b-wimpern']) === null);
$future = null;
for ($i = 3; $i < 40 && !$future; $i++) if (opening_for(add_days(today(), $i))) $future = add_days(today(), $i);
$slots = free_slots($future, 60, [[600, 660]]);
check('Belegte Zeit 10–11 Uhr blockiert 10:00 und 10:45', !in_array('10:00', $slots, true) && !in_array('10:45', $slots, true));
check('11:00 direkt danach ist frei', in_array('11:00', $slots, true));
check('Termin muss vor Ladenschluss enden', !in_array(to_time(opening_for($future)[1] - 45), $slots, true));

section('Gutscheine');
check('Code-Format AJ-XXXX-XXXX', (bool)preg_match('/^AJ-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$/', voucher_code()));
check('Betrag 50 € erlaubt', voucher_amount_ok(50) === 50);
check('Betrag 5 € abgelehnt', voucher_amount_ok(5) === null);
check('Betrag 12,5 € abgelehnt', voucher_amount_ok(12.5) === null);
$pdf = voucher_pdf(['code' => 'AJ-TEST-TEST', 'amount' => 75, 'recipient' => 'Jörg Müller', 'message' => 'Alles Gute!', 'valid_until' => voucher_valid_until()]);
preg_match('/startxref\n(\d+)/', $pdf, $m);
check('Gutschein-PDF gültig aufgebaut', str_starts_with($pdf, '%PDF-1.4') && str_ends_with($pdf, "%%EOF\n") && substr($pdf, (int)($m[1] ?? 0), 4) === 'xref');

// ---------- 2. Server starten ----------
section('Testserver');
$cmd = sprintf('AJ_LOCAL_CONFIG=%s exec php -S 127.0.0.1:%d -t %s %s',
    escapeshellarg("{$tmp}/config.local.php"), $port, escapeshellarg("{$root}/public"), escapeshellarg("{$root}/dev-router.php"));
$proc = proc_open($cmd, [1 => ['file', "{$tmp}/server.log", 'a'], 2 => ['file', "{$tmp}/server.log", 'a']], $pipes);
register_shutdown_function(function () use ($proc, $tmp) {
    if (is_resource($proc)) proc_terminate($proc);
    exec('rm -rf ' . escapeshellarg($tmp));
});
for ($i = 0; $i < 50 && !@fsockopen('127.0.0.1', $port); $i++) usleep(100000);
check('Server gestartet', (bool)@fsockopen('127.0.0.1', $port));

section('Seiten');
foreach (['/' => 200, '/preise' => 200, '/termin' => 200, '/leistungen/balayage' => 200, '/gutscheine' => 200, '/ratgeber' => 200, '/gibtsnicht' => 404] as $p => $want) {
    [$st] = http('GET', $p);
    check("{$p} → {$want}", $st === $want, "erhalten {$st}");
}
[$st, , , ] = http('GET', '/preise.php');
[$st2, $body] = http('GET', '/sitemap.xml');
check('Sitemap enthält mindestens 20 Seiten', substr_count($body, '<loc>') >= 20);
[$st, , $cfg] = http('GET', '/api/booking-config.php');
check('Live-Konfiguration liefert buchbare Tage', $st === 200 && count($cfg['days'] ?? []) > 30);

section('Buchung');
[$st, , $av] = http('GET', "/api/availability.php?date={$future}&services=h-schnitt");
$t1 = $av['slots'][0] ?? null;
check('Freie Zeiten werden geliefert', $st === 200 && $t1 !== null);
$booking = ['services' => ['h-schnitt'], 'date' => $future, 'time' => $t1, 'name' => 'Test Kunde', 'phone' => '0511 123456',
    'email' => 'kunde@example.org', 'consent' => true, 'payment' => 'onsite', 'followupOptin' => true];
[$st, , $res] = http('POST', '/api/booking.php', $booking);
check('Buchung wird angenommen', $st === 201 && ($res['ok'] ?? false));
[$st] = http('POST', '/api/booking.php', $booking);
check('Gleicher Termin ein zweites Mal → abgelehnt (409)', $st === 409);
[$st] = http('POST', '/api/booking.php', ['time' => to_time(to_minutes($t1) + 15)] + $booking);
check('Überlappender Termin → abgelehnt (409)', $st === 409);
[$st] = http('POST', '/api/booking.php', ['email' => 'kein-mail'] + $booking);
check('Ungültige E-Mail → 400', $st === 400);
[$st] = http('POST', '/api/booking.php', ['consent' => false] + $booking);
check('Ohne Einwilligung → 400', $st === 400);
$before = (int)db()->query("SELECT COUNT(*) FROM entries")->fetchColumn();
[$st] = http('POST', '/api/booking.php', ['website' => 'spam', 'time' => $av['slots'][8] ?? $t1] + $booking);
check('Bot (Honeypot) wird still verworfen', $st === 200 && (int)db()->query("SELECT COUNT(*) FROM entries")->fetchColumn() === $before);
$row = db()->query("SELECT * FROM entries WHERE type = 'booking' ORDER BY created_at DESC LIMIT 1")->fetch();
check('Folgetermin-Einwilligung gespeichert', (int)$row['followup_optin'] === 1);
[$st, , $av2] = http('GET', "/api/availability.php?date={$future}&services=h-schnitt");
check('Gebuchte Zeit ist nicht mehr frei', !in_array($t1, $av2['slots'] ?? [], true));

section('Storno');
[$st] = http('POST', '/api/cancel.php', ['id' => $row['id'], 't' => 'falsch']);
check('Falscher Storno-Link → 404', $st === 404);
[$st, , $res] = http('POST', '/api/cancel.php', ['id' => $row['id'], 't' => $row['cancel_token']]);
check('Storno mit gültigem Link', $st === 200 && ($res['ok'] ?? false));
[$st, , $av3] = http('GET', "/api/availability.php?date={$future}&services=h-schnitt");
check('Stornierte Zeit ist wieder frei', in_array($t1, $av3['slots'] ?? [], true));

section('Verwaltung');
[$st] = http('GET', "/api/admin.php?from={$future}");
check('Ohne Anmeldung → 401', $st === 401);
[$st] = http('POST', '/api/admin.php?action=login', ['password' => 'falsch']);
check('Falsches Passwort → 401', $st === 401);
[$st, , $login] = http('POST', '/api/admin.php?action=login', ['password' => $password]);
check('Anmeldung', $st === 200 && !empty($login['csrf']));
[$st, , $list] = http('GET', "/api/admin.php?from={$future}&days=1");
check('Termine werden angezeigt', $st === 200 && count($list['entries'] ?? []) >= 1);
[$st] = http('POST', '/api/admin.php', ['date' => $future, 'time' => '12:00', 'duration' => 60]);
check('Blocken ohne Sicherheitstoken → 403', $st === 403);
[$st] = http('POST', '/api/admin.php', ['date' => $future, 'time' => '12:00', 'duration' => 60, 'note' => 'Pause'], ['X-CSRF-Token: ' . $login['csrf']]);
check('Zeit blocken', $st === 201);
[$st, , $av4] = http('GET', "/api/availability.php?date={$future}&services=h-bart");
check('Geblockte Zeit ist nicht buchbar', !in_array('12:00', $av4['slots'] ?? [], true) && !in_array('12:45', $av4['slots'] ?? [], true));

section('Gutscheine (Server)');
[$st] = http('POST', '/api/voucher-order.php', ['amount' => 50]);
check('Ohne PayPal-Zugang → 503 statt Fehlbuchung', $st === 503);
$v = ['id' => uuid(), 'code' => voucher_code(), 'amount' => 100, 'balance' => 100, 'buyer_name' => 'Test', 'buyer_email' => 't@example.org',
    'recipient' => null, 'message' => null, 'paypal_order' => 'TEST' . bin2hex(random_bytes(4)), 'paypal_capture' => 'CAP', 'dl_token' => bin2hex(random_bytes(16)),
    'valid_until' => voucher_valid_until(), 'created_at' => date('c')];
db()->prepare('INSERT INTO vouchers (id, code, amount, balance, buyer_name, buyer_email, recipient, message, paypal_order, paypal_capture, dl_token, valid_until, created_at)
    VALUES (:id, :code, :amount, :balance, :buyer_name, :buyer_email, :recipient, :message, :paypal_order, :paypal_capture, :dl_token, :valid_until, :created_at)')->execute($v);
$csrf = ['X-CSRF-Token: ' . $login['csrf']];
[$st, , $r1] = http('POST', '/api/admin.php?action=redeem', ['code' => $v['code'], 'amount' => 60], $csrf);
check('Teilbetrag einlösen → Rest 40 €', $st === 200 && abs(($r1['balance'] ?? 0) - 40) < 0.01);
[$st] = http('POST', '/api/admin.php?action=redeem', ['code' => $v['code'], 'amount' => 50], $csrf);
check('Mehr als Restguthaben → abgelehnt', $st === 409);
[$st] = http('POST', '/api/admin.php?action=redeem', ['code' => $v['code'], 'amount' => 40], $csrf);
[$st2] = http('POST', '/api/admin.php?action=redeem', ['code' => $v['code'], 'amount' => 1], $csrf);
check('Vollständig eingelöst → keine weitere Einlösung', $st === 200 && $st2 === 409);
[$st, , , $type] = http('GET', '/gutschein-pdf?c=' . $v['code'] . '&t=' . $v['dl_token']);
check('Gutschein-PDF herunterladbar', $st === 200 && str_starts_with($type, 'application/pdf'));
[$st] = http('GET', '/gutschein-pdf?c=' . $v['code'] . '&t=falsch');
check('PDF mit falschem Link → 404', $st === 404);

section('Kontaktformular');
[$st] = http('POST', '/api/contact.php', ['name' => 'Test', 'email' => 't@example.org', 'message' => 'Hallo, eine Frage.', 'consent' => false]);
check('Ohne Einwilligung → 400', $st === 400);
[$st] = http('POST', '/api/contact.php', ['name' => 'Test', 'email' => 't@example.org', 'message' => 'Hallo, eine Frage.', 'consent' => true]);
check('Ohne Salon-Adresse → 503 mit Telefonhinweis', $st === 503);

section('Erinnerungen (Cron)');
$ins = db()->prepare("INSERT INTO entries (id, type, status, date, start_min, duration, services, name, phone, email, cancel_token, created_at, followup_optin)
    VALUES (?, 'booking', 'confirmed', ?, ?, 40, ?, ?, '0511 1', ?, 'tok', ?, ?)");
$soon = time() + 20 * 3600;
$herren = json_encode([['id' => 'h-schnitt', 'name' => 'Herrenschnitt', 'price' => 45, 'from' => false]]);
$ids = ['rem' => uuid(), 'fu' => uuid(), 'fu_skip' => uuid(), 'fu_later' => uuid(), 'fresh' => uuid()];
$old = date('c', time() - 10 * 86400);
$ins->execute([$ids['rem'], date('Y-m-d', $soon), (int)date('G', $soon) * 60, $herren, 'Erinnerung', 'a@example.org', $old, 0]);
$ins->execute([$ids['fresh'], date('Y-m-d', $soon), (int)date('G', $soon) * 60, $herren, 'Gerade gebucht', 'f@example.org', date('c'), 0]);
$ins->execute([$ids['fu'], add_days(today(), -30), 600, $herren, 'Folgetermin', 'b@example.org', $old, 1]);
$ins->execute([$ids['fu_skip'], add_days(today(), -30), 600, $herren, 'Hat neuen Termin', 'c@example.org', $old, 1]);
$ins->execute([$ids['fu_later'], add_days(today(), 5), 600, $herren, 'Hat neuen Termin', 'c@example.org', $old, 0]);
exec(sprintf('AJ_LOCAL_CONFIG=%s AJ_IGNORE_HOURS=1 php %s 2>&1', escapeshellarg("{$tmp}/config.local.php"), escapeshellarg("{$root}/app/cron.php")), $out, $rc);
check('Cron läuft fehlerfrei', $rc === 0, implode(' | ', $out));
$get = fn(string $id, string $col) => db()->query("SELECT {$col} FROM entries WHERE id = " . db()->quote($id))->fetchColumn();
check('Terminerinnerung für morgen versucht', $get($ids['rem'], 'reminder_sent_at') !== null);
check('Keine Erinnerung bei ganz frischer Buchung', $get($ids['fresh'], 'reminder_sent_at') === null);
check('Folgetermin-Erinnerung nach 4 Wochen (Herrenschnitt) versucht', $get($ids['fu'], 'followup_sent_at') !== null && !str_starts_with((string)$get($ids['fu'], 'followup_sent_at'), 'entfällt'));
check('Keine Folgetermin-Mail, wenn schon neuer Termin gebucht', str_starts_with((string)$get($ids['fu_skip'], 'followup_sent_at'), 'entfällt'));
exec(sprintf('AJ_LOCAL_CONFIG=%s AJ_IGNORE_HOURS=1 php %s 2>&1', escapeshellarg("{$tmp}/config.local.php"), escapeshellarg("{$root}/app/cron.php")), $out2);
check('Zweiter Lauf verschickt nichts doppelt', count($out2) === 0, implode(' | ', $out2));

section('Überwachung');
[$st, , $health] = http('GET', '/api/health.php');
check('Statusseite antwortet', in_array($st, [200, 503], true) && isset($health['checks']));
check('Datenbank & Speicher in Ordnung', ($health['checks']['database'] ?? false) && ($health['checks']['disk'] ?? false));
check('Cron-Lebenszeichen erkannt', $health['checks']['cron'] ?? false);
check('Fehlender Mailzugang wird gemeldet (503)', $st === 503 && ($health['checks']['mail_configured'] ?? true) === false);

section('Statische Seiten (dist)');
exec(sprintf('php %s --url=%s --out=%s 2>&1', escapeshellarg("{$root}/tools/build-static.php"), escapeshellarg('https://example.org'), escapeshellarg("{$tmp}/dist")), $bout, $brc);
check('Build läuft durch', $brc === 0, implode(' | ', $bout));
foreach (['index.html', 'preise.html', 'termin.html', 'leistungen/balayage.html', '404.html', 'sitemap.xml', 'css/styles.css', 'js/main.js'] as $f) {
    check("dist/{$f} vorhanden", is_file("{$tmp}/dist/{$f}"));
}
$idx = (string)@file_get_contents("{$tmp}/dist/index.html");
check('Canonical zeigt auf die angegebene Domain', str_contains($idx, '<link rel="canonical" href="https://example.org/">'));
check('Keine PHP-Reste in den Seiten', !preg_match('/<\?php|Warning:|Fatal error|Notice:/', $idx . @file_get_contents("{$tmp}/dist/termin.html")));

$log = (string)@file_get_contents("{$tmp}/server.log");
check('Keine PHP-Warnungen im Serverprotokoll', !preg_match('/(Warning|Fatal|Deprecated|Notice):/', $log), mb_substr($log, 0, 300));

echo "\n" . ($failed ? '✗ ' . count($failed) . " Test(s) fehlgeschlagen, {$passed} bestanden\n" : "✓ Alle {$passed} Tests bestanden\n");
exit($failed ? 1 : 0);
