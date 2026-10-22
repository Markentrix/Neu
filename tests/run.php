<?php
declare(strict_types=1);

// Testsuite – nur PHP nötig:
//   php tests/run.php
// Baut website-fertig/ in einen Temp-Ordner und prüft alles, was der Upload im Markentrix-Portal
// verlangt (Website-Vertrag „mk-api v1“, Skill „Website mit Portal“), plus Logik und SEO-Grundlagen.
// Exit-Code 0 = alles in Ordnung.

if (PHP_SAPI !== 'cli') exit(1);
$root = dirname(__DIR__);
require $root . '/app/lib.php';
require $root . '/app/routes.php';

// ---------- Mini-Testrahmen ----------
$passed = 0;
$failed = [];
function check(string $name, bool $ok, string $detail = ''): void
{
    global $passed, $failed;
    if ($ok) {
        $passed++;
        echo "  ✓ {$name}\n";
    } else {
        $failed[] = $name;
        echo "  ✗ {$name}" . ($detail !== '' ? " – {$detail}" : '') . "\n";
    }
}
function section(string $t): void { echo "\n{$t}\n"; }
function short(array $list): string { return implode(', ', array_slice($list, 0, 5)) . (count($list) > 5 ? ' …' : ''); }

// ---------- 1. Logik ----------
section('Feiertage und Adressen');
$h = holidays(2026);
check('Karfreitag 2026 = 03.04.', isset($h['2026-04-03']));
check('Pfingstmontag 2026 = 25.05.', isset($h['2026-05-25']));
check('Reformationstag (Niedersachsen)', isset($h['2026-10-31']));
check('Startseite → index.html', page_file('/') === 'index.html');
check('Unterseite liegt flach im Hauptordner', page_file('/leistungen/balayage') === 'leistungen-balayage.html');
check('Parameter und Anker bleiben erhalten', page_file('/termin?leistung=f-balayage') === 'termin.html?leistung=f-balayage' && page_file('/#termin') === 'index.html#termin');
check('Dateien behalten ihren Pfad', page_file('/css/styles.css?v=1') === 'css/styles.css?v=1');
check('Canonical ohne .html (Server leitet um)', site_url('/leistungen/balayage') === rtrim(cfg()['siteUrl'], '/') . '/leistungen-balayage');
check('Canonical der Startseite ohne index.html', site_url('/') === rtrim(cfg()['siteUrl'], '/') . '/');
check('Jede Preislisten-Leistung hat Kurzname, Preis und Dauer', !array_filter(services(), fn($s) => !preg_match('/^[a-z0-9-]+$/', $s['id']) || !isset($s['price'], $s['duration'])));

// ---------- 2. Build ----------
section('Build');
$out = sys_get_temp_dir() . '/ajtest-' . bin2hex(random_bytes(4)) . '/website-fertig';
exec('php ' . escapeshellarg("{$root}/tools/build.php") . ' --out=' . escapeshellarg($out) . ' 2>&1', $buildOut, $buildCode);
$buildText = implode("\n", $buildOut);
check('Build läuft ohne Fehler und Warnungen', $buildCode === 0 && !preg_match('/Warning|Notice|Deprecated|Fatal/i', $buildText), $buildText);
check('index.html liegt direkt im Ordner', is_file("{$out}/index.html"));
foreach (['impressum.html', 'datenschutz.html', '404.html', 'danke.html', 'sitemap.xml', 'robots.txt', 'favicon.svg'] as $f) {
    check("Pflichtdatei {$f}", is_file("{$out}/{$f}"));
}

