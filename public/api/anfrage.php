<?php
declare(strict_types=1);

/*
 * Anfrage-Endpunkt für psschneider.de
 *
 * Nimmt das Kontaktformular samt Schadenfotos entgegen, prüft alles, verkleinert die Fotos,
 * entfernt dabei Metadaten wie den Aufnahmeort und schickt eine E-Mail per SMTP an das Postfach.
 *
 * Aufrufe:
 *   GET  /api/anfrage.php?aktion=token   liefert ein signiertes Token für das Formular
 *   POST /api/anfrage.php                nimmt eine Anfrage entgegen (multipart/form-data)
 *   php anfrage.php selftest             Umgebung prüfen (auf dem Server in der Konsole)
 *   php anfrage.php purge                alte Zwischenspeicher löschen (täglich per Cron)
 *
 * Die Konfiguration liegt außerhalb des Webroots in ../private/config.php, siehe server/private.example/.
 * Es werden keine Cookies gesetzt. IP-Adressen werden nur als Hash mit geheimem Schlüssel und Datum
 * für die Mengenbegrenzung verwendet und nie im Klartext gespeichert.
 */

if (PHP_VERSION_ID < 80100) {
    http_response_code(500);
    exit("PHP 8.1 oder neuer erforderlich.\n");
}

@ini_set('display_errors', '0');
@ini_set('log_errors', '1');
@ini_set('memory_limit', '256M');
@set_time_limit(90);
date_default_timezone_set('Europe/Berlin');
header_remove('X-Powered-By');

/* ------------------------------------------------------------------ Konfiguration */

function private_dir(): string
{
    $env = getenv('PSS_PRIVATE_DIR');
    if (is_string($env) && $env !== '') {
        return rtrim($env, '/');
    }
    return dirname(__DIR__, 2) . '/private';
}

function config(): array
{
    static $cfg = null;
    if ($cfg !== null) {
        return $cfg;
    }
    $file = private_dir() . '/config.php';
    if (!is_file($file)) {
        throw new RuntimeException('Konfiguration fehlt: ' . $file);
    }
    $user = require $file;
    if (!is_array($user)) {
        throw new RuntimeException('config.php muss ein Array zurückgeben.');
    }
    $defaults = [
        'secret' => '',
        'mail_to' => '',
        'mail_from' => '',
        'mail_from_name' => 'Website psschneider.de',
        'transport' => 'smtp',               // smtp oder mail
        'smtp' => ['host' => '', 'port' => 587, 'secure' => 'starttls', 'user' => '', 'pass' => '', 'verify_peer' => true, 'timeout' => 20],
        'allowed_origins' => [],
        'trusted_proxies' => [],
        'max_photos' => 5,
        'max_photo_mb' => 15,
        'max_edge_px' => 2400,
        'jpeg_quality' => 85,
        'max_message_chars' => 5000,
        'min_seconds' => 4,
        'rate_per_hour' => 5,
        'rate_per_day' => 15,
        'keep_failed_days' => 14,
        // Bestätigung an den Absender der Anfrage (feste Texte, ohne seine Eingaben)
        'confirm_customer' => true,
        'confirm_per_address_day' => 2,
        'sign_name' => 'PS Schneider – Sachverständiger für Fahrzeugtechnik',
        'sign_address' => 'Im Röthel 43, 29225 Celle',
        'sign_phone' => '0172 517 81 50',
    ];
    $cfg = array_replace_recursive($defaults, $user);
    foreach (['secret', 'mail_to', 'mail_from'] as $k) {
        if (!is_string($cfg[$k]) || $cfg[$k] === '') {
            throw new RuntimeException("Konfigurationswert fehlt: $k");
        }
    }
    if (strlen($cfg['secret']) < 32) {
        throw new RuntimeException('secret muss mindestens 32 Zeichen lang sein.');
    }
    return $cfg;
}

function ensure_dir(string $dir): void
{
    if (!is_dir($dir) && !@mkdir($dir, 0750, true) && !is_dir($dir)) {
        throw new RuntimeException('Verzeichnis nicht anlegbar: ' . $dir);
    }
}

function log_line(string $status, string $extra = ''): void
{
    try {
        $dir = private_dir() . '/logs';
        ensure_dir($dir);
        $line = date('c') . ' ' . $status . ($extra !== '' ? ' ' . $extra : '') . "\n";
        @file_put_contents($dir . '/anfragen.log', $line, FILE_APPEND | LOCK_EX);
    } catch (Throwable $e) {
        error_log('anfrage.php: Log nicht schreibbar: ' . $e->getMessage());
    }
}

/* ------------------------------------------------------------------ Sprache der Meldungen */

$GLOBALS['pss_lang'] = 'de';

/** Wählt den deutschen oder englischen Text, je nach Sprache der Seite, von der das Formular kam. */
function tr(string $de, string $en): string
{
    return $GLOBALS['pss_lang'] === 'en' ? $en : $de;
}

