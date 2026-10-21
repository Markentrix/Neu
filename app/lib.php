<?php
declare(strict_types=1);

// Gemeinsame Funktionen für Website, Buchungs-API und Verwaltung.

function cfg(): array
{
    static $cfg = null;
    if ($cfg === null) {
        $cfg = require __DIR__ . '/config.php';
        $local = __DIR__ . '/config.local.php';
        $cfg['local'] = is_file($local) ? require $local : require __DIR__ . '/config.local.example.php';
        date_default_timezone_set($cfg['booking']['timezone']);
    }
    return $cfg;
}

function e(?string $s): string
{
    return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function site_url(string $path = '/'): string
{
    return rtrim(cfg()['local']['siteUrl'] ?? '', '/') . $path;
}

function euro(float $n, bool $decimals = false): string
{
    return number_format($n, $decimals || fmod($n, 1.0) !== 0.0 ? 2 : 0, ',', '.') . ' €';
}

// ---------- Leistungen ----------

function services(): array
{
    static $map = null;
    if ($map === null) {
        $map = [];
        foreach (cfg()['categories'] as $cat) {
            foreach ($cat['services'] as $s) {
                $s['category'] = $cat['id'];
                $s['fullName'] = $s['bookingName'] ?? (isset($s['group']) ? "{$s['group']} – {$s['name']}" : $s['name']);
                $s['from'] = !empty($s['from']);
                $s['consult'] = !empty($s['consult']);
                $map[$s['id']] = $s;
            }
        }
    }
    return $map;
}

function online_amount(array $s): float
{
    if ($s['consult']) return 0.0;
    return (float)($s['from'] ? $s['deposit'] : $s['price']);
}

/** Fasst gewählte Leistungen zusammen oder liefert null bei ungültiger Auswahl. */
function summarize(array $ids): ?array
{
    $ids = array_values(array_unique(array_map('strval', $ids)));
    if (!$ids || count($ids) > cfg()['booking']['maxServices']) return null;
    $all = services();
    $items = [];
    foreach ($ids as $id) {
        if (!isset($all[$id])) return null;
        $items[] = $all[$id];
    }
    return [
        'items'    => $items,
        'duration' => array_sum(array_column($items, 'duration')),
        'price'    => (float)array_sum(array_column($items, 'price')),
        'hasFrom'  => (bool)array_filter($items, fn($s) => $s['from'] || $s['consult']),
        'payNow'   => array_sum(array_map('online_amount', $items)),
    ];
}

// ---------- Zeit, Feiertage, Öffnungszeiten ----------

function to_minutes(?string $t): ?int
{
    return ($t !== null && preg_match('/^([01]\d|2[0-3]):([0-5]\d)$/', $t, $m)) ? (int)$m[1] * 60 + (int)$m[2] : null;
}

function to_time(int $m): string
{
    return sprintf('%02d:%02d', intdiv($m, 60), $m % 60);
}

function valid_date(?string $d): bool
{
    if ($d === null || !preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $d, $m)) return false;
    return checkdate((int)$m[2], (int)$m[3], (int)$m[1]);
}

function today(): string
{
    return date('Y-m-d');
}

function add_days(string $date, int $days): string
{
    return (new DateTimeImmutable($date))->modify("{$days} days")->format('Y-m-d');
}

/** Gesetzliche Feiertage Niedersachsen + Heiligabend/Silvester. */
function holidays(int $year): array
{
    $easter = (new DateTimeImmutable("{$year}-03-21"))->modify('+' . easter_offset($year) . ' days');
    $rel = fn(int $d) => $easter->modify("{$d} days")->format('Y-m-d');
    return [
        "{$year}-01-01" => 'Neujahr',
        $rel(-2) => 'Karfreitag',
        $rel(1) => 'Ostermontag',
        "{$year}-05-01" => 'Tag der Arbeit',
        $rel(39) => 'Christi Himmelfahrt',
        $rel(50) => 'Pfingstmontag',
        "{$year}-10-03" => 'Tag der Deutschen Einheit',
        "{$year}-10-31" => 'Reformationstag',
        "{$year}-12-24" => 'Heiligabend',
        "{$year}-12-25" => '1. Weihnachtstag',
        "{$year}-12-26" => '2. Weihnachtstag',
        "{$year}-12-31" => 'Silvester',
    ];
}

