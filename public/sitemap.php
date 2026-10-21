<?php
declare(strict_types=1);
require_once __DIR__ . '/../app/lib.php';
require_once __DIR__ . '/../app/routes.php';
header('Content-Type: application/xml; charset=utf-8');

// Änderungsdatum: jüngste Änderung an Inhalten, Konfiguration oder Vorlagen
$files = array_merge(glob(__DIR__ . '/../app/{content,pages}/*.php', GLOB_BRACE) ?: [], [__DIR__ . '/../app/config.php', __DIR__ . '/../app/layout.php', __DIR__ . '/../app/partials.php']);
$lastmod = date('Y-m-d', max(array_map('filemtime', $files)));
echo '<?xml version="1.0" encoding="UTF-8"?>', "\n";
?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<?php foreach (routes() as $path => [$page, $params, $prio]): if ($prio === null) continue; ?>
  <url><loc><?= e(site_url($path)) ?></loc><lastmod><?= $lastmod ?></lastmod><priority><?= number_format($prio, 1) ?></priority></url>
<?php endforeach; ?>
</urlset>
