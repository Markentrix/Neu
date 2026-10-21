<?php
declare(strict_types=1);
require __DIR__ . '/../app/lib.php';
require __DIR__ . '/../app/layout.php';
$s = cfg()['salon'];

page_start([
    'title' => 'Datenschutz | AJ Atelier – Friseur in Burgwedel-Wettmar',
    'description' => 'Datenschutzerklärung von AJ Atelier: Online-Terminbuchung, PayPal-Zahlung und Ihre Rechte nach DSGVO.',
    'path' => '/datenschutz.php',
    'robots' => 'noindex, follow',
]);
?>
  <main id="main" class="page">
    <div class="container narrow card">
      <h1>Datenschutzerklärung</h1>
      <p class="hint">Bitte vor Veröffentlichung rechtlich prüfen lassen und Platzhalter ergänzen.</p>

      <h2>1. Verantwortliche Stelle</h2>
      <p><span class="placeholder">[Vor- und Nachname]</span>, <?= e($s['legalName']) ?>, <?= e($s['street']) ?>, <?= e("{$s['zip']} {$s['city']}") ?><br>
        Telefon: <?= e($s['phoneDisplay']) ?> · E-Mail: <span class="placeholder">[E-Mail-Adresse]</span></p>

      <h2>2. Hosting &amp; Server-Logfiles</h2>
      <p>Diese Website wird bei <span class="placeholder">[Name des Hosters, Anschrift]</span> betrieben. Beim Aufruf werden technisch notwendige Daten (IP-Adresse, Datum/Uhrzeit, aufgerufene Seite, Browser) in Server-Logfiles verarbeitet, um den sicheren Betrieb zu gewährleisten (Art. 6 Abs. 1 lit. f DSGVO). Die Logfiles werden nach spätestens <span class="placeholder">[14]</span> Tagen gelöscht.</p>

      <h2>3. Keine Cookies, kein Tracking</h2>
      <p>Wir setzen keine Analyse- oder Marketing-Tools ein und laden keine Schriftarten oder Karten von Drittanbietern. Schriftarten werden lokal von unserem Server ausgeliefert. Lediglich die passwortgeschützte Terminverwaltung des Salons verwendet ein technisch notwendiges Sitzungs-Cookie.</p>

      <h2>4. Online-Terminbuchung</h2>
      <p>Für die Buchung verarbeiten wir Name, Telefonnummer, E-Mail-Adresse, gewählte Leistungen, Termin und optional Ihre Anmerkung. Zweck ist die Durchführung des Termins und die Bestätigung per E-Mail (Art. 6 Abs. 1 lit. b DSGVO). Zum Schutz vor Missbrauch speichern wir kurzzeitig einen nicht rückrechenbaren Hashwert Ihrer IP-Adresse (max. 24 Stunden, Art. 6 Abs. 1 lit. f DSGVO). Buchungsdaten werden gelöscht, sobald sie nicht mehr benötigt werden, spätestens nach Ablauf gesetzlicher Aufbewahrungsfristen.</p>

      <h2>5. Zahlung mit PayPal</h2>
      <p>Wenn Sie „Jetzt mit PayPal bezahlen“ wählen, wird das PayPal-Skript geladen und Ihre Zahlung über PayPal (Europe) S.à r.l. et Cie, S.C.A., 22–24 Boulevard Royal, L-2449 Luxemburg abgewickelt. Dabei werden Zahlungsdaten und technische Daten an PayPal übermittelt (Art. 6 Abs. 1 lit. b DSGVO). Wählen Sie „Vor Ort bezahlen“, wird PayPal nicht geladen. Details: <a href="https://www.paypal.com/de/legalhub/privacy-full" rel="noopener" target="_blank">Datenschutzerklärung von PayPal</a>.</p>

      <h2>6. Externe Links</h2>
      <p>Links zu Instagram, Google Maps und OpenStreetMap werden erst beim Anklicken geöffnet; vorher werden keine Daten an diese Anbieter übertragen.</p>

      <h2>7. Ihre Rechte</h2>
      <p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie Widerspruch (Art. 15–21 DSGVO). Zudem können Sie sich bei einer Aufsichtsbehörde beschweren, z. B. bei der Landesbeauftragten für den Datenschutz Niedersachsen.</p>
    </div>
  </main>
<?php page_end();