// Tage vom 21. März bis Ostersonntag (Gauß, funktioniert ohne ext-calendar)
function easter_offset(int $y): int
{
    $a = $y % 19; $b = intdiv($y, 100); $c = $y % 100;
    $d = intdiv($b, 4); $e = $b % 4; $f = intdiv($b + 8, 25);
    $g = intdiv($b - $f + 1, 3); $h = (19 * $a + $b - $d - $g + 15) % 30;
    $i = intdiv($c, 4); $k = $c % 4; $l = (32 + 2 * $e + 2 * $i - $h - $k) % 7;
    $m = intdiv($a + 11 * $h + 22 * $l, 451);
    $month = intdiv($h + $l - 7 * $m + 114, 31);
    $day = (($h + $l - 7 * $m + 114) % 31) + 1;
    return (int)(new DateTimeImmutable("{$y}-03-21"))->diff(new DateTimeImmutable(sprintf('%d-%02d-%02d', $y, $month, $day)))->days;
}

/** [open, close] in Minuten oder null, wenn geschlossen. */
function opening_for(string $date): ?array
{
    if (!valid_date($date)) return null;
    $c = cfg();
    if (in_array($date, $c['closedDates'], true)) return null;
    if (isset(holidays((int)substr($date, 0, 4))[$date])) return null;
    $h = $c['hours'][(int)date('w', strtotime($date))] ?? null;
    return $h ? [to_minutes($h[0]), to_minutes($h[1])] : null;
}

function within_horizon(string $date): bool
{
    return $date >= today() && $date <= add_days(today(), cfg()['booking']['horizonDays']);
}

/** Buchbare Tage für den Kalender im Frontend. */
function bookable_days(): array
{
    $days = [];
    for ($i = 0; $i <= cfg()['booking']['horizonDays']; $i++) {
        $d = add_days(today(), $i);
        $open = opening_for($d);
        // Heute nur anbieten, wenn nach dem Mindestvorlauf noch Zeit bis Ladenschluss bleibt
        if ($open && $i === 0 && (int)date('G') * 60 + (int)date('i') + cfg()['booking']['leadTime'] + 15 > $open[1]) $open = null;
        $days[] = ['date' => $d, 'open' => $open !== null];
    }
    return $days;
}

/** Freie Startzeiten. $busy = [[start, end], ...] in Minuten. */
function free_slots(string $date, int $duration, array $busy): array
{
    $hours = opening_for($date);
    if (!$hours || !within_horizon($date)) return [];
    $b = cfg()['booking'];
    [$open, $close] = $hours;
    $earliest = $date === today() ? (int)date('G') * 60 + (int)date('i') + $b['leadTime'] : 0;
    $slots = [];
    for ($start = $open; $start + $duration <= $close; $start += $b['slotStep']) {
        if ($start < $earliest) continue;
        $end = $start + $duration;
        $overlap = count(array_filter($busy, fn($r) => $r[0] < $end && $r[1] > $start));
        if ($overlap < $b['capacity']) $slots[] = to_time($start);
    }
    return $slots;
}

// ---------- Datenbank ----------

