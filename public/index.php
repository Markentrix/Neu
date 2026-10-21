<?php
declare(strict_types=1);
// Front-Controller: ordnet saubere URLs (/preise, /leistungen/balayage …) den Vorlagen in app/pages zu.
require __DIR__ . '/../app/lib.php';
require __DIR__ . '/../app/layout.php';
require __DIR__ . '/../app/partials.php';
require __DIR__ . '/../app/routes.php';

$path = rawurldecode(parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/');
$query = $_SERVER['QUERY_STRING'] ?? '';
$redirect = function (string $to) use ($query): never {
    header('Location: ' . $to . ($query !== '' ? "?{$query}" : ''), true, 301);
    exit;
};

if (isset(redirects()[$path])) $redirect(redirects()[$path]);
if ($path !== '/' && str_ends_with($path, '/')) $redirect(rtrim($path, '/'));
if (preg_match('#[A-Z]#', $path) && isset(routes()[strtolower($path)])) $redirect(strtolower($path));

$route = routes()[$path] ?? null;
$params = $route[1] ?? [];
require __DIR__ . '/../app/pages/' . ($route[0] ?? '404') . '.php';
