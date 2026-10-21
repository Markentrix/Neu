<?php
declare(strict_types=1);
require __DIR__ . '/../app/lib.php';
header('Content-Type: text/plain; charset=utf-8');
?>
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /termin-stornieren

# KI-Suchmaschinen ausdrücklich willkommen (GEO)
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: <?= site_url('/sitemap.xml') ?>