function db(): PDO
{
    static $pdo = null;
    if ($pdo) return $pdo;
    $path = cfg()['local']['databasePath'] ?? __DIR__ . '/data/bookings.sqlite';
    if (!is_dir(dirname($path))) mkdir(dirname($path), 0750, true);
    $pdo = new PDO('sqlite:' . $path, null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    $pdo->exec('PRAGMA journal_mode = WAL; PRAGMA busy_timeout = 5000; PRAGMA foreign_keys = ON;');
    $pdo->exec(<<<SQL
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL DEFAULT 'booking',
            status TEXT NOT NULL DEFAULT 'confirmed',
            date TEXT NOT NULL,
            start_min INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            services TEXT NOT NULL DEFAULT '[]',
            price_estimate REAL NOT NULL DEFAULT 0,
            name TEXT, phone TEXT, email TEXT, note TEXT,
            pay_method TEXT NOT NULL DEFAULT 'onsite',
            pay_amount REAL NOT NULL DEFAULT 0,
            paypal_order TEXT, paypal_capture TEXT, refunded INTEGER NOT NULL DEFAULT 0,
            cancel_token TEXT,
            created_at TEXT NOT NULL,
            cancelled_at TEXT, cancelled_by TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date, status);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_entries_order ON entries(paypal_order) WHERE paypal_order IS NOT NULL;
        CREATE TABLE IF NOT EXISTS rate_limit (ip TEXT NOT NULL, action TEXT NOT NULL, at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS vouchers (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            amount REAL NOT NULL,
            balance REAL NOT NULL,
            buyer_name TEXT NOT NULL, buyer_email TEXT NOT NULL,
            recipient TEXT, message TEXT,
            paypal_order TEXT UNIQUE, paypal_capture TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            dl_token TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS voucher_redemptions (
            voucher_id TEXT NOT NULL REFERENCES vouchers(id),
            amount REAL NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        );
    SQL);
    // Spalten, die nach der ersten Version dazugekommen sind
    $cols = array_column($pdo->query('PRAGMA table_info(entries)')->fetchAll(), 'name');
    if (!in_array('review_optin', $cols, true)) $pdo->exec('ALTER TABLE entries ADD COLUMN review_optin INTEGER NOT NULL DEFAULT 0');
    if (!in_array('review_sent_at', $cols, true)) $pdo->exec('ALTER TABLE entries ADD COLUMN review_sent_at TEXT');
    return $pdo;
}

function busy_ranges(string $date): array
{
    $st = db()->prepare("SELECT start_min, duration FROM entries WHERE date = ? AND status != 'cancelled'");
    $st->execute([$date]);
    return array_map(fn($r) => [(int)$r['start_min'], (int)$r['start_min'] + (int)$r['duration']], $st->fetchAll());
}

/** Prüft Leistungen + Termin. Liefert ['summary' => …] oder ['error' => …, 'status' => …]. */
function check_slot(array $in): array
{
    $summary = summarize(is_array($in['services'] ?? null) ? $in['services'] : []);
    if (!$summary) return ['error' => 'Bitte wählen Sie mindestens eine gültige Leistung.', 'status' => 400];
    $date = (string)($in['date'] ?? '');
    $time = (string)($in['time'] ?? '');
    if (!valid_date($date) || to_minutes($time) === null) return ['error' => 'Ungültiges Datum oder Uhrzeit.', 'status' => 400];
    if (!in_array($time, free_slots($date, $summary['duration'], busy_ranges($date)), true)) {
        return ['error' => 'Dieser Termin ist leider nicht mehr frei. Bitte wählen Sie eine andere Uhrzeit.', 'status' => 409];
    }
    return ['summary' => $summary];
}

function rate_limited(string $action, int $max, int $windowSec): bool
{
    $ip = hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '') . $action); // keine Klartext-IPs speichern
    $pdo = db();
    $pdo->prepare('DELETE FROM rate_limit WHERE at < ?')->execute([time() - 86400]);
    $st = $pdo->prepare('SELECT COUNT(*) FROM rate_limit WHERE ip = ? AND action = ? AND at > ?');
    $st->execute([$ip, $action, time() - $windowSec]);
    if ((int)$st->fetchColumn() >= $max) return true;
    $pdo->prepare('INSERT INTO rate_limit (ip, action, at) VALUES (?, ?, ?)')->execute([$ip, $action, time()]);
    return false;
}

function uuid(): string
{
    $b = random_bytes(16);
    $b[6] = chr(ord($b[6]) & 0x0f | 0x40);
    $b[8] = chr(ord($b[8]) & 0x3f | 0x80);
    return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($b), 4));
}

// ---------- HTTP / JSON ----------

