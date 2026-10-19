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
  'confirm'        => getenv('MX_CONFIRM') !== '0',     // Bestätigungsmail an Absender; MX_CONFIRM=0 schaltet sie ab
  'confirm_max'    => 2,                                // höchstens so viele Bestätigungen je Adresse in 24 Stunden
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
$order   = ['quelle', 'name', 'firma', 'email', 'tel', 'thema', 'budget', 'aktion', 'bedarf', 'status', 'zeitplan', 'branche', 'kanal', 'anfragen', 'empfehlung', 'wunschtermin', 'termin_iso', 'nachricht_text', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_referrer', 'website_check', 'kontakt_gewuenscht', 'seite', 'zeit'];
$lines   = [];
foreach ($order as $k) {
  if (isset($clean[$k]) && $clean[$k] !== '') $lines[] = str_pad($k, 14) . ': ' . $clean[$k];
}
foreach ($clean as $k => $v) {
  if (!in_array($k, $order, true) && !in_array($k, ['nachricht', 'form-name', 'einwilligung', 'bericht_token'], true) && $v !== '') $lines[] = str_pad($k, 14) . ': ' . $v;
}
// Website-Check: Bericht aus dem temporären Speicher laden (Token wurde vom Check erzeugt, nicht frei wählbar)
$report = null; $reportFile = '';
if ($quelle === 'Website-Check' && preg_match('/^[a-f0-9]{32}$/', (string) ($clean['bericht_token'] ?? ''))) {
  $reportFile = sys_get_temp_dir() . '/mx-report-' . $clean['bericht_token'] . '.json';
  if (is_file($reportFile) && @filemtime($reportFile) > time() - 7200) $report = json_decode((string) file_get_contents($reportFile), true);
  if (!is_array($report) || empty($report['categories'])) $report = null;
}
if ($report) {
  $lines[] = '';
  $lines[] = 'Website-Check ' . $report['host'] . ': ' . $report['score'] . ' von 100 (' . $report['grade'] . ')' . ($report['cap'] ? ', gedeckelt: ' . $report['cap'] : '');
  foreach ($report['categories'] as $cat) $lines[] = '  ' . str_pad((string) $cat['score'], 3, ' ', STR_PAD_LEFT) . '  ' . $cat['title'];
  $worst = [];
  foreach ($report['categories'] as $cat) foreach ($cat['items'] as $it) if ($it['status'] === 'bad') $worst[] = '  - ' . $it['title'];
  if ($worst) { $lines[] = 'Mangelhaft:'; foreach (array_slice($worst, 0, 12) as $w) $lines[] = $w; }
  $lines[] = '';
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

/** Versand über SMTP oder mail(), je nach Konfiguration. */
function deliver(array $c, string $to, string $encodedSubject, string $body, array $headers): bool {
  if ($c['smtp_host'] !== '') return smtp_send($c, $to, $encodedSubject, $body, $headers);
  return @mail($to, $encodedSubject, $body, implode("\r\n", $headers), '-f' . $c['from']);
}

$sent = deliver($CONFIG, $CONFIG['to'], $encodedSubject, $body, $headers);

/** Baut die Bericht-Mail (Text und HTML) aus dem Ergebnis des Website-Checks. */
function report_mail(array $r, string $name): array {
  $h = fn(string $x): string => htmlspecialchars($x, ENT_QUOTES, 'UTF-8');
  $label = ['bad' => 'Mangelhaft', 'warn' => 'Auffällig', 'ok' => 'In Ordnung', 'info' => 'Hinweis'];
  $gradeTxt = ['stark' => 'Starke Grundlagen, wenige Lücken.', 'gut' => 'Solide, aber mit spürbaren Lücken.', 'mittel' => 'Mittelmaß: hier bleiben Anfragen liegen.', 'schwach' => 'Erheblicher Rückstand bei Auffindbarkeit und Vertrauen.'][$r['grade']] ?? '';
  $order = ['bad' => 0, 'warn' => 1, 'ok' => 2, 'info' => 3];
  $link = 'https://markentrix.de/kontakt?utm_source=website-check&utm_medium=email&utm_campaign=bericht';
  $hello = 'Guten Tag ' . preg_replace('/[\x00-\x1F\x7F]/', '', mb_substr($name, 0, 80)) . ',';
  // Text
  $t = $hello . "\n\nhier ist Ihr Website-Check für " . $r['host'] . " vom " . $r['date'] . ".\n\n"
     . 'Gesamtwertung: ' . $r['score'] . " von 100\n" . $gradeTxt . "\n" . ($r['cap'] ? 'Gedeckelt wegen: ' . $r['cap'] . "\n" : '')
     . $r['checks'] . ' Merkmale geprüft: ' . $r['counts']['ok'] . ' in Ordnung, ' . $r['counts']['warn'] . ' auffällig, ' . $r['counts']['bad'] . " mangelhaft.\n\nBereichswerte\n";
  foreach ($r['categories'] as $c) $t .= '  ' . str_pad((string) $c['score'], 3, ' ', STR_PAD_LEFT) . ' von 100  ' . $c['title'] . "\n";
  foreach ($r['categories'] as $c) {
    $t .= "\n" . mb_strtoupper($c['title']) . "\n";
    $its = $c['items']; usort($its, fn($a, $b) => $order[$a['status']] <=> $order[$b['status']]);
    foreach ($its as $i) $t .= '[' . $label[$i['status']] . '] ' . $i['title'] . "\n    " . $i['detail'] . "\n";
  }
  $t .= "\nSo lesen Sie den Bericht: Die Punktzahl ist ein Orientierungswert, keine Messung von Rankings. Geprüft wurden Startseite, robots.txt, Sitemap, llms.txt, eine nicht vorhandene Adresse und eine Stichprobe interner Seiten. Nicht geprüft werden Rankings, die tatsächliche Ladezeit auf dem Smartphone, Texte, Backlinks, Google-Bewertungen und die rechtliche Vollständigkeit von Impressum und Datenschutzerklärung.\n\n"
      . "Was davon für Ihren Betrieb wirklich zählt, ordnen wir gern mit Ihnen ein: Im kostenlosen Erstgespräch, rund 30 Minuten, unverbindlich.\n"
      . "Termin vereinbaren: " . $link . "\nOder antworten Sie auf diese E-Mail, oder rufen Sie an: 0176 20370429, Mo bis Do 09:00 bis 17:00 Uhr, Fr 09:00 bis 15:00 Uhr.\n\n"
      . "Sie erhalten diese Nachricht einmalig, weil Sie den Bericht auf markentrix.de angefordert haben. Weitere Werbe-E-Mails senden wir nur mit Ihrer ausdrücklichen Einwilligung. Hinweise zum Datenschutz: https://markentrix.de/datenschutz\n\n"
      . "Markentrix · Christian Wien · Celle\nhttps://markentrix.de · info@markentrix.de\nImpressum: https://markentrix.de/impressum\n";
  // HTML (Tabellenlayout, Stile inline, wie in E-Mails üblich)
  $col = fn(int $sc): string => $sc >= 80 ? '#15803D' : ($sc >= 55 ? '#D97706' : '#B91C1C');
  $badge = ['bad' => ['#FBE4E4', '#991B1B'], 'warn' => ['#FDF0DC', '#8A4308'], 'ok' => ['#E3F4EA', '#116430'], 'info' => ['#EEF1F6', '#33405A']];
  $m = '<!doctype html><html lang="de"><body style="margin:0;background:#F4F6FA;font-family:Arial,Helvetica,sans-serif;color:#2C3446"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">'
     . '<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#fff;border-radius:14px;overflow:hidden">'
     . '<tr><td style="background:#0B1020;padding:22px 28px;color:#fff;font-size:15px;letter-spacing:.3em;font-weight:bold">MARKENTRIX</td></tr>'
     . '<tr><td style="padding:28px 28px 8px"><p style="margin:0 0 6px;font-size:13px;color:#6D3FD1;letter-spacing:.08em;text-transform:uppercase;font-weight:bold">Website-Check · ' . $h($r['date']) . '</p>'
     . '<h1 style="margin:0 0 6px;font-size:24px;line-height:1.25;color:#0B1020">' . $h($r['host']) . '</h1><p style="margin:0 0 14px;font-size:15px">' . $h($hello) . ' hier ist Ihr Bericht.</p>'
     . '<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;background:#F8FAFD;border:1px solid #E3E8F0;border-radius:12px"><tr><td style="padding:18px 20px;width:110px"><div style="font-size:44px;line-height:1;font-weight:bold;color:' . $col((int) $r['score']) . '">' . (int) $r['score'] . '</div><div style="font-size:12px;color:#5B6478">von 100</div></td>'
     . '<td style="padding:18px 20px 18px 0"><div style="font-size:17px;font-weight:bold;color:#0B1020">' . $h($gradeTxt) . '</div><div style="font-size:13px;margin-top:6px">' . (int) $r['checks'] . ' Merkmale geprüft: ' . (int) $r['counts']['ok'] . ' in Ordnung, ' . (int) $r['counts']['warn'] . ' auffällig, ' . (int) $r['counts']['bad'] . ' mangelhaft.</div>'
     . ($r['cap'] ? '<div style="font-size:13px;margin-top:6px;color:#B91C1C;font-weight:bold">Gedeckelt wegen: ' . $h($r['cap']) . '</div>' : '') . '</td></tr></table></td></tr>'
     . '<tr><td style="padding:14px 28px 4px"><p style="margin:0 0 8px;font-size:14px;font-weight:bold;color:#0B1020">Bereichswerte</p>';
  foreach ($r['categories'] as $c) {
    $m .= '<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;margin-bottom:8px"><tr><td style="font-size:13px;padding-bottom:3px">' . $h($c['title']) . '</td><td align="right" style="font-size:13px;font-weight:bold;color:#0B1020">' . (int) $c['score'] . ' / 100</td></tr>'
        . '<tr><td colspan="2" style="background:#E8ECF3;border-radius:6px;height:8px;line-height:8px;font-size:0"><div style="width:' . max(2, (int) $c['score']) . '%;background:' . $col((int) $c['score']) . ';height:8px;border-radius:6px"></div></td></tr></table>';
  }
  $m .= '</td></tr>';
  foreach ($r['categories'] as $c) {
    $m .= '<tr><td style="padding:18px 28px 0"><p style="margin:0 0 8px;font-size:16px;font-weight:bold;color:#0B1020;border-top:1px solid #E3E8F0;padding-top:14px">' . $h($c['title']) . '</p>';
    $its = $c['items']; usort($its, fn($a, $b) => $order[$a['status']] <=> $order[$b['status']]);
    foreach ($its as $i) {
      $b = $badge[$i['status']];
      $m .= '<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;margin-bottom:8px;border:1px solid #E3E8F0;border-left:4px solid ' . $b[1] . ';border-radius:8px"><tr><td style="padding:10px 12px"><span style="display:inline-block;background:' . $b[0] . ';color:' . $b[1] . ';font-size:11px;font-weight:bold;letter-spacing:.05em;text-transform:uppercase;padding:3px 8px;border-radius:999px">' . $label[$i['status']] . '</span>'
          . '<div style="font-size:14px;font-weight:bold;color:#0B1020;margin-top:6px">' . $h($i['title']) . '</div><div style="font-size:13px;line-height:1.5;margin-top:3px">' . $h($i['detail']) . '</div></td></tr></table>';
    }
    $m .= '</td></tr>';
  }
  $m .= '<tr><td style="padding:22px 28px 6px"><p style="margin:0;font-size:12px;line-height:1.5;color:#5B6478">So lesen Sie den Bericht: Die Punktzahl ist ein Orientierungswert, keine Messung von Rankings. Nicht geprüft werden Rankings, die tatsächliche Ladezeit auf dem Smartphone, Texte, Backlinks, Google-Bewertungen und die rechtliche Vollständigkeit von Impressum und Datenschutzerklärung.</p></td></tr>'
      . '<tr><td style="padding:16px 28px 28px"><div style="background:#F3EFFD;border:1px solid #DCD0F7;border-radius:12px;padding:20px"><p style="margin:0 0 8px;font-size:17px;font-weight:bold;color:#0B1020">Was davon zählt für Ihren Betrieb?</p>'
      . '<p style="margin:0 0 14px;font-size:14px;line-height:1.5">Wir ordnen die Befunde gern mit Ihnen ein: im kostenlosen Erstgespräch, rund 30 Minuten, unverbindlich.</p>'
      . '<a href="' . $h($link) . '" style="display:inline-block;background:#1E9BFF;color:#06101F;font-weight:bold;font-size:15px;text-decoration:none;padding:12px 22px;border-radius:10px">Gespräch vereinbaren</a>'
      . '<p style="margin:14px 0 0;font-size:13px">Oder rufen Sie an: <b>0176 20370429</b> (Mo bis Do 09:00 bis 17:00 Uhr, Fr 09:00 bis 15:00 Uhr) oder antworten Sie auf diese E-Mail.</p></div></td></tr>'
      . '<tr><td style="background:#F8FAFD;padding:16px 28px;font-size:12px;line-height:1.5;color:#5B6478">Sie erhalten diese Nachricht einmalig, weil Sie den Bericht auf markentrix.de angefordert haben. Weitere Werbe-E-Mails senden wir nur mit Ihrer ausdrücklichen Einwilligung. <a href="https://markentrix.de/datenschutz" style="color:#0B63C6">Datenschutz</a> · <a href="https://markentrix.de/impressum" style="color:#0B63C6">Impressum</a><br>Markentrix · Christian Wien · Celle · info@markentrix.de</td></tr>'
      . '</table></td></tr></table></body></html>';
  return [$t, $m];
}

// Bericht des Website-Checks an den Absender (statt der allgemeinen Bestätigung)
$reported = false;
if ($sent && $report) {
  $rrate = sys_get_temp_dir() . '/mx-rep-' . hash('sha256', strtolower($email)) . '.json';
  $rhits = is_file($rrate) ? (json_decode((string) file_get_contents($rrate), true) ?: []) : [];
  $rhits = array_values(array_filter($rhits, fn($t) => $now - (int) $t < 86400));
  if (count($rhits) < 3) {
    [$rText, $rHtml] = report_mail($report, $name);
    $b = 'mx' . bin2hex(random_bytes(8));
    $rBody = "--$b\nContent-Type: text/plain; charset=UTF-8\nContent-Transfer-Encoding: base64\n\n" . rtrim(chunk_split(base64_encode($rText), 76, "\n")) . "\n"
           . "--$b\nContent-Type: text/html; charset=UTF-8\nContent-Transfer-Encoding: base64\n\n" . rtrim(chunk_split(base64_encode($rHtml), 76, "\n")) . "\n" . "--$b--\n";
    $rHeaders = [
      'From: ' . $fromName . ' <' . $CONFIG['from'] . '>', 'Reply-To: ' . $CONFIG['to'], 'MIME-Version: 1.0',
      'Content-Type: multipart/alternative; boundary="' . $b . '"', 'X-Mailer: markentrix-website',
    ];
    $reported = deliver($CONFIG, $email, '=?UTF-8?B?' . base64_encode('Ihr Website-Check-Bericht für ' . $report['host']) . '?=', $rBody, $rHeaders);
    if ($reported) { $rhits[] = $now; @file_put_contents($rrate, json_encode($rhits)); @unlink($reportFile); }
  }
}

// Bestätigung an den Absender: kurze, sachliche Eingangsbestätigung ohne Werbung.
$confirmed = false;
if ($sent && $CONFIG['confirm'] && !$report) {
  $crate = sys_get_temp_dir() . '/mx-conf-' . hash('sha256', strtolower($email)) . '.json';
  $chits = is_file($crate) ? (json_decode((string) file_get_contents($crate), true) ?: []) : [];
  $chits = array_values(array_filter($chits, fn($t) => $now - (int) $t < 86400));
  if (count($chits) < $CONFIG['confirm_max']) {
    $labels = ['landingpage' => 'Landingpage', 'website' => 'Unternehmenswebsite', 'relaunch' => 'Relaunch einer bestehenden Website', 'funnel' => 'Website mit Anfragestrecke', 'unklar' => 'Noch offen, Beratung gewünscht'];
    $about = [];
    if (!empty($clean['bedarf']) && isset($labels[$clean['bedarf']])) $about[] = 'Anliegen: ' . $labels[$clean['bedarf']];
    if (!empty($clean['thema'])) $about[] = 'Thema: ' . mb_substr($clean['thema'], 0, 120);
    if (!empty($clean['wunschtermin'])) $about[] = 'Wunschtermin: ' . mb_substr($clean['wunschtermin'], 0, 120);
    if (!empty($clean['nachricht_text'])) $about[] = 'Ihre Nachricht: ' . mb_substr($clean['nachricht_text'], 0, 400);
    $hello = 'Guten Tag ' . preg_replace('/[\x00-\x1F\x7F]/', '', mb_substr($name, 0, 80)) . ',';
    $cbody = $hello . "\n\n"
      . "vielen Dank für Ihre Anfrage bei Markentrix. Sie ist bei uns eingegangen, wir melden uns werktags innerhalb von 24 Stunden persönlich bei Ihnen.\n\n"
      . ($about ? "Ihre Angaben im Überblick:\n" . implode("\n", $about) . "\n\n" : '')
      . "Wie es weitergeht:\n"
      . "1. Wir lesen Ihre Anfrage und melden uns werktags innerhalb von 24 Stunden.\n"
      . "2. Im Erstgespräch, rund 30 Minuten, klären wir Ausgangslage und Ziel.\n"
      . "3. Sie erhalten ein Angebot mit Festpreis und klarem Umfang und entscheiden in Ruhe.\n\n"
      . "Eilig? Rufen Sie uns an: 0176 20370429, Mo bis Do 09:00 bis 17:00 Uhr, Fr 09:00 bis 15:00 Uhr. Oder antworten Sie einfach auf diese E-Mail.\n\n"
      . "Diese Nachricht wurde automatisch versendet, weil Sie das Formular auf markentrix.de ausgefüllt haben. Ihre Angaben verwenden wir ausschließlich zur Bearbeitung Ihrer Anfrage. Hinweise zum Datenschutz: https://markentrix.de/datenschutz\n\n"
      . "Markentrix · Christian Wien · Celle\nhttps://markentrix.de · info@markentrix.de\nImpressum: https://markentrix.de/impressum\n";
    $cheaders = [
      'From: ' . $fromName . ' <' . $CONFIG['from'] . '>',
      'Reply-To: ' . $CONFIG['to'],
      'MIME-Version: 1.0',
      'Content-Type: text/plain; charset=UTF-8',
      'Content-Transfer-Encoding: 8bit',
      'Auto-Submitted: auto-replied',
      'X-Auto-Response-Suppress: All',
      'X-Mailer: markentrix-website',
    ];
    $confirmed = deliver($CONFIG, $email, '=?UTF-8?B?' . base64_encode('Ihre Anfrage bei Markentrix ist eingegangen') . '?=', $cbody, $cheaders);
    if ($confirmed) { $chits[] = $now; @file_put_contents($crate, json_encode($chits)); }
  }
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

// Portal: Lead anlegen, nur beim Website-Check und nur, wenn die Person den Kontaktwunsch freiwillig angekreuzt hat.
// Schlüssel: Umgebungsvariable MX_LEAD_SECRET oder Datei "lead-secret" im Ordner der Protokolldatei (außerhalb des Webroots).
// Fehler hier blockieren den Nutzer nicht.
$leadSent = null;
if ($quelle === 'Website-Check' && ($clean['kontakt_gewuenscht'] ?? '') === 'ja' && function_exists('curl_init')) {
  $leadKey = (string) (getenv('MX_LEAD_SECRET') ?: '');
  if ($leadKey === '' && $CONFIG['log_file'] !== '') {
    $leadKeyFile = dirname($CONFIG['log_file']) . '/lead-secret';
    if (is_file($leadKeyFile)) $leadKey = trim((string) @file_get_contents($leadKeyFile));
  }
  if ($leadKey !== '') {
    $ergebnis = [];
    $leadScore = null;
    if ($report) {
      $leadScore = (int) $report['score'];
      $bad = []; $warn = 0;
      foreach ($report['categories'] as $cat) foreach ($cat['items'] as $it) { if ($it['status'] === 'bad') $bad[] = $cat['title'] . ': ' . $it['title']; elseif ($it['status'] === 'warn') $warn++; }
      $ergebnis = [
        'host' => $report['host'], 'datum' => $report['date'], 'bewertung' => $report['score'], 'stufe' => $report['grade'], 'gedeckelt' => $report['cap'],
        'bereiche' => array_map(fn($c) => ['bereich' => $c['title'], 'wert' => $c['score']], $report['categories']),
        'mangelhaft' => array_slice($bad, 0, 30), 'auffaellig_anzahl' => $warn, 'zaehlung' => $report['counts'],
      ];
    } elseif (!empty($clean['website_check'])) {
      $ergebnis = ['hinweis' => 'Bericht lag nicht mehr vor', 'angabe' => $clean['website_check']];
    }
    $leadBody = json_encode([
      'email' => $email, 'name' => $name, 'firma' => $clean['firma'] ?? '', 'telefon' => $clean['tel'] ?? '',
      'website' => $report ? (string) $report['host'] : '', 'score' => $leadScore, 'ergebnis' => $ergebnis,
      'einwilligung' => true,
      'einwilligung_text' => 'Bericht per E-Mail (Einwilligung) und freiwillig angekreuzt: persönliche Kontaktaufnahme zum Ergebnis, E-Mail oder Telefon (' . gmdate('c') . ' UTC)',
    ], JSON_UNESCAPED_UNICODE);
    $ch = curl_init(getenv('MX_LEAD_URL') ?: 'https://portal.markentrix.de/api/public/website-check');
    curl_setopt_array($ch, [
      CURLOPT_POST => true, CURLOPT_POSTFIELDS => $leadBody, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 6, CURLOPT_CONNECTTIMEOUT => 4,
      CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'X-MK: 1', 'X-Lead-Secret: ' . $leadKey],
    ]);
    @curl_exec($ch);
    $leadSent = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
  }
}

// Portal: normale Anfragen (Kontaktformular, Potenzial-Check, …) als heißen Lead anlegen. Voraussetzung: Einwilligung zur Bearbeitung der Anfrage.
if ($quelle !== 'Website-Check' && $leadSent === null && function_exists('curl_init') && ($clean['einwilligung'] ?? '') === 'ja') {
  $leadKey2 = (string) (getenv('MX_LEAD_SECRET') ?: '');
  if ($leadKey2 === '' && $CONFIG['log_file'] !== '') {
    $leadKeyFile2 = dirname($CONFIG['log_file']) . '/lead-secret';
    if (is_file($leadKeyFile2)) $leadKey2 = trim((string) @file_get_contents($leadKeyFile2));
  }
  if ($leadKey2 !== '') {
    $kBody = json_encode([
      'email' => $email, 'name' => $name, 'firma' => $clean['firma'] ?? '', 'telefon' => $clean['tel'] ?? '',
      'thema' => ($clean['thema'] ?? '') !== '' ? $clean['thema'] : $quelle, 'budget' => $clean['budget'] ?? '',
      'nachricht' => $clean['nachricht_text'] ?? '', 'wunschtermin' => $clean['wunschtermin'] ?? '',
      'einwilligung' => true,
      'einwilligung_text' => 'Anfrage über "' . $quelle . '" mit Einwilligung zur Bearbeitung (' . gmdate('c') . ' UTC)',
    ], JSON_UNESCAPED_UNICODE);
    $kUrl = getenv('MX_LEAD_URL') ?: 'https://portal.markentrix.de/api/public/website-check';
    $kUrl = preg_replace('#/website-check$#', '/kontakt-lead', $kUrl);
    $ch = curl_init($kUrl);
    curl_setopt_array($ch, [
      CURLOPT_POST => true, CURLOPT_POSTFIELDS => $kBody, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 6, CURLOPT_CONNECTTIMEOUT => 4,
      CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'X-MK: 1', 'X-Lead-Secret: ' . $leadKey2],
    ]);
    @curl_exec($ch);
    $leadSent = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
  }
}

// Optional: Protokoll (eine JSON-Zeile je Anfrage, außerhalb des Webroots)
if ($CONFIG['log_file'] !== '') {
  @file_put_contents($CONFIG['log_file'], json_encode(['t' => gmdate('c'), 'sent' => $sent, 'bestaetigt' => $confirmed, 'bericht' => $reported, 'lead' => $leadSent] + array_diff_key($clean, ['bericht_token' => 1]), JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
}

if (!$sent) {
  respond(500, ['ok' => false, 'error' => 'mail']);
}
respond(200, ['ok' => true]);
