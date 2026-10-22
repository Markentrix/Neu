<?php
declare(strict_types=1);

// Seitenverzeichnis: welche URL welche Vorlage lädt. Sitemap, Navigation und llms.txt lesen von hier.

function leistungen(): array
{
    static $l = null;
    return $l ??= require __DIR__ . '/content/leistungen.php';
}

function orte(): array
{
    static $o = null;
    return $o ??= require __DIR__ . '/content/orte.php';
}

function ratgeber(): array
{
    static $r = null;
    return $r ??= require __DIR__ . '/content/ratgeber.php';
}

function general_faq(): array
{
    $c = cfg();
    $s = $c['salon'];
    return [
        ['Wie kann ich einen Termin bei AJ Atelier buchen?', "Rund um die Uhr online unter „Termin buchen“: Leistung wählen, freie Uhrzeit aussuchen, Kontaktdaten eingeben. Sie erhalten eine Bestätigung mit Vorgangsnummer per E-Mail. Telefonisch erreichen Sie uns unter {$s['phoneDisplay']}."],
        ['Wie kann ich bezahlen?', 'Bezahlt wird nach dem Termin im Salon, bar oder mit Karte. Gutscheine können Sie online anfragen und per PayPal bezahlen; den Zahlungslink erhalten Sie per E-Mail.'],
        ['Was kostet eine Balayage in Wettmar?', 'Balayage und Babylights beginnen bei AJ Atelier ab 250 €. Der genaue Preis richtet sich nach Haarlänge, Haardichte und Materialverbrauch. Vor dem Start erhalten Sie einen individuellen Kostenvoranschlag.'],
        ['Was kostet ein Haarschnitt?', 'Waschen, Schneiden und Föhnen für Damen kostet 55 € (kurz), 60 € (mittel) oder 70 € (lang). Der Herrenschnitt inklusive Waschen und Styling kostet 45 €, ein Maschinenschnitt 30 €.'],
        ['Wann hat AJ Atelier geöffnet?', 'Dienstag bis Freitag von 10 bis 18 Uhr und Samstag von 10 bis 14 Uhr. Sonntag, Montag und an Feiertagen in Niedersachsen ist geschlossen.'],
        ['Wo finde ich AJ Atelier?', "In der {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']} (Region Hannover). Aus Großburgwedel sind es rund 7 Minuten, aus Isernhagen rund 15 Minuten mit dem Auto."],
        ['Kann ich meinen Termin absagen?', "Ja. In der Bestätigungs- und in der Erinnerungs-E-Mail finden Sie einen Link zum Absagen. Bitte sagen Sie spätestens 24 Stunden vorher ab, damit wir den Termin neu vergeben können. Kurzfristig erreichen Sie uns telefonisch unter {$s['phoneDisplay']}."],
        ['Kann ich mehrere Leistungen in einem Termin buchen?', 'Ja. Wählen Sie online die Hauptleistung, zum Beispiel Ansatzfarbe, und schreiben Sie weitere Wünsche wie einen Haarschnitt ins Feld „Anmerkung“. Wir planen die Zeit dann passend ein und melden uns, falls etwas nicht passt.'],
        ['Bietet AJ Atelier Extensions an?', 'Extensions kommen in Kürze ins Angebot. Folgen Sie uns auf Instagram (@ajat.elier), um den Start nicht zu verpassen.'],
    ];
}

/** Alle öffentlichen Seiten: Pfad => [Vorlage, Parameter, Sitemap-Priorität oder null] */
function routes(): array
{
    static $r = null;
    if ($r !== null) return $r;
    $r = [
        '/' => ['home', [], 1.0],
        '/leistungen' => ['leistungen', [], 0.9],
        '/preise' => ['preise', [], 0.9],
        '/termin' => ['termin', [], 0.9],
        '/ueber-uns' => ['ueber-uns', [], 0.6],
        '/kontakt' => ['kontakt', [], 0.7],
        '/faq' => ['faq', [], 0.6],
        '/gutscheine' => ['gutscheine', [], 0.8],
        '/ratgeber' => ['ratgeber', [], 0.6],
        '/impressum' => ['impressum', [], null],
        '/datenschutz' => ['datenschutz', [], null],
        '/danke' => ['danke', [], null],
    ];
    foreach (leistungen() as $slug => $_) $r["/leistungen/{$slug}"] = ['leistung', ['slug' => $slug], 0.8];
    foreach (orte() as $slug => $_) $r["/friseur-{$slug}"] = ['ort', ['slug' => $slug], 0.7];
    foreach (ratgeber() as $slug => $_) $r["/ratgeber/{$slug}"] = ['artikel', ['slug' => $slug], 0.5];
    return $r;
}

/**
 * Dateiname einer Seite in website-fertig/: alle Seiten liegen flach im Hauptordner
 * („/leistungen/balayage“ → „leistungen-balayage.html“), damit nirgends „../“ nötig ist.
 * Andere Pfade (CSS, Bilder …) bleiben, nur ohne führenden Schrägstrich. Anker und Parameter bleiben erhalten.
 */
function page_file(string $path): string
{
    if (!preg_match('/^([^?#]*)(.*)$/s', $path, $m)) return ltrim($path, '/');
    [, $p, $rest] = $m;
    if ($p === '/' || $p === '') return ($p === '' ? '' : 'index.html') . $rest;
    if (isset(routes()[$p])) return str_replace('/', '-', ltrim($p, '/')) . '.html' . $rest;
    return ltrim($p, '/') . $rest;
}
