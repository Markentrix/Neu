<?php
/**
 * Markentrix · Wochenbericht über Anfragen, Website-Checks und Bewerbungen (nur Kommandozeile).
 *
 * Liest das Eingangsprotokoll (MX_LOG_FILE, eine JSON-Zeile je Anfrage) und schickt eine Zusammenfassung der letzten
 * 7 Tage per E-Mail an MX_MAIL_TO. Gleiche Umgebungsvariablen wie anfrage.php (SMTP-Zugang, Absender, Empfänger).
 * Es wird immer gesendet, auch ohne Anfragen: Bleibt die Mail aus, läuft etwas nicht.
 *
 * Aufruf im PHP-Container (siehe docs/server/WOCHENBERICHT.md):
 *   php /srv/sites/markentrix/api/wochenbericht.php            sendet den Bericht
 *   php /srv/sites/markentrix/api/wochenbericht.php --dry      zeigt den Text, sendet nichts
 *   php /srv/sites/markentrix/api/wochenbericht.php --tage=14  anderer Zeitraum
 */
declare(strict_types=1);

if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require_once __DIR__ . '/mx-mail.php';
date_default_timezone_set('Europe/Berlin');

$opts = getopt('', ['dry', 'tage::']);
$dry = isset($opts['dry']);
$days = max(1, min(60, (int) ($opts['tage'] ?? 7)));

$C = [
  'to'            => getenv('MX_MAIL_TO') ?: 'info@markentrix.de',
  'from'          => getenv('MX_MAIL_FROM') ?: 'website@markentrix.de',
  'smtp_host'     => getenv('MX_SMTP_HOST') ?: '',
  'smtp_port'     => (int) (getenv('MX_SMTP_PORT') ?: 465),
  'smtp_user'     => getenv('MX_SMTP_USER') ?: '',
  'smtp_pass'     => getenv('MX_SMTP_PASS') ?: '',
  'smtp_security' => getenv('MX_SMTP_SECURITY') ?: '',
];
$logFile = getenv('MX_LOG_FILE') !== false ? (string) getenv('MX_LOG_FILE') : '';
if ($logFile === '') { fwrite(STDERR, "MX_LOG_FILE ist nicht gesetzt.\n"); exit(1); }

// Protokoll lesen
$now = time();
$curFrom = $now - $days * 86400; $prevFrom = $curFrom - $days * 86400;
$cur = []; $prev = [];
if (is_file($logFile)) {
  $fh = fopen($logFile, 'r');
  while ($fh && ($line = fgets($fh)) !== false) {
    $r = json_decode(trim($line), true);
    if (!is_array($r) || empty($r['t'])) continue;
    $ts = strtotime((string) $r['t']);
    if (!$ts) continue;
    $r['_ts'] = $ts;
    if ($ts >= $curFrom) $cur[] = $r; elseif ($ts >= $prevFrom) $prev[] = $r;
  }
  if ($fh) fclose($fh);
}
usort($cur, fn($a, $b) => $b['_ts'] <=> $a['_ts']);

function by(array $rows, callable $f): array { $o = []; foreach ($rows as $r) { $k = $f($r); if ($k === null || $k === '') continue; $o[$k] = ($o[$k] ?? 0) + 1; } arsort($o); return $o; }
function quelle(array $r): string { return (string) ($r['quelle'] ?? 'Sonstige'); }
function herkunft(array $r): string {
  foreach (['kanal' => 'Angabe', 'utm_source' => 'Link', 'utm_referrer' => 'Verweis'] as $k => $t) if (!empty($r[$k])) return $t . ': ' . $r[$k];
  return 'direkt oder unbekannt';
}
function pct(int $a, int $b): string { if ($b === 0) return $a > 0 ? 'neu' : '0'; $d = $a - $b; return ($d >= 0 ? '+' : '') . $d . ' zur Vorperiode (' . $b . ')'; }

$total = count($cur); $totalPrev = count($prev);
$byQ = by($cur, 'quelle'); $byQPrev = by($prev, 'quelle');
$failed = array_values(array_filter($cur, fn($r) => array_key_exists('sent', $r) && $r['sent'] === false));
$wish = count(array_filter($cur, fn($r) => ($r['kontakt_gewuenscht'] ?? '') === 'ja'));
$reports = count(array_filter($cur, fn($r) => !empty($r['bericht'])));
$scores = [];
foreach ($cur as $r) if (quelle($r) === 'Website-Check' && preg_match('/\((\d+) von 100\)/', (string) ($r['website_check'] ?? ''), $m)) $scores[] = (int) $m[1];
$avg = $scores ? (int) round(array_sum($scores) / count($scores)) : null;
$byH = by($cur, 'herkunft');
$byPage = by($cur, fn($r) => $r['seite'] ?? null);
$byNeed = by($cur, fn($r) => $r['bedarf'] ?? ($r['thema'] ?? null));
$byRole = by(array_filter($cur, fn($r) => quelle($r) === 'Bewerbung'), fn($r) => $r['rolle'] ?? null);