function is_en(): bool
{
    return $GLOBALS['pss_lang'] === 'en';
}

/* ------------------------------------------------------------------ Antworten */

function respond(int $code, array $data): never
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

/* ------------------------------------------------------------------ Schutz vor Missbrauch */

function client_ip(array $cfg): string
{
    $ip = (string)($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0');
    if (in_array($ip, $cfg['trusted_proxies'], true) && !empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $first = trim(explode(',', (string)$_SERVER['HTTP_X_FORWARDED_FOR'])[0]);
        if (filter_var($first, FILTER_VALIDATE_IP)) {
            return $first;
        }
    }
    return $ip;
}

function rate_file(array $cfg, string $who = ''): string
{
    $key = hash_hmac('sha256', ($who !== '' ? $who : client_ip($cfg)) . '|' . gmdate('Y-m-d'), $cfg['secret']);
    $dir = private_dir() . '/ratelimit';
    ensure_dir($dir);
    return $dir . '/' . $key . '.json';
}

/** Gibt zurück, ob noch Anfragen erlaubt sind. Mit $record = true wird ein Versuch gezählt. */
function rate_limit(array $cfg, bool $record, string $who = '', int $perHour = 0, int $perDay = 0): bool
{
    $perHour = $perHour > 0 ? $perHour : (int)$cfg['rate_per_hour'];
    $perDay = $perDay > 0 ? $perDay : (int)$cfg['rate_per_day'];
    $fh = fopen(rate_file($cfg, $who), 'c+');
    if ($fh === false) {
        return true; // lieber Anfragen annehmen als sie wegen eines Speicherfehlers zu verlieren
    }
    flock($fh, LOCK_EX);
    $times = json_decode((string)stream_get_contents($fh), true);
    $times = is_array($times) ? $times : [];
    $now = time();
    $times = array_values(array_filter($times, static fn($t) => is_int($t) && $t > $now - 86400));
    $lastHour = count(array_filter($times, static fn($t) => $t > $now - 3600));
    $allowed = $lastHour < $perHour && count($times) < $perDay;
    if ($allowed && $record) {
        $times[] = $now;
        ftruncate($fh, 0);
        rewind($fh);
        fwrite($fh, json_encode($times));
    }
    flock($fh, LOCK_UN);
    fclose($fh);
    return $allowed;
}

function token_issue(array $cfg): string
{
    $ts = (string)time();
    return $ts . '.' . hash_hmac('sha256', $ts, $cfg['secret']);
}

function token_error(array $cfg, string $token): ?string
{
    $parts = explode('.', $token);
    if (count($parts) !== 2 || !ctype_digit($parts[0])) {
        return tr('Bitte laden Sie die Seite neu und versuchen Sie es erneut.', 'Please reload the page and try again.');
    }
    if (!hash_equals(hash_hmac('sha256', $parts[0], $cfg['secret']), $parts[1])) {
        return tr('Bitte laden Sie die Seite neu und versuchen Sie es erneut.', 'Please reload the page and try again.');
    }
    $age = time() - (int)$parts[0];
    if ($age < (int)$cfg['min_seconds']) {
        return tr('Das ging zu schnell. Bitte warten Sie einen Moment und senden Sie erneut.', 'That was too fast. Please wait a moment and send again.');
    }
    if ($age > 7200) {
        return tr('Das Formular ist abgelaufen. Bitte laden Sie die Seite neu.', 'The form has expired. Please reload the page.');
    }
    return null;
}

function origin_allowed(array $cfg): bool
{
    $allowed = array_map(static fn($o) => rtrim((string)$o, '/'), $cfg['allowed_origins']);
    $origin = (string)($_SERVER['HTTP_ORIGIN'] ?? '');
    if ($origin !== '') {
        return in_array(rtrim($origin, '/'), $allowed, true);
    }
    $ref = (string)($_SERVER['HTTP_REFERER'] ?? '');
    if ($ref !== '') {
        $p = parse_url($ref);
        if (is_array($p) && isset($p['scheme'], $p['host'])) {
            $o = $p['scheme'] . '://' . $p['host'] . (isset($p['port']) ? ':' . $p['port'] : '');
            return in_array($o, $allowed, true);
        }
    }
    return false;
}

/* ------------------------------------------------------------------ Eingaben prüfen */

function cut(string $s, int $max): string
{
    return function_exists('mb_substr') ? mb_substr($s, 0, $max, 'UTF-8') : substr($s, 0, $max);
}

function one_line(mixed $v, int $max): string
{
    if (!is_string($v)) {
        return '';
    }
    $v = preg_replace('/[\x00-\x1F\x7F\x{2028}\x{2029}]+/u', ' ', $v) ?? '';
    return cut(trim((string)preg_replace('/\s+/u', ' ', $v)), $max);
}

function multi_line(mixed $v, int $max): string
{
    if (!is_string($v)) {
        return '';
    }
    $v = str_replace(["\r\n", "\r"], "\n", $v);
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]+/u', '', $v) ?? '';
    return cut(trim($v), $max);
}

