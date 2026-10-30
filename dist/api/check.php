<?php
/**
 * Markentrix · Website-Check (Endpunkt für /website-check).
 *
 * Eingang:  POST /api/check.php  mit JSON {"url":"https://beispiel.de"}
 * Ausgang:  JSON mit Gesamtwertung, Bereichswerten und Kurzbefund je Bereich (Anzahl offener Punkte, davon mit hohem Gewicht,
 *           sowie die Titel dessen, was bereits in Ordnung ist). Die einzelnen Befunde zu offenen Punkten (Titel, Beschreibung)
 *           verlassen den Server nicht: Sie liegen nur im internen Bericht (temporärer Speicher) und gehen an Markentrix.
 *
 * Was passiert: Die angegebene öffentliche Adresse wird abgerufen (Startseite, robots.txt, Sitemap, llms.txt,
 * eine nicht existierende Adresse zur Prüfung der Fehlerseite, bis zu drei interne Seiten als Stichprobe)
 * und nach überprüfbaren Merkmalen aus den Bereichen SEO, lokale Sichtbarkeit, GEO (Auffindbarkeit in KI-Antworten),
 * Technik und Tempo, Zugänglichkeit sowie Vertrauen und Anfrage ausgewertet. Adresse und Ergebnis werden nicht protokolliert,
 * gehen aber als interne Benachrichtigung per E-Mail an Markentrix (ohne Name, ohne IP-Adresse; abschaltbar mit MX_CHECK_NOTIFY=0,
 * Empfänger MX_MAIL_TO, SMTP wie in anfrage.php). Das Ergebnis liegt höchstens zwei Stunden im temporären Ordner (Zufalls-Token, ohne Personenbezug), damit es auf Wunsch
 * per E-Mail zugesandt werden kann (siehe anfrage.php); außerdem Dateien für die Begrenzung (Hash der IP, Platzhalter).
 *
 * Schutz gegen Missbrauch: nur http/https auf Port 80/443, nur öffentliche IP-Adressen (auch nach Weiterleitungen, die
 * aufgelöste Adresse wird fest verwendet), höchstens 5 Weiterleitungen, je Abruf Zeit- und Größenbegrenzung, insgesamt
 * höchstens 24 Sekunden, 8 Prüfungen je IP in 10 Minuten, höchstens 2 gleichzeitige Prüfungen auf dem Server.
 * Nur für Tests: MX_CHECK_ALLOW_PRIVATE=1 erlaubt lokale Adressen und Ports.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

const MAX_BYTES = 1500000;
const MAX_HOPS = 5;
const RATE_LIMIT = 8;
const RATE_WINDOW = 600;
const DEADLINE = 24.0;
$ALLOW_PRIVATE = getenv('MX_CHECK_ALLOW_PRIVATE') === '1';
$T0 = microtime(true);

function respond(int $status, array $body): void {
  http_response_code($status);
  echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}
function time_left(): float { global $T0; return DEADLINE - (microtime(true) - $T0); }

set_exception_handler(function (Throwable $e) { respond(500, ['ok' => false, 'error' => 'server']); });
@set_time_limit(40);

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') respond(405, ['ok' => false, 'error' => 'method']);
if (!function_exists('curl_init') || !class_exists('DOMDocument')) respond(500, ['ok' => false, 'error' => 'server']);

// Herkunft: nur Aufrufe von der eigenen Seite (soweit der Browser einen Origin-Header sendet)
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && !$ALLOW_PRIVATE) {
  $oh = parse_url($origin, PHP_URL_HOST) ?: '';
  $sh = preg_replace('/:\d+$/', '', (string) ($_SERVER['HTTP_HOST'] ?? ''));
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

// Gleichzeitigkeit: höchstens zwei Prüfungen parallel, damit Formular und Website nicht blockiert werden
$slot = null;
foreach ([0, 1] as $n) {
  $fh = @fopen(sys_get_temp_dir() . '/mx-check-slot-' . $n, 'c');
  if ($fh && flock($fh, LOCK_EX | LOCK_NB)) { $slot = $fh; break; }
  if ($fh) fclose($fh);
}
if ($slot === null) respond(503, ['ok' => false, 'error' => 'busy']);

/** Prüft, ob eine IP öffentlich erreichbar ist (keine privaten, reservierten oder lokalen Bereiche). */
function is_public_ip(string $ip): bool {
  return filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) !== false;
}

/** Löst den Host auf und liefert eine öffentliche IP (IPv4 bevorzugt) oder null. */
function resolve_public(string $host): ?string {
  global $ALLOW_PRIVATE;
  if (filter_var($host, FILTER_VALIDATE_IP)) return ($ALLOW_PRIVATE || is_public_ip($host)) ? $host : null;
  if (!preg_match('/^[a-z0-9]([a-z0-9\-\.]{0,251}[a-z0-9])?$/i', $host) || (strpos($host, '.') === false && !$ALLOW_PRIVATE)) return null;
  $ips = [];
  $v4 = @gethostbynamel($host);
  if (is_array($v4)) foreach ($v4 as $a) if (is_string($a)) $ips[] = $a;
  $v6 = @dns_get_record($host, DNS_AAAA);
  if (is_array($v6)) foreach ($v6 as $r) if (!empty($r['ipv6'])) $ips[] = (string) $r['ipv6'];
  if (!$ips) return null;
  foreach ($ips as $a) if (!$ALLOW_PRIVATE && !is_public_ip($a)) return null; // ein einziger nichtöffentlicher Eintrag führt zum Abbruch
  return $ips[0];
}

/**
 * Ruft eine Adresse ab, folgt Weiterleitungen manuell und prüft jeden Schritt.
 * @return array{ok:bool,status:int,body:string,headers:array,final:string,hops:int,ttfb:float,total:float,truncated:bool,error:string,chain:array,http:int,bytes:int}
 */
function safe_fetch(string $url, int $maxBytes = MAX_BYTES, int $timeout = 8): array {
  global $ALLOW_PRIVATE;
  $res = ['ok' => false, 'status' => 0, 'body' => '', 'headers' => [], 'final' => $url, 'hops' => 0, 'ttfb' => 0.0, 'total' => 0.0, 'truncated' => false, 'error' => '', 'chain' => [], 'http' => 0, 'bytes' => 0];
  $timeout = (int) max(2, min($timeout, floor(time_left())));
  if (time_left() < 2) { $res['error'] = 'timeout'; return $res; }
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
      CURLOPT_TIMEOUT => $timeout,
      CURLOPT_ENCODING => '',
      CURLOPT_USERAGENT => 'MarkentrixWebsiteCheck/2.0 (+https://markentrix.de/website-check)',
      CURLOPT_HTTPHEADER => ['Accept: text/html,application/xhtml+xml,text/plain,application/xml;q=0.9,*/*;q=0.5', 'Accept-Language: de-DE,de;q=0.9'],
      CURLOPT_RESOLVE => [$host . ':' . $port . ':' . (strpos($ip, ':') !== false ? '[' . $ip . ']' : $ip)],
      CURLOPT_SSL_VERIFYPEER => true,
      CURLOPT_SSL_VERIFYHOST => 2,
      CURLOPT_HEADERFUNCTION => function ($c, $line) use (&$headers, &$status) {
        $t = trim($line);
        if (stripos($t, 'HTTP/') === 0) { $status = (int) (explode(' ', $t)[1] ?? 0); $headers = []; }
        elseif (strpos($t, ':') !== false) { [$k, $v] = explode(':', $t, 2); $k = strtolower(trim($k)); $headers[$k] = isset($headers[$k]) ? $headers[$k] . ', ' . trim($v) : trim($v); }
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
    $res['http'] = (int) ($info['http_version'] ?? 0);
    if (in_array($status, [301, 302, 303, 307, 308], true) && !empty($headers['location'])) {
      $loc = $headers['location'];
      if (preg_match('#^//#', $loc)) $loc = $scheme . ':' . $loc;
      elseif (!preg_match('#^https?://#i', $loc)) {
        $base = $scheme . '://' . $host . (isset($p['port']) ? ':' . $p['port'] : '');
        $loc = $loc[0] === '/' ? $base . $loc : $base . rtrim(dirname($p['path'] ?? '/'), '/') . '/' . $loc;
      }
      $url = $loc; $res['hops'] = $hop + 1; continue;
    }
    $res['ok'] = true; $res['status'] = $status; $res['body'] = $body; $res['headers'] = $headers; $res['final'] = $url; $res['truncated'] = $truncated; $res['bytes'] = strlen($body);
    return $res;
  }
  $res['error'] = 'redirects';
  return $res;
}

// ── Hilfsfunktionen für die Auswertung ───────────────────────────────────────
function len(string $s): int { return function_exists('mb_strlen') ? mb_strlen($s) : strlen($s); }
function cut(string $s, int $n): string { return function_exists('mb_substr') ? mb_substr($s, 0, $n) : substr($s, 0, $n); }
function norm(string $s): string { return trim((string) preg_replace('/\s+/u', ' ', $s)); }
function lc(string $s): string { return function_exists('mb_strtolower') ? mb_strtolower($s) : strtolower($s); }

/** Liest ein HTML-Dokument in eine auswertbare Struktur. */
function parse_page(string $html): array {
  libxml_use_internal_errors(true);
  $doc = new DOMDocument();
  $doc->loadHTML('<?xml encoding="utf-8" ?>' . $html, LIBXML_NOWARNING | LIBXML_NOERROR | LIBXML_COMPACT);
  libxml_clear_errors();
  $xp = new DOMXPath($doc);
  $q = function (string $e) use ($xp): array { $r = $xp->query($e); return $r ? iterator_to_array($r) : []; };
  $first = function (string $e, string $a) use ($q): string { $n = $q($e); return $n ? trim((string) $n[0]->getAttribute($a)) : ''; };
  $t = $q('//title');
  $p = ['doc' => $doc, 'q' => $q];
  $p['title'] = $t ? norm($t[0]->textContent) : '';
  $p['desc'] = $first('//meta[translate(@name,"DESCRIPTION","description")="description"]', 'content');
  $p['h1'] = array_values(array_filter(array_map(fn($n) => norm($n->textContent), $q('//h1')), fn($x) => $x !== ''));
  $p['h2'] = array_values(array_filter(array_map(fn($n) => norm($n->textContent), $q('//h2')), fn($x) => $x !== ''));
  $p['h3'] = count($q('//h3'));
  $p['lang'] = $first('//html', 'lang');
  $p['canonical'] = $first('//link[@rel="canonical"]', 'href');
  $p['robots'] = lc($first('//meta[translate(@name,"ROBTS","robts")="robots"]', 'content'));
  $p['viewport'] = $first('//meta[@name="viewport"]', 'content');
  $b = $doc->getElementsByTagName('body')->item(0);
  $text = '';
  if ($b) {
    $c = $b->cloneNode(true);
    foreach (['script', 'style', 'noscript', 'template'] as $tag) { while (($n = $c->getElementsByTagName($tag)->item(0)) !== null) $n->parentNode->removeChild($n); }
    $text = norm($c->textContent);
  }
  $p['text'] = $text;
  $p['words'] = $text === '' ? 0 : count(preg_split('/\s+/u', $text));
  return $p;
}