$from = date('d.m.Y', $curFrom); $to = date('d.m.Y', $now);
$h = fn(string $x): string => htmlspecialchars($x, ENT_QUOTES, 'UTF-8');
$list = function (array $m, int $n = 6): array { return array_slice($m, 0, $n, true); };

// Text
$t = "Wochenbericht markentrix.de · $from bis $to ($days Tage)\n\n";
$t .= "Anfragen insgesamt: $total (" . pct($total, $totalPrev) . ")\n";
foreach ($byQ as $q => $n) $t .= "  $q: $n" . (isset($byQPrev[$q]) ? " (Vorperiode " . $byQPrev[$q] . ")" : '') . "\n";
$t .= "Kontaktwunsch ausdrücklich: $wish\nWebsite-Check-Berichte versendet: $reports" . ($avg !== null ? ", Durchschnitt der Bewertungen: $avg von 100" : '') . "\n";
if ($failed) {
  $t .= "\nACHTUNG: " . count($failed) . " Anfrage(n) konnten nicht per E-Mail zugestellt werden (nur im Protokoll vorhanden):\n";
  foreach ($failed as $r) $t .= '  ' . date('d.m. H:i', $r['_ts']) . '  ' . quelle($r) . '  ' . ($r['name'] ?? '') . '  ' . ($r['email'] ?? '') . "\n";
}
foreach (['Herkunft' => $byH, 'Seiten' => $byPage, 'Anliegen und Themen' => $byNeed, 'Bewerbungen nach Rolle' => $byRole] as $title => $m) {
  if (!$m) continue;
  $t .= "\n$title\n"; foreach ($list($m) as $k => $n) $t .= "  $n x  $k\n";
}
$t .= "\nEinzelne Eingänge (neueste zuerst)\n";
if (!$cur) $t .= "  Keine Anfragen in diesem Zeitraum.\n";
foreach (array_slice($cur, 0, 40) as $r) {
  $info = array_filter([$r['rolle'] ?? '', $r['bedarf'] ?? '', $r['thema'] ?? '', $r['website_check'] ?? '']);
  $t .= '  ' . date('d.m. H:i', $r['_ts']) . '  ' . str_pad(quelle($r), 15) . ' ' . ($r['name'] ?? '') . (!empty($r['firma']) ? ' (' . $r['firma'] . ')' : '') . '  ' . ($r['email'] ?? '') . (!empty($r['tel']) ? '  ' . $r['tel'] : '')
      . (($r['kontakt_gewuenscht'] ?? '') === 'ja' ? '  [Kontaktwunsch]' : '') . ($info ? '  · ' . implode(' · ', $info) : '') . "\n";
}
if (count($cur) > 40) $t .= '  … und ' . (count($cur) - 40) . " weitere im Protokoll.\n";
$t .= "\nDieser Bericht entsteht automatisch aus dem Eingangsprotokoll auf dem Server. Er enthält personenbezogene Daten, bitte vertraulich behandeln und nicht weiterleiten.\n";

// HTML
$row = fn(string $a, string $b) => '<tr><td style="padding:6px 0;border-bottom:1px solid #E8ECF3">' . $h($a) . '</td><td align="right" style="padding:6px 0;border-bottom:1px solid #E8ECF3;font-weight:bold">' . $h($b) . '</td></tr>';
$m = '<!doctype html><html lang="de"><body style="margin:0;background:#F4F6FA;font-family:Arial,Helvetica,sans-serif;color:#2C3446"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">'
   . '<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#fff;border-radius:14px;overflow:hidden">'
   . '<tr><td style="background:#0B1020;padding:20px 28px;color:#fff;font-size:15px;letter-spacing:.3em;font-weight:bold">MARKENTRIX</td></tr>'
   . '<tr><td style="padding:24px 28px 8px"><p style="margin:0 0 4px;font-size:13px;color:#6D3FD1;letter-spacing:.08em;text-transform:uppercase;font-weight:bold">Wochenbericht · ' . $h($from) . ' bis ' . $h($to) . '</p>'
   . '<h1 style="margin:0 0 12px;font-size:24px;color:#0B1020">' . $total . ' Anfragen' . ($total === 1 ? '' : '') . '</h1><p style="margin:0 0 14px;font-size:14px">' . $h(pct($total, $totalPrev)) . '. Kontaktwunsch ausdrücklich: ' . $wish . '. Website-Check-Berichte versendet: ' . $reports . ($avg !== null ? ', Durchschnitt der Bewertungen ' . $avg . ' von 100' : '') . '.</p>';
