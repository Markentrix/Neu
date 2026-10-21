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

    // E-Mail-Versand. Auf Hetzner ist Port 25 gesperrt → SMTP des E-Mail-Postfachs nutzen
    // (z. B. Hetzner KonsoleH/mail.your-server.de, IONOS, Strato, Google Workspace …)
    'mail' => [
        'from'       => 'termine@aj-atelier-wettmar.de', // Absender = SMTP-Postfach
        'salonEmail' => 'info@aj-atelier-wettmar.de',    // erhält jede neue Buchung
        'smtp' => [
            'host' => 'mail.your-server.de', // leer lassen = PHP mail() des Servers
            'port' => 587,                   // 587 (STARTTLS) oder 465 (SSL)
            'user' => 'termine@aj-atelier-wettmar.de',
            'pass' => '',
        ],
    ],

    // Speicherort der SQLite-Datenbank (Ordner muss beschreibbar sein)
    'databasePath' => __DIR__ . '/data/bookings.sqlite',
];