function json_out(array $data, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function json_fail(string $msg, int $status = 400): never
{
    json_out(['error' => $msg], $status);
}

function json_in(): array
{
    $data = json_decode(file_get_contents('php://input') ?: '', true);
    return is_array($data) ? $data : [];
}

function require_method(string $method): void
{
    if ($_SERVER['REQUEST_METHOD'] !== $method) json_fail('Methode nicht erlaubt.', 405);
}

function clean_text($v, int $max): string
{
    return mb_substr(trim(preg_replace('/[\x00-\x1F\x7F]+/u', ' ', (string)$v) ?? ''), 0, $max);
}

// ---------- PayPal ----------

function paypal_enabled(): bool
{
    $p = cfg()['local']['paypal'] ?? [];
    return !empty($p['clientId']) && !empty($p['clientSecret']);
}

function paypal_request(string $method, string $path, ?array $body = null): array
{
    $p = cfg()['local']['paypal'];
    $base = ($p['env'] ?? 'sandbox') === 'live' ? 'https://api-m.paypal.com' : 'https://api-m.sandbox.paypal.com';

    static $token = null;
    if ($token === null) {
        $ch = curl_init("{$base}/v1/oauth2/token");
        curl_setopt_array($ch, [
            CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20,
            CURLOPT_USERPWD => "{$p['clientId']}:{$p['clientSecret']}",
            CURLOPT_POSTFIELDS => 'grant_type=client_credentials',
        ]);
        $res = json_decode((string)curl_exec($ch), true);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        if ($code !== 200 || empty($res['access_token'])) throw new RuntimeException("PayPal-Auth fehlgeschlagen ({$code})");
        $token = $res['access_token'];
    }

    $ch = curl_init($base . $path);
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST => $method, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 30,
        CURLOPT_HTTPHEADER => ["Authorization: Bearer {$token}", 'Content-Type: application/json', 'Prefer: return=representation'],
        CURLOPT_POSTFIELDS => $body === null ? '{}' : json_encode($body, JSON_UNESCAPED_UNICODE),
    ]);
    $raw = (string)curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $data = json_decode($raw, true) ?: [];
    if ($code < 200 || $code >= 300) {
        throw new RuntimeException("PayPal {$path} → {$code}: " . ($data['details'][0]['issue'] ?? $data['name'] ?? ''));
    }
    return $data;
}

function paypal_create_order(float $amount, string $reference, string $description): string
{
    $order = paypal_request('POST', '/v2/checkout/orders', [
        'intent' => 'CAPTURE',
        'purchase_units' => [[
            'reference_id' => $reference,
            'description' => mb_substr($description, 0, 127),
            'amount' => ['currency_code' => 'EUR', 'value' => number_format($amount, 2, '.', '')],
        ]],
        'payment_source' => ['paypal' => ['experience_context' => [
            'brand_name' => cfg()['salon']['name'], 'locale' => 'de-DE',
            'shipping_preference' => 'NO_SHIPPING', 'user_action' => 'PAY_NOW',
        ]]],
    ]);
    return $order['id'];
}

function paypal_capture(string $orderId): array
{
    $d = paypal_request('POST', '/v2/checkout/orders/' . rawurlencode($orderId) . '/capture');
    $cap = $d['purchase_units'][0]['payments']['captures'][0] ?? [];
    return [
        'status'    => $d['status'] ?? '',
        'captureId' => $cap['id'] ?? null,
        'amount'    => (float)($cap['amount']['value'] ?? 0),
        'currency'  => $cap['amount']['currency_code'] ?? '',
        'reference' => $d['purchase_units'][0]['reference_id'] ?? '',
    ];
}

function paypal_refund(string $captureId): void
{
    paypal_request('POST', '/v2/payments/captures/' . rawurlencode($captureId) . '/refund');
}

// ---------- E-Mail ----------

/** $attachments = [['dateiname.pdf', 'application/pdf', $bytes], …] */
function send_mail(?string $to, string $subject, string $html, ?string $replyTo = null, array $attachments = []): bool
{
    $mail = cfg()['local']['mail'] ?? [];
    $from = $mail['from'] ?? '';
    if (!$to || !$from || !filter_var($to, FILTER_VALIDATE_EMAIL)) return false;
    $headers = [
        'MIME-Version: 1.0',
        'From: ' . mb_encode_mimeheader(cfg()['salon']['name']) . " <{$from}>",
    ];
    if ($replyTo && filter_var($replyTo, FILTER_VALIDATE_EMAIL)) $headers[] = "Reply-To: {$replyTo}";
    $subject = mb_encode_mimeheader($subject, 'UTF-8');
    $htmlPart = chunk_split(base64_encode('<!doctype html><html><body style="font-family:Georgia,serif;color:#2c2620;line-height:1.6">' . $html . '</body></html>'));

    if (!$attachments) {
        $headers[] = 'Content-Type: text/html; charset=UTF-8';
        $headers[] = 'Content-Transfer-Encoding: base64';
        $body = $htmlPart;
    } else {
        $boundary = 'aj_' . bin2hex(random_bytes(12));
        $headers[] = "Content-Type: multipart/mixed; boundary=\"{$boundary}\"";
        $body = "--{$boundary}\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n{$htmlPart}";
        foreach ($attachments as [$name, $mime, $bytes]) {
            $name = preg_replace('/[^A-Za-z0-9._-]/', '_', $name);
            $body .= "--{$boundary}\r\nContent-Type: {$mime}; name=\"{$name}\"\r\nContent-Transfer-Encoding: base64\r\n"
                . "Content-Disposition: attachment; filename=\"{$name}\"\r\n\r\n" . chunk_split(base64_encode($bytes));
        }
        $body .= "--{$boundary}--\r\n";
    }

    try {
        if (!empty($mail['smtp']['host'])) {
            smtp_send($mail['smtp'], $from, $to, $subject, $body, $headers);
            return true;
        }
        return @mail($to, $subject, $body, implode("\r\n", $headers), "-f{$from}");
    } catch (Throwable $e) {
        error_log('Mailversand fehlgeschlagen: ' . $e->getMessage());
        return false;
    }
}