/** Alle JSON-LD-Knoten (flach) und ungültige Blöcke. */
function ld_nodes(array $p): array {
  $nodes = []; $invalid = 0;
  $walk = function ($n) use (&$walk, &$nodes) {
    if (!is_array($n)) return;
    if (isset($n['@type'])) $nodes[] = $n;
    foreach ($n as $v) if (is_array($v)) $walk($v);
  };
  foreach (($p['q'])('//script[@type="application/ld+json"]') as $s) {
    $j = json_decode(trim($s->textContent), true);
    if ($j === null) { $invalid++; continue; }
    $walk($j);
  }
  return [$nodes, $invalid];
}
function node_types(array $n): array { return array_map('strval', (array) ($n['@type'] ?? [])); }

/** Prüft, ob robots.txt einem Crawler den Zugriff auf die Startseite verbietet. */
function robots_blocks(string $robots, string $agent): bool {
  $groups = []; $cur = [];
  foreach (preg_split('/\R/', $robots) as $line) {
    $line = trim(preg_replace('/#.*$/', '', $line));
    if ($line === '') continue;
    if (stripos($line, 'user-agent:') === 0) {
      $ua = strtolower(trim(substr($line, 11)));
      if (!empty($cur['rules'])) { $groups[] = $cur; $cur = []; }
      $cur['agents'][] = $ua;
    } elseif (preg_match('/^(allow|disallow):\s*(.*)$/i', $line, $m)) {
      $cur['rules'][] = [strtolower($m[1]), trim($m[2])];
    }
  }
  if (!empty($cur['agents'])) $groups[] = $cur;
  $pick = null; $star = null; $agent = strtolower($agent);
  foreach ($groups as $g) {
    if (in_array($agent, $g['agents'] ?? [], true)) $pick = $g;
    if (in_array('*', $g['agents'] ?? [], true)) $star = $g;
  }
  $g = $pick ?? $star;
  if (!$g) return false;
  $dis = false; $allow = false;
  foreach ($g['rules'] ?? [] as [$k, $v]) {
    if ($k === 'disallow' && $v === '/') $dis = true;
    if ($k === 'allow' && ($v === '/' || $v === '')) $allow = $allow || $v === '/';
  }
  return $dis && !$allow;
}

// ── Abruf der Startseite ────────────────────────────────────────────────────
$main = safe_fetch($input, MAX_BYTES, 9);
if (!$main['ok']) {
  $msg = ['host' => 'Diese Adresse ist nicht öffentlich erreichbar oder nicht gültig.', 'port' => 'Es sind nur Adressen mit den Standardports möglich.', 'url' => 'Bitte geben Sie eine gültige Adresse an, zum Beispiel https://www.ihre-seite.de.',
          'timeout' => 'Die Seite hat nicht rechtzeitig geantwortet.', 'tls' => 'Die sichere Verbindung (HTTPS) konnte nicht aufgebaut werden. Das Zertifikat ist abgelaufen oder passt nicht zur Adresse.',
          'connect' => 'Die Seite ist nicht erreichbar.', 'redirects' => 'Die Seite leitet zu oft weiter.'][$main['error']] ?? 'Die Seite konnte nicht abgerufen werden.';
  respond(200, ['ok' => false, 'error' => $main['error'], 'message' => $msg]);
}

$finalUrl = $main['final'];
$fp = parse_url($finalUrl);
$host = (string) $fp['host'];
$bareHost = preg_replace('/^www\./i', '', $host);
$scheme = (string) ($fp['scheme'] ?? 'https');
$origin = $scheme . '://' . $host . (isset($fp['port']) ? ':' . $fp['port'] : '');
$status = $main['status'];
$html = $main['body'];
$H = $main['headers'];
$ctype = strtolower($H['content-type'] ?? '');
$isHtml = $html !== '' && (strpos($ctype, 'html') !== false || strpos($ctype, 'xml') !== false || $ctype === '');

// ── Sammlung der Befunde ────────────────────────────────────────────────────
$CATS = [
  'seo'   => ['title' => 'SEO: Auffindbarkeit bei Google', 'weight' => 28],
  'local' => ['title' => 'Lokale Sichtbarkeit', 'weight' => 16],
  'geo'   => ['title' => 'GEO: Auffindbarkeit in KI-Antworten', 'weight' => 18],
  'tech'  => ['title' => 'Technik, Tempo und Sicherheit', 'weight' => 14],
  'ux'    => ['title' => 'Smartphone und Zugänglichkeit', 'weight' => 10],
  'trust' => ['title' => 'Vertrauen und Anfrage', 'weight' => 14],
];
$items = []; // je Bereich
$caps = [];  // harte Obergrenzen für die Gesamtwertung
$W = ['high' => 3.0, 'mid' => 2.0, 'low' => 1.0];
function add(string $cat, string $status, string $impact, string $title, string $detail, string $fix = ''): void {
  global $items;
  $items[$cat][] = ['status' => $status, 'impact' => $impact, 'title' => $title, 'detail' => $detail, 'fix' => $fix];
}

if (!$isHtml) {
  respond(200, ['ok' => false, 'error' => 'html', 'message' => 'Die Adresse liefert keine Webseite im HTML-Format. Bitte geben Sie die Adresse der Startseite an.']);
}
$P = parse_page($html);
$q = $P['q'];
[$ldNodes, $ldInvalid] = ld_nodes($P);
$ldTypes = [];
foreach ($ldNodes as $n) foreach (node_types($n) as $t) $ldTypes[] = $t;
$ldTypes = array_values(array_unique($ldTypes));
$bizTypes = ['LocalBusiness', 'ProfessionalService', 'Store', 'Restaurant', 'Dentist', 'Physician', 'MedicalBusiness', 'Electrician', 'Plumber', 'HVACBusiness', 'RoofingContractor', 'HomeAndConstructionBusiness', 'GeneralContractor', 'AutoRepair', 'BeautySalon', 'HairSalon', 'LegalService', 'AccountingService', 'FinancialService', 'RealEstateAgent', 'Bakery', 'CafeOrCoffeeShop', 'FoodEstablishment', 'Hotel', 'LodgingBusiness', 'HealthAndBeautyBusiness', 'SportsActivityLocation', 'Florist', 'TravelAgency', 'EmploymentAgency', 'Locksmith', 'MovingCompany'];
$biz = null; $org = null;
foreach ($ldNodes as $n) {
  $ts = node_types($n);
  if (!$biz && array_intersect($ts, $bizTypes)) $biz = $n;
  if (!$org && array_intersect($ts, ['Organization', 'Corporation', 'NGO'])) $org = $n;
}
$entity = $biz ?? $org;
$lower = lc($html);

// ===== TECHNIK =====
$https = $scheme === 'https';
if (!$https) $caps[] = [35, 'Die Seite wird ohne HTTPS ausgeliefert.'];
add('tech', $https ? 'ok' : 'bad', 'high', $https ? 'Sichere Verbindung (HTTPS)' : 'Keine sichere Verbindung (HTTPS)',
  $https ? 'Die Seite wird verschlüsselt ausgeliefert.' : 'Browser markieren die Seite als „nicht sicher“, Formulare werden gewarnt, Google bevorzugt HTTPS.',
  $https ? '' : 'Zertifikat beim Hoster aktivieren und alle Adressen dauerhaft (301) auf https umleiten.');
$okStatus = $status >= 200 && $status < 300;
if (!$okStatus) $caps[] = [30, 'Die Startseite antwortet mit Fehler ' . $status . '.'];
add('tech', $okStatus ? 'ok' : 'bad', 'high', $okStatus ? 'Startseite antwortet normal' : 'Startseite antwortet mit Fehler ' . $status, $okStatus ? 'Kein Fehlercode.' : 'Suchmaschinen und Besucher erhalten keine normale Seite.', $okStatus ? '' : 'Ursache beim Hoster oder in der Serverkonfiguration beheben.');
if ($main['hops'] > 0) {
  add('tech', $main['hops'] <= 1 ? 'ok' : 'warn', 'low', 'Weiterleitungen beim Aufruf: ' . $main['hops'], $main['hops'] <= 1 ? 'Eine Weiterleitung, zum Beispiel auf https oder www, ist normal.' : 'Mehrere Weiterleitungen nacheinander kosten Zeit und Crawl-Budget.', $main['hops'] <= 1 ? '' : 'Alle Varianten direkt auf die endgültige Adresse weiterleiten.');
}
$ttfb = $main['ttfb'];
add('tech', $ttfb <= 0.6 ? 'ok' : ($ttfb <= 1.2 ? 'warn' : 'bad'), 'mid', 'Antwortzeit des Servers: ' . number_format($ttfb, 1, ',', '') . ' s',
  $ttfb <= 0.6 ? 'Der Server antwortet zügig (einzelne Messung aus Deutschland).' : 'Der Server braucht lange bis zur ersten Antwort. Das verlangsamt jede Seite und drückt die Bewertung bei Google (einzelne Messung, kann schwanken).',
  $ttfb <= 0.6 ? '' : 'Hosting prüfen, Zwischenspeicherung (Cache) einschalten, schwere Plug-ins und Datenbankabfragen reduzieren.');
$enc = strtolower($H['content-encoding'] ?? '');
add('tech', $enc !== '' ? 'ok' : 'warn', 'mid', $enc !== '' ? 'Komprimierte Auslieferung (' . $enc . ')' : 'Keine Komprimierung des HTML', $enc !== '' ? 'Texte werden komprimiert übertragen.' : 'Ohne Komprimierung ist das HTML drei- bis fünfmal so groß wie nötig.', $enc !== '' ? '' : 'Gzip oder Brotli im Server aktivieren.');
$hv = $main['http'];
if ($hv > 0) add('tech', $hv >= 3 ? 'ok' : 'info', 'low', $hv >= 3 ? 'Modernes Protokoll (HTTP/2 oder neuer)' : 'Älteres Protokoll (HTTP/1.x)', $hv >= 3 ? 'Mehrere Dateien werden parallel geladen.' : 'HTTP/2 lädt Dateien parallel und ist bei vielen Anbietern ein Schalter.', $hv >= 3 ? '' : 'Beim Hoster HTTP/2 aktivieren lassen.');
$kb = (int) round(strlen($html) / 1024);
add('tech', $kb <= 150 ? 'ok' : ($kb <= 400 ? 'warn' : 'bad'), 'low', 'Größe des HTML-Dokuments: ' . $kb . ' KB' . ($main['truncated'] ? ' oder mehr' : ''),
  $kb <= 150 ? 'Schlank genug für schnelle Darstellung.' : 'Sehr viel Inhalt oder Code im Dokument selbst, oft durch eingebettete Skripte, Stile oder Bilder (Base64).', $kb <= 150 ? '' : 'Eingebettete Skripte und Stile auslagern, unnötige Bausteine entfernen.');
