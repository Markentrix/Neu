<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';

// Live-Daten für statische Seiten: buchbare Tage, Feiertage, PayPal-Client-ID.
// Die HTML-Seiten enthalten einen Stand vom Build; dieser Aufruf aktualisiert ihn.
require_method('GET');
$c = cfg();
header('Cache-Control: no-store');
json_out([
    'days' => bookable_days(),
    'holidays' => array_keys(holidays((int)date('Y')) + holidays((int)date('Y') + 1)),
    'paypalClientId' => paypal_enabled() ? $c['local']['paypal']['clientId'] : null,
]);
