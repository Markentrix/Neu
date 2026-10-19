<?php
/**
 * Markentrix · Website-Schnellcheck (Endpunkt für /website-check).
 *
 * Eingang:  POST /api/check.php  mit JSON {"url":"https://beispiel.de"}
 * Ausgang:  JSON {"ok":true,"url":…,"score":0-100,"groups":[{"title":…,"items":[{"status":"ok|warn|bad|info","title":…,"detail":…}]}]}
 *
 * Was passiert: Die angegebene öffentliche Adresse wird einmal abgerufen (HTML, robots.txt, sitemap.xml)
 * und nach sichtbaren, überprüfbaren Merkmalen ausgewertet. Es werden weder Adresse noch Ergebnis gespeichert
 * oder protokolliert. Für die Ratenbegrenzung liegt kurzzeitig eine Datei im temporären Ordner, benannt nach einem Hash der IP.
 *
 * Schutz gegen Missbrauch: nur http/https auf Port 80/443, nur öffentliche IP-Adressen (auch nach Weiterleitungen, die
 * aufgelöste Adresse wird fest verwendet), höchstens 5 Weiterleitungen, 8 Sekunden je Abruf, 1,5 MB je Antwort,
 * 8 Prüfungen je IP in 10 Minuten. Nur für Tests: MX_CHECK_ALLOW_PRIVATE=1 erlaubt lokale Adressen und Ports.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

const MAX_BYTES = 1500000;
const MAX_HOPS = 5;
const RATE_LIMIT = 8;
const RATE_WINDOW = 600;
$ALLOW_PRIVATE = getenv('MX_CHECK_ALLOW_PRIVATE') === '1';

function respond(int $status, array $body): void {
  http_response_code($status);
  echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}

set_exception_handler(function (Throwable $e) { respond(500, ['ok' => false, 'error' => 'server']); });

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') respond(405, ['ok' => false, 'error' => 'method']);
if (!function_exists('curl_init')) respond(500, ['ok' => false, 'error' => 'server']);

// Herkunft: nur Aufrufe von der eigenen Seite (soweit der Browser einen Origin-Header sendet)
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && !$ALLOW_PRIVATE) {
  $oh = parse_url($origin, PHP_URL_HOST) ?: '';
  $sh = $_SERVER['HTTP_HOST'] ?? '';
  $sh = preg_replace('/:\d+$/', '', (string) $sh);
  if (strcasecmp((string) $oh, (string) $sh) !== 0) respond(403, ['ok' => false, 'error' => 'origin']);
}

$data = json_decode((string) file_get_contents('php://input'), true);
$input = is_array($data) ? trim((string) ($data['url'] ?? '')) : '';
if ($input === '' || strlen($input) > 300) respond(422, ['ok' => false, 'error' => 'url']);
if (!preg_match('#^https?://#i', $input)) $input = 'https://' . $input;

// Ratenbegrenzung je IP
$ip = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
$ip = trim(explode(',', (string) $ip)[0]);
$rateFile = sys_get_temp_dir() . '/mx-check-' . hash('sha256', $ip) . '.json';
$hits = is_file($rateFile) ? (json_decode((string) file_get_contents($rateFile), true) ?: []) : [];
$now = time();
$hits = array_values(array_filter($hits, fn($t) => $now - (int) $t < RATE_WINDOW));
if (count($hits) >= RATE_LIMIT) respond(429, ['ok' => false, 'error' => 'rate']);
$hits[] = $now;
@file_put_contents($rateFile, json_encode($hits));

/** Prüft, ob eine IP öffentlich erreichbar ist (keine privaten, reservierten oder lokalen Bereiche). */
function is_public_ip(string $ip): bool {
  return filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) !== false;
}

/** Löst den Host auf und liefert eine öffentliche IP (IPv4 bevorzugt) oder null. */
function resolve_public(string $host): ?string {
  global $ALLOW_PRIVATE;
  if (filter_var($host, FILTER_VALIDATE_IP)) return ($ALLOW_PRIVATE || is_public_ip($host)) ? $host : null;
  if (!preg_match('/^[a-z0-9]([a-z0-9\-\.]{0,251}[a-z0-9])?$/i', $host) || strpos($host, '.') === false && !$ALLOW_PRIVATE) return null;
  $ips = [];
  $v4 = @gethostbynamel($host);
  if (is_array($v4)) foreach ($v4 as $a) if (is_string($a)) $ips[] = $a;
  $v6 = @dns_get_record($host, DNS_AAAA);
  if (is_array($v6)) foreach ($v6 as $r) if (!empty($r['ipv6'])) $ips[] = (string) $r['ipv6'];
  if (!$ips) return null;
  foreach ($ips as $a) if (!$ALLOW_PRIVATE && !is_public_ip($a)) return null; // ein einziger nichtöffentlicher Eintrag reicht zum Abbruch
  return $ips[0];
}