// Skripte, Stile, Fremdanbieter
$scripts = $q('//script[@src]'); $styles = $q('//link[@rel="stylesheet"]');
$blocking = 0;
foreach ($q('//head//script[@src]') as $s) { if (!$s->hasAttribute('async') && !$s->hasAttribute('defer') && strtolower($s->getAttribute('type')) !== 'module') $blocking++; }
$reqCount = count($scripts) + count($styles) + count($q('//img[@src]'));
add('tech', $blocking === 0 ? 'ok' : ($blocking <= 2 ? 'warn' : 'bad'), 'mid', $blocking === 0 ? 'Keine blockierenden Skripte im Kopfbereich' : $blocking . ' Skript(e) blockieren den Seitenaufbau',
  $blocking === 0 ? 'Skripte verzögern die Darstellung nicht.' : 'Skripte im Kopfbereich ohne async oder defer verzögern, bis der Besucher etwas sieht.', $blocking === 0 ? '' : 'Skripte mit defer laden oder ans Seitenende verschieben.');
add('tech', $reqCount <= 40 ? 'ok' : ($reqCount <= 80 ? 'warn' : 'bad'), 'low', 'Eingebundene Dateien auf der Startseite: ca. ' . $reqCount, $reqCount <= 40 ? 'Überschaubar.' : 'Viele Einzeldateien verlängern die Ladezeit, besonders mobil.', $reqCount <= 40 ? '' : 'Dateien bündeln, ungenutzte Plug-ins und Schriften entfernen.');
$ext = [];
foreach (array_merge($q('//script[@src]'), $q('//link[@href]'), $q('//iframe[@src]'), $q('//img[@src]')) as $n) {
  $u = $n->getAttribute($n->hasAttribute('src') ? 'src' : 'href');
  if (preg_match('#^(?:https?:)?//([^/:]+)#i', $u, $m)) { $h = strtolower($m[1]); if (substr($h, -strlen($bareHost)) !== $bareHost) $ext[$h] = true; }
}
$extHosts = array_keys($ext);
$privacy = [];
foreach ($extHosts as $h) {
  if (preg_match('/fonts\.(googleapis|gstatic)\.com/', $h)) $privacy['Google Fonts von Google-Servern'] = true;
  elseif (preg_match('/(^|\.)youtube\.com$/', $h)) $privacy['YouTube-Einbettung'] = true;
  elseif (preg_match('/maps\.(google|gstatic)|google\.[a-z]+$/', $h) && strpos($h, 'fonts') === false && strpos($h, 'tagmanager') === false && strpos($h, 'analytics') === false) $privacy['Google Maps'] = true;
  elseif (preg_match('/googletagmanager|google-analytics|analytics\.google|doubleclick|facebook\.(net|com)|connect\.facebook|hotjar|clarity\.ms|tiktok|linkedin\.com|pinterest|matomo|etracker/', $h)) $privacy['Tracking oder Werbedienste'] = true;
}
$consentTool = (bool) preg_match('/cookiebot|usercentrics|borlabs|complianz|cookieconsent|onetrust|consentmanager|cookie-notice|cookie-banner|cookie_consent|iubenda|klaro/', $lower);
if ($privacy) {
  add('tech', $consentTool ? 'info' : 'warn', 'high', 'Fremdanbieter beim Laden der Seite: ' . implode(', ', array_keys($privacy)),
    $consentTool ? 'Ein Einwilligungsbanner ist erkennbar. Ob die Dienste erst nach Zustimmung laden, prüft dieser Check nicht.' : 'Solche Dienste übertragen Daten an Dritte, sobald die Seite geöffnet wird. Ohne Einwilligung ist das in Deutschland ein typisches Abmahn- und Bußgeldrisiko. Ein Einwilligungsbanner ist nicht erkennbar.',
    $consentTool ? '' : 'Schriften lokal einbinden, Karten und Videos erst nach Klick laden, Tracking nur mit Einwilligung.');
} else {
  add('tech', 'ok', 'mid', 'Keine kritischen Fremdanbieter erkannt', 'Auf der Startseite werden keine bekannten Tracking-, Karten-, Video- oder Schriftdienste von Dritten direkt geladen.');
}
// Sicherheitsköpfe
$sec = []; $secMissing = [];
$hsts = isset($H['strict-transport-security']); $xcto = isset($H['x-content-type-options']); $csp = isset($H['content-security-policy']);
$frame = isset($H['x-frame-options']) || (isset($H['content-security-policy']) && stripos($H['content-security-policy'], 'frame-ancestors') !== false);
$ref = isset($H['referrer-policy']);
foreach (['HSTS' => $hsts, 'X-Content-Type-Options' => $xcto, 'Schutz vor Einbettung (Frame)' => $frame, 'Referrer-Policy' => $ref, 'Content-Security-Policy' => $csp] as $k => $v) { if (!$v) $secMissing[] = $k; }
$secOk = 5 - count($secMissing);
if ($https) add('tech', $secOk >= 4 ? 'ok' : ($secOk >= 2 ? 'warn' : 'bad'), 'low', 'Sicherheits-Kopfzeilen: ' . $secOk . ' von 5', $secOk >= 4 ? 'Wichtige Schutzkopfzeilen sind gesetzt.' : 'Es fehlen: ' . implode(', ', $secMissing) . '. Sie schützen vor Einbettung, Manipulation und Datenabfluss und gelten bei Prüfungen als Mindeststandard.', $secOk >= 4 ? '' : 'Beim Hoster oder in der Serverkonfiguration ergänzen lassen.');
// Fehlerseite
$rand = 'mx-pruefung-' . bin2hex(random_bytes(4));
$nf = time_left() > 6 ? safe_fetch($origin . '/' . $rand, 120000, 5) : ['ok' => false];
if (!empty($nf['ok'])) {
  $nfPath = (string) (parse_url($nf['final'], PHP_URL_PATH) ?: '/');
  $soft = $nf['status'] >= 200 && $nf['status'] < 300;
  $toHome = $nf['hops'] > 0 && ($nfPath === '/' || $nfPath === '');
  add('tech', ($nf['status'] === 404 || $nf['status'] === 410) && !$toHome ? 'ok' : 'warn', 'mid', ($nf['status'] === 404 || $nf['status'] === 410) && !$toHome ? 'Nicht vorhandene Seiten melden korrekt „404“' : 'Nicht vorhandene Seiten melden keinen Fehler (Soft-404)',
    ($nf['status'] === 404 || $nf['status'] === 410) && !$toHome ? 'Suchmaschinen erkennen, welche Adressen es nicht gibt.' : ($toHome ? 'Unbekannte Adressen werden still auf die Startseite geleitet.' : 'Unbekannte Adressen antworten mit Status ' . $nf['status'] . ' statt 404.') . ' Google wertet das als „Soft-404“, es verschwendet Crawl-Budget und kann Seiten in den Index bringen, die dort nichts zu suchen haben.',
    ($nf['status'] === 404 || $nf['status'] === 410) && !$toHome ? '' : 'Eine echte Fehlerseite mit Status 404 einrichten (mit Links zu Startseite und Kontakt).');
}

// ===== SEO =====
$title = $P['title']; $tl = len($title);
$noindex = strpos($P['robots'], 'noindex') !== false || stripos($H['x-robots-tag'] ?? '', 'noindex') !== false;
if ($noindex) $caps[] = [20, 'Die Startseite ist per noindex für Suchmaschinen gesperrt.'];
add('seo', $noindex ? 'bad' : 'ok', 'high', $noindex ? 'Startseite ist für Suchmaschinen gesperrt (noindex)' : 'Startseite darf indexiert werden', $noindex ? 'Solange noindex gesetzt ist, taucht die Seite nicht bei Google auf.' : 'Keine Sperre per noindex.', $noindex ? 'noindex entfernen (Einstellung im Seitensystem oder in den SEO-Optionen).' : '');
$genericTitle = (bool) preg_match('/^(startseite|home|willkommen|herzlich willkommen|index|untitled|neue seite|website|my site|startpage)\b/iu', $title);
if ($tl === 0) { $caps[] = [60, 'Es fehlt ein Seitentitel.']; add('seo', 'bad', 'high', 'Seitentitel fehlt', 'Der Titel ist das, was Google und Kunden in der Trefferliste zuerst lesen.', 'Titel mit Leistung, Ort und Firmenname setzen, 30 bis 60 Zeichen.'); }
elseif ($genericTitle) add('seo', 'bad', 'high', 'Seitentitel ist nichtssagend: „' . cut($title, 70) . '“', 'Titel wie „Startseite“ oder „Willkommen“ verschenken den wichtigsten Platz in der Trefferliste.', 'Leistung und Ort nennen, zum Beispiel „Elektriker in Celle: Installation und Notdienst | Firma“.');
else add('seo', ($tl >= 30 && $tl <= 62) ? 'ok' : 'warn', 'high', 'Seitentitel: ' . $tl . ' Zeichen', '„' . cut($title, 90) . '“' . (($tl >= 30 && $tl <= 62) ? '. Länge passt.' : ($tl > 62 ? '. Der Titel wird in der Trefferliste voraussichtlich abgeschnitten.' : '. Der Titel ist sehr kurz und nennt kaum Leistung und Ort.')), ($tl >= 30 && $tl <= 62) ? '' : 'Auf 30 bis 60 Zeichen bringen, Leistung und Ort nach vorn.');
$dl = len($P['desc']);
$descSame = $dl > 0 && lc($P['desc']) === lc($title);
add('seo', ($dl >= 90 && $dl <= 160 && !$descSame) ? 'ok' : ($dl === 0 ? 'bad' : 'warn'), 'mid', $dl === 0 ? 'Beschreibung für die Trefferliste fehlt' : 'Beschreibung: ' . $dl . ' Zeichen' . ($descSame ? ' (gleich dem Titel)' : ''),
  $dl === 0 ? 'Google wählt dann einen beliebigen Textausschnitt, meist unvorteilhaft.' : (($dl >= 90 && $dl <= 160 && !$descSame) ? 'Länge passt.' : 'Richtwert: 90 bis 160 Zeichen. Eine Beschreibung, die nur den Titel wiederholt, liefert keinen zusätzlichen Nutzen.'),
  ($dl >= 90 && $dl <= 160 && !$descSame) ? '' : 'Eigenen, werbenden Text schreiben: Was bieten Sie, für wen, wo, mit welchem nächsten Schritt?');