// ---------- 3. Upload-Regeln ----------
section('Upload-Regeln des Portals');
$allowed = ['html', 'css', 'js', 'json', 'xml', 'txt', 'ico', 'png', 'jpg', 'webp', 'avif', 'gif', 'svg', 'woff', 'woff2', 'ttf', 'otf', 'webmanifest', 'pdf', 'mp4', 'webm', 'mp3'];
$files = [];
$bad = $hidden = $links = $big = [];
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($out, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::SELF_FIRST);
foreach ($it as $f) {
    $rel = substr($f->getPathname(), strlen($out) + 1);
    if ($f->isLink()) $links[] = $rel;
    if (preg_match('#(^|/)\.#', $rel)) $hidden[] = $rel;
    if ($f->isDir()) continue;
    $files[] = $rel;
    if (!in_array(strtolower(pathinfo($rel, PATHINFO_EXTENSION)), $allowed, true)) $bad[] = $rel;
    if (preg_match('/\.(png|jpe?g|webp|avif|gif)$/i', $rel) && $f->getSize() > 1.5 * 1024 * 1024) $big[] = $rel;
}
check('Nur erlaubte Dateitypen', !$bad, short($bad));
check('Keine versteckten Dateien', !$hidden, short($hidden));
check('Keine Symlinks', !$links, short($links));
check('Bilder unter 1,5 MB', !$big, short($big));
check('Gesamtgröße unter 120 MB', array_sum(array_map(fn($f) => filesize("{$out}/{$f}"), $files)) < 120 * 1024 * 1024);

$text = array_filter($files, fn($f) => preg_match('/\.(html|css|js|json|xml|txt|webmanifest|svg)$/', $f));
$hits = fn(string $re) => array_values(array_filter($text, fn($f) => preg_match($re, file_get_contents("{$out}/{$f}"))));
check('Kein localhost / 127.0.0.1', !($x = $hits('/localhost|127\.0\.0\.1/i')), short($x));
check('Kein Lorem ipsum', !($x = $hits('/lorem/i')), short($x));
check('Keine Google Fonts', !($x = $hits('/fonts\.(googleapis|gstatic)/i')), short($x));
check('Keine Fremd-CDNs', !($x = $hits('/jsdelivr|cdnjs|unpkg|cdn\./i')), short($x));
check('Keine .php-Verweise', !($x = $hits('/\.php\b/i')), short($x));
check('Kein http:// in Links, Skripten und Formularen', !($x = $hits('/(?:src|href|action)\s*=\s*["\']http:\/\//i')), short($x));
check('Kein „../“ in Pfaden', !($x = $hits('/(?:src|href|action)\s*=\s*["\'][^"\']*\.\.\/|url\(\s*["\']?\.\.\//i')), short($x));
check('Keine Einbettungen von YouTube, Google Maps oder Facebook', !($x = $hits('/<iframe|youtube\.com\/embed|maps\.google\.[a-z]+\/maps\?.*output=embed|facebook\.com\/plugins/i')), short($x));
check('Kein eigenes PayPal-Skript', !($x = $hits('/paypal\.com\/sdk/i')), short($x));
check('Markentrix-Skript nicht selbst eingebunden', !($x = $hits('/data-site=|static\/js\/site\.js/i')), short($x));
$fonts = glob("{$out}/css/fonts/*.woff2");
check('Schriften lokal als woff2', count($fonts) >= 2);

