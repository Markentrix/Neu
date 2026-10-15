<?php
/**
 * Markentrix · Formular-Endpunkt für Kontaktformular und Potenzial-Check.
 * Läuft auf dem eigenen Server (Hetzner, Caddy oder nginx + PHP-FPM ≥ 7.4). Gleiche Domain, kein CORS.
 *
 * Versand: Sind die Umgebungsvariablen MX_SMTP_HOST, MX_SMTP_USER und MX_SMTP_PASS gesetzt
 * (z. B. in docker-compose.yml), geht die Mail direkt per SMTP raus (Port 465 SSL oder 587 STARTTLS).
 * Sonst wird mail() benutzt, was einen lokalen Mailserver voraussetzt. Optional: MX_SMTP_PORT,
 * MX_MAIL_TO, MX_MAIL_FROM, MX_LOG_FILE, MX_WEBHOOK, MX_SMTP_SECURITY (ssl, tls, none).
 *
 * Eingang:  POST /api/anfrage.php  mit JSON (Content-Type: application/json) oder Formulardaten
 * Ausgang:  JSON {"ok":true} bzw. {"ok":false,"error":"…"} mit passendem HTTP-Status
 *
 * Ablauf: Honeypot prüfen → Pflichtfelder prüfen → Ratenbegrenzung je IP → E-Mail an Postfach
 *         → optional Weiterleitung an einen Webhook (n8n o. ä.) → optional Protokollzeile.
 * Konfiguration nur in $CONFIG. Keine Ausgabe von Serverpfaden oder Stacktraces an den Browser.
 */
declare(strict_types=1);

$CONFIG = [
  'to'             => getenv('MX_MAIL_TO')   ?: 'info@markentrix.de',    // Empfänger der Anfragen
  'from'           => getenv('MX_MAIL_FROM') ?: 'website@markentrix.de', // Absender, muss zur Domain passen (SPF/DKIM beim Hoster)
  'subject_prefix' => '[markentrix.de] ',
  'webhook'        => getenv('MX_WEBHOOK') ?: '',      // optional, z. B. https://n8n.example.de/webhook/markentrix-anfrage
  'log_file'       => getenv('MX_LOG_FILE') !== false ? (string) getenv('MX_LOG_FILE') : dirname(__DIR__, 2) . '/anfragen.log', // außerhalb des Webroots; '' = kein Protokoll
  'smtp_host'      => getenv('MX_SMTP_HOST') ?: '',    // leer = mail() verwenden
  'smtp_port'      => (int) (getenv('MX_SMTP_PORT') ?: 465),
  'smtp_user'      => getenv('MX_SMTP_USER') ?: '',
  'smtp_pass'      => getenv('MX_SMTP_PASS') ?: '',
  'smtp_security'  => getenv('MX_SMTP_SECURITY') ?: '', // ssl (Standard bei 465), tls = STARTTLS (Standard sonst), none = nur für lokale Relays
  'rate_limit'     => 6,                               // Anfragen je IP …
  'rate_window'    => 600,                             // … innerhalb von Sekunden
  'max_len'        => 4000,
];

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function respond(int $status, array $body): void {
  http_response_code($status);
  echo json_encode($body, JSON_UNESCAPED_UNICODE);
  exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
  respond(405, ['ok' => false, 'error' => 'method']);
}

// Eingabe lesen (JSON bevorzugt, sonst klassische Formulardaten)
$raw  = (string) file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
  $data = $_POST;
}
if (!is_array($data) || !$data) {
  respond(400, ['ok' => false, 'error' => 'empty']);
}

// Honeypot: Bots füllen das versteckte Feld aus → still "ok" zurückgeben
if (!empty($data['website'])) {
  respond(200, ['ok' => true]);
}

// Felder bereinigen
$clean = [];
foreach ($data as $key => $value) {
  if (!is_string($key) || !preg_match('/^[a-z_\-]{1,40}$/i', $key)) continue;
  if (is_array($value)) $value = implode(', ', array_map('strval', $value));
  $value = trim(strip_tags((string) $value));
  $value = preg_replace('/[\r\n]+/', "\n", $value);
  $clean[$key] = mb_substr($value, 0, $CONFIG['max_len']);
}

$name  = $clean['name']  ?? '';
$email = $clean['email'] ?? '';
if ($name === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
  respond(422, ['ok' => false, 'error' => 'fields']);
}
if (($clean['einwilligung'] ?? '') !== 'ja') {
  respond(422, ['ok' => false, 'error' => 'consent']);
}

// Ratenbegrenzung je IP (einfach, dateibasiert)
$ip   = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
$ip   = trim(explode(',', $ip)[0]);
$rate = sys_get_temp_dir() . '/mx-rate-' . hash('sha256', $ip) . '.json';
$hits = [];
if (is_file($rate)) {
  $hits = json_decode((string) file_get_contents($rate), true) ?: [];
}
$now  = time();
$hits = array_values(array_filter($hits, fn($t) => $now - (int) $t < $CONFIG['rate_window']));
if (count($hits) >= $CONFIG['rate_limit']) {
  respond(429, ['ok' => false, 'error' => 'rate']);
}
$hits[] = $now;
@file_put_contents($rate, json_encode($hits));