$hc = count($P['h1']);
$genericH1 = $hc > 0 && preg_match('/^(willkommen|herzlich willkommen|startseite|home|hallo)\b/iu', $P['h1'][0]);
if ($hc === 0) $caps[] = [65, 'Es fehlt eine Hauptüberschrift (H1).'];
add('seo', ($hc === 1 && !$genericH1) ? 'ok' : ($hc === 0 ? 'bad' : 'warn'), 'high', $hc === 1 ? ($genericH1 ? 'Hauptüberschrift ist nichtssagend: „' . cut($P['h1'][0], 60) . '“' : 'Genau eine Hauptüberschrift (H1)') : ($hc === 0 ? 'Hauptüberschrift (H1) fehlt' : $hc . ' Hauptüberschriften (H1)'),
  $hc === 1 && !$genericH1 ? '„' . cut($P['h1'][0], 100) . '“' : ($hc === 0 ? 'Die H1 sagt Suchmaschinen und Besuchern, worum es geht. Ohne sie fehlt der wichtigste inhaltliche Anker.' : ($genericH1 ? '„Willkommen“ sagt weder Besuchern noch Google, was Sie anbieten.' : 'Mehrere H1 verwässern das Thema der Seite.')),
  ($hc === 1 && !$genericH1) ? '' : 'Eine H1 mit Leistung und Ort, zum Beispiel „Heizungsbau in Celle und Umgebung“.');
$h2c = count($P['h2']);
add('seo', $h2c >= 3 ? 'ok' : ($h2c >= 1 ? 'warn' : 'bad'), 'mid', 'Gliederung mit Zwischenüberschriften (H2): ' . $h2c, $h2c >= 3 ? 'Die Seite ist inhaltlich gegliedert.' : 'Wenige oder keine Zwischenüberschriften: Besucher und Suchmaschinen erkennen kaum, welche Themen die Seite abdeckt.', $h2c >= 3 ? '' : 'Je Leistung oder Frage eine H2 setzen.');
$words = $P['words'];
add('seo', $words >= 400 ? 'ok' : ($words >= 200 ? 'warn' : 'bad'), 'high', 'Textmenge der Startseite: ca. ' . $words . ' Wörter', $words >= 400 ? 'Genug Text, um Leistungen und Ort zu erklären.' : 'Zu wenig Text, um für Suchanfragen relevant zu sein. Seiten mit sehr wenig Text ranken selten, und KI-Antworten finden kaum zitierbare Aussagen.', $words >= 400 ? '' : 'Leistungen, Einsatzgebiet, Ablauf und häufige Fragen in eigenen Abschnitten beschreiben.');
$canon = $P['canonical'];
$canonOk = false; $canonDetail = '';
if ($canon === '') $canonDetail = 'Ohne canonical können Varianten der Seite (mit und ohne www, mit Parametern) als Dubletten gelten.';
else { $ch = strtolower((string) parse_url($canon, PHP_URL_HOST)); $canonOk = $ch === '' || preg_replace('/^www\./', '', $ch) === strtolower($bareHost); $canonDetail = $canonOk ? 'Die Hauptadresse ist gesetzt.' : 'Die kanonische Adresse zeigt auf eine andere Domain (' . $ch . '). Das schickt Google weg von dieser Seite.'; }
add('seo', $canonOk ? 'ok' : ($canon === '' ? 'warn' : 'bad'), 'mid', $canon === '' ? 'Kanonische Adresse fehlt' : ($canonOk ? 'Kanonische Adresse gesetzt' : 'Kanonische Adresse zeigt auf fremde Domain'), $canonDetail, $canonOk ? '' : 'Eine canonical-Angabe auf die eigene Hauptadresse setzen.');
add('seo', $P['lang'] !== '' ? 'ok' : 'warn', 'low', $P['lang'] !== '' ? 'Sprache angegeben (' . $P['lang'] . ')' : 'Sprache der Seite nicht angegeben', $P['lang'] !== '' ? 'Browser, Vorlesehilfen und Suchmaschinen erkennen die Sprache.' : 'Das lang-Attribut fehlt.', $P['lang'] !== '' ? '' : 'Am HTML-Element lang="de" setzen.');
// Robots, Sitemap
$robots = time_left() > 4 ? safe_fetch($origin . '/robots.txt', 200000, 5) : ['ok' => false];
$robotsOk = !empty($robots['ok']) && $robots['status'] === 200 && stripos($robots['headers']['content-type'] ?? 'text/plain', 'html') === false;
$blocksAll = $robotsOk && robots_blocks($robots['body'], 'googlebot');
if ($blocksAll) $caps[] = [20, 'Die robots.txt sperrt die ganze Seite für Suchmaschinen.'];
add('seo', $blocksAll ? 'bad' : ($robotsOk ? 'ok' : 'warn'), $blocksAll ? 'high' : 'low', $blocksAll ? 'robots.txt sperrt die ganze Seite' : ($robotsOk ? 'robots.txt vorhanden' : 'robots.txt nicht gefunden'), $blocksAll ? 'Die Datei verbietet Suchmaschinen den Zugriff auf alles. Bei einer Live-Seite fast immer ein Fehler.' : ($robotsOk ? 'Die Datei steuert, was Suchmaschinen abrufen dürfen.' : 'Kein Pflichtbestandteil, aber der übliche Ort für den Sitemap-Verweis.'), $blocksAll ? 'Die Zeile „Disallow: /“ entfernen.' : ($robotsOk ? '' : 'Eine einfache robots.txt mit Sitemap-Verweis anlegen.'));
$sitemapUrl = '';
if ($robotsOk && preg_match('/^\s*Sitemap:\s*(\S+)/im', $robots['body'], $m) && strcasecmp((string) parse_url($m[1], PHP_URL_HOST), $host) === 0) $sitemapUrl = $m[1];
$sm = time_left() > 4 ? safe_fetch($sitemapUrl !== '' ? $sitemapUrl : $origin . '/sitemap.xml', 400000, 6) : ['ok' => false];
$sitemapOk = !empty($sm['ok']) && $sm['status'] === 200 && (stripos($sm['body'], '<urlset') !== false || stripos($sm['body'], '<sitemapindex') !== false);
$smUrls = $sitemapOk ? preg_match_all('#<loc>\s*([^<]+?)\s*</loc>#i', $sm['body'], $mm) : 0;
add('seo', $sitemapOk ? ($smUrls >= 4 || stripos($sm['body'], '<sitemapindex') !== false ? 'ok' : 'warn') : 'bad', 'mid', $sitemapOk ? 'Sitemap gefunden (' . $smUrls . ' Einträge)' : 'Keine Sitemap gefunden',
  $sitemapOk ? ($smUrls >= 4 || stripos($sm['body'], '<sitemapindex') !== false ? 'Suchmaschinen finden alle Seiten schneller.' : 'Die Sitemap nennt sehr wenige Adressen. Entweder ist die Seite winzig, oder Unterseiten fehlen.') : 'Ohne Sitemap hängt es vom Zufall ab, wie schnell neue Seiten gefunden werden.',
  $sitemapOk ? ($smUrls >= 4 || stripos($sm['body'], '<sitemapindex') !== false ? '' : 'Alle wichtigen Seiten aufnehmen.') : 'Sitemap erzeugen, in der robots.txt nennen und in der Search Console einreichen.');