/**
 * Ruft eine Adresse ab, folgt Weiterleitungen manuell und prüft jeden Schritt.
 * @return array{ok:bool,status:int,body:string,headers:array,final:string,hops:int,ttfb:float,total:float,truncated:bool,error:string,chain:array}
 */
function safe_fetch(string $url, int $maxBytes = MAX_BYTES): array {
  global $ALLOW_PRIVATE;
  $res = ['ok' => false, 'status' => 0, 'body' => '', 'headers' => [], 'final' => $url, 'hops' => 0, 'ttfb' => 0.0, 'total' => 0.0, 'truncated' => false, 'error' => '', 'chain' => []];
  for ($hop = 0; $hop <= MAX_HOPS; $hop++) {
    $p = parse_url($url);
    if (!$p || empty($p['host']) || !in_array(strtolower($p['scheme'] ?? ''), ['http', 'https'], true)) { $res['error'] = 'url'; return $res; }
    $scheme = strtolower($p['scheme']);
    $port = (int) ($p['port'] ?? ($scheme === 'https' ? 443 : 80));
    if (!$ALLOW_PRIVATE && !in_array($port, [80, 443], true)) { $res['error'] = 'port'; return $res; }
    if (!empty($p['user']) || !empty($p['pass'])) { $res['error'] = 'url'; return $res; }
    $host = $p['host'];
    $ip = resolve_public($host);
    if ($ip === null) { $res['error'] = 'host'; return $res; }
    $body = ''; $truncated = false; $headers = []; $status = 0;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
      CURLOPT_RETURNTRANSFER => false,
      CURLOPT_FOLLOWLOCATION => false,
      CURLOPT_PROTOCOLS => CURLPROTO_HTTP | CURLPROTO_HTTPS,
      CURLOPT_CONNECTTIMEOUT => 4,
      CURLOPT_TIMEOUT => 8,
      CURLOPT_ENCODING => '',
      CURLOPT_USERAGENT => 'MarkentrixSiteCheck/1.0 (+https://markentrix.de/website-check)',
      CURLOPT_HTTPHEADER => ['Accept: text/html,application/xhtml+xml,text/plain,application/xml;q=0.9,*/*;q=0.5', 'Accept-Language: de-DE,de;q=0.9'],
      CURLOPT_RESOLVE => [$host . ':' . $port . ':' . (strpos($ip, ':') !== false ? '[' . $ip . ']' : $ip)],
      CURLOPT_SSL_VERIFYPEER => true,
      CURLOPT_SSL_VERIFYHOST => 2,
      CURLOPT_HEADERFUNCTION => function ($c, $line) use (&$headers, &$status) {
        $t = trim($line);
        if (stripos($t, 'HTTP/') === 0) { $status = (int) (explode(' ', $t)[1] ?? 0); $headers = []; }
        elseif (strpos($t, ':') !== false) { [$k, $v] = explode(':', $t, 2); $headers[strtolower(trim($k))] = trim($v); }
        return strlen($line);
      },
      CURLOPT_WRITEFUNCTION => function ($c, $chunk) use (&$body, &$truncated, $maxBytes) {
        $room = $maxBytes - strlen($body);
        if ($room <= 0) { $truncated = true; return 0; }
        if (strlen($chunk) > $room) { $body .= substr($chunk, 0, $room); $truncated = true; return 0; }
        $body .= $chunk; return strlen($chunk);
      },
    ]);
    curl_exec($ch);
    $errno = curl_errno($ch);
    $info = curl_getinfo($ch);
    curl_close($ch);
    if ($errno !== 0 && !($truncated && $errno === 23)) {
      $res['error'] = in_array($errno, [28], true) ? 'timeout' : (in_array($errno, [35, 51, 58, 60, 77], true) ? 'tls' : 'connect');
      $res['final'] = $url; return $res;
    }
    $res['chain'][] = ['url' => $url, 'status' => $status];
    $res['ttfb'] = (float) ($info['starttransfer_time'] ?? 0);
    $res['total'] = (float) ($info['total_time'] ?? 0);
    if (in_array($status, [301, 302, 303, 307, 308], true) && !empty($headers['location'])) {
      $loc = $headers['location'];
      if (preg_match('#^//#', $loc)) $loc = $scheme . ':' . $loc;
      elseif (!preg_match('#^https?://#i', $loc)) {
        $base = $scheme . '://' . $host . (isset($p['port']) ? ':' . $p['port'] : '');
        $loc = $loc[0] === '/' ? $base . $loc : $base . rtrim(dirname($p['path'] ?? '/'), '/') . '/' . $loc;
      }
      $url = $loc; $res['hops'] = $hop + 1; continue;
    }
    $res['ok'] = true; $res['status'] = $status; $res['body'] = $body; $res['headers'] = $headers; $res['final'] = $url; $res['truncated'] = $truncated;
    return $res;
  }
  $res['error'] = 'redirects';
  return $res;
}