/** Kennzeichen: nur Buchstaben, Ziffern, Leerzeichen und Bindestrich, in Großbuchstaben. */
function plate_clean(mixed $v): string
{
    $v = preg_replace('/[^\p{L}0-9 \-]/u', '', one_line($v, 15)) ?? '';
    return function_exists('mb_strtoupper') ? mb_strtoupper(trim($v), 'UTF-8') : strtoupper(trim($v));
}

function validate_fields(array $cfg): array
{
    $e = [];
    $d = [
        'name' => one_line($_POST['name'] ?? '', 100),
        'email' => one_line($_POST['email'] ?? '', 254),
        'phone' => preg_replace('/[^0-9+\-\/() ]/', '', one_line($_POST['phone'] ?? '', 40)) ?? '',
        'subject' => one_line($_POST['subject'] ?? '', 80),
        'message' => multi_line($_POST['message'] ?? '', (int)$cfg['max_message_chars']),
        'plate' => plate_clean($_POST['plate'] ?? ''),
        'insurer' => one_line($_POST['insurer'] ?? '', 80),
        'pref' => ($_POST['pref'] ?? '') === 'callback' ? 'callback' : 'email',
    ];
    if ($d['name'] === '') {
        $e['name'] = tr('Bitte geben Sie Ihren Namen an.', 'Please enter your name.');
    }
    if ($d['email'] === '' || !filter_var($d['email'], FILTER_VALIDATE_EMAIL)) {
        $e['email'] = tr('Bitte geben Sie eine gültige E-Mail-Adresse an.', 'Please enter a valid email address.');
    }
    if ($d['subject'] === '') {
        $e['subject'] = tr('Bitte wählen Sie Ihr Anliegen.', 'Please choose your topic.');
    }
    if (strlen($d['message']) < 5) {
        $e['message'] = tr('Bitte schreiben Sie kurz, worum es geht.', 'Please briefly say what it is about.');
    }
    if ($d['pref'] === 'callback' && strlen((string)preg_replace('/\D/', '', $d['phone'])) < 6) {
        $e['phone'] = tr('Für einen Rückruf brauchen wir Ihre Telefonnummer.', 'We need your phone number to call you back.');
    }
    if (($_POST['consent'] ?? '') !== '1') {
        $e['consent'] = tr('Bitte stimmen Sie der Datenschutzerklärung zu.', 'Please agree to the privacy policy.');
    }
    return [$d, $e];
}

/* ------------------------------------------------------------------ Fotos */

function normalize_files(string $field): array
{
    if (empty($_FILES[$field]) || !is_array($_FILES[$field])) {
        return [];
    }
    $f = $_FILES[$field];
    if (!is_array($f['name'])) {
        $f = array_map(static fn($v) => [$v], $f);
    }
    $out = [];
    foreach ($f['name'] as $i => $name) {
        if (($f['error'][$i] ?? UPLOAD_ERR_NO_FILE) === UPLOAD_ERR_NO_FILE) {
            continue;
        }
        $out[] = ['name' => (string)$name, 'tmp' => (string)$f['tmp_name'][$i], 'error' => (int)$f['error'][$i], 'size' => (int)$f['size'][$i]];
    }
    return $out;
}