// E-Mail zusammensetzen
$quelle  = $clean['quelle'] ?? 'Website';
$order   = ['quelle', 'name', 'firma', 'email', 'tel', 'thema', 'budget', 'bedarf', 'status', 'zeitplan', 'branche', 'kanal', 'anfragen', 'empfehlung', 'wunschtermin', 'termin_iso', 'nachricht_text', 'seite', 'zeit'];
$lines   = [];
foreach ($order as $k) {
  if (isset($clean[$k]) && $clean[$k] !== '') $lines[] = str_pad($k, 14) . ': ' . $clean[$k];
}
foreach ($clean as $k => $v) {
  if (!in_array($k, $order, true) && !in_array($k, ['nachricht', 'form-name', 'einwilligung'], true) && $v !== '') $lines[] = str_pad($k, 14) . ': ' . $v;
}
$lines[] = str_pad('einwilligung', 14) . ': ja (' . gmdate('c') . ' UTC, IP-Hash ' . substr(hash('sha256', $ip), 0, 12) . ')';
$body    = "Neue Anfrage über markentrix.de\n\n" . implode("\n", $lines) . "\n";
$subject = $CONFIG['subject_prefix'] . $quelle . ': ' . $name;

$fromName = '=?UTF-8?B?' . base64_encode('Markentrix Website') . '?=';
$headers  = [
  'From: ' . $fromName . ' <' . $CONFIG['from'] . '>',
  'Reply-To: ' . $email,
  'MIME-Version: 1.0',
  'Content-Type: text/plain; charset=UTF-8',
  'Content-Transfer-Encoding: 8bit',
  'X-Mailer: markentrix-website',
];
$encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';

/** Minimaler SMTP-Versand (AUTH LOGIN, SSL auf 465 oder STARTTLS auf 587). Gibt true/false zurück. */
function smtp_send(array $c, string $to, string $subject, string $body, array $headers): bool {
  $sec  = $c['smtp_security'] ?: ($c['smtp_port'] === 465 ? 'ssl' : 'tls');
  $ssl  = $sec === 'ssl';
  $ctx  = stream_context_create(['ssl' => ['verify_peer' => true, 'verify_peer_name' => true, 'SNI_enabled' => true, 'peer_name' => $c['smtp_host']]]);
  $sock = @stream_socket_client(($ssl ? 'ssl://' : 'tcp://') . $c['smtp_host'] . ':' . $c['smtp_port'], $errno, $errstr, 10, STREAM_CLIENT_CONNECT, $ctx);
  if (!$sock) return false;
  stream_set_timeout($sock, 10);
  $read = function () use ($sock): string {
    $out = '';
    while (($line = fgets($sock, 1024)) !== false) { $out .= $line; if (!isset($line[3]) || $line[3] !== '-') break; }
    return $out;
  };
  $cmd = function (string $line, string $expect) use ($sock, $read): bool {
    fwrite($sock, $line . "\r\n");
    return strpos($read(), $expect) === 0;
  };
  if (strpos($read(), '220') !== 0) { fclose($sock); return false; }
  $host = $_SERVER['SERVER_NAME'] ?? 'markentrix.de';
  if (!$cmd('EHLO ' . $host, '250')) { fclose($sock); return false; }
  if ($sec === 'tls') {
    if (!$cmd('STARTTLS', '220') || !@stream_socket_enable_crypto($sock, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) { fclose($sock); return false; }
    if (!$cmd('EHLO ' . $host, '250')) { fclose($sock); return false; }
  }
  $ok = ($c['smtp_user'] === '' || ($cmd('AUTH LOGIN', '334') && $cmd(base64_encode($c['smtp_user']), '334') && $cmd(base64_encode($c['smtp_pass']), '235')))
     && $cmd('MAIL FROM:<' . $c['from'] . '>', '250') && $cmd('RCPT TO:<' . $to . '>', '250') && $cmd('DATA', '354');
  if ($ok) {
    $msg = implode("\r\n", array_merge(['To: ' . $to, 'Subject: ' . $subject, 'Date: ' . date(DATE_RFC2822)], $headers)) . "\r\n\r\n"
         . preg_replace('/^\./m', '..', str_replace("\n", "\r\n", $body));
    fwrite($sock, $msg . "\r\n.\r\n");
    $ok = strpos($read(), '250') === 0;
  }
  @fwrite($sock, "QUIT\r\n");
  fclose($sock);
  return $ok;
}

if ($CONFIG['smtp_host'] !== '') {
  $sent = smtp_send($CONFIG, $CONFIG['to'], $encodedSubject, $body, $headers);
} else {
  $sent = @mail($CONFIG['to'], $encodedSubject, $body, implode("\r\n", $headers), '-f' . $CONFIG['from']);
}

// Optional: Weiterleitung an Webhook (Fehler dort blockieren den Nutzer nicht)
if ($CONFIG['webhook'] !== '' && function_exists('curl_init')) {
  $ch = curl_init($CONFIG['webhook']);
  curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_POSTFIELDS => json_encode($clean, JSON_UNESCAPED_UNICODE),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 5,
  ]);
  @curl_exec($ch);
  curl_close($ch);
}

// Optional: Protokoll (eine JSON-Zeile je Anfrage, außerhalb des Webroots)
if ($CONFIG['log_file'] !== '') {
  @file_put_contents($CONFIG['log_file'], json_encode(['t' => gmdate('c'), 'sent' => $sent] + $clean, JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
}

if (!$sent) {
  respond(500, ['ok' => false, 'error' => 'mail']);
}
respond(200, ['ok' => true]);
