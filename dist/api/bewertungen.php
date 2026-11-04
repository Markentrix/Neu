<?php
/**
 * Aktuelle Google-Bewertungen für markentrix.de (nur lesend, nur GET).
 *
 * Der Server fragt die Google Places API (New) ab und gibt Gesamtwertung, Anzahl und die von Google gelieferten
 * Bewertungen als JSON zurück. Der Browser der Besucher spricht nie mit Google, es werden keine Besucherdaten
 * an Google übertragen und es ist keine Einwilligung nötig.
 *
 * Einrichtung (Umgebungsvariablen im php-Container, siehe docs/server/BEWERTUNGEN.md):
 *   MX_GOOGLE_API_KEY   API-Schlüssel, beschränkt auf „Places API (New)“ und die Server-IP
 *   MX_GOOGLE_PLACE_ID  Place-ID des Unternehmensprofils
 *   MX_GOOGLE_CACHE_TTL optional, Sekunden, Standard 3600 (Mindestwert 300)
 *   MX_GOOGLE_BASE      optional, nur für Tests (Standard https://places.googleapis.com)
 *
 * Ohne Schlüssel oder Place-ID antwortet der Endpunkt mit {"ok":false} und die Website zeigt keinen Abschnitt.
 * Es werden nur die von Google gelieferten Bewertungen weitergegeben, ungefiltert und unverändert (keine Auswahl
 * nach Sternen). Bei einem Fehler von Google wird höchstens 24 Stunden alter Zwischenspeicher ausgeliefert.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex');
header('Cache-Control: public, max-age=600');

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    http_response_code(405);
    echo '{"ok":false}';
    exit;
}

$key = getenv('MX_GOOGLE_API_KEY') ?: '';
$place = getenv('MX_GOOGLE_PLACE_ID') ?: '';
if ($key === '' || !preg_match('/^[A-Za-z0-9_\-]{10,200}$/', $place)) {
    echo '{"ok":false}';
    exit;
}
$ttl = max(300, (int) (getenv('MX_GOOGLE_CACHE_TTL') ?: 3600));
$base = rtrim(getenv('MX_GOOGLE_BASE') ?: 'https://places.googleapis.com', '/');
$cache = sys_get_temp_dir() . '/mx-bewertungen-' . hash('sha256', $place) . '.json';

function out_cached(string $file, int $maxAge): bool
{
    if (!is_file($file) || filemtime($file) < time() - $maxAge) {
        return false;
    }
    $raw = @file_get_contents($file);
    if ($raw === false || $raw === '') {
        return false;
    }
    echo $raw;
    return true;
}

if (out_cached($cache, $ttl)) {
    exit;
}

// Nur ein Abruf gleichzeitig, damit parallele Besucher nicht mehrere Google-Anfragen auslösen.
$lock = @fopen($cache . '.lock', 'c');
if ($lock) {
    @flock($lock, LOCK_EX);
    if (out_cached($cache, $ttl)) {
        exit;
    }
}

$url = $base . '/v1/places/' . rawurlencode($place) . '?languageCode=de';
$ctx = stream_context_create(['http' => [
    'method' => 'GET',
    'timeout' => 6,
    'ignore_errors' => true,
    'header' => "X-Goog-Api-Key: $key\r\nX-Goog-FieldMask: rating,userRatingCount,googleMapsUri,reviews\r\nAccept: application/json\r\n",
]]);
$body = @file_get_contents($url, false, $ctx);
$status = 0;
foreach ((array) ($http_response_header ?? []) as $h) {
    if (preg_match('#^HTTP/\S+\s+(\d{3})#', $h, $m)) {
        $status = (int) $m[1];
    }
}
$j = $body !== false ? json_decode($body, true) : null;

if ($status !== 200 || !is_array($j) || !isset($j['rating'])) {
    // Fehler bei Google: alten Stand bis 24 Stunden weiter ausliefern, sonst nichts anzeigen.
    if (!out_cached($cache, 86400)) {
        echo '{"ok":false}';
    }
    exit;
}

$reviews = [];
foreach ((array) ($j['reviews'] ?? []) as $r) {
    $text = trim((string) ($r['originalText']['text'] ?? $r['text']['text'] ?? ''));
    $stars = (int) ($r['rating'] ?? 0);
    if ($stars < 1 || $stars > 5) {
        continue;
    }
    $reviews[] = [
        'name' => mb_substr(trim((string) ($r['authorAttribution']['displayName'] ?? '')), 0, 80),
        'sterne' => $stars,
        'text' => mb_substr($text, 0, 900),
        'zeit' => mb_substr((string) ($r['relativePublishTimeDescription'] ?? ''), 0, 60),
        'datum' => substr((string) ($r['publishTime'] ?? ''), 0, 10),
    ];
}

$res = json_encode([
    'ok' => true,
    'gesamt' => round((float) $j['rating'], 1),
    'anzahl' => (int) ($j['userRatingCount'] ?? 0),
    'profil' => preg_match('#^https://(www\.)?google\.[a-z.]+/#', (string) ($j['googleMapsUri'] ?? '')) ? $j['googleMapsUri'] : '',
    'bewertungen' => $reviews,
    'abgerufen' => gmdate('c'),
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

if ($res !== false) {
    @file_put_contents($cache . '.tmp', $res);
    @rename($cache . '.tmp', $cache);
    echo $res;
} else {
    echo '{"ok":false}';
}