// Strukturierte Daten
if ($ldInvalid > 0) add('seo', 'bad', 'mid', 'Strukturierte Daten fehlerhaft (' . $ldInvalid . ' Block/Blöcke ungültig)', 'Fehlerhaftes JSON-LD wird von Google ignoriert.', 'Mit dem Test für Rich-Ergebnisse von Google prüfen und korrigieren.');
$ldBreadcrumb = in_array('BreadcrumbList', $ldTypes, true);
$ldWebsite = in_array('WebSite', $ldTypes, true) || in_array('WebPage', $ldTypes, true);
add('seo', $ldTypes ? 'ok' : 'warn', 'mid', $ldTypes ? 'Strukturierte Daten vorhanden (' . implode(', ', array_slice($ldTypes, 0, 4)) . ')' : 'Keine strukturierten Daten', $ldTypes ? 'Die Seite liefert maschinenlesbare Angaben.' : 'Ohne JSON-LD müssen Suchmaschinen alles aus dem Text erraten.', $ldTypes ? '' : 'Organisations- oder LocalBusiness-Daten als JSON-LD ergänzen.');
// Bilder
$imgs = $q('//img'); $imgTotal = count($imgs); $noAlt = 0; $emptyAlt = 0; $noDim = 0; $lazy = 0; $modern = 0;
foreach ($imgs as $i => $im) {
  if (!$im->hasAttribute('alt')) $noAlt++; elseif (trim($im->getAttribute('alt')) === '') $emptyAlt++;
  if (!$im->hasAttribute('width') || !$im->hasAttribute('height')) $noDim++;
  if (strtolower($im->getAttribute('loading')) === 'lazy') $lazy++;
  $src = strtolower($im->getAttribute('src') . ' ' . $im->getAttribute('srcset'));
  if (preg_match('/\.(webp|avif|svg)(\?|\s|$)/', $src)) $modern++;
}
if ($imgTotal > 0) {
  add('seo', $noAlt === 0 ? 'ok' : ($noAlt / $imgTotal > 0.5 ? 'bad' : 'warn'), 'mid', $noAlt === 0 ? 'Alle Bilder haben ein alt-Attribut' : $noAlt . ' von ' . $imgTotal . ' Bildern ohne Textalternative', $noAlt === 0 ? 'Gut für Barrierefreiheit und Bildersuche.' : 'Ohne Alternativtext sind Bilder für Vorlesehilfen und Suchmaschinen unsichtbar.', $noAlt === 0 ? '' : 'Jedem inhaltlichen Bild einen kurzen, beschreibenden Text geben.');
  add('tech', $noDim <= $imgTotal * 0.2 ? 'ok' : 'warn', 'mid', $noDim === 0 ? 'Bilder mit Breite und Höhe angegeben' : $noDim . ' von ' . $imgTotal . ' Bildern ohne Größenangabe', $noDim <= $imgTotal * 0.2 ? 'Die Seite springt beim Laden kaum.' : 'Ohne Größenangaben verschiebt sich der Inhalt beim Laden. Das verschlechtert die „Layoutverschiebung“, einen Core Web Vital.', $noDim <= $imgTotal * 0.2 ? '' : 'width und height an jedes Bild schreiben.');
  if ($imgTotal >= 4) add('tech', ($lazy >= 1 && $modern >= $imgTotal * 0.5) ? 'ok' : 'warn', 'low', 'Bildformate und Nachladen', ($lazy >= 1 && $modern >= $imgTotal * 0.5) ? 'Moderne Formate und verzögertes Laden sind im Einsatz.' : 'Moderne Formate (WebP, AVIF) und verzögertes Laden (loading="lazy") sparen auf dem Smartphone viele Sekunden. ' . $modern . ' von ' . $imgTotal . ' Bildern in modernem Format, ' . $lazy . ' mit verzögertem Laden.', ($lazy >= 1 && $modern >= $imgTotal * 0.5) ? '' : 'Bilder als WebP ausliefern und unterhalb des ersten Bildschirms lazy laden.');
}
// Stichprobe interner Seiten
$sample = [];
if (time_left() > 8) {
  $seen = [];
  foreach ($q('//a[@href]') as $a) {
    $h = trim($a->getAttribute('href'));
    if ($h === '' || $h[0] === '#' || preg_match('#^(mailto:|tel:|javascript:|whatsapp:|sms:)#i', $h)) continue;
    $abs = preg_match('#^https?://#i', $h) ? $h : (preg_match('#^//#', $h) ? $scheme . ':' . $h : (($h[0] === '/') ? $origin . $h : $origin . '/' . ltrim($h, './')));
    $pp = parse_url($abs); if (empty($pp['host']) || preg_replace('/^www\./i', '', strtolower($pp['host'])) !== strtolower($bareHost)) continue;
    $path = rtrim((string) ($pp['path'] ?? '/'), '/'); if ($path === '' || preg_match('/(impressum|datenschutz|agb|privacy|cookie|login|wp-admin)(\.html?|\.php)?$|\.(pdf|jpg|jpeg|png|webp|zip|docx?)$/i', $path)) continue;
    if (isset($seen[$path])) continue; $seen[$path] = $origin . $path;
    if (count($seen) >= 3) break;
  }
  foreach ($seen as $u) {
    if (time_left() < 5) break;
    $r = safe_fetch($u, 600000, 5);
    if (empty($r['ok']) || $r['status'] >= 400 || stripos($r['headers']['content-type'] ?? 'text/html', 'html') === false) { $sample[] = ['url' => $u, 'bad' => true, 'status' => $r['status'] ?? 0]; continue; }
    $pp = parse_page($r['body']);
    $sample[] = ['url' => $u, 'title' => $pp['title'], 'desc' => $pp['desc'], 'h1' => $pp['h1'][0] ?? '', 'noindex' => strpos($pp['robots'], 'noindex') !== false, 'words' => $pp['words'], 'ttfb' => $r['ttfb']];
  }
}
if (count($sample) >= 2) {
  $broken = count(array_filter($sample, fn($s) => !empty($s['bad'])));
  $good = array_values(array_filter($sample, fn($s) => empty($s['bad'])));
  $titles = array_merge([lc($title)], array_map(fn($s) => lc($s['title']), $good));
  $dupT = count($titles) - count(array_unique($titles));
  $noT = count(array_filter($good, fn($s) => $s['title'] === ''));
  $descs = array_filter(array_merge([lc($P['desc'])], array_map(fn($s) => lc($s['desc']), $good)), fn($d) => $d !== '');
  $dupD = count($descs) - count(array_unique($descs));
  $noD = count(array_filter($good, fn($s) => $s['desc'] === ''));
  $thin = count(array_filter($good, fn($s) => $s['words'] < 150));
  $noH1 = count(array_filter($good, fn($s) => $s['h1'] === ''));
  $noi = count(array_filter($good, fn($s) => $s['noindex']));
  $n = count($sample);
  add('seo', ($dupT === 0 && $noT === 0) ? 'ok' : 'bad', 'high', 'Stichprobe (' . $n . ' interne Seiten): ' . (($dupT === 0 && $noT === 0) ? 'Titel sind eindeutig' : ($dupT > 0 ? 'doppelte Seitentitel' : 'Titel fehlen')), ($dupT === 0 && $noT === 0) ? 'Jede geprüfte Seite hat ihren eigenen Titel.' : 'Seiten mit gleichem oder fehlendem Titel konkurrieren miteinander und sind in der Trefferliste nicht unterscheidbar. Das ist einer der häufigsten Fehler bei kleinen Websites.', ($dupT === 0 && $noT === 0) ? '' : 'Jeder Seite einen eigenen Titel mit Leistung und Ort geben.');
  add('seo', ($dupD === 0 && $noD === 0) ? 'ok' : 'warn', 'mid', 'Stichprobe: ' . (($dupD === 0 && $noD === 0) ? 'Beschreibungen vorhanden und eindeutig' : ($noD > 0 ? 'Beschreibungen fehlen auf Unterseiten' : 'doppelte Beschreibungen')), ($dupD === 0 && $noD === 0) ? 'Jede geprüfte Seite hat eine eigene Beschreibung.' : 'Fehlende oder doppelte Beschreibungen kosten Klicks in der Trefferliste.', ($dupD === 0 && $noD === 0) ? '' : 'Je Seite eine eigene Beschreibung schreiben.');
  if ($thin > 0 || $noH1 > 0 || $noi > 0 || $broken > 0) {
    $why = array_filter([$broken ? $broken . ' Seite(n) nicht abrufbar' : '', $noi ? $noi . ' per noindex gesperrt' : '', $noH1 ? $noH1 . ' ohne H1' : '', $thin ? $thin . ' mit sehr wenig Text' : '']);
    add('seo', 'warn', 'mid', 'Stichprobe: Probleme auf Unterseiten', implode(', ', $why) . '.', 'Unterseiten einzeln prüfen: sie sollen erreichbar, indexierbar und mit eigener H1 und ausreichend Text versehen sein.');
  } else add('seo', 'ok', 'low', 'Stichprobe: Unterseiten in Ordnung', 'Alle geprüften Seiten sind erreichbar, indexierbar und haben eine H1 und ausreichend Text.');
} else {
  add('seo', 'warn', 'mid', 'Kaum interne Seiten erkennbar', 'Auf der Startseite wurden weniger als zwei interne Unterseiten verlinkt. Eine Website mit nur einer Seite deckt nur eine Suchanfrage ab.', 'Je Leistung eine eigene Seite anlegen und von der Startseite verlinken.');
}

// ===== LOKALE SICHTBARKEIT =====
$bodyText = $P['text'];
$plz = null; $ort = null;
if (preg_match('/\b(\d{5})\s+([A-ZÄÖÜ][\p{L}\-]+(?:\s+(?:am|an der|im|bei|a\.)\s+[A-ZÄÖÜ][\p{L}\-]+)?)/u', $bodyText, $m)) { $plz = $m[1]; $ort = $m[2]; }
$ldAddr = is_array($entity['address'] ?? null) ? $entity['address'] : null;
if ($ldAddr && !empty($ldAddr['addressLocality'])) { $ort = (string) $ldAddr['addressLocality']; $plz = $plz ?: (string) ($ldAddr['postalCode'] ?? ''); }
$hasAddress = $ort !== null;
add('local', $hasAddress ? 'ok' : 'bad', 'high', $hasAddress ? 'Anschrift auf der Seite erkennbar (' . cut(trim(($plz ? $plz . ' ' : '') . $ort), 40) . ')' : 'Keine Anschrift mit Postleitzahl und Ort erkennbar', $hasAddress ? 'Besucher und Suchmaschinen sehen, wo Sie arbeiten.' : 'Für lokale Suchen ist die Anschrift das stärkste Signal. Ohne sie ist der Ortsbezug nur zu erraten.', $hasAddress ? '' : 'Vollständige Anschrift gut sichtbar im Fußbereich und auf der Kontaktseite angeben, ebenso im Impressum.');
if ($hasAddress) {
  $o = lc($ort);
  $inTitle = strpos(lc($title), $o) !== false; $inH1 = $P['h1'] && strpos(lc($P['h1'][0]), $o) !== false; $inDesc = strpos(lc($P['desc']), $o) !== false;
  $count = (int) $inTitle + (int) $inH1 + (int) $inDesc;
  add('local', $count >= 2 ? 'ok' : ($count === 1 ? 'warn' : 'bad'), 'high', 'Ortsbezug in Titel, Überschrift und Beschreibung: ' . $count . ' von 3', $count >= 2 ? 'Der Ort „' . $ort . '“ steht an den wichtigsten Stellen.' : 'Der Ort „' . $ort . '“ kommt an den wichtigsten Stellen kaum vor. Wer „Leistung + Ort“ sucht, findet Sie dadurch schlechter.', $count >= 2 ? '' : 'Ort in Titel, H1 und Beschreibung nennen, zum Beispiel „… in ' . $ort . ' und Umgebung“.');
  $mentions = substr_count(lc($bodyText), $o);
  add('local', $mentions >= 3 ? 'ok' : 'warn', 'mid', 'Ortsnennung im Text: ' . $mentions . 'x', $mentions >= 3 ? 'Der Ort wird im Text mehrfach natürlich erwähnt.' : 'Der Ortsname taucht im Text kaum auf.', $mentions >= 3 ? '' : 'Einsatzgebiet und Orte im Text nennen, soweit es für Kunden relevant ist.');
}
$areaStr = '';
$hasHours = (bool) preg_match('/Öffnungszeit|geöffnet|Sprechzeit|Mo\.?\s*(–|-|bis)\s*(Fr|Do|Sa|So)/iu', $bodyText);
add('local', $hasHours ? 'ok' : 'warn', 'mid', $hasHours ? 'Öffnungs- oder Erreichbarkeitszeiten genannt' : 'Keine Öffnungs- oder Erreichbarkeitszeiten erkennbar', $hasHours ? 'Kunden wissen, wann sie Sie erreichen.' : 'Kunden entscheiden schnell, ob Sie jetzt erreichbar sind. Fehlende Zeiten kosten Anrufe.', $hasHours ? '' : 'Zeiten sichtbar nennen und im Google-Unternehmensprofil identisch pflegen.');
$phoneText = (bool) preg_match('/(\+49|0)\s?[\d\s\/\-\(\)]{7,}/', $bodyText);
add('local', $phoneText ? 'ok' : 'warn', 'mid', $phoneText ? 'Telefonnummer im Text vorhanden' : 'Keine Telefonnummer im sichtbaren Text', $phoneText ? 'Name, Anschrift und Telefon lassen sich abgleichen.' : 'Telefonnummer fehlt im Text oder ist nur als Bild eingebunden.', $phoneText ? '' : 'Telefonnummer als Text angeben, identisch mit dem Google-Profil.');
if ($entity) {
  $addr = is_array($entity['address'] ?? null) ? $entity['address'] : [];
  $need = ['Anschrift (Straße, PLZ, Ort)' => !empty($addr['streetAddress']) && !empty($addr['postalCode']) && !empty($addr['addressLocality']), 'Telefon' => !empty($entity['telephone']), 'Öffnungszeiten' => !empty($entity['openingHoursSpecification']) || !empty($entity['openingHours']), 'Standort (geo)' => !empty($entity['geo']), 'Logo oder Bild' => !empty($entity['image']) || !empty($entity['logo']), 'Profile (sameAs)' => !empty($entity['sameAs']), 'Einsatzgebiet (areaServed)' => !empty($entity['areaServed'])];
  $miss = array_keys(array_filter($need, fn($v) => !$v));
  $isBiz = (bool) $biz;
  add('local', (!$isBiz) ? 'warn' : (count($miss) <= 2 ? 'ok' : (count($miss) <= 4 ? 'warn' : 'bad')), 'high', $isBiz ? 'Unternehmensdaten (LocalBusiness) vollständig zu ' . (7 - count($miss)) . ' von 7' : 'Nur allgemeine Organisationsdaten, kein LocalBusiness',
    $isBiz ? ($miss ? 'Es fehlen: ' . implode(', ', $miss) . '.' : 'Alle wichtigen Felder sind gepflegt.') : 'Für lokale Betriebe ist der Typ LocalBusiness (oder ein Untertyp) mit Anschrift und Öffnungszeiten der Standard.', $miss || !$isBiz ? 'LocalBusiness-Daten als JSON-LD vervollständigen, mit Angaben identisch zum Google-Profil.' : '');
} else {
  add('local', 'bad', 'high', 'Keine Unternehmensdaten als strukturierte Daten', 'Suchmaschinen und KI-Antworten müssen Name, Anschrift und Leistungen aus dem Fließtext erraten.', 'Organization oder LocalBusiness mit Anschrift, Telefon, Öffnungszeiten und Profilen als JSON-LD hinterlegen.');
}
$mapLink = (bool) preg_match('#google\.[a-z.]+/maps|maps\.app\.goo\.gl|goo\.gl/maps|openstreetmap\.org|maps\.apple\.com#i', $html);
add('local', $mapLink ? 'ok' : 'info', 'low', $mapLink ? 'Karte oder Routenlink vorhanden' : 'Kein Karten- oder Routenlink', $mapLink ? 'Besucher finden den Weg direkt.' : 'Weder Routenlink noch Karte gefunden.', '');
$reviewWords = (bool) preg_match('/Bewertung|Rezension|Kundenstimme|Erfahrungen|Referenz|Testimonial|★|Sterne|Google-Bewertung/iu', $bodyText . ' ' . $html);
add('local', $reviewWords ? 'ok' : 'warn', 'mid', $reviewWords ? 'Bewertungen oder Kundenstimmen erwähnt' : 'Keine Bewertungen oder Kundenstimmen erkennbar', $reviewWords ? 'Bewertungen sind für lokale Suchen ein Rankingfaktor und für Kunden ein Vertrauenssignal. Echtheit und Menge prüft dieser Check nicht.' : 'Bewertungen sind bei lokalen Suchen ein starkes Signal und entscheiden oft zwischen zwei Anbietern.', $reviewWords ? '' : 'Echte Kundenstimmen mit Erlaubnis zeigen und aktiv um Google-Bewertungen bitten.');

