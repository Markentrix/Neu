<?php
// Nur für lokale Entwicklung: php -S localhost:8000 -t public dev-router.php
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$map = ['/robots.txt' => 'robots.php', '/sitemap.xml' => 'sitemap.php', '/llms.txt' => 'llms.php'];
if (isset($map[$path])) { require __DIR__ . '/public/' . $map[$path]; return true; }
$file = __DIR__ . '/public' . $path;
if ($path !== '/' && !file_exists($file)) { require __DIR__ . '/public/404.php'; return true; }
return false;