/** Verarbeitet ein Foto. Gibt eine Fehlermeldung zurück oder null bei Erfolg. */
function process_photo(array $file, string $dest, array $cfg): ?string
{
    $label = one_line($file['name'], 60);
    $q = static fn(string $t): string => is_en() ? "\u{201C}$t\u{201D}" : "\u{201E}$t\u{201C}";
    $name = $q($label);
    if ($file['error'] !== UPLOAD_ERR_OK) {
        return in_array($file['error'], [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true)
            ? $name . tr(' ist zu groß.', ' is too large.')
            : $name . tr(' konnte nicht hochgeladen werden.', ' could not be uploaded.');
    }
    if ($file['size'] > (int)$cfg['max_photo_mb'] * 1024 * 1024) {
        return $name . tr(" ist zu groß (höchstens {$cfg['max_photo_mb']} MB).", " is too large (maximum {$cfg['max_photo_mb']} MB).");
    }
    if (!is_uploaded_file($file['tmp'])) {
        return $name . tr(' konnte nicht verarbeitet werden.', ' could not be processed.');
    }
    $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file['tmp']);
    if (!in_array($mime, ['image/jpeg', 'image/png', 'image/webp'], true)) {
        return $name . tr(' hat ein nicht unterstütztes Format. Erlaubt sind JPG, PNG und WebP.', ' is not a supported format. JPG, PNG and WebP are allowed.');
    }
    $info = @getimagesize($file['tmp']);
    if ($info === false || $info[0] < 1 || $info[1] < 1) {
        return $name . tr(' ist kein gültiges Bild.', ' is not a valid image.');
    }
    if ($info[0] > 16000 || $info[1] > 16000 || $info[0] * $info[1] > 60_000_000) {
        return $name . tr(' hat zu viele Pixel.', ' has too many pixels.');
    }
    $raw = @file_get_contents($file['tmp']);
    $img = $raw === false ? false : @imagecreatefromstring($raw);
    if ($img === false) {
        return $name . tr(' konnte nicht gelesen werden.', ' could not be read.');
    }

    // Ausrichtung aus den Metadaten übernehmen, bevor diese entfernt werden
    if ($mime === 'image/jpeg' && function_exists('exif_read_data')) {
        $exif = @exif_read_data($file['tmp']);
        $angle = match ((int)($exif['Orientation'] ?? 1)) {
            3 => 180, 6 => -90, 8 => 90, default => 0,
        };
        if ($angle !== 0) {
            $rot = imagerotate($img, $angle, 0);
            if ($rot !== false) {
                $img = $rot;
            }
        }
    }

    $w = imagesx($img);
    $h = imagesy($img);
    $edge = (int)$cfg['max_edge_px'];
    $scale = min(1.0, $edge / max($w, $h));
    $nw = max(1, (int)round($w * $scale));
    $nh = max(1, (int)round($h * $scale));
    // Neues Bild auf weißem Grund: entfernt Transparenz und alle Metadaten
    $out = imagecreatetruecolor($nw, $nh);
    imagefill($out, 0, 0, imagecolorallocate($out, 255, 255, 255));
    imagecopyresampled($out, $img, 0, 0, 0, 0, $nw, $nh, $w, $h);
    $ok = imagejpeg($out, $dest, (int)$cfg['jpeg_quality']);
    unset($img, $out);
    if (!$ok || !is_file($dest) || filesize($dest) < 100) {
        return $name . tr(' konnte nicht verarbeitet werden.', ' could not be processed.');
    }
    @chmod($dest, 0640);
    return null;
}

/* ------------------------------------------------------------------ E-Mail */

function encode_header(string $s): string
{
    $s = preg_replace('/[\r\n]+/', ' ', $s) ?? '';
    return preg_match('/^[\x20-\x7E]*$/', $s) ? $s : '=?UTF-8?B?' . base64_encode($s) . '?=';
}

function mail_domain(string $addr): string
{
    $at = strrpos($addr, '@');
    return $at === false ? 'localhost' : substr($addr, $at + 1);
}

/** Baut die Nachricht. Gibt ['headers' => [...], 'body' => '...'] zurück. */
function build_message(array $cfg, array $d, array $photos, string $ref): array
{
    $when = date('d.m.Y H:i');
    $lines = [
        'Neue Anfrage über psschneider.de',
        "Referenz: $ref",
        "Eingegangen: $when Uhr",
        '',
        'Anliegen: ' . $d['subject'],
        'Name:     ' . $d['name'],
        'E-Mail:   ' . $d['email'],
        'Telefon:  ' . ($d['phone'] !== '' ? $d['phone'] : 'nicht angegeben'),
        'Kennzeichen: ' . ($d['plate'] !== '' ? $d['plate'] : 'nicht angegeben'),
        'Versicherung: ' . ($d['insurer'] !== '' ? $d['insurer'] : 'nicht angegeben'),
        'Gewünschte Antwort: ' . ($d['pref'] === 'callback' ? 'RÜCKRUF unter ' . $d['phone'] : 'per E-Mail'),
        '',
        'Nachricht:',
        $d['message'],
        '',
        $photos ? 'Fotos: ' . count($photos) . ' Anhang/Anhänge (verkleinert, ohne Standortdaten)' : 'Fotos: keine',
        'Datenschutzerklärung zugestimmt: ja',
        ...(is_en() ? ['Sprache der Seite: Englisch. Bitte möglichst auf Englisch antworten.'] : []),
        '',
        'Antworten Sie direkt auf diese E-Mail. Die Antwort geht an ' . $d['email'] . '.',
    ];
    $text = implode("\r\n", array_map(static fn($l) => str_replace("\n", "\r\n", $l), $lines)) . "\r\n";

    $boundary = '=_pss_' . bin2hex(random_bytes(12));
    $domain = mail_domain($cfg['mail_from']);
    $subject = cut('Anfrage' . ($d['pref'] === 'callback' ? ' [RÜCKRUF]' : '') . (is_en() ? ' [EN]' : '') . ': ' . $d['subject'] . ' – ' . $d['name'], 150);
    $headers = [
        'Date' => date('r'),
        'From' => encode_header((string)$cfg['mail_from_name']) . ' <' . $cfg['mail_from'] . '>',
        'To' => $cfg['mail_to'],
        'Reply-To' => $d['email'],
        'Subject' => encode_header($subject),
        'Message-ID' => '<' . $ref . '.' . time() . '@' . $domain . '>',
        'MIME-Version' => '1.0',
        'X-Mailer' => 'psschneider-formular',
    ];

    $part = static fn(string $head, string $content) => $head . "\r\n\r\n" . chunk_split(base64_encode($content), 76, "\r\n");
    if (!$photos) {
        $headers['Content-Type'] = 'text/plain; charset=UTF-8';
        $headers['Content-Transfer-Encoding'] = 'base64';
        return ['headers' => $headers, 'body' => chunk_split(base64_encode($text), 76, "\r\n")];
    }
    $headers['Content-Type'] = 'multipart/mixed; boundary="' . $boundary . '"';
    $body = "--$boundary\r\n" . $part("Content-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64", $text);
    foreach ($photos as $i => $path) {
        $name = 'foto-' . ($i + 1) . '.jpg';
        $body .= "--$boundary\r\n" . $part(
            "Content-Type: image/jpeg; name=\"$name\"\r\nContent-Transfer-Encoding: base64\r\nContent-Disposition: attachment; filename=\"$name\"",
            (string)file_get_contents($path)
        );
    }
    $body .= "--$boundary--\r\n";
    return ['headers' => $headers, 'body' => $body];
}

