<?php
// Ortsseiten (/friseur-<slug>): Anfahrt aus den Nachbarorten.
// Entfernungen und Fahrzeiten: OpenStreetMap/OSRM, Auto, ohne Verkehr (Stand Oktober 2026).

return [
    'burgwedel' => [
        'name' => 'Burgwedel',
        'title' => 'Friseur in Burgwedel',
        'metaTitle' => 'Friseur Burgwedel | AJ Atelier Wettmar – Balayage & Schnitt',
        'description' => 'Friseur für Burgwedel: AJ Atelier in Wettmar, wenige Minuten von Großburgwedel, Kleinburgwedel, Thönse, Engensen und Fuhrberg. Jetzt online Termin buchen.',
        'intro' => 'Wettmar ist ein Ortsteil von Burgwedel. Unser Salon in der Hauptstraße 64 liegt damit mitten in der Stadt, nur wenige Autominuten von den anderen Burgwedeler Ortsteilen entfernt. Ob Sie in Großburgwedel arbeiten, in Thönse wohnen oder aus Fuhrberg kommen: Zu uns ist es nicht weit.',
        'routes' => [
            ['Kleinburgwedel', 2.8, 3],
            ['Engensen', 2.7, 3],
            ['Thönse', 3.1, 4],
            ['Großburgwedel', 5.4, 7],
            ['Fuhrberg', 10.4, 11],
        ],
        'text' => [
            'Viele unserer Kundinnen und Kunden kommen aus ganz Burgwedel. Für sie ist besonders praktisch, dass sie ihren Termin rund um die Uhr online buchen können. Freie Zeiten sehen Sie sofort, die Bestätigung kommt per E-Mail.',
            'Ins Navi geben Sie einfach „Hauptstraße 64, 30938 Burgwedel“ ein. Der Salon liegt an der Hauptstraße in Wettmar.',
        ],
    ],

    'isernhagen' => [
        'name' => 'Isernhagen',
        'title' => 'Friseur für Isernhagen',
        'metaTitle' => 'Friseur nahe Isernhagen | AJ Atelier Wettmar',
        'description' => 'Friseur für Isernhagen: AJ Atelier in Burgwedel-Wettmar, rund 15 Minuten von Isernhagen H.B. und Kirchhorst. Balayage, Babylights, Schnitt und Farbe, online buchen.',
        'intro' => 'Von Isernhagen sind Sie in rund einer Viertelstunde bei uns in Wettmar. Gerade für aufwendige Farbtermine wie Balayage oder Babylights nehmen viele Kundinnen die kurze Fahrt gern in Kauf, um in Ruhe und ohne Hektik beraten zu werden.',
        'routes' => [
            ['Isernhagen H.B.', 11.0, 15],
            ['Isernhagen Kirchhorst', 11.7, 15],
        ],
        'text' => [
            'Ins Navi geben Sie einfach „Hauptstraße 64, 30938 Burgwedel“ ein. Der Salon liegt an der Hauptstraße in Wettmar.',
            'Den Termin buchen Sie bequem online und sehen sofort, welche Zeiten frei sind. Bei Farbbehandlungen mit „ab“-Preis erhalten Sie vorab einen Kostenvoranschlag, bezahlt wird nach Aufwand im Salon.',
        ],
    ],

    'langenhagen' => [
        'name' => 'Langenhagen',
        'title' => 'Friseur für Langenhagen',
        'metaTitle' => 'Friseur für Langenhagen | Balayage bei AJ Atelier Wettmar',
        'description' => 'Aus Langenhagen in rund 25 Minuten zu AJ Atelier in Burgwedel-Wettmar: Balayage, Babylights, Blondierung, Schnitt & Styling. Online Termin buchen.',
        'intro' => 'Aus Langenhagen erreichen Sie unseren Salon in Wettmar in rund 25 Minuten. Viele Kundinnen verbinden den Weg mit einem längeren Termin für Farbe und Schnitt und genießen die ruhige Atmosphäre außerhalb der Stadt.',
        'routes' => [
            ['Langenhagen (Zentrum)', 17.1, 27],
        ],
        'text' => [
            'Ins Navi geben Sie einfach „Hauptstraße 64, 30938 Burgwedel“ ein. Der Salon liegt an der Hauptstraße in Wettmar.',
            'Für längere Behandlungen wie Balayage oder Blondierung planen Sie bitte etwa 3 bis 4 Stunden ein. Alle Zeiten sehen Sie direkt in der Online-Buchung.',
        ],
    ],

    'hannover' => [
        'name' => 'Hannover',
        'title' => 'Friseur für Hannover-Nord',
        'metaTitle' => 'Friseur nördlich von Hannover | AJ Atelier Wettmar',
        'description' => 'Aus Hannover-Bothfeld oder der List in rund 20 bis 30 Minuten zu AJ Atelier in Burgwedel-Wettmar. Balayage, Babylights, Farbe und Schnitt, online buchen.',
        'intro' => 'Nördlich von Hannover, in Burgwedel-Wettmar, finden Sie das AJ Atelier. Aus den nördlichen Stadtteilen wie Bothfeld oder der List sind Sie in rund 20 bis 30 Minuten bei uns, ganz ohne Parkplatzsuche in der Innenstadt.',
        'routes' => [
            ['Hannover-Bothfeld', 24.7, 22],
            ['Hannover-List', 29.5, 31],
        ],
        'text' => [
            'Ins Navi geben Sie einfach „Hauptstraße 64, 30938 Burgwedel“ ein. Der Salon liegt an der Hauptstraße in Wettmar.',
            'Gerade für Farbtermine lohnt sich die Fahrt: Bei uns nehmen wir uns Zeit für Beratung und Kostenvoranschlag, bevor wir beginnen.',
        ],
    ],
];