/** Minimaler SMTP-Client (SSL auf 465 oder STARTTLS auf 587) – keine Abhängigkeiten nötig. */
function smtp_send(array $c, string $from, string $to, string $subject, string $body, array $headers): void
{
    $port = (int)($c['port'] ?? 587);
    $host = ($port === 465 ? 'ssl://' : 'tcp://') . $c['host'];
    $fp = @stream_socket_client("{$host}:{$port}", $errno, $err, 15);
    if (!$fp) throw new RuntimeException("SMTP-Verbindung fehlgeschlagen: {$err}");
    stream_set_timeout($fp, 15);
    $read = function () use ($fp): string {
        $data = '';
        while (($line = fgets($fp, 515)) !== false) {
            $data .= $line;
            if (isset($line[3]) && $line[3] === ' ') break;
        }
        return $data;
    };
    $cmd = function (string $line, array $ok) use ($fp, $read): string {
        if ($line !== '') fwrite($fp, $line . "\r\n");
        $res = $read();
        if (!in_array((int)substr($res, 0, 3), $ok, true)) throw new RuntimeException('SMTP: ' . trim($res));
        return $res;
    };
    $helo = parse_url(site_url('/'), PHP_URL_HOST) ?: 'localhost';
    $cmd('', [220]);
    $cmd("EHLO {$helo}", [250]);
    if ($port !== 465) {
        $cmd('STARTTLS', [220]);
        if (!stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLSv1_2_CLIENT | STREAM_CRYPTO_METHOD_TLSv1_3_CLIENT)) {
            throw new RuntimeException('SMTP: TLS fehlgeschlagen');
        }
        $cmd("EHLO {$helo}", [250]);
    }
    if (!empty($c['user'])) {
        $cmd('AUTH LOGIN', [334]);
        $cmd(base64_encode($c['user']), [334]);
        $cmd(base64_encode($c['pass'] ?? ''), [235]);
    }
    $cmd("MAIL FROM:<{$from}>", [250]);
    $cmd("RCPT TO:<{$to}>", [250, 251]);
    $cmd('DATA', [354]);
    $msg = implode("\r\n", array_merge($headers, [
        "To: <{$to}>",
        "Subject: {$subject}",
        'Date: ' . date('r'),
        'Message-ID: <' . bin2hex(random_bytes(12)) . '@' . substr(strrchr($from, '@'), 1) . '>',
    ])) . "\r\n\r\n" . $body;
    $cmd(preg_replace('/^\./m', '..', $msg) . "\r\n.", [250]);
    $cmd('QUIT', [221]);
    fclose($fp);
}

function is_https(): bool
{
    return !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'
        || ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https';
}

function german_date(string $iso): string
{
    $days = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
    return $days[(int)date('w', strtotime($iso))] . ', ' . date('d.m.Y', strtotime($iso));
}

// ---------- Verwaltung ----------

function admin_session(): void
{
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_name('aj_admin');
        session_set_cookie_params(['httponly' => true, 'samesite' => 'Strict', 'secure' => is_https(), 'path' => '/']);
        session_start();
    }
}

function is_admin(): bool
{
    admin_session();
    return !empty($_SESSION['admin']) && ($_SESSION['admin_until'] ?? 0) > time();
}

function csrf_token(): string
{
    admin_session();
    return $_SESSION['csrf'] ??= bin2hex(random_bytes(16));
}