/** Feste Bestätigung an den Absender. Enthält keine seiner Eingaben außer der Referenz. */
function build_confirmation(array $cfg, array $d, string $ref): array
{
    $next = $d['pref'] === 'callback'
        ? tr('Wir rufen Sie unter der angegebenen Nummer zurück.', 'We will call you back on the number you gave.')
        : tr('Wir antworten Ihnen per E-Mail.', 'We will reply to you by email.');
    $lines = is_en() ? [
        'Hello,', '',
        'Thank you for your enquiry. It has reached us.', "Your reference: $ref", '',
        $next, '',
        'If your vehicle has just been damaged, please call directly: ' . $cfg['sign_phone'], '',
        $cfg['sign_name'], $cfg['sign_address'], '',
        'This message was created automatically. You received it because your email address was entered in our contact form. If that was not you, you can ignore this message.',
    ] : [
        'Guten Tag,', '',
        'vielen Dank für Ihre Anfrage. Sie ist bei uns eingegangen.', "Ihre Referenz: $ref", '',
        $next, '',
        'Bei einem akuten Schaden rufen Sie bitte direkt an: ' . $cfg['sign_phone'], '',
        $cfg['sign_name'], $cfg['sign_address'], '',
        'Diese Nachricht wurde automatisch erstellt. Sie erhalten sie, weil Ihre E-Mail-Adresse in unserem Kontaktformular angegeben wurde. Waren Sie das nicht, können Sie diese Nachricht ignorieren.',
    ];
    $text = implode("\r\n", $lines) . "\r\n";
    $headers = [
        'Date' => date('r'),
        'From' => encode_header((string)$cfg['mail_from_name']) . ' <' . $cfg['mail_from'] . '>',
        'To' => $d['email'],
        'Reply-To' => $cfg['mail_to'],
        'Subject' => encode_header(tr("Ihre Anfrage bei PS Schneider, Referenz $ref", "Your enquiry to PS Schneider, reference $ref")),
        'Message-ID' => '<' . $ref . '.c.' . time() . '@' . mail_domain($cfg['mail_from']) . '>',
        'Auto-Submitted' => 'auto-replied',
        'MIME-Version' => '1.0',
        'Content-Type' => 'text/plain; charset=UTF-8',
        'Content-Transfer-Encoding' => 'base64',
        'X-Mailer' => 'psschneider-formular',
    ];
    return ['headers' => $headers, 'body' => chunk_split(base64_encode($text), 76, "\r\n")];
}

final class Smtp
{
    /** @var resource|null */
    private $fp = null;

    public function __construct(private array $c)
    {
    }

