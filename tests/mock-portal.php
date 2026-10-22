<?php
declare(strict_types=1);

// Nachbau der Portal-Schnittstelle (mk-api v1) für die lokale Vorschau und Browser-Tests.
//   php tools/build.php && php -S 127.0.0.1:8080 tests/mock-portal.php
// Liefert website-fertig/ aus und beantwortet /api/* mit Beispieldaten. Nur zum Testen, nie hochladen.
// MOCK_MODE=wunsch → selfBooking:false, MOCK_MODE=ohne-leistungen → leere Leistungsliste, MOCK_MODE=aus → /api antwortet 502.

$root = dirname(__DIR__) . '/website-fertig';
$path = rawurldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?: '/');
$mode = getenv('MOCK_MODE') ?: '';
$state = sys_get_temp_dir() . '/aj-mock-portal.json';

$json = function (array $data, int $status = 200): never {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
};

if (str_starts_with($path, '/api/')) {
    if ($mode === 'aus') { http_response_code(502); exit; }
    $booked = is_file($state) ? json_decode((string)file_get_contents($state), true) : [];
    $day = fn(int $i) => date('Y-m-d', strtotime("+{$i} day"));
    $times = ['10:00', '10:30', '11:00', '11:30', '13:00', '14:00', '15:30', '16:30'];
    switch ($path) {
        case '/api/leistungen':
            $json(['leistungen' => $mode === 'ohne-leistungen' ? [] : [
                ['key' => 'd-wsf-mittel', 'name' => 'Waschen, Schneiden & Föhnen – mittel', 'beschreibung' => '', 'preis' => 60, 'dauer' => 60],
                ['key' => 'h-schnitt', 'name' => 'Herrenschnitt inkl. Waschen & Styling', 'beschreibung' => '', 'preis' => 45, 'dauer' => 40],
                ['key' => 'f-balayage', 'name' => 'Balayage', 'beschreibung' => 'inkl. Beratung', 'preis' => 'ab 250 €', 'dauer' => 210],
            ]]);
        case '/api/mitarbeiter':
            $json(['mitarbeiter' => [
                ['key' => 'aj', 'name' => 'Aylin', 'leistungen' => []],
                ['key' => 'jo', 'name' => 'Jana', 'leistungen' => ['d-wsf-mittel', 'f-balayage']],
            ]]);
        case '/api/verfuegbarkeit':
            $json(['blocked' => [$day(3)], 'closedWeekdays' => [0, 1], 'nextFree' => null, 'selfBooking' => $mode !== 'wunsch', 'slotTimes' => $times]);
        case '/api/slots':
            $tag = (string)($_GET['tag'] ?? '');
            $json(['tag' => $tag, 'slots' => array_map(fn($t) => ['zeit' => $t, 'frei' => !in_array("{$tag} {$t}", $booked, true) && $t !== '11:00'], $times)]);
        case '/api/anfrage':
            $in = json_decode((string)file_get_contents('php://input'), true) ?: [];
            if (($in['website'] ?? '') !== '') $json(['ok' => true, 'ref' => 'X000000-SPAM']);
            $err = [];
            if (mb_strlen(trim((string)($in['name'] ?? ''))) < 2) $err['name'] = 'Bitte Namen angeben.';
            if (($in['einwilligung'] ?? '') !== 'ja') $err['einwilligung'] = 'Bitte zustimmen.';
            if (($in['typ'] ?? '') === 'termin') {
                if (!filter_var($in['email'] ?? '', FILTER_VALIDATE_EMAIL)) $err['email'] = 'Bitte eine gültige E-Mail-Adresse angeben.';
                $slot = ($in['datum'] ?? '') . ' ' . ($in['uhrzeit'] ?? '');
                // Name „Konflikt“ simuliert eine gleichzeitige Buchung derselben Zeit
                if (in_array($slot, $booked, true) || ($in['name'] ?? '') === 'Konflikt Test') $err['uhrzeit'] = 'Diese Uhrzeit ist gerade vergeben worden.';
                if (!$err) { $booked[] = $slot; file_put_contents($state, json_encode($booked)); }
            }
            if ($err) $json(['ok' => false, 'errors' => $err], 422);
            file_put_contents(sys_get_temp_dir() . '/aj-mock-last.json', json_encode($in, JSON_UNESCAPED_UNICODE));
            $json(['ok' => true, 'ref' => strtoupper(substr((string)$in['typ'], 0, 1)) . date('ymd') . '-AB12', 'status' => 'neu']);
        default:
            $json(['ok' => false], 404);
    }
}

// Statische Dateien wie Caddy: /seite → seite.html
$file = $root . ($path === '/' ? '/index.html' : $path);
if (!is_file($file) && is_file("{$file}.html")) $file = "{$file}.html";
if (!is_file($file) || !str_starts_with(realpath($file), realpath($root))) {
    http_response_code(404);
    $file = "{$root}/404.html";
}
$types = ['html' => 'text/html; charset=utf-8', 'css' => 'text/css', 'js' => 'text/javascript', 'svg' => 'image/svg+xml', 'png' => 'image/png', 'woff2' => 'font/woff2', 'xml' => 'application/xml', 'txt' => 'text/plain; charset=utf-8', 'webmanifest' => 'application/manifest+json'];
header('Content-Type: ' . ($types[pathinfo($file, PATHINFO_EXTENSION)] ?? 'application/octet-stream'));
readfile($file);
