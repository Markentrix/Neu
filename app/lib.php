<?php
declare(strict_types=1);

// Hilfsfunktionen für den Seitengenerator (tools/build.php). Läuft nur beim Bauen, nie auf dem Server.

function cfg(): array
{
    static $cfg = null;
    if ($cfg === null) {
        $cfg = require __DIR__ . '/config.php';
        // Die Domain kann beim Bauen vorgegeben werden: php tools/build.php --url=https://…
        if (getenv('SITE_URL')) $cfg['siteUrl'] = rtrim((string)getenv('SITE_URL'), '/');
        date_default_timezone_set($cfg['timezone']);
    }
    return $cfg;
}

function e(?string $s): string
{
    return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Absolute Adresse für Canonical, Sitemap und strukturierte Daten („/leistungen/balayage“ → „https://…/leistungen-balayage“). */
function site_url(string $path = '/'): string
{
    // Der Server leitet „/seite.html“ auf „/seite“ und „/index.html“ auf „/“ um (Caddy-Snippet kunden_site),
    // deshalb nennen Canonical und Sitemap gleich die endgültige Adresse.
    $file = preg_replace(['/^index\.html/', '/\.html(?=$|[?#])/'], '', page_file($path));
    return rtrim(cfg()['siteUrl'], '/') . '/' . $file;
}

function euro(float $n, bool $decimals = false): string
{
    return number_format($n, $decimals || fmod($n, 1.0) !== 0.0 ? 2 : 0, ',', '.') . ' €';
}

// ---------- Leistungen (Preisliste der Website; buchbar sind die im Portal gepflegten Leistungen) ----------

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

// ---------- Feiertage (für „Jetzt geöffnet“) ----------

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

/** Kurzer Inhalts-Hash für „?v=…“: Browser laden CSS/JS nach einer Änderung neu, sonst aus dem Cache. */
function asset_version(string $file): string
{
    return substr(md5_file(__DIR__ . '/../assets/' . $file), 0, 8);
}