// ===== GEO: KI-ANTWORTEN =====
$aiBots = ['GPTBot', 'ChatGPT-User', 'OAI-SearchBot', 'ClaudeBot', 'Claude-User', 'anthropic-ai', 'PerplexityBot', 'Google-Extended', 'Applebot-Extended', 'CCBot', 'Bytespider'];
$blockedBots = [];
if ($robotsOk) foreach ($aiBots as $b) if (robots_blocks($robots['body'], $b)) $blockedBots[] = $b;
if ($robotsOk && !$blocksAll) {
  add('geo', !$blockedBots ? 'ok' : (count($blockedBots) >= 4 ? 'bad' : 'warn'), 'high', !$blockedBots ? 'KI-Crawler sind nicht ausgesperrt' : 'KI-Crawler ausgesperrt: ' . implode(', ', array_slice($blockedBots, 0, 5)),
    !$blockedBots ? 'KI-Dienste dürfen Ihre Seite lesen und in Antworten berücksichtigen.' : 'Gesperrte Dienste können Ihre Inhalte nicht für Antworten nutzen. Das kann gewollt sein, kostet dann aber Sichtbarkeit in diesen Antworten.', !$blockedBots ? '' : 'Bewusst entscheiden: Wenn Sie in KI-Antworten genannt werden wollen, diese Sperren in der robots.txt entfernen.');
} else if (!$robotsOk) {
  add('geo', 'info', 'low', 'KI-Crawler: keine Regeln erkennbar', 'Ohne robots.txt gelten keine Sperren. Es sind keine Crawler-Regeln hinterlegt.', '');
}
$llms = time_left() > 3 ? safe_fetch($origin . '/llms.txt', 100000, 4) : ['ok' => false];
$llmsOk = !empty($llms['ok']) && $llms['status'] === 200 && stripos($llms['headers']['content-type'] ?? 'text/plain', 'html') === false && len($llms['body']) > 80;
add('geo', $llmsOk ? 'ok' : 'info', 'low', $llmsOk ? 'llms.txt vorhanden' : 'Keine llms.txt', $llmsOk ? 'Eine kurze, maschinenlesbare Beschreibung Ihres Angebots für KI-Dienste. Kein offizieller Standard, wird aber von einigen Diensten gelesen.' : 'Eine optionale Textdatei, die Angebot, Orte und wichtige Seiten für KI-Dienste zusammenfasst. Kein offizieller Standard.', $llmsOk ? '' : 'Eine llms.txt mit Beschreibung, Leistungen, Einsatzgebiet und Links anlegen.');
$sameAs = !empty($entity['sameAs']) ? (array) $entity['sameAs'] : [];
add('geo', $entity ? ($sameAs ? 'ok' : 'warn') : 'bad', 'high', $entity ? ($sameAs ? 'Eindeutige Identität: Profile verknüpft (sameAs: ' . count($sameAs) . ')' : 'Unternehmen definiert, aber ohne verknüpfte Profile') : 'Unternehmen ist für Maschinen nicht eindeutig beschrieben',
  $entity ? ($sameAs ? 'KI-Dienste können Ihre Website, Ihr Google-Profil und Ihre Social-Profile derselben Firma zuordnen.' : 'Ohne sameAs-Verknüpfung (Google-Profil, Facebook, LinkedIn, Branchenverzeichnisse) ist die Zuordnung unsicher.') : 'KI-Antworten nennen Anbieter, die sie eindeutig erkennen und zuordnen können.', $entity && $sameAs ? '' : 'In den Unternehmensdaten (JSON-LD) alle Profile unter sameAs verknüpfen.');
$qHeads = 0; foreach (array_merge($P['h2'], array_map(fn($n) => norm($n->textContent), $q('//h3'))) as $h) if (preg_match('/\?\s*$/u', $h)) $qHeads++;
$hasFaqText = (bool) preg_match('/häufige fragen|\bFAQ\b|fragen und antworten/iu', $bodyText);
$hasFaqLd = in_array('FAQPage', $ldTypes, true);
$geoFaq = $qHeads >= 3 || $hasFaqLd || ($hasFaqText && $qHeads >= 2);
add('geo', $geoFaq ? 'ok' : ($qHeads >= 1 || $hasFaqText ? 'warn' : 'bad'), 'high', $geoFaq ? 'Fragen und Antworten vorhanden' . ($hasFaqLd ? ' (auch als strukturierte Daten)' : '') : 'Kaum Fragen und Antworten auf der Seite',
  $geoFaq ? 'KI-Antworten greifen gern auf klar formulierte Fragen mit knappen Antworten zurück.' : 'KI-Dienste zitieren Seiten, die Kundenfragen direkt und knapp beantworten. Ohne solche Abschnitte werden Sie selten genannt.', $geoFaq ? '' : 'Die zehn häufigsten Kundenfragen als Überschriften mit zwei bis vier Sätzen Antwort aufnehmen.');
$lists = count($q('//ul')) + count($q('//ol')) + count($q('//table'));
$hasPrices = (bool) preg_match('/\d[\d\.]*\s?(€|EUR|Euro)\b|ab\s+\d+\s?€/u', $bodyText);
add('geo', ($lists >= 2 && $hasPrices) ? 'ok' : (($lists >= 2 || $hasPrices) ? 'warn' : 'bad'), 'mid', 'Zitierfähige Fakten: ' . ($hasPrices ? 'Preise genannt' : 'keine Preise') . ', ' . $lists . ' Listen oder Tabellen',
  ($lists >= 2 && $hasPrices) ? 'Konkrete Angaben und Aufzählungen lassen sich in Antworten übernehmen.' : 'KI-Antworten übernehmen konkrete Angaben (Preise, Umfang, Ablauf, Zeiten) und gegliederte Listen. Allgemeine Werbesprache wird kaum zitiert.', ($lists >= 2 && $hasPrices) ? '' : 'Leistungen mit Umfang, Dauer und (Ab-)Preis in Listen oder Tabellen darstellen.');
$semantic = (int) (count($q('//main')) > 0) + (int) (count($q('//nav')) > 0) + (int) (count($q('//footer')) > 0) + (int) (count($q('//header')) > 0) + (int) (count($q('//article|//section')) > 0);
add('geo', $semantic >= 4 ? 'ok' : ($semantic >= 2 ? 'warn' : 'bad'), 'low', 'Saubere HTML-Struktur: ' . $semantic . ' von 5 Gliederungselementen', $semantic >= 4 ? 'main, nav, header, footer und Abschnitte helfen Maschinen, Inhalt von Rahmen zu trennen.' : 'Ohne klare Gliederung (main, nav, header, footer, section) ist es für Maschinen schwerer, den eigentlichen Inhalt zu erkennen.', $semantic >= 4 ? '' : 'Seitenvorlage mit semantischen Elementen aufbauen lassen.');
$dateLd = false; foreach ($ldNodes as $n) if (!empty($n['dateModified']) || !empty($n['datePublished'])) $dateLd = true;
$lastMod = isset($H['last-modified']);
$years = []; if (preg_match_all('/(?:©|&copy;|\(c\)|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d{2})/iu', $bodyText . ' ' . $html, $ym)) $years = array_map('intval', $ym[1]);
$yNow = (int) date('Y'); $yMax = $years ? max($years) : 0;
if ($yMax > 0) add('geo', $yMax >= $yNow - 0 ? 'ok' : ($yMax === $yNow - 1 ? 'warn' : 'bad'), 'mid', 'Aktualität: Copyright-Jahr ' . $yMax, $yMax >= $yNow ? 'Der Fußbereich ist auf dem aktuellen Stand.' : 'Ein veraltetes Jahr im Fußbereich lässt die Seite vernachlässigt wirken, bei Kunden wie bei Systemen, die Aktualität bewerten.', $yMax >= $yNow ? '' : 'Jahr aktualisieren, am besten automatisch, und Inhalte regelmäßig prüfen.');
else add('geo', ($dateLd || $lastMod) ? 'ok' : 'info', 'low', ($dateLd || $lastMod) ? 'Aktualitätsangabe vorhanden' : 'Keine Aktualitätsangabe erkennbar', 'Angaben zu Datum oder letzter Änderung helfen Suchmaschinen und KI-Diensten, die Aktualität einzuschätzen.', '');
$aboutLink = (bool) preg_match('/über uns|ueber-uns|about|team|wir über uns|unternehmen/iu', implode(' ', array_map(fn($a) => $a->getAttribute('href') . ' ' . $a->textContent, $q('//a[@href]'))));
add('geo', $aboutLink ? 'ok' : 'warn', 'low', $aboutLink ? 'Seite „Über uns“ vorhanden' : 'Keine Seite „Über uns“ erkennbar', $aboutLink ? 'Menschen und Maschinen finden, wer hinter dem Unternehmen steht.' : 'Wer hinter einem Angebot steht, ist ein zentrales Vertrauens- und Qualitätssignal.', $aboutLink ? '' : 'Eine Seite mit Gesicht, Werdegang und Arbeitsweise anlegen.');
$jsOnly = $words < 120 && count($scripts) >= 3;
if ($jsOnly) add('geo', 'bad', 'high', 'Inhalt wird vermutlich erst per Skript geladen', 'Im ausgelieferten HTML steht kaum Text, aber mehrere Skripte. Was nicht im HTML steht, sehen viele Suchmaschinen und fast alle KI-Crawler nicht.', 'Inhalte serverseitig ausliefern (Server-Rendering oder statisches HTML).');
else add('geo', 'ok', 'mid', 'Inhalt steht im ausgelieferten HTML', 'Suchmaschinen und KI-Crawler lesen Ihre Texte, ohne Skripte ausführen zu müssen.');