    public function send(string $from, string $to, string $raw): void
    {
        $secure = (string)$this->c['secure'];
        $host = (string)$this->c['host'];
        $ctx = stream_context_create(['ssl' => [
            'verify_peer' => (bool)$this->c['verify_peer'],
            'verify_peer_name' => (bool)$this->c['verify_peer'],
            'peer_name' => $host,
            'allow_self_signed' => !(bool)$this->c['verify_peer'],
        ]]);
        $addr = ($secure === 'ssl' ? 'ssl://' : 'tcp://') . $host . ':' . (int)$this->c['port'];
        $this->fp = @stream_socket_client($addr, $errno, $errstr, (float)$this->c['timeout'], STREAM_CLIENT_CONNECT, $ctx);
        if (!$this->fp) {
            throw new RuntimeException("SMTP: Verbindung zu $host:{$this->c['port']} fehlgeschlagen ($errstr)");
        }
        stream_set_timeout($this->fp, (int)$this->c['timeout']);
        try {
            $this->expect([220]);
            $ehlo = 'EHLO ' . mail_domain($from);
            $caps = $this->cmd($ehlo, [250]);
            if ($secure === 'starttls') {
                $this->cmd('STARTTLS', [220]);
                if (!@stream_socket_enable_crypto($this->fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
                    throw new RuntimeException('SMTP: TLS konnte nicht aufgebaut werden');
                }
                $caps = $this->cmd($ehlo, [250]);
            }
            if ((string)$this->c['user'] !== '') {
                $cred = (string)$this->c['user'];
                $pass = (string)$this->c['pass'];
                if (stripos($caps, 'PLAIN') !== false) {
                    $this->cmd('AUTH PLAIN ' . base64_encode("\0$cred\0$pass"), [235], true);
                } else {
                    $this->cmd('AUTH LOGIN', [334]);
                    $this->cmd(base64_encode($cred), [334], true);
                    $this->cmd(base64_encode($pass), [235], true);
                }
            }
            $this->cmd("MAIL FROM:<$from>", [250]);
            $this->cmd("RCPT TO:<$to>", [250, 251]);
            $this->cmd('DATA', [354]);
            $data = preg_replace('/\r\n|\r|\n/', "\r\n", $raw) ?? $raw;
            $data = preg_replace('/^\./m', '..', $data) ?? $data;
            fwrite($this->fp, $data . "\r\n.\r\n");
            $this->expect([250]);
            $this->cmd('QUIT', [221]);
        } finally {
            if (is_resource($this->fp)) {
                fclose($this->fp);
            }
        }
    }

    private function cmd(string $line, array $ok, bool $secret = false): string
    {
        fwrite($this->fp, $line . "\r\n");
        return $this->expect($ok, $secret ? '(Zugangsdaten)' : $line);
    }

    private function expect(array $ok, string $after = ''): string
    {
        $lines = [];
        do {
            $l = fgets($this->fp, 1024);
            if ($l === false) {
                throw new RuntimeException('SMTP: Verbindung unterbrochen' . ($after !== '' ? " nach $after" : ''));
            }
            $lines[] = rtrim($l);
            $more = isset($l[3]) && $l[3] === '-';
        } while ($more);
        $code = (int)substr($lines[0], 0, 3);
        if (!in_array($code, $ok, true)) {
            throw new RuntimeException("SMTP $code" . ($after !== '' ? " nach $after" : '') . ': ' . implode(' | ', $lines));
        }
        return implode("\n", $lines);
    }
}

function deliver(array $cfg, array $msg, ?string $to = null): void
{
    if ($cfg['transport'] === 'mail') {
        $h = $msg['headers'];
        $to = (string)$h['To'];
        $subject = (string)$h['Subject'];
        unset($h['To'], $h['Subject']);
        $headerStr = implode("\r\n", array_map(static fn($k, $v) => "$k: $v", array_keys($h), $h));
        if (!mail($to, $subject, $msg['body'], $headerStr, '-f' . $cfg['mail_from'])) {
            throw new RuntimeException('mail() hat den Versand abgelehnt');
        }
        return;
    }
    $raw = implode("\r\n", array_map(static fn($k, $v) => "$k: $v", array_keys($msg['headers']), $msg['headers']))
        . "\r\n\r\n" . $msg['body'];
    (new Smtp($cfg['smtp']))->send($cfg['mail_from'], $to ?? $cfg['mail_to'], $raw);
}

/* ------------------------------------------------------------------ Aufräumen */

function remove_dir(string $dir): void
{
    if (!is_dir($dir)) {
        return;
    }
    foreach (scandir($dir) ?: [] as $f) {
        if ($f !== '.' && $f !== '..') {
            $p = $dir . '/' . $f;
            is_dir($p) ? remove_dir($p) : @unlink($p);
        }
    }
    @rmdir($dir);
}

function purge(array $cfg): array
{
    $removed = ['inbox' => 0, 'ratelimit' => 0];
    $inbox = private_dir() . '/inbox';
    foreach (is_dir($inbox) ? (scandir($inbox) ?: []) : [] as $d) {
        $p = $inbox . '/' . $d;
        if ($d[0] !== '.' && is_dir($p) && filemtime($p) <= time() - (int)$cfg['keep_failed_days'] * 86400) {
            remove_dir($p);
            $removed['inbox']++;
        }
    }
    $rl = private_dir() . '/ratelimit';
    foreach (is_dir($rl) ? (scandir($rl) ?: []) : [] as $f) {
        $p = $rl . '/' . $f;
        if ($f[0] !== '.' && is_file($p) && filemtime($p) < time() - 2 * 86400) {
            @unlink($p);
            $removed['ratelimit']++;
        }
    }
    return $removed;
}

/* ------------------------------------------------------------------ Selbsttest (Konsole) */

function selftest(): void
{
    $ok = true;
    $say = static function (string $label, bool $good, string $note = '') use (&$ok): void {
        $ok = $ok && $good;
        echo ($good ? '[ok]    ' : '[FEHLER]') . ' ' . $label . ($note !== '' ? " ($note)" : '') . "\n";
    };
    $say('PHP ab 8.1', PHP_VERSION_ID >= 80100, PHP_VERSION);
    foreach (['gd', 'fileinfo', 'openssl', 'hash', 'json'] as $ext) {
        $say("Erweiterung $ext", extension_loaded($ext));
    }
    $say('Erweiterung exif (Fotos richtig drehen)', extension_loaded('exif'), 'optional');
    $say('Erweiterung mbstring', extension_loaded('mbstring'), 'optional');
    $webp = function_exists('gd_info') && !empty(gd_info()['WebP Support']);
    $say('GD mit WebP', $webp, 'optional');
    echo 'Private Daten: ' . private_dir() . "\n";
    try {
        $cfg = config();
        $say('config.php lesbar und vollständig', true);
        foreach (['inbox', 'ratelimit', 'logs'] as $sub) {
            $dir = private_dir() . '/' . $sub;
            try {
                ensure_dir($dir);
                $say("$sub beschreibbar", is_writable($dir), $dir);
            } catch (Throwable $e) {
                $say("$sub beschreibbar", false, $e->getMessage());
            }
        }
        $say('Zulässige Herkunft eingetragen', count($cfg['allowed_origins']) > 0);
        $say('upload_max_filesize >= ' . $cfg['max_photo_mb'] . ' MB', ini_size('upload_max_filesize') >= (int)$cfg['max_photo_mb'] * 1048576, (string)ini_get('upload_max_filesize'));
        $say('post_max_size >= 30 MB', ini_size('post_max_size') >= 30 * 1048576, (string)ini_get('post_max_size'));
        $say('max_file_uploads >= ' . $cfg['max_photos'], (int)ini_get('max_file_uploads') >= (int)$cfg['max_photos'], (string)ini_get('max_file_uploads'));
        if ($cfg['transport'] === 'smtp') {
            $c = $cfg['smtp'];
            $say('SMTP-Server eingetragen', (string)$c['host'] !== '');
            if ((string)$c['host'] !== '') {
                $fp = @stream_socket_client('tcp://' . $c['host'] . ':' . (int)$c['port'], $en, $es, 8);
                $say('SMTP erreichbar ' . $c['host'] . ':' . $c['port'], (bool)$fp, $fp ? '' : $es);
                if ($fp) {
                    fclose($fp);
                }
            }
        }
    } catch (Throwable $e) {
        $say('Konfiguration', false, $e->getMessage());
    }
    echo "\nHinweis: Die PHP-Grenzen oben gelten für die Konsole. Für den Webserver zählen php-fpm bzw. die Datei .user.ini.\n";
    echo $ok ? "\nAlles bereit.\n" : "\nEs gibt Fehler, siehe oben.\n";
    exit($ok ? 0 : 1);
}

function ini_size(string $key): int
{
    $v = trim((string)ini_get($key));
    $n = (int)$v;
    return match (strtolower(substr($v, -1))) {
        'g' => $n * 1073741824,
        'm' => $n * 1048576,
        'k' => $n * 1024,
        default => $n,
    };
}

/* ------------------------------------------------------------------ Ablauf */

if (PHP_SAPI === 'cli') {
    $cmd = $argv[1] ?? '';
    if ($cmd === 'selftest') {
        selftest();
    }
    if ($cmd === 'purge') {
        echo json_encode(purge(config())) . "\n";
        exit(0);
    }
    echo "Verwendung: php anfrage.php selftest|purge\n";
    exit(2);
}

try {
    $cfg = config();
} catch (Throwable $e) {
    error_log('anfrage.php: ' . $e->getMessage());
    respond(500, ['ok' => false, 'error' => tr('Das Formular ist gerade nicht verfügbar. Bitte rufen Sie an oder schreiben Sie eine E-Mail.', 'The form is not available at the moment. Please call or send an email.')]);
}

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

if ($method === 'GET') {
    if (($_GET['aktion'] ?? '') === 'token') {
        respond(200, ['token' => token_issue($cfg)]);
    }
    respond(405, ['ok' => false, 'error' => 'POST only.']);
}
if ($method !== 'POST') {
    respond(405, ['ok' => false, 'error' => 'POST only.']);
}

// Sprache der Seite, von der das Formular kam (nur für die Meldungen)
$GLOBALS['pss_lang'] = ($_POST['lang'] ?? '') === 'en' ? 'en' : 'de';

if (!origin_allowed($cfg)) {
    log_line('abgelehnt', 'herkunft');
    respond(403, ['ok' => false, 'error' => tr('Anfrage nicht zulässig.', 'Request not allowed.')]);
}

// Zu große Anfragen kommen bei PHP ohne Inhalt an
if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 0 && empty($_POST) && empty($_FILES)) {
    log_line('abgelehnt', 'zu_gross');
    respond(413, ['ok' => false, 'error' => tr('Die Fotos sind zusammen zu groß. Bitte senden Sie weniger oder kleinere Fotos.', 'The photos together are too large. Please send fewer or smaller photos.'), 'errors' => ['photos' => tr('Die Fotos sind zusammen zu groß.', 'The photos together are too large.')]]);
}