$main = safe_fetch($input);
if (!$main['ok']) {
  $msg = ['host' => 'Diese Adresse ist nicht öffentlich erreichbar oder nicht gültig.', 'port' => 'Es sind nur Adressen mit den Standardports möglich.', 'url' => 'Bitte geben Sie eine gültige Adresse an, zum Beispiel https://www.ihre-seite.de.',
          'timeout' => 'Die Seite hat nicht rechtzeitig geantwortet.', 'tls' => 'Die sichere Verbindung (HTTPS) konnte nicht aufgebaut werden. Das Zertifikat ist abgelaufen oder passt nicht zur Adresse.',
          'connect' => 'Die Seite ist nicht erreichbar.', 'redirects' => 'Die Seite leitet zu oft weiter.'][$main['error']] ?? 'Die Seite konnte nicht abgerufen werden.';
  respond(200, ['ok' => false, 'error' => $main['error'], 'message' => $msg]);
}

$finalUrl = $main['final'];
$fp = parse_url($finalUrl);
$origin = ($fp['scheme'] ?? 'https') . '://' . $fp['host'] . (isset($fp['port']) ? ':' . $fp['port'] : '');
$status = $main['status'];
$html = $main['body'];
$ctype = strtolower($main['headers']['content-type'] ?? '');
$isHtml = $html !== '' && (strpos($ctype, 'html') !== false || strpos($ctype, 'xml') !== false || $ctype === '');

// ── HTML auswerten ──────────────────────────────────────────────────────────
$doc = null; $xp = null;
if ($isHtml) {
  libxml_use_internal_errors(true);
  $doc = new DOMDocument();
  $doc->loadHTML('<?xml encoding="utf-8" ?>' . $html, LIBXML_NOWARNING | LIBXML_NOERROR | LIBXML_COMPACT);
  libxml_clear_errors();
  $xp = new DOMXPath($doc);
}
function q(?DOMXPath $xp, string $expr): array { return $xp ? iterator_to_array($xp->query($expr)) : []; }
function txt(DOMNode $n): string { return trim(preg_replace('/\s+/u', ' ', $n->textContent)); }
function attr(?DOMXPath $xp, string $expr, string $a): string { $n = q($xp, $expr); return $n ? trim((string) $n[0]->getAttribute($a)) : ''; }
function len(string $s): int { return function_exists('mb_strlen') ? mb_strlen($s) : strlen($s); }

