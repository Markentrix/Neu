<?php
// Zentrale Salon-Konfiguration: Preise, Dauer, Öffnungszeiten, Anzahlungen.
// Website, Preisliste, SEO-Daten und Buchungssystem lesen alle aus dieser Datei.

return [
    'salon' => [
        'name'        => 'AJ Atelier',
        'legalName'   => 'AJ Atelier – Hair & Beauty',
        'phone'       => '+4951399856600',
        'phoneDisplay'=> '05139 9856600',
        'street'      => 'Hauptstraße 64',
        'zip'         => '30938',
        'city'        => 'Burgwedel',
        'district'    => 'Wettmar',
        'region'      => 'Niedersachsen',
        'lat'         => 52.5126788,
        'lng'         => 9.9151511,
        'instagram'   => 'https://www.instagram.com/ajat.elier/',
        'priceRange'  => '€€',
        'areaServed'  => ['Wettmar', 'Burgwedel', 'Großburgwedel', 'Kleinburgwedel', 'Thönse', 'Engensen', 'Fuhrberg', 'Isernhagen', 'Hannover'],
    ],

    'booking' => [
        'timezone'      => 'Europe/Berlin',
        'capacity'      => 1,    // gleichzeitig bedienbare Kund:innen
        'slotStep'      => 15,   // Raster der Startzeiten (Minuten)
        'leadTime'      => 120,  // Mindestvorlauf (Minuten)
        'horizonDays'   => 60,   // so weit im Voraus buchbar
        'freeCancelHours' => 24, // kostenfreie Online-Stornierung bis X Std. vorher
        'maxServices'   => 5,
    ],

    // 0 = Sonntag … 6 = Samstag; [Öffnung, Schluss] als "HH:MM", null = geschlossen
    'hours' => [
        0 => null,
        1 => null,
        2 => ['10:00', '18:00'],
        3 => ['10:00', '18:00'],
        4 => ['10:00', '18:00'],
        5 => ['10:00', '18:00'],
        6 => ['10:00', '14:00'],
    ],

    // Zusätzliche Schließtage (Urlaub, Fortbildung …) als "YYYY-MM-DD"
    'closedDates' => [],

    // price = Grundpreis €, from = "ab"-Preis, consult = nach Beratung,
    // duration = Minuten, deposit = online fällige Anzahlung bei "ab"-Preisen
    'categories' => [
        [
            'id' => 'damen', 'title' => 'Damen', 'subtitle' => 'Schnitt & Styling',
            'services' => [
                ['id' => 'd-wsf-kurz',   'group' => 'Waschen, Schneiden & Föhnen', 'name' => 'kurz',   'price' => 55, 'duration' => 45],
                ['id' => 'd-wsf-mittel', 'group' => 'Waschen, Schneiden & Föhnen', 'name' => 'mittel', 'price' => 60, 'duration' => 60],
                ['id' => 'd-wsf-lang',   'group' => 'Waschen, Schneiden & Föhnen', 'name' => 'lang',   'price' => 70, 'duration' => 75],
                ['id' => 'd-wf-kurz',    'group' => 'Waschen & Föhnen', 'name' => 'kurz',   'price' => 35, 'duration' => 30],
                ['id' => 'd-wf-mittel',  'group' => 'Waschen & Föhnen', 'name' => 'mittel', 'price' => 40, 'duration' => 40],
                ['id' => 'd-wf-lang',    'group' => 'Waschen & Föhnen', 'name' => 'lang',   'price' => 50, 'duration' => 50],
                ['id' => 'd-hochstecken', 'name' => 'Hochstecken', 'price' => 55, 'from' => true, 'deposit' => 20, 'duration' => 60],
            ],
        ],
        [
            'id' => 'herren', 'title' => 'Herren', 'subtitle' => 'Schnitt & Barber',
            'services' => [
                ['id' => 'h-schnitt',  'name' => 'Herrenschnitt inkl. Waschen & Styling', 'price' => 45, 'duration' => 40],
                ['id' => 'h-maschine', 'name' => 'Maschinenschnitt', 'price' => 30, 'duration' => 20],
                ['id' => 'h-bart',     'name' => 'Bart schneiden', 'price' => 20, 'duration' => 15],
            ],
        ],
        [
            'id' => 'farbe', 'title' => 'Farbe & Techniken', 'subtitle' => 'Individuell nach Aufwand',
            'note' => 'Alle Farbpreise werden nach Aufwand und Verbrauch berechnet. Vor Ort erstellen wir einen individuellen Kostenvoranschlag.',
            'services' => [
                ['id' => 'f-ansatz',      'name' => 'Ansatzfarbe', 'price' => 55,  'from' => true, 'deposit' => 20, 'duration' => 90],
                ['id' => 'f-faerben',     'name' => 'Färben',      'price' => 50,  'from' => true, 'deposit' => 20, 'duration' => 120],
                ['id' => 'f-glossing',    'name' => 'Glossing',    'price' => 22,  'from' => true, 'deposit' => 10, 'duration' => 45],
                ['id' => 'f-balayage',    'name' => 'Balayage',    'price' => 250, 'from' => true, 'deposit' => 50, 'duration' => 210],
                ['id' => 'f-babylights',  'name' => 'Babylights',  'price' => 250, 'from' => true, 'deposit' => 50, 'duration' => 210],
                ['id' => 'f-blondierung', 'name' => 'Blondierung', 'price' => 55,  'from' => true, 'deposit' => 20, 'duration' => 120],
                ['id' => 'f-correction',  'name' => 'Color Correction', 'price' => 0, 'consult' => true, 'duration' => 30, 'bookingName' => 'Color Correction – Beratungstermin'],
            ],
        ],
        [
            'id' => 'pflege', 'title' => 'Pflege & Wellness', 'subtitle' => 'Für gesundes, glänzendes Haar',
            'services' => [
                ['id' => 'p-haarpflege', 'name' => 'Haarpflege',    'price' => 15, 'from' => true, 'deposit' => 10, 'duration' => 15],
                ['id' => 'p-bond',       'name' => 'Bond Treatment', 'price' => 20, 'from' => true, 'deposit' => 10, 'duration' => 30],
            ],
        ],
        [
            'id' => 'brauen', 'title' => 'Augenbrauen & Wimpern', 'subtitle' => 'Der perfekte Rahmen',
            'services' => [
                ['id' => 'b-zupfen',  'name' => 'Augenbrauen zupfen', 'price' => 15, 'from' => true, 'deposit' => 10, 'duration' => 15],
                ['id' => 'b-faerben', 'name' => 'Augenbrauen färben', 'price' => 15, 'from' => true, 'deposit' => 10, 'duration' => 15],
                ['id' => 'b-wimpern', 'name' => 'Wimpern färben',     'price' => 16, 'duration' => 20],
            ],
        ],
    ],
];
