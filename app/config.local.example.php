<?php
// Kopieren nach app/config.local.php und ausfüllen. Diese Datei NIE ins Git einchecken.

return [
    // Öffentliche Adresse der Website, ohne Schrägstrich am Ende
    'siteUrl' => 'https://www.aj-atelier-wettmar.de',

    // Passwort für die Terminverwaltung unter /admin/ (mind. 12 Zeichen)
    // Erzeugen: php -r "echo password_hash('MEIN-PASSWORT', PASSWORD_DEFAULT), PHP_EOL;"
    'adminPasswordHash' => '',

    // PayPal REST-App: https://developer.paypal.com/dashboard/applications
    // 'sandbox' zum Testen, 'live' für echte Zahlungen
    'paypal' => [
        'env'          => 'sandbox',
        'clientId'     => '',
        'clientSecret' => '',
    ],

    // E-Mail-Versand über PHP mail() des Servers
    'mail' => [
        'from'       => 'termine@aj-atelier-wettmar.de', // Absender (Domain des Servers verwenden!)
        'salonEmail' => 'info@aj-atelier-wettmar.de',    // erhält jede neue Buchung
    ],

    // Speicherort der SQLite-Datenbank (Ordner muss beschreibbar sein)
    'databasePath' => __DIR__ . '/data/bookings.sqlite',
];
