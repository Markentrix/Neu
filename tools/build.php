<?php
declare(strict_types=1);

// Baut den Ordner website-fertig/ für den Upload ins Markentrix-Portal.
//
//   php tools/build.php [--url=https://www.aj-atelier-wettmar.de]
//
// website-fertig/ enthält nur fertige Dateien (HTML, CSS, JS, Schriften, Bilder) und wird als ZIP
// im Portal hochgeladen. Texte und Preise bitte in app/ ändern und neu bauen, nicht in website-fertig/,
// sonst gehen Änderungen beim nächsten Build verloren.

if (PHP_SAPI !== 'cli') exit(1);
$opts = getopt('', ['url:', 'out:']);
if (!empty($opts['url'])) putenv('SITE_URL=' . $opts['url']);

$root = dirname(__DIR__);
require_once $root . '/app/lib.php';
require_once $root . '/app/layout.php';
require_once $root . '/app/partials.php';
require_once $root . '/app/routes.php';

$out = rtrim($opts['out'] ?? $root . '/website-fertig', '/');
// Sicherheitsnetz, weil der Zielordner vorher geleert wird: nur „…/website-fertig“ oder ein Ordner im Temp-Verzeichnis
if (basename($out) !== 'website-fertig' && !str_starts_with($out, rtrim(sys_get_temp_dir(), '/') . '/')) {
    fwrite(STDERR, "Zielordner muss „website-fertig“ heißen oder im Temp-Verzeichnis liegen: {$out}\n");
    exit(1);
}

if (is_dir($out)) {
    $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($out, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
    foreach ($it as $f) $f->isDir() ? rmdir($f->getPathname()) : unlink($f->getPathname());
}
@mkdir($out, 0755, true);

function render(string $file, array $params = []): string
{
    $GLOBALS['hours_data_done'] = false;
    ob_start();
    (function () use ($file, $params) {
        include $file;
    })();
    return ob_get_clean();
}

/**
 * Interne Verweise („/leistungen/balayage“, „/css/styles.css“) auf die Dateien in website-fertig/ umstellen.
 * Alle Seiten liegen im Hauptordner, daher reichen relative Pfade ohne „../“ – das funktioniert auf der Domain,
 * auf der Vorschau-Adresse und per Doppelklick vom PC. Die 404-Seite wird für beliebige Pfade ausgeliefert
 * und bekommt deshalb Pfade ab der Wurzel („/css/styles.css“).
 */
function link_files(string $html, bool $fromRoot = false): string
{
    return preg_replace_callback('/\b(href|src)="\/(?!\/)([^"]*)"/', function ($m) use ($fromRoot) {
        $target = page_file('/' . html_entity_decode($m[2]));
        return $m[1] . '="' . ($fromRoot ? '/' : '') . htmlspecialchars($target, ENT_QUOTES) . '"';
    }, $html);
}

$count = 0;
foreach (routes() as $path => [$page, $params]) {
    file_put_contents($out . '/' . page_file($path), link_files(render("{$root}/app/pages/{$page}.php", $params)));
    $count++;
}
file_put_contents($out . '/404.html', link_files(render("{$root}/app/pages/404.php"), true));

foreach (['robots' => 'robots.txt', 'sitemap' => 'sitemap.xml', 'llms' => 'llms.txt'] as $src => $dst) {
    file_put_contents("{$out}/{$dst}", render("{$root}/app/generated/{$src}.php"));
}

// Dateien, die 1:1 übernommen werden
$copy = function (string $from, string $to) use (&$copy) {
    if (is_dir($from)) {
        foreach (scandir($from) as $f) if ($f[0] !== '.') $copy("{$from}/{$f}", "{$to}/{$f}");
    } else {
        @mkdir(dirname($to), 0755, true);
        copy($from, $to);
    }
};
foreach (scandir("{$root}/assets") as $item) if ($item[0] !== '.') $copy("{$root}/assets/{$item}", "{$out}/{$item}");

echo "website-fertig/ gebaut: {$count} Seiten + 404, Domain " . site_url('/') . "\n";
