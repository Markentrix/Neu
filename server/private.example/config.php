<?php
/*
 * Konfiguration für den Anfrage-Endpunkt (public/api/anfrage.php).
 *
 * Diese Datei gehört NICHT ins Webroot. Auf dem Server als
 *     <Projektordner>/private/config.php
 * ablegen, also neben den Ordner public/, und nur für den Webserver-Benutzer lesbar machen:
 *     chown www-data:www-data private/config.php && chmod 640 private/config.php
 *
 * Liegt der Ordner woanders, den Pfad per Umgebungsvariable PSS_PRIVATE_DIR angeben
 * (bei nginx: fastcgi_param PSS_PRIVATE_DIR /pfad/zu/private;).
 *
 * Geheimen Schlüssel erzeugen:  openssl rand -hex 32
 */

return [
    // Geheimer Schlüssel für Token und Hash der IP-Adresse. Mindestens 32 Zeichen, nie veröffentlichen.
    'secret' => 'HIER-ZUFAELLIGEN-SCHLUESSEL-EINTRAGEN',

    // Hierhin gehen die Anfragen
    'mail_to' => 'info@psschneider.de',

    // Absender. Muss eine Adresse sein, die der SMTP-Zugang versenden darf, am besten die des Zugangs selbst.
    'mail_from' => 'anfragen@psschneider.de',
    'mail_from_name' => 'Website psschneider.de',

    // 'smtp' (empfohlen) oder 'mail' (PHP mail(), braucht einen lokalen Mailserver)
    'transport' => 'smtp',

    // Auf Hetzner Cloud ist ausgehend Port 25 gesperrt. Verwenden Sie den Einreichungsport 587 mit STARTTLS
    // oder 465 mit 'ssl' beim Postfachanbieter.
    'smtp' => [
        'host' => 'smtp.example.com',
        'port' => 587,
        'secure' => 'starttls',    // starttls, ssl oder none
        'user' => 'anfragen@psschneider.de',
        'pass' => 'HIER-PASSWORT-DES-POSTFACHS',
        'verify_peer' => true,     // Zertifikat prüfen. Nur für Tests auf false stellen.
        'timeout' => 20,
    ],

    // Von welchen Adressen das Formular aufgerufen werden darf (Schutz vor Fremdseiten)
    'allowed_origins' => [
        'https://psschneider.de',
        'https://www.psschneider.de',
    ],

    // Nur eintragen, wenn der Server hinter einem Proxy oder Load Balancer steht, dessen Adresse hier steht
    'trusted_proxies' => [],

    // Fotos
    'max_photos' => 5,
    'max_photo_mb' => 15,
    'max_edge_px' => 2400,
    'jpeg_quality' => 85,

    // Missbrauchsschutz
    'min_seconds' => 4,        // frühestens so viele Sekunden nach dem Laden des Formulars
    'rate_per_hour' => 5,      // Anfragen pro Verbindung und Stunde
    'rate_per_day' => 15,      // und pro Tag

    // Nur wenn der Versand fehlschlägt, wird die Anfrage so lange zwischengespeichert (Tage)
    'keep_failed_days' => 14,
];
