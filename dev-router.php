<?php
// Nur für lokale Entwicklung: php -S localhost:8000 -t public dev-router.php
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$map = ['/robots.txt' => 'robots.php', '/sitemap.xml' => 'sitemap.php', '/llms.txt' => 'llms.php'];
if (isset($map[$path])) { require __DIR__ . '/public/' . $map[$path]; return true; }
$file = __DIR__ . '/public' . $path;
if ($path !== '/' && is_file($file) && !str_ends_with($path, '/index.php')) return false;
if ($path !== '/' && is_dir($file) && is_file(rtrim($file, '/') . '/index.php')) return false;
require __DIR__ . '/public/index.php';
return true;