if (!rate_limit($cfg, false)) {
    log_line('abgelehnt', 'zu_viele');
    respond(429, ['ok' => false, 'error' => tr('Zu viele Anfragen von Ihrer Verbindung. Bitte versuchen Sie es später erneut oder rufen Sie an.', 'Too many requests from your connection. Please try again later or call.')]);
}

// Köderfeld: Menschen sehen es nicht. Bots bekommen scheinbar Erfolg.
if (one_line($_POST['website'] ?? '', 200) !== '') {
    log_line('köder');
    respond(200, ['ok' => true, 'ref' => strtoupper(bin2hex(random_bytes(4)))]);
}

$tokenError = token_error($cfg, (string)($_POST['token'] ?? ''));
if ($tokenError !== null) {
    log_line('abgelehnt', 'token');
    respond(400, ['ok' => false, 'error' => $tokenError, 'errors' => ['general' => $tokenError]]);
}

[$data, $errors] = validate_fields($cfg);
$files = normalize_files('photos');
if (count($files) > (int)$cfg['max_photos']) {
    $errors['photos'] = tr('Bitte senden Sie höchstens ' . $cfg['max_photos'] . ' Fotos.', 'Please send no more than ' . $cfg['max_photos'] . ' photos.');
}
if ($errors) {
    respond(400, ['ok' => false, 'error' => tr('Bitte prüfen Sie Ihre Angaben.', 'Please check your details.'), 'errors' => $errors]);
}