$title = ''; $t = q($xp, '//title'); if ($t) $title = txt($t[0]);
$desc = attr($xp, '//meta[translate(@name,"DESCRIPTION","description")="description"]', 'content');
$h1s = array_values(array_filter(array_map('txt', q($xp, '//h1')), fn($x) => $x !== ''));
$lang = attr($xp, '//html', 'lang');
$canonical = attr($xp, '//link[@rel="canonical"]', 'href');
$robotsMeta = strtolower(attr($xp, '//meta[translate(@name,"ROBTS","robts")="robots"]', 'content'));
$xrobots = strtolower($main['headers']['x-robots-tag'] ?? '');
$viewport = attr($xp, '//meta[@name="viewport"]', 'content');
$ogTitle = attr($xp, '//meta[@property="og:title"]', 'content');
$ogImage = attr($xp, '//meta[@property="og:image"]', 'content');
$bodyText = '';
if ($doc) {
  $b = $doc->getElementsByTagName('body')->item(0);
  if ($b) { $c = $b->cloneNode(true); foreach (['script', 'style', 'noscript'] as $tag) { while (($n = $c->getElementsByTagName($tag)->item(0)) !== null) $n->parentNode->removeChild($n); } $bodyText = txt($c); }
}
$imgs = q($xp, '//img'); $imgTotal = count($imgs); $imgNoAlt = 0;
foreach ($imgs as $im) { if (!$im->hasAttribute('alt')) $imgNoAlt++; }
$links = q($xp, '//a[@href]'); $hasImpressum = false; $hasDatenschutz = false; $hasTel = false; $hasMail = false;
foreach ($links as $a) {
  $h = strtolower($a->getAttribute('href')); $tx = strtolower(txt($a));
  if (strpos($h, 'impressum') !== false || strpos($tx, 'impressum') !== false) $hasImpressum = true;
  if (strpos($h, 'datenschutz') !== false || strpos($tx, 'datenschutz') !== false || strpos($h, 'privacy') !== false) $hasDatenschutz = true;
  if (strpos($h, 'tel:') === 0) $hasTel = true;
  if (strpos($h, 'mailto:') === 0) $hasMail = true;
}
$hasForm = count(q($xp, '//form')) > 0;

// Strukturierte Daten
$ldTypes = [];
function collect_types($node, array &$out): void {
  if (is_array($node)) {
    if (isset($node['@type'])) foreach ((array) $node['@type'] as $t) if (is_string($t)) $out[] = $t;
    foreach ($node as $v) if (is_array($v)) collect_types($v, $out);
  }
}
foreach (q($xp, '//script[@type="application/ld+json"]') as $s) {
  $j = json_decode(trim($s->textContent), true);
  if ($j !== null) collect_types($j, $ldTypes);
}
$ldTypes = array_values(array_unique($ldTypes));
$localTypes = array_values(array_intersect($ldTypes, ['LocalBusiness', 'Organization', 'ProfessionalService', 'Store', 'Restaurant', 'Dentist', 'Physician', 'Electrician', 'Plumber', 'HVACBusiness', 'RoofingContractor', 'HomeAndConstructionBusiness', 'AutoRepair', 'BeautySalon', 'HairSalon', 'LegalService', 'AccountingService', 'Person']));
$hasFaq = in_array('FAQPage', $ldTypes, true);

// robots.txt und Sitemap
$robots = safe_fetch($origin . '/robots.txt', 200000);
$robotsOk = $robots['ok'] && $robots['status'] === 200 && stripos($robots['headers']['content-type'] ?? 'text/plain', 'html') === false;
$robotsBlocksAll = $robotsOk && preg_match('/^\s*User-agent:\s*\*\s*$(?:\R(?!\s*User-agent).*)*?\R\s*Disallow:\s*\/\s*$/im', $robots['body']);
$sitemapUrl = '';
if ($robotsOk && preg_match('/^\s*Sitemap:\s*(\S+)/im', $robots['body'], $m) && strcasecmp((string) parse_url($m[1], PHP_URL_HOST), $fp['host']) === 0) $sitemapUrl = $m[1];
$sm = safe_fetch($sitemapUrl !== '' ? $sitemapUrl : $origin . '/sitemap.xml', 300000);
$sitemapOk = $sm['ok'] && $sm['status'] === 200 && (stripos($sm['body'], '<urlset') !== false || stripos($sm['body'], '<sitemapindex') !== false);

// ── Bewertung ───────────────────────────────────────────────────────────────
$groups = []; $earned = 0.0; $possible = 0.0;
function add(array &$groups, string $group, string $status, string $title, string $detail, float $weight = 1.0): void {
  global $earned, $possible;
  $groups[$group][] = ['status' => $status, 'title' => $title, 'detail' => $detail];
  if ($status === 'info') return;
  $possible += $weight; $earned += ['ok' => 1.0, 'warn' => 0.5, 'bad' => 0.0][$status] * $weight;
}

$https = ($fp['scheme'] ?? '') === 'https';
add($groups, 'Grundlagen', $https ? 'ok' : 'bad', $https ? 'Sichere Verbindung (HTTPS)' : 'Keine sichere Verbindung (HTTPS)',
  $https ? 'Die Seite wird verschlüsselt ausgeliefert. Browser zeigen kein Warnzeichen.' : 'Ohne HTTPS warnen Browser vor der Seite, und Kunden brechen ab. Das sollte zuerst behoben werden.', 2);
