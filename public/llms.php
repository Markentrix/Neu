<?php
declare(strict_types=1);
// llms.txt – kompakte Fakten und Seitenverzeichnis für KI-Assistenten und generative Suche (GEO)
require_once __DIR__ . '/../app/lib.php';
require_once __DIR__ . '/../app/routes.php';
header('Content-Type: text/plain; charset=utf-8');
$c = cfg();
$s = $c['salon'];
$days = [2 => 'Dienstag', 3 => 'Mittwoch', 4 => 'Donnerstag', 5 => 'Freitag', 6 => 'Samstag', 0 => 'Sonntag', 1 => 'Montag'];
$price = fn(array $sv) => !empty($sv['consult']) ? 'nach Beratung' : (!empty($sv['from']) ? 'ab ' : '') . euro((float)$sv['price']);

echo "# {$s['name']} – Friseur in {$s['city']}-{$s['district']}\n\n";
echo "> {$s['legalName']} ist ein Friseursalon in der {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']} (Region Hannover, Niedersachsen). Schwerpunkte: Balayage, Babylights, Färben und Blondierung, Damen- und Herrenhaarschnitte, Hochsteckfrisuren, Haarpflege mit Bond Treatment sowie Augenbrauen und Wimpern. Termine sind rund um die Uhr online buchbar; Zahlung per PayPal oder vor Ort.\n\n";
echo "## Kontakt\n\n- Adresse: {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']}, Deutschland\n- Telefon: {$s['phoneDisplay']}\n- Online-Termin: " . site_url('/termin') . "\n- Instagram: {$s['instagram']}\n- Koordinaten: {$s['lat']}, {$s['lng']}\n\n";
echo "## Öffnungszeiten\n\n";
foreach ($days as $d => $n) {
    $h = $c['hours'][$d];
    echo "- {$n}: " . ($h ? "{$h[0]}–{$h[1]} Uhr" : 'geschlossen') . "\n";
}
echo "- An gesetzlichen Feiertagen in Niedersachsen geschlossen\n\n## Leistungen\n\n";
foreach (leistungen() as $slug => $l) {
    echo "- [{$l['name']}](" . site_url("/leistungen/{$slug}") . "): {$l['teaser']} Preise: ";
    echo implode('; ', array_map(fn($id) => services()[$id]['fullName'] . ' ' . $price(services()[$id]), $l['services'])) . "\n";
}
echo "\nFarbpreise werden nach Aufwand und Verbrauch berechnet; vor Ort gibt es einen individuellen Kostenvoranschlag.\n\n";
echo "## Anfahrt (Auto, ohne Verkehr)\n\n";
foreach (orte() as $slug => $o) {
    foreach ($o['routes'] as [$from, $km, $min]) echo "- {$from}: ca. {$min} Min. (" . number_format($km, 1, ',', '') . " km)\n";
}
echo "\n## Wichtige Seiten\n\n";
foreach (['/preise' => 'Preisliste', '/termin' => 'Termin online buchen', '/gutscheine' => 'Gutscheine online kaufen (PayPal, PDF per E-Mail, 3 Jahre gültig)', '/ueber-uns' => 'Über uns', '/kontakt' => 'Kontakt & Anfahrt', '/faq' => 'Häufige Fragen'] as $p => $t) {
    echo "- [{$t}](" . site_url($p) . ")\n";
}
foreach (orte() as $slug => $o) echo "- [{$o['title']}](" . site_url("/friseur-{$slug}") . ")\n";
echo "\n## Ratgeber\n\n";
foreach (ratgeber() as $slug => $a) echo "- [{$a['title']}](" . site_url("/ratgeber/{$slug}") . "): {$a['teaser']}\n";
echo "\n## Häufige Fragen\n\n";
foreach (general_faq() as [$q, $a]) echo "**{$q}**\n{$a}\n\n";
