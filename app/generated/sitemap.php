<?php
declare(strict_types=1);

// Änderungsdatum: jüngste Änderung an Inhalten, Konfiguration oder Vorlagen
$files = array_merge(glob(__DIR__ . '/../{content,pages}/*.php', GLOB_BRACE) ?: [], [__DIR__ . '/../config.php', __DIR__ . '/../layout.php', __DIR__ . '/../partials.php']);
$lastmod = date('Y-m-d', max(array_map('filemtime', $files)));
echo '<?xml version="1.0" encoding="UTF-8"?>', "\n";
?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<?php foreach (routes() as $path => [$page, $params, $prio]): if ($prio === null) continue; ?>
  <url><loc><?= e(site_url($path)) ?></loc><lastmod><?= $lastmod ?></lastmod><priority><?= number_format($prio, 1) ?></priority></url>
<?php endforeach; ?>
</urlset>