if (preg_match('#^http://#i', $input) && $https) add($groups, 'Grundlagen', 'ok', 'Weiterleitung auf HTTPS', 'Die unsichere Adresse leitet auf die sichere Version weiter.', 0.5);
$okStatus = $status >= 200 && $status < 300;
add($groups, 'Grundlagen', $okStatus ? 'ok' : 'bad', $okStatus ? 'Seite antwortet normal' : 'Seite antwortet mit Fehler ' . $status, $okStatus ? 'Die Startseite wird ohne Fehlermeldung ausgeliefert.' : 'Statuscode ' . $status . ': Suchmaschinen und Besucher bekommen keine normale Seite.', 2);
$ttfb = $main['ttfb'];
add($groups, 'Grundlagen', $ttfb <= 0.8 ? 'ok' : ($ttfb <= 1.8 ? 'warn' : 'bad'), 'Antwortzeit des Servers: ' . number_format($ttfb, 1, ',', '') . ' Sekunden',
  $ttfb <= 0.8 ? 'Der Server antwortet zügig. Das ist die Grundlage für eine schnelle Seite.' : 'Der Server braucht lange bis zur ersten Antwort. Hosting, Zwischenspeicherung und Programmierung prüfen. Ein einzelner Abruf kann schwanken.', 1);
$kb = (int) round(strlen($html) / 1024);
add($groups, 'Grundlagen', 'info', 'Größe des HTML-Dokuments: ' . $kb . ' KB' . ($main['truncated'] ? ' oder mehr' : ''), 'Bilder, Schriften und Skripte kommen dazu. Eine vollständige Messung der Ladezeit liefert zum Beispiel PageSpeed Insights.');

