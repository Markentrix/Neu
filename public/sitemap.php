<?php
declare(strict_types=1);
require __DIR__ . '/../app/lib.php';
header('Content-Type: application/xml; charset=utf-8');
$lastmod = date('Y-m-d', max(filemtime(__DIR__ . '/index.php'), filemtime(__DIR__ . '/../app/config.php')));
$pages = ['/' => '1.0', '/impressum.php' => '0.2', '/datenschutz.php' => '0.2'];
echo '<?xml version="1.0" encoding="UTF-8"?>', "\n";
?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<?php foreach ($pages as $path => $prio): ?>
  <url><loc><?= e(site_url($path)) ?></loc><lastmod><?= $lastmod ?></lastmod><priority><?= $prio ?></priority></url>
<?php endforeach; ?>
</urlset>