// ---------- 4. Jede Seite ----------
section('Seiten');
$pages = array_values(array_filter($files, fn($f) => str_ends_with($f, '.html')));
$dom = function (string $file): DOMDocument {
    $d = new DOMDocument();
    libxml_use_internal_errors(true);
    $d->loadHTML('<?xml encoding="utf-8"?>' . file_get_contents($file));
    libxml_clear_errors();
    return $d;
};
$problems = [];
$broken = [];
foreach ($pages as $p) {
    $d = $dom("{$out}/{$p}");
    $x = new DOMXPath($d);
    $title = trim((string)$x->evaluate('string(//title)'));
    $why = [];
    if ($x->evaluate('string(//html/@lang)') !== 'de') $why[] = 'lang';
    if ($title === '' || mb_strlen($title) >= 60) $why[] = "title ({$title})";
    if (trim((string)$x->evaluate('string(//meta[@name="description"]/@content)')) === '') $why[] = 'description';
    if (!str_contains((string)$x->evaluate('string(//meta[@name="viewport"]/@content)'), 'width=device-width')) $why[] = 'viewport';
    if ($x->query('//h1')->length !== 1) $why[] = 'h1 × ' . $x->query('//h1')->length;
    if ($x->query('//img[not(@alt)]')->length) $why[] = 'img ohne alt';
    if ($x->query('//img[not(@width) or not(@height)]')->length) $why[] = 'img ohne width/height';
    if (!$x->query('//footer//a[contains(@href,"impressum")]')->length || !$x->query('//footer//a[contains(@href,"datenschutz")]')->length) $why[] = 'Footer-Rechtslinks';
    if ($x->query('//link[@rel="icon"]')->length === 0) $why[] = 'favicon';
    if ($why) $problems[] = "{$p}: " . implode(', ', $why);

    // Interne Verweise auflösen wie die Prüfung im Portal (/pfad → pfad.html → pfad/index.html)
    foreach ($x->query('//*[@href or @src]') as $el) {
        $ref = trim($el->getAttribute('href') ?: $el->getAttribute('src'));
        if ($ref === '' || preg_match('#^(\#|mailto:|tel:|javascript:|data:|https?://|//)#i', $ref)) continue;
        $path = rawurldecode((string)parse_url($ref, PHP_URL_PATH));
        if ($path === '') continue;
        $target = str_starts_with($path, '/') ? $out . $path : $out . '/' . $path;
        if (!is_file($target) && !is_file("{$target}.html") && !is_file(rtrim($target, '/') . '/index.html')) $broken[] = "{$p} → {$ref}";
    }
}
check('Alle ' . count($pages) . ' Seiten: lang, title < 60, description, viewport, genau eine h1, Bilder mit alt, Footer-Links, Favicon', !$problems, short($problems));
check('Keine toten internen Links', !$broken, short(array_unique($broken)));
$index = file_get_contents("{$out}/index.html");
check('Startseite hat tel:- oder mailto:-Link', (bool)preg_match('/href="(tel|mailto):/', $index));
check('Statistik-Einstellungen im Footer (data-mk="cookies")', !array_filter($pages, fn($p) => !str_contains(file_get_contents("{$out}/{$p}"), 'data-mk="cookies"')));
check('Google-Bewertungen als Baustein auf der Startseite', str_contains($index, 'data-mk="bewertungen"'));
check('404-Seite nutzt Pfade ab der Wurzel', (bool)preg_match('#href="/css/styles\.css#', file_get_contents("{$out}/404.html")));
check('danke.html und 404.html nicht in der Sitemap', !preg_match('#/(danke|404)<#', file_get_contents("{$out}/sitemap.xml")));
$sitemap = file_get_contents("{$out}/sitemap.xml");
check('Sitemap nennt alle Seiten mit sauberer Adresse', substr_count($sitemap, '<loc>') === count(array_filter(routes(), fn($r) => $r[2] !== null)) && !str_contains($sitemap, '.html<'));
check('robots.txt verweist auf die Sitemap', str_contains(file_get_contents("{$out}/robots.txt"), 'Sitemap: ' . site_url('/sitemap.xml')));
check('Strukturierte Daten (HairSalon) sind gültiges JSON', (function () use ($index) {
    preg_match_all('#<script type="application/ld\+json">(.*?)</script>#s', $index, $m);
    $types = array_map(fn($j) => json_decode($j, true)['@type'] ?? null, $m[1]);
    return in_array('HairSalon', $types, true) && !in_array(null, $types, true);
})());

