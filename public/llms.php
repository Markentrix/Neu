<?php
declare(strict_types=1);
// llms.txt – kompakte Fakten für KI-Assistenten und generative Suche (GEO)
require __DIR__ . '/../app/lib.php';
header('Content-Type: text/plain; charset=utf-8');
$c = cfg();
$s = $c['salon'];
$days = [2 => 'Dienstag', 3 => 'Mittwoch', 4 => 'Donnerstag', 5 => 'Freitag', 6 => 'Samstag', 0 => 'Sonntag', 1 => 'Montag'];
echo "# {$s['name']} – Friseur in {$s['city']}-{$s['district']}\n\n";
echo "> {$s['legalName']} ist ein Friseursalon in der {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']} (Region Hannover, Niedersachsen). Spezialisiert auf Balayage, Babylights, Färben, Damen- und Herrenschnitte, Styling, Haarpflege sowie Augenbrauen und Wimpern. Termine sind rund um die Uhr online buchbar; Zahlung per PayPal oder vor Ort.\n\n";
echo "## Kontakt\n\n- Adresse: {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']}, Deutschland\n- Telefon: {$s['phoneDisplay']}\n- Online-Termin: " . site_url('/#termin') . "\n- Instagram: {$s['instagram']}\n- Koordinaten: {$s['lat']}, {$s['lng']}\n- Einzugsgebiet: " . implode(', ', $s['areaServed']) . "\n\n";
echo "## Öffnungszeiten\n\n";
foreach ($days as $d => $n) {
    $h = $c['hours'][$d];
    echo "- {$n}: " . ($h ? "{$h[0]}–{$h[1]} Uhr" : 'geschlossen') . "\n";
}
echo "- An gesetzlichen Feiertagen in Niedersachsen geschlossen\n\n## Preise (Euro, inkl. MwSt.)\n";
foreach ($c['categories'] as $cat) {
    echo "\n### {$cat['title']} – {$cat['subtitle']}\n\n";
    foreach ($cat['services'] as $sv) {
        $name = isset($sv['group']) ? "{$sv['group']} ({$sv['name']})" : $sv['name'];
        $price = !empty($sv['consult']) ? 'nach Beratung' : (!empty($sv['from']) ? 'ab ' : '') . euro((float)$sv['price']);
        echo "- {$name}: {$price}\n";
    }
    if (!empty($cat['note'])) echo "\n{$cat['note']}\n";
}
echo "\n## Gut zu wissen\n\n- Online-Buchung mit sofortiger E-Mail-Bestätigung\n- Bezahlung: PayPal (online), bar oder Karte vor Ort\n- Bei „ab“-Preisen wird online nur eine Anzahlung fällig, die vor Ort verrechnet wird\n- Kostenfreie Stornierung bis {$c['booking']['freeCancelHours']} Stunden vor dem Termin\n- Extensions: demnächst im Angebot\n";
