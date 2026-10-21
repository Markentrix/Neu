<?php
declare(strict_types=1);

// Erzeugt den Ordner dist/ mit fertigen HTML-Seiten – wie bei den anderen Kundenseiten.
//
//   php tools/build-static.php --url=https://www.aj-atelier-wettmar.de
//
// dist/ wird danach wie gewohnt nach /srv/sites/kunden/<Kundennummer> hochgeladen.
// Buchung, Gutscheine, Admin und Storno laufen weiter über den Container „aj-atelier“
// (Caddy leitet /api/*, /admin/*, /gutschein-pdf und /termin-stornieren dorthin).
// Texte bitte in app/ ändern und neu bauen, nicht in dist/ – sonst gehen Änderungen beim nächsten Build verloren.

if (PHP_SAPI !== 'cli') exit(1);
$opts = getopt('', ['url:']);
if (!empty($opts['url'])) putenv('SITE_URL=' . $opts['url']);

$root = dirname(__DIR__);
require_once $root . '/app/lib.php';
require_once $root . '/app/layout.php';
require_once $root . '/app/partials.php';
require_once $root . '/app/routes.php';

$out = $root . '/dist';
$dynamic = ['gutschein-pdf', 'termin-stornieren']; // nur im Container

// dist/ leeren (nur genau diesen Ordner)
if (is_dir($out)) {
    $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($out, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
    foreach ($it as $f) $f->isDir() ? rmdir($f->getPathname()) : unlink($f->getPathname());
}
@mkdir($out, 0755, true);

function render_page(string $page, array $params): string
{
    $GLOBALS['booking_data_done'] = false;
    ob_start();
    (function () use ($page, $params) {
        include dirname(__DIR__) . "/app/pages/{$page}.php";
    })();
    return ob_get_clean();
}

function write_file(string $path, string $content): void
{
    @mkdir(dirname($path), 0755, true);
    file_put_contents($path, $content);
}

$count = 0;
foreach (routes() as $path => [$page, $params]) {
    if (in_array($page, $dynamic, true)) continue;
    $file = $path === '/' ? '/index.html' : $path . '.html';
    write_file($out . $file, render_page($page, $params));
    $count++;
}
write_file($out . '/404.html', render_page('404', []));

foreach (['robots.php' => 'robots.txt', 'sitemap.php' => 'sitemap.xml', 'llms.php' => 'llms.txt'] as $src => $dst) {
    ob_start();
    include $root . '/public/' . $src;
    write_file("{$out}/{$dst}", ob_get_clean());
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
foreach (['css', 'js', 'fonts', 'img', 'favicon.svg', 'site.webmanifest'] as $item) $copy("{$root}/public/{$item}", "{$out}/{$item}");

echo "dist/ gebaut: {$count} Seiten + 404, Domain " . site_url('/') . "\n";