if (!$isHtml) {
  add($groups, 'Auffindbarkeit', 'bad', 'Keine HTML-Seite erkannt', 'Die Adresse liefert kein Webseiten-Dokument. Bitte die Adresse der Startseite angeben.', 3);
} else {
  if ($robotsMeta !== '' && strpos($robotsMeta, 'noindex') !== false || strpos($xrobots, 'noindex') !== false)
    add($groups, 'Auffindbarkeit', 'bad', 'Seite ist für Suchmaschinen gesperrt (noindex)', 'Solange noindex gesetzt ist, taucht die Seite nicht in Google auf. Bei einer Live-Seite fast immer ein Fehler.', 3);
  else add($groups, 'Auffindbarkeit', 'ok', 'Seite darf indexiert werden', 'Es gibt keine Sperre per noindex.', 1);
  $tl = len($title);
  add($groups, 'Auffindbarkeit', $tl === 0 ? 'bad' : (($tl >= 25 && $tl <= 65) ? 'ok' : 'warn'), $tl === 0 ? 'Seitentitel fehlt' : 'Seitentitel: ' . $tl . ' Zeichen',
    $tl === 0 ? 'Der Titel ist das Wichtigste, was Google und Kunden in der Trefferliste sehen. Er sollte Leistung und Ort nennen.' : (($tl >= 25 && $tl <= 65) ? '„' . $title . '“. Länge passt für die Trefferliste.' : '„' . $title . '“. Ideal sind etwa 25 bis 65 Zeichen mit Leistung und Ort, sonst wird er gekürzt oder sagt zu wenig.'), 2);
  $dl = len($desc);
  add($groups, 'Auffindbarkeit', $dl === 0 ? 'warn' : (($dl >= 70 && $dl <= 165) ? 'ok' : 'warn'), $dl === 0 ? 'Beschreibung für die Trefferliste fehlt' : 'Beschreibung: ' . $dl . ' Zeichen',
    $dl === 0 ? 'Ohne eigene Beschreibung wählt Google einen beliebigen Textausschnitt. Ein guter Text erhöht die Klickrate.' : (($dl >= 70 && $dl <= 165) ? 'Länge passt für die Trefferliste.' : 'Ideal sind etwa 70 bis 165 Zeichen, die Nutzen und nächsten Schritt nennen.'), 1);
  $hc = count($h1s);
  add($groups, 'Auffindbarkeit', $hc === 1 ? 'ok' : ($hc === 0 ? 'bad' : 'warn'), $hc === 1 ? 'Genau eine Hauptüberschrift (H1)' : ($hc === 0 ? 'Hauptüberschrift (H1) fehlt' : $hc . ' Hauptüberschriften (H1)'),
    $hc === 1 ? '„' . mb_substr($h1s[0], 0, 100) . '“' : ($hc === 0 ? 'Die H1 sagt Suchmaschinen und Besuchern, worum es auf der Seite geht. Sie sollte Leistung und Ort enthalten.' : 'Eine Seite sollte eine klare Hauptüberschrift haben.'), 2);
  add($groups, 'Auffindbarkeit', $lang !== '' ? 'ok' : 'warn', $lang !== '' ? 'Sprache angegeben (' . $lang . ')' : 'Sprache der Seite nicht angegeben', $lang !== '' ? 'Browser, Vorlesehilfen und Suchmaschinen erkennen die Sprache.' : 'Das lang-Attribut am HTML-Element fehlt. Es hilft Vorlesehilfen und Suchmaschinen.', 0.5);
  add($groups, 'Auffindbarkeit', $canonical !== '' ? 'ok' : 'warn', $canonical !== '' ? 'Kanonische Adresse gesetzt' : 'Kanonische Adresse fehlt', $canonical !== '' ? 'Doppelte Adressen werden einer Hauptadresse zugeordnet.' : 'Ohne canonical können Varianten der Seite (mit und ohne www, mit Parametern) als Dubletten gelten.', 0.5);
  add($groups, 'Auffindbarkeit', $robotsOk && !$robotsBlocksAll ? 'ok' : ($robotsBlocksAll ? 'bad' : 'warn'), $robotsBlocksAll ? 'robots.txt sperrt die ganze Seite' : ($robotsOk ? 'robots.txt vorhanden' : 'robots.txt nicht gefunden'),
    $robotsBlocksAll ? 'Die Datei verbietet allen Suchmaschinen den Zugriff. Bei einer Live-Seite fast immer ein Fehler.' : ($robotsOk ? 'Die Datei steuert, was Suchmaschinen abrufen dürfen.' : 'Eine robots.txt ist kein Muss, gehört aber zum sauberen Standard und nennt die Sitemap.'), 0.5);
  add($groups, 'Auffindbarkeit', $sitemapOk ? 'ok' : 'warn', $sitemapOk ? 'Sitemap gefunden' : 'Sitemap nicht gefunden', $sitemapOk ? 'Suchmaschinen finden alle Seiten schneller.' : 'Eine sitemap.xml hilft Google, alle Seiten zu finden. Nach dem Anlegen in der Search Console einreichen.', 1);
  add($groups, 'Auffindbarkeit', $localTypes ? 'ok' : 'warn', $localTypes ? 'Strukturierte Daten zum Unternehmen (' . implode(', ', array_slice($localTypes, 0, 3)) . ')' : 'Keine strukturierten Daten zum Unternehmen',
    $localTypes ? 'Name, Adresse und Leistungen sind maschinenlesbar. Das hilft bei Google und in KI-Antworten.' : 'Strukturierte Daten (zum Beispiel LocalBusiness) sagen Suchmaschinen und KI-Antworten eindeutig, wer Sie sind, wo Sie arbeiten und was Sie anbieten.', 2);
  add($groups, 'Auffindbarkeit', 'info', $hasFaq ? 'Häufige Fragen als strukturierte Daten vorhanden' : 'Keine Fragen-und-Antworten-Daten', $hasFaq ? 'Gut für Suche und KI-Antworten, sofern die Fragen echte Kundenfragen sind.' : 'Eine FAQ mit echten Kundenfragen kann für Google und KI-Antworten nützlich sein. Kein Muss.');

  add($groups, 'Mobil und Darstellung', $viewport !== '' ? 'ok' : 'bad', $viewport !== '' ? 'Für Smartphones eingerichtet' : 'Nicht für Smartphones eingerichtet', $viewport !== '' ? 'Das Viewport-Tag ist gesetzt, die Seite kann sich an kleine Bildschirme anpassen.' : 'Das Viewport-Tag fehlt. Auf dem Smartphone erscheint die Seite winzig. Die Mehrheit der lokalen Suchen kommt vom Handy.', 3);
  if ($imgTotal > 0) add($groups, 'Mobil und Darstellung', $imgNoAlt === 0 ? 'ok' : ($imgNoAlt / $imgTotal > 0.5 ? 'bad' : 'warn'), $imgNoAlt === 0 ? 'Alle Bilder haben eine Textalternative' : $imgNoAlt . ' von ' . $imgTotal . ' Bildern ohne Textalternative',
    $imgNoAlt === 0 ? 'Gut für Barrierefreiheit und Bildersuche.' : 'Alternativtexte beschreiben Bilder für Vorlesehilfen und Suchmaschinen. Dekorative Bilder erhalten einen leeren alt-Text.', 1);
  $thin = len($bodyText) < 300;
  add($groups, 'Mobil und Darstellung', $thin ? 'warn' : 'ok', $thin ? 'Sehr wenig Text im HTML' : 'Inhalt im HTML vorhanden', $thin ? 'Entweder ist die Seite sehr knapp, oder der Inhalt wird erst per Skript geladen. Dann sehen Suchmaschinen und KI-Antworten unter Umständen wenig davon.' : 'Texte stehen direkt im HTML und sind für Suchmaschinen lesbar.', 1);
  add($groups, 'Mobil und Darstellung', ($ogTitle !== '' && $ogImage !== '') ? 'ok' : 'warn', ($ogTitle !== '' && $ogImage !== '') ? 'Vorschau für Soziale Netzwerke vorhanden' : 'Keine Vorschau für Soziale Netzwerke', ($ogTitle !== '' && $ogImage !== '') ? 'Geteilte Links erscheinen mit Titel und Bild.' : 'Ohne Open-Graph-Angaben (Titel und Bild) wirken geteilte Links in WhatsApp, Facebook und LinkedIn nackt.', 0.5);

  add($groups, 'Vertrauen und Anfrage', $hasImpressum ? 'ok' : 'bad', $hasImpressum ? 'Impressum verlinkt' : 'Impressum nicht gefunden', $hasImpressum ? 'Ein Link zum Impressum ist vorhanden. Ob die Angaben vollständig sind, prüft dieser Check nicht.' : 'Geschäftsmäßige Websites brauchen ein leicht erreichbares Impressum (§ 5 DDG).', 2);
  add($groups, 'Vertrauen und Anfrage', $hasDatenschutz ? 'ok' : 'bad', $hasDatenschutz ? 'Datenschutzerklärung verlinkt' : 'Datenschutzerklärung nicht gefunden', $hasDatenschutz ? 'Ein Link zur Datenschutzerklärung ist vorhanden. Den Inhalt prüft dieser Check nicht.' : 'Eine Datenschutzerklärung ist Pflicht, sobald Daten verarbeitet werden, schon bei Server-Protokollen oder einem Formular.', 2);
  $contact = $hasTel || $hasForm || $hasMail;
  add($groups, 'Vertrauen und Anfrage', $contact ? 'ok' : 'bad', $contact ? 'Kontaktweg auf der Startseite' : 'Kein Kontaktweg auf der Startseite', $contact ? implode(', ', array_filter([$hasTel ? 'Telefon zum Antippen' : '', $hasForm ? 'Formular' : '', $hasMail ? 'E-Mail-Link' : ''])) . ' gefunden.' : 'Es gibt weder Telefonlink, Formular noch E-Mail-Link. Besucher müssen suchen, und viele gehen.', 3);
  add($groups, 'Vertrauen und Anfrage', $hasTel ? 'ok' : 'warn', $hasTel ? 'Telefonnummer ist antippbar' : 'Telefonnummer nicht als Link', $hasTel ? 'Auf dem Smartphone genügt ein Tippen zum Anruf.' : 'Mit einem tel:-Link wird aus der Nummer ein Anruf per Tippen. Auf dem Smartphone entscheidet das oft über die Anfrage.', 1);
}

$score = $possible > 0 ? (int) round($earned / $possible * 100) : 0;
$out = [];
foreach ($groups as $gt => $items) $out[] = ['title' => $gt, 'items' => $items];
respond(200, [
  'ok' => true, 'url' => $finalUrl, 'host' => $fp['host'], 'status' => $status, 'redirects' => $main['hops'], 'score' => $score,
  'counts' => [
    'ok' => count(array_filter(array_merge(...array_map(fn($g) => $g['items'], $out)), fn($i) => $i['status'] === 'ok')),
    'warn' => count(array_filter(array_merge(...array_map(fn($g) => $g['items'], $out)), fn($i) => $i['status'] === 'warn')),
    'bad' => count(array_filter(array_merge(...array_map(fn($g) => $g['items'], $out)), fn($i) => $i['status'] === 'bad')),
  ],
  'groups' => $out,
]);
