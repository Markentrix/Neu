<?php
/**
 * Markentrix · Formular-Endpunkt für Kontaktformular und Potenzial-Check.
 * Läuft auf dem eigenen Server (Hetzner, nginx + PHP-FPM ≥ 7.4). Gleiche Domain, kein CORS.
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
  'to'             => 'info@markentrix.de',            // Empfänger der Anfragen
  'from'           => 'website@markentrix.de',         // Absender, muss zur Domain passen (SPF/DKIM beim Hoster)
  'subject_prefix' => '[markentrix.de] ',
  'webhook'        => '',                              // optional, z. B. https://n8n.example.de/webhook/markentrix-anfrage
  'log_file'       => dirname(__DIR__, 2) . '/anfragen.log', // außerhalb des Webroots; '' = kein Protokoll
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
$order   = ['quelle', 'name', 'firma', 'email', 'tel', 'thema', 'budget', 'branche', 'kanal', 'anfragen', 'empfehlung', 'wunschtermin', 'termin_iso', 'nachricht_text', 'seite', 'zeit'];
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
$sent = @mail($CONFIG['to'], $encodedSubject, $body, implode("\r\n", $headers), '-f' . $CONFIG['from']);

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
