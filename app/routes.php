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

function general_faq(): array
{
    $c = cfg();
    $s = $c['salon'];
    return [
        ['Wie kann ich einen Termin bei AJ Atelier buchen?', "Rund um die Uhr online unter „Termin buchen“: Leistung wählen, freie Uhrzeit aussuchen, Kontaktdaten eingeben. Sie erhalten sofort eine Bestätigung per E-Mail. Telefonisch erreichen Sie uns unter {$s['phoneDisplay']}."],
        ['Kann ich mit PayPal bezahlen?', 'Ja. Leistungen mit Festpreis, etwa Haarschnitte, können Sie bei der Online-Buchung direkt mit PayPal bezahlen. Bei Leistungen mit „ab“-Preis wie Balayage zahlen Sie online nur eine Anzahlung, die vor Ort verrechnet wird. Bar oder mit Karte im Salon geht natürlich auch.'],
        ['Was kostet eine Balayage in Wettmar?', 'Balayage und Babylights beginnen bei AJ Atelier ab 250 €. Der genaue Preis richtet sich nach Haarlänge, Haardichte und Materialverbrauch. Vor dem Start erhalten Sie einen individuellen Kostenvoranschlag.'],
        ['Was kostet ein Haarschnitt?', 'Waschen, Schneiden und Föhnen für Damen kostet 55 € (kurz), 60 € (mittel) oder 70 € (lang). Der Herrenschnitt inklusive Waschen und Styling kostet 45 €, ein Maschinenschnitt 30 €.'],
        ['Wann hat AJ Atelier geöffnet?', 'Dienstag bis Freitag von 10 bis 18 Uhr und Samstag von 10 bis 14 Uhr. Sonntag, Montag und an Feiertagen in Niedersachsen ist geschlossen.'],
        ['Wo finde ich AJ Atelier?', "In der {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']} (Region Hannover). Aus Großburgwedel sind es rund 7 Minuten, aus Isernhagen rund 15 Minuten mit dem Auto."],
        ['Kann ich meinen Termin stornieren?', "Ja, bis {$c['booking']['freeCancelHours']} Stunden vor dem Termin kostenfrei über den Link in Ihrer Bestätigungs-E-Mail. Eine online geleistete Zahlung wird dabei automatisch erstattet. Kurzfristiger erreichen Sie uns telefonisch."],
        ['Kann ich mehrere Leistungen in einem Termin buchen?', 'Ja. Wählen Sie bei der Online-Buchung einfach mehrere Leistungen aus, zum Beispiel Ansatzfarbe und Haarschnitt. Die Dauer wird automatisch zusammengerechnet.'],
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
        '/impressum' => ['impressum', [], null],
        '/datenschutz' => ['datenschutz', [], null],
        '/termin-stornieren' => ['termin-stornieren', [], null],
    ];
    foreach (leistungen() as $slug => $_) $r["/leistungen/{$slug}"] = ['leistung', ['slug' => $slug], 0.8];
    foreach (orte() as $slug => $_) $r["/friseur-{$slug}"] = ['ort', ['slug' => $slug], 0.7];
    return $r;
}

/** Alte Adressen dauerhaft umleiten (Query-String bleibt erhalten). */
function redirects(): array
{
    return [
        '/index.php' => '/',
        '/impressum.php' => '/impressum',
        '/datenschutz.php' => '/datenschutz',
        '/termin-stornieren.php' => '/termin-stornieren',
        '/404.php' => '/',
    ];
}