// ---------- 5. Formulare ----------
section('Formulare');
$forms = [
    'termin.html' => '[data-customer-form]',
    'index.html' => '[data-customer-form]',
    'kontakt.html' => '[data-anfrage="kontakt"]',
    'gutscheine.html' => '[data-anfrage="gutschein"]',
];
foreach ($forms as $page => $sel) {
    $d = $dom("{$out}/{$page}");
    $x = new DOMXPath($d);
    $attr = preg_match('/\[([\w-]+)(?:="([\w-]+)")?\]/', $sel, $m) ? $m : [];
    $q = isset($attr[2]) ? "//form[@{$attr[1]}='{$attr[2]}']" : "//form[@{$attr[1]}]";
    $form = $x->query($q)->item(0);
    $ok = $form !== null;
    $why = [];
    if ($ok) {
        $consent = $x->query('.//input[@type="checkbox"][@name="einwilligung"][@required]', $form)->item(0);
        if (!$consent) $why[] = 'Einwilligung';
        elseif (!$x->query('ancestor::label//a[contains(@href,"datenschutz")]', $consent)->length) $why[] = 'Link zur Datenschutzerklärung';
        $hp = $x->query('.//input[@name="website"]', $form)->item(0);
        if (!$hp || $hp->getAttribute('tabindex') !== '-1' || $hp->getAttribute('autocomplete') !== 'off') $why[] = 'Lockfeld';
        if (!$x->query('.//input[@name="name"][@required]', $form)->length) $why[] = 'Name Pflicht';
        if (!$x->query('.//input[@name="email"][@type="email"][@required]', $form)->length) $why[] = 'E-Mail Pflicht';
        if (!$x->query('.//*[@data-form-error]', $form)->length) $why[] = 'Fehlertext';
        if ($sel === '[data-customer-form]' && !$x->query('.//input[@name="telefon"][@required]', $form)->length) $why[] = 'Telefon Pflicht';
    }
    // Ausweichmöglichkeit (Telefon) für den Fall, dass das Portal nicht erreichbar ist
    if (!$x->query('//*[@data-fallback]//a[starts-with(@href,"tel:")]')->length) $why[] = 'Ausweichmöglichkeit';
    check("{$page}: Pflichtfelder, Einwilligung, Lockfeld, Fehlertext, Ausweichmöglichkeit", $ok && !$why, $ok ? implode(', ', $why) : 'Formular fehlt');
}
$css = file_get_contents("{$out}/css/styles.css");
check('Lockfeld ist unsichtbar (display:none)', (bool)preg_match('/\.hp\s*\{[^}]*display:\s*none/', $css));
$js = file_get_contents("{$out}/js/main.js") . file_get_contents("{$out}/js/formulare.js");
check('Anfragen gehen an /api/anfrage', str_contains($js, '"/api/anfrage"'));
check('Danach Weiterleitung auf danke.html mit typ und ref', str_contains($js, 'danke.html?typ='));
check('Buchung nutzt /api/leistungen, /api/mitarbeiter, /api/verfuegbarkeit, /api/slots', str_contains($js, '/api/leistungen') && str_contains($js, '/api/mitarbeiter') && str_contains($js, '/api/verfuegbarkeit') && str_contains($js, '/api/slots'));
check('Nur freie Uhrzeiten (frei:true) werden angeboten', str_contains($js, 's.frei'));
check('Terminwunsch, wenn das Portal keine Selbstbuchung erlaubt', str_contains($js, 'selfBooking') && str_contains($js, 'Terminwunsch senden'));
check('429 wird als „später noch einmal“ gemeldet', str_contains($js, 'status === 429') && str_contains($js, 'noch einmal'));
check('Doppelklick-Sperre beim Senden', substr_count($js, 'if (sending) return') + substr_count($js, 'if (state.sending) return') >= 2);

// ---------- Ergebnis ----------
exec('rm -rf ' . escapeshellarg(dirname($out)));
echo "\n" . ($failed ? '✗ ' . count($failed) . " fehlgeschlagen, {$passed} bestanden\n" : "✓ Alle {$passed} Tests bestanden\n");
exit($failed ? 1 : 0);