if ($failed) {
  $m .= '<div style="background:#FBE4E4;border:1px solid #F3BDBD;border-radius:10px;padding:12px 14px;margin:0 0 14px;color:#991B1B;font-size:14px"><b>Achtung:</b> ' . count($failed) . ' Anfrage(n) konnten nicht per E-Mail zugestellt werden und stehen nur im Protokoll:<br>';
  foreach ($failed as $r) $m .= $h(date('d.m. H:i', $r['_ts']) . '  ' . quelle($r) . '  ' . ($r['name'] ?? '') . '  ' . ($r['email'] ?? '')) . '<br>';
  $m .= '</div>';
}
$m .= '</td></tr>';
$sections = ['Nach Quelle' => $byQ, 'Herkunft' => $byH, 'Seiten' => $byPage, 'Anliegen und Themen' => $byNeed, 'Bewerbungen nach Rolle' => $byRole];
foreach ($sections as $title => $mm) {
  if (!$mm) continue;
  $m .= '<tr><td style="padding:8px 28px"><p style="margin:10px 0 4px;font-size:15px;font-weight:bold;color:#0B1020">' . $h($title) . '</p><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px">';
  foreach ($list($mm, 8) as $k => $n) $m .= $row((string) $k, (string) $n);
  $m .= '</table></td></tr>';
}
$m .= '<tr><td style="padding:12px 28px 4px"><p style="margin:10px 0 6px;font-size:15px;font-weight:bold;color:#0B1020">Einzelne Eingänge</p>';
if (!$cur) $m .= '<p style="margin:0;font-size:14px">Keine Anfragen in diesem Zeitraum.</p>';
foreach (array_slice($cur, 0, 40) as $r) {
  $info = array_filter([$r['rolle'] ?? '', $r['bedarf'] ?? '', $r['thema'] ?? '', $r['website_check'] ?? '']);
  $m .= '<div style="border:1px solid #E3E8F0;border-radius:8px;padding:9px 12px;margin-bottom:6px;font-size:13px;line-height:1.5"><b style="color:#0B1020">' . $h((string) ($r['name'] ?? '')) . '</b>' . (!empty($r['firma']) ? ' · ' . $h((string) $r['firma']) : '')
      . ' <span style="color:#5B6478">· ' . $h(date('d.m. H:i', $r['_ts'])) . ' · ' . $h(quelle($r)) . '</span>' . (($r['kontakt_gewuenscht'] ?? '') === 'ja' ? ' <span style="background:#E3F4EA;color:#116430;font-weight:bold;font-size:11px;padding:2px 7px;border-radius:999px">KONTAKTWUNSCH</span>' : '')
      . '<br>' . $h((string) ($r['email'] ?? '')) . (!empty($r['tel']) ? ' · ' . $h((string) $r['tel']) : '') . ($info ? '<br><span style="color:#5B6478">' . $h(implode(' · ', $info)) . '</span>' : '') . '</div>';
}
if (count($cur) > 40) $m .= '<p style="font-size:13px">… und ' . (count($cur) - 40) . ' weitere im Protokoll.</p>';
$m .= '</td></tr><tr><td style="background:#F8FAFD;padding:14px 28px;font-size:12px;line-height:1.5;color:#5B6478">Dieser Bericht entsteht automatisch aus dem Eingangsprotokoll auf dem Server. Er enthält personenbezogene Daten, bitte vertraulich behandeln und nicht weiterleiten.</td></tr></table></td></tr></table></body></html>';

if ($dry) { echo $t; exit(0); }
$b = 'mx' . bin2hex(random_bytes(8));
$body = "--$b\nContent-Type: text/plain; charset=UTF-8\nContent-Transfer-Encoding: base64\n\n" . rtrim(chunk_split(base64_encode($t), 76, "\n")) . "\n"
      . "--$b\nContent-Type: text/html; charset=UTF-8\nContent-Transfer-Encoding: base64\n\n" . rtrim(chunk_split(base64_encode($m), 76, "\n")) . "\n--$b--\n";
$fromName = '=?UTF-8?B?' . base64_encode('Markentrix Website') . '?=';
$headers = ['From: ' . $fromName . ' <' . $C['from'] . '>', 'MIME-Version: 1.0', 'Content-Type: multipart/alternative; boundary="' . $b . '"', 'Auto-Submitted: auto-generated', 'X-Mailer: markentrix-wochenbericht'];
$subject = 'Wochenbericht markentrix.de: ' . $total . ' Anfragen' . ($failed ? ' (ACHTUNG: Zustellfehler)' : '');
$ok = deliver($C, $C['to'], '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, $headers);
echo $ok ? "Wochenbericht gesendet an {$C['to']} ($total Anfragen).\n" : "Versand fehlgeschlagen.\n";
exit($ok ? 0 : 2);