// ===== SMARTPHONE UND ZUGÄNGLICHKEIT =====
$vp = lc($P['viewport']);
if ($vp === '') $caps[] = [60, 'Die Seite ist nicht für Smartphones eingerichtet.'];
add('ux', $vp !== '' && strpos($vp, 'width=device-width') !== false ? 'ok' : 'bad', 'high', $vp !== '' ? ((strpos($vp, 'width=device-width') !== false) ? 'Für Smartphones eingerichtet' : 'Viewport-Angabe unvollständig') : 'Nicht für Smartphones eingerichtet', $vp !== '' ? 'Die Seite passt sich der Bildschirmbreite an.' : 'Auf dem Smartphone erscheint die Seite winzig. Die Mehrheit der lokalen Suchen kommt vom Handy, und Google bewertet vor allem die mobile Seite.', $vp !== '' && strpos($vp, 'width=device-width') !== false ? '' : 'Das Viewport-Tag mit width=device-width setzen und die Seite mobil gestalten.');
if ($vp !== '' && (strpos($vp, 'user-scalable=no') !== false || preg_match('/maximum-scale=1(\.0)?(?!\d)/', $vp))) add('ux', 'warn', 'mid', 'Vergrößern auf dem Smartphone ist gesperrt', 'Sehbehinderte Besucher können nicht zoomen. Das ist ein Verstoß gegen gängige Zugänglichkeitsregeln.', 'user-scalable=no und maximum-scale=1 aus dem Viewport-Tag entfernen.');
$inputs = array_filter($q('//input[not(@type="hidden") and not(@type="submit") and not(@type="button")]|//textarea|//select'), fn($n) => true);
$unl = 0; foreach ($inputs as $in) { $id = $in->getAttribute('id'); $hasL = $in->hasAttribute('aria-label') || $in->hasAttribute('aria-labelledby') || ($id !== '' && count($q('//label[@for="' . preg_replace('/[^A-Za-z0-9_\-:.]/', '', $id) . '"]')) > 0) || $in->parentNode && $in->parentNode->nodeName === 'label'; if (!$hasL) $unl++; }
if ($inputs) add('ux', $unl === 0 ? 'ok' : 'warn', 'mid', $unl === 0 ? 'Formularfelder sind beschriftet' : $unl . ' von ' . count($inputs) . ' Formularfeldern ohne Beschriftung', $unl === 0 ? 'Vorlesehilfen können Felder benennen.' : 'Felder ohne Beschriftung sind für Screenreader unbenutzbar. Ein Platzhaltertext ersetzt keine Beschriftung.', $unl === 0 ? '' : 'Jedem Feld ein sichtbares Label zuordnen.');
$emptyLinks = 0; foreach ($q('//a[@href]') as $a) { if (norm($a->textContent) === '' && !$a->hasAttribute('aria-label') && !$a->hasAttribute('title') && count($a->getElementsByTagName('img')) === 0 && count($a->getElementsByTagName('svg')) === 0) $emptyLinks++; }
$generic = 0; foreach ($q('//a[@href]') as $a) if (preg_match('/^(hier|mehr|weiter|mehr erfahren|weiterlesen|klicken sie hier|click here|read more|link)\.?$/iu', norm($a->textContent))) $generic++;
add('ux', ($emptyLinks === 0 && $generic <= 2) ? 'ok' : 'warn', 'low', ($emptyLinks === 0 && $generic <= 2) ? 'Linktexte sind aussagekräftig' : ($emptyLinks ? $emptyLinks . ' Links ohne Text' : '') . ($emptyLinks && $generic ? ', ' : '') . ($generic ? $generic . ' Links mit „hier“ oder „mehr“' : ''), ($emptyLinks === 0 && $generic <= 2) ? 'Links erklären, wohin sie führen.' : 'Links wie „hier“ oder „mehr“ und leere Links sagen weder Vorlesehilfen noch Suchmaschinen, wohin sie führen.', ($emptyLinks === 0 && $generic <= 2) ? '' : 'Linktexte beschreibend formulieren („Leistungen ansehen“, „Preise und Pakete“).');
$skip = (bool) $q('//a[contains(translate(@href,"#MAINCONTENT","#maincontent"),"#main") or contains(translate(@href,"INHALT","inhalt"),"inhalt")]') || strpos($lower, 'skip') !== false;
add('ux', count($q('//main')) > 0 ? 'ok' : 'warn', 'low', count($q('//main')) > 0 ? 'Hauptbereich (main) ausgezeichnet' : 'Kein main-Bereich ausgezeichnet', count($q('//main')) > 0 ? 'Vorlesehilfen können direkt zum Inhalt springen.' : 'Ohne main-Bereich fehlt Vorlesehilfen die Sprungmarke zum Inhalt.', count($q('//main')) > 0 ? '' : 'Den Hauptinhalt in ein main-Element setzen.');
$icon = (bool) $q('//link[contains(@rel,"icon")]');
add('ux', $icon ? 'ok' : 'warn', 'low', $icon ? 'Favicon vorhanden' : 'Kein Favicon', $icon ? 'Das Symbol erscheint in Tabs und bei Google.' : 'Das kleine Symbol erscheint in Browser-Tabs und neben dem Treffer bei Google.', $icon ? '' : 'Favicon als SVG oder PNG einbinden.');
$ogT = (bool) $q('//meta[@property="og:title"]'); $ogI = (bool) $q('//meta[@property="og:image"]'); $ogD = (bool) $q('//meta[@property="og:description"]');
add('ux', ($ogT && $ogI && $ogD) ? 'ok' : (($ogT || $ogI) ? 'warn' : 'bad'), 'low', ($ogT && $ogI && $ogD) ? 'Vorschau beim Teilen vollständig' : 'Vorschau beim Teilen unvollständig', ($ogT && $ogI && $ogD) ? 'Geteilte Links erscheinen mit Titel, Text und Bild.' : 'Ohne Open-Graph-Angaben wirken Links in WhatsApp, Facebook und LinkedIn nackt, das kostet Klicks.', ($ogT && $ogI && $ogD) ? '' : 'og:title, og:description und og:image (1200 x 630) setzen.');

// ===== VERTRAUEN UND ANFRAGE =====
$hasImp = false; $hasDS = false; $hasTel = false; $hasMail = false; $hasWa = false; $social = [];
foreach ($q('//a[@href]') as $a) {
  $h = strtolower($a->getAttribute('href')); $tx = lc(norm($a->textContent));
  if (strpos($h, 'impressum') !== false || strpos($tx, 'impressum') !== false) $hasImp = true;
  if (strpos($h, 'datenschutz') !== false || strpos($tx, 'datenschutz') !== false || strpos($h, 'privacy') !== false) $hasDS = true;
  if (strpos($h, 'tel:') === 0) $hasTel = true;
  if (strpos($h, 'mailto:') === 0) $hasMail = true;
  if (preg_match('#wa\.me|api\.whatsapp|whatsapp://#', $h)) $hasWa = true;
  if (preg_match('#(instagram|facebook|linkedin|youtube|tiktok|xing|pinterest)\.com#', $h, $mm2)) $social[$mm2[1]] = true;
}
$hasForm = count($q('//form')) > 0;
add('trust', $hasImp ? 'ok' : 'bad', 'high', $hasImp ? 'Impressum verlinkt' : 'Impressum nicht gefunden', $hasImp ? 'Ein Link ist vorhanden. Ob die Angaben vollständig sind (Name, Anschrift, Kontakt, Register, Umsatzsteuer-ID), prüft dieser Check nicht.' : 'Geschäftsmäßige Websites brauchen ein leicht erreichbares Impressum (§ 5 DDG). Das Fehlen ist abmahnfähig.', $hasImp ? '' : 'Impressum anlegen und im Fußbereich jeder Seite verlinken.');
add('trust', $hasDS ? 'ok' : 'bad', 'high', $hasDS ? 'Datenschutzerklärung verlinkt' : 'Datenschutzerklärung nicht gefunden', $hasDS ? 'Ein Link ist vorhanden. Den Inhalt prüft dieser Check nicht.' : 'Eine Datenschutzerklärung ist Pflicht, sobald Daten verarbeitet werden, schon bei Server-Protokollen oder einem Formular.', $hasDS ? '' : 'Datenschutzerklärung anlegen (am besten rechtlich geprüft) und im Fußbereich verlinken.');
$contact = $hasTel || $hasForm || $hasMail || $hasWa;
if (!$contact) $caps[] = [70, 'Auf der Startseite gibt es keinen Kontaktweg.'];
add('trust', $contact ? 'ok' : 'bad', 'high', $contact ? 'Kontaktweg auf der Startseite' : 'Kein Kontaktweg auf der Startseite', $contact ? implode(', ', array_filter([$hasTel ? 'Telefon zum Antippen' : '', $hasForm ? 'Formular' : '', $hasMail ? 'E-Mail-Link' : '', $hasWa ? 'WhatsApp' : ''])) . ' gefunden.' : 'Weder Telefonlink, Formular, E-Mail noch WhatsApp. Besucher müssen suchen, und viele gehen.', $contact ? '' : 'Telefon, Formular oder E-Mail gut sichtbar ergänzen.');
add('trust', $hasTel ? 'ok' : 'warn', 'mid', $hasTel ? 'Telefonnummer ist antippbar' : 'Telefonnummer nicht als Link', $hasTel ? 'Auf dem Smartphone genügt ein Tippen zum Anruf.' : 'Mit einem tel:-Link wird aus der Nummer ein Anruf per Tippen. Auf dem Smartphone entscheidet das oft über die Anfrage.', $hasTel ? '' : 'Nummer als Link hinterlegen (tel:+49…).');
$ctaRe = '/(anfrag|angebot|termin|kontakt|anruf|jetzt|beratung|buchen|reservier|kostenlos|sprechen|schreiben|unverbindlich|check|starten|vereinbaren|bestellen|bewerben)/iu';
$ctaTop = 0; $k = 0;
foreach ($q('//a[@href]|//button') as $n) { if ($k++ >= 30) break; if (preg_match($ctaRe, norm($n->textContent))) $ctaTop++; }
add('trust', $ctaTop >= 2 ? 'ok' : ($ctaTop === 1 ? 'warn' : 'bad'), 'high', 'Handlungsaufforderung im oberen Bereich: ' . $ctaTop, $ctaTop >= 2 ? 'Besucher werden früh zur Anfrage geführt.' : 'Die Seite sagt nicht deutlich, was der Besucher als Nächstes tun soll.', $ctaTop >= 2 ? '' : 'Im ersten Bildschirm eine klare Schaltfläche („Termin anfragen“, „Jetzt anrufen“) platzieren.');
$fieldCount = count($q('//form//input[not(@type="hidden") and not(@type="submit") and not(@type="checkbox") and not(@type="radio") and not(@tabindex="-1")]|//form//textarea|//form//select'));
if ($hasForm && $fieldCount > 0) add('trust', $fieldCount <= 6 ? 'ok' : ($fieldCount <= 9 ? 'warn' : 'bad'), 'mid', 'Formular mit ' . $fieldCount . ' Feldern', $fieldCount <= 6 ? 'Kurze Formulare werden häufiger ausgefüllt.' : 'Je mehr Pflichtfelder, desto weniger Anfragen. Jedes zusätzliche Feld senkt die Abschlussquote.', $fieldCount <= 6 ? '' : 'Auf Name, Kontakt und Anliegen kürzen, den Rest im Gespräch klären.');
add('trust', $social ? 'ok' : 'info', 'low', $social ? 'Social-Profile verlinkt (' . implode(', ', array_keys($social)) . ')' : 'Keine Social-Profile verlinkt', $social ? 'Besucher finden weitere Eindrücke, und die Profile lassen sich als sameAs zuordnen.' : 'Verlinkte Profile stärken Vertrauen und die Zuordnung der Marke.', '');
add('trust', $hasWa ? 'ok' : 'info', 'low', $hasWa ? 'WhatsApp als Kontaktweg' : 'Kein WhatsApp-Kontakt', $hasWa ? 'Viele Kunden schreiben lieber, als anzurufen.' : 'Für viele lokale Betriebe ist WhatsApp ein bequemer Einstieg. Optional.', '');