rate_limit($cfg, true);

$ref = strtoupper(bin2hex(random_bytes(4)));
$dir = private_dir() . '/inbox/' . $ref;
try {
    ensure_dir($dir);
} catch (Throwable $e) {
    error_log('anfrage.php: ' . $e->getMessage());
    respond(500, ['ok' => false, 'error' => tr('Das Formular ist gerade nicht verfügbar. Bitte rufen Sie an oder schreiben Sie eine E-Mail.', 'The form is not available at the moment. Please call or send an email.')]);
}

$photos = [];
foreach ($files as $i => $file) {
    $dest = $dir . '/foto-' . ($i + 1) . '.jpg';
    $err = process_photo($file, $dest, $cfg);
    if ($err !== null) {
        remove_dir($dir);
        log_line('abgelehnt', 'foto');
        respond(400, ['ok' => false, 'error' => $err, 'errors' => ['photos' => $err]]);
    }
    $photos[] = $dest;
}

@file_put_contents($dir . '/anfrage.json', json_encode($data + ['ref' => $ref, 'fotos' => count($photos), 'zeit' => date('c')], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
@chmod($dir . '/anfrage.json', 0640);

try {
    deliver($cfg, build_message($cfg, $data, $photos, $ref));
    remove_dir($dir); // nichts aufheben, was nicht gebraucht wird
    log_line('ok', "ref=$ref fotos=" . count($photos));
    // Bestätigung an den Absender: nur wenn erlaubt, begrenzt pro Adresse, und nie ein Grund, die Anfrage abzulehnen
    $confirmed = false;
    if ($cfg['confirm_customer'] && rate_limit($cfg, true, 'mail|' . strtolower($data['email']), 1, (int)$cfg['confirm_per_address_day'])) {
        try {
            deliver($cfg, build_confirmation($cfg, $data, $ref), $data['email']);
            $confirmed = true;
        } catch (Throwable $e) {
            log_line('bestaetigung_fehler', "ref=$ref " . cut(preg_replace('/[^\x20-\x7E]/', '?', $e->getMessage()) ?? '', 120));
        }
    }
    respond(200, ['ok' => true, 'ref' => $ref, 'confirmed' => $confirmed]);
} catch (Throwable $e) {
    // Die Anfrage bleibt zur Wiederherstellung für keep_failed_days Tage im Ordner inbox.
    log_line('mail_fehler', "ref=$ref " . cut(preg_replace('/[^\x20-\x7E]/', '?', $e->getMessage()) ?? '', 200));
    respond(502, ['ok' => false, 'error' => tr('Die Anfrage konnte technisch nicht zugestellt werden. Bitte rufen Sie an oder schreiben Sie direkt eine E-Mail.', 'The enquiry could not be delivered for technical reasons. Please call or send an email directly.'), 'ref' => $ref]);
}