/**
 * Interne Benachrichtigung über einen durchgeführten Check (ohne Name, ohne IP-Adresse): Adresse, Wert, Bereichswerte und
 * die offenen Punkte (Status, Gewicht) als Gesprächsgrundlage, falls sich der Besucher später meldet. Begrenzung: dieselbe Adresse höchstens
 * einmal je 6 Stunden, insgesamt höchstens 40 Mails je Stunde. Abschalten mit MX_CHECK_NOTIFY=0.
 */
function notify_owner(array $r): void {
  if (getenv('MX_CHECK_NOTIFY') === '0') return;
  $dir = sys_get_temp_dir();
  $now = time();
  $dup = $dir . '/mx-notify-' . hash('sha256', strtolower((string) $r['host'])) . '.txt';
  if (is_file($dup) && @filemtime($dup) > $now - 6 * 3600) return;
  $cnt = $dir . '/mx-notify-count.json';
  $hits = is_file($cnt) ? (json_decode((string) @file_get_contents($cnt), true) ?: []) : [];
  $hits = array_values(array_filter($hits, fn($x) => $now - (int) $x < 3600));
  if (count($hits) >= 40) return;
  $hits[] = $now; @file_put_contents($cnt, json_encode($hits)); @touch($dup);
  require_once __DIR__ . '/mx-mail.php';
  $c = [
    'smtp_host' => getenv('MX_SMTP_HOST') ?: '', 'smtp_port' => (int) (getenv('MX_SMTP_PORT') ?: 465), 'smtp_user' => getenv('MX_SMTP_USER') ?: '',
    'smtp_pass' => getenv('MX_SMTP_PASS') ?: '', 'smtp_security' => getenv('MX_SMTP_SECURITY') ?: '', 'from' => getenv('MX_MAIL_FROM') ?: 'website@markentrix.de',
  ];
  $to = getenv('MX_MAIL_TO') ?: 'info@markentrix.de';
  $L = ['Ein Besucher hat den kostenlosen Website-Check genutzt.', '',
        'Adresse     : ' . $r['url'], 'Zeitpunkt   : ' . date('d.m.Y H:i') . ' Uhr',
        'Wert        : ' . $r['score'] . ' von 100 (' . $r['grade'] . ')' . ($r['cap'] ? ', gedeckelt: ' . $r['cap'] : ''),
        'Merkmale    : ' . $r['checks'] . ' geprüft, ' . $r['counts']['ok'] . ' in Ordnung, ' . $r['counts']['warn'] . ' auffällig, ' . $r['counts']['bad'] . ' mangelhaft', '', 'Bereichswerte'];
  foreach ($r['categories'] as $cat) $L[] = '  ' . str_pad((string) $cat['score'], 3, ' ', STR_PAD_LEFT) . '  ' . $cat['title'];
  $L[] = ''; $L[] = 'Offene Punkte (Status, Gewicht)';
  $n = 0;
  foreach ($r['categories'] as $cat) foreach ($cat['items'] as $it) {
    if (in_array($it['status'], ['bad', 'warn'], true)) { $n++; $L[] = '  [' . ($it['status'] === 'bad' ? 'mangelhaft' : 'auffällig') . ', ' . ['high' => 'hoch', 'mid' => 'mittel', 'low' => 'gering'][$it['impact']] . '] ' . $cat['title'] . ': ' . $it['title']; }
  }
  if ($n === 0) $L[] = '  keine';
  $L[] = ''; $L[] = 'Der Besucher hat keinen Namen und keine Kontaktdaten angegeben. Fordert er die Kurzfassung per E-Mail an, kommt eine eigene Mail mit seinen Angaben (Quelle: Website-Check).';
  $L[] = 'Diese Mail enthält weder eine IP-Adresse noch einen Namen.';
  $subject = '[markentrix.de] Website-Check: ' . $r['host'] . ' (' . $r['score'] . ' von 100)';
  $headers = ['From: =?UTF-8?B?' . base64_encode('Markentrix Website') . '?= <' . $c['from'] . '>', 'MIME-Version: 1.0', 'Content-Type: text/plain; charset=UTF-8', 'Content-Transfer-Encoding: 8bit', 'X-Mailer: markentrix-website'];
  deliver($c, $to, '=?UTF-8?B?' . base64_encode($subject) . '?=', implode("\n", $L) . "\n", $headers);
}

// ── Auswertung ───────────────────────────────────────────────────────────────
$cats = []; $totalW = 0.0; $sum = 0.0; $all = [];
foreach ($CATS as $key => $meta) {
  $list = $items[$key] ?? [];
  $earn = 0.0; $poss = 0.0;
  foreach ($list as $it) {
    if ($it['status'] === 'info') continue;
    $w = $W[$it['impact']] ?? 1.0;
    $poss += $w; $earn += ['ok' => 1.0, 'warn' => 0.4, 'bad' => 0.0][$it['status']] * $w;
  }
  $sc = $poss > 0 ? (int) round($earn / $poss * 100) : 0;
  // Empfehlungen (fix) werden bewusst nicht ausgegeben: Der Check stellt fest, die Beratung folgt im Gespräch.
  $pub = array_map(fn($i) => ['status' => $i['status'], 'impact' => $i['impact'], 'title' => $i['title'], 'detail' => $i['detail']], $list);
  $cats[] = ['key' => $key, 'title' => $meta['title'], 'score' => $sc, 'counts' => [
    'ok' => count(array_filter($list, fn($i) => $i['status'] === 'ok')), 'warn' => count(array_filter($list, fn($i) => $i['status'] === 'warn')), 'bad' => count(array_filter($list, fn($i) => $i['status'] === 'bad'))], 'items' => $pub];
  if ($poss > 0) { $totalW += $meta['weight']; $sum += $sc * $meta['weight']; }
  foreach ($list as $it) $all[] = $it + ['cat' => $key, 'catTitle' => $meta['title']];
}
$score = $totalW > 0 ? (int) round($sum / $totalW) : 0;
$capReason = '';
foreach ($caps as [$limit, $why]) { if ($score > $limit) { $score = $limit; $capReason = $why; } }
$counts = ['ok' => count(array_filter($all, fn($i) => $i['status'] === 'ok')), 'warn' => count(array_filter($all, fn($i) => $i['status'] === 'warn')), 'bad' => count(array_filter($all, fn($i) => $i['status'] === 'bad')), 'info' => count(array_filter($all, fn($i) => $i['status'] === 'info'))];
$grade = $score >= 85 ? 'stark' : ($score >= 70 ? 'gut' : ($score >= 50 ? 'mittel' : 'schwach'));
$samplePublic = array_map(fn($s) => ['path' => (string) (parse_url($s['url'], PHP_URL_PATH) ?: '/'), 'ok' => empty($s['bad'])], $sample);
// Bericht für die Zusendung per E-Mail: Ergebnis kurzzeitig im temporären Speicher (Zufalls-Token, ohne Personenbezug), höchstens zwei Stunden
$token = bin2hex(random_bytes(16));
$report = ['host' => $host, 'url' => $finalUrl, 'score' => $score, 'grade' => $grade, 'cap' => $capReason, 'counts' => $counts, 'checks' => count($all) - $counts['info'],
           'categories' => $cats, 'sample' => $samplePublic, 'date' => date('d.m.Y'), 'created' => time()];
foreach ((array) glob(sys_get_temp_dir() . '/mx-report-*.json') as $old) { if (@filemtime($old) < time() - 7200) @unlink($old); }
@file_put_contents(sys_get_temp_dir() . '/mx-report-' . $token . '.json', json_encode($report, JSON_UNESCAPED_UNICODE));
// Öffentliche Kurzfassung: keine Titel oder Beschreibungen zu offenen Punkten, nur Zähler und was bereits in Ordnung ist
$pubCats = array_map(function ($c) {
  $open = array_values(array_filter($c['items'], fn($i) => in_array($i['status'], ['warn', 'bad'], true)));
  $good = array_values(array_filter($c['items'], fn($i) => $i['status'] === 'ok'));
  return [
    'key' => $c['key'], 'title' => $c['title'], 'score' => $c['score'], 'counts' => $c['counts'],
    'open' => count($open), 'open_high' => count(array_filter($open, fn($i) => $i['impact'] === 'high')),
    'good' => array_map(fn($i) => $i['title'], array_slice($good, 0, 4)),
  ];
}, $cats);
$response = [
  'ok' => true, 'token' => $token, 'url' => $finalUrl, 'host' => $host, 'status' => $status, 'score' => $score, 'grade' => $grade, 'cap' => $capReason,
  'counts' => $counts, 'categories' => $pubCats, 'sample' => $samplePublic, 'checks' => count($all) - $counts['info'],
  'seconds' => round(microtime(true) - $T0, 1),
];
http_response_code(200);
echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
// Antwort zuerst ausliefern, dann die interne Benachrichtigung senden (der Besucher wartet nicht auf den Mailversand)
if (function_exists('fastcgi_finish_request')) { fastcgi_finish_request(); }
try { notify_owner($report); } catch (Throwable $e) { /* Benachrichtigung darf den Check nie stören */ }
exit;

