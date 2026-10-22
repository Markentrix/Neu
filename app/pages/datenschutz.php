<?php
$s = cfg()['salon'];

page_start([
    'title' => 'Datenschutz | AJ Atelier – Friseur in Burgwedel-Wettmar',
    'description' => 'Datenschutzerklärung von AJ Atelier: Online-Terminbuchung, PayPal-Zahlung und Ihre Rechte nach DSGVO.',
    'path' => '/datenschutz',
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

      <h2>5. Kontaktformular</h2>
      <p>Wenn Sie uns über das Kontaktformular schreiben, verarbeiten wir Name, E-Mail-Adresse, optional Telefonnummer und Ihre Nachricht, um Ihre Anfrage zu beantworten (Art. 6 Abs. 1 lit. b bzw. f DSGVO). Die Nachricht wird per E-Mail an uns übermittelt und nicht auf der Website gespeichert.</p>

      <h2>6. Terminerinnerung und Folgetermin-Erinnerung</h2>
      <p>Etwa 24 Stunden vor Ihrem Termin erhalten Sie eine Erinnerung per E-Mail. Sie dient der Durchführung des gebuchten Termins (Art. 6 Abs. 1 lit. b DSGVO). Nur wenn Sie bei der Buchung zusätzlich zustimmen, schicken wir Ihnen einmalig eine Erinnerung, wenn Ihr nächster Termin fällig ist, etwa für Ansatz oder Nachschnitt (Art. 6 Abs. 1 lit. a DSGVO). Diese Einwilligung können Sie jederzeit formlos widerrufen; haben Sie bereits einen neuen Termin gebucht, entfällt die Erinnerung.</p>

      <h2>7. Bitte um eine Google-Bewertung</h2>
      <p>Nur wenn Sie bei der Buchung ausdrücklich zustimmen, schicken wir Ihnen am Tag nach dem Termin einmalig eine E-Mail mit der Bitte um eine Bewertung bei Google (Art. 6 Abs. 1 lit. a DSGVO). Sie können die Einwilligung jederzeit formlos widerrufen. Eine Bewertung bei Google geben Sie freiwillig und direkt bei Google ab; dafür gelten die Datenschutzbestimmungen von Google.</p>

      <h2>8. Kauf von Gutscheinen</h2>
      <p>Beim Online-Kauf eines Gutscheins verarbeiten wir Ihren Namen, Ihre E-Mail-Adresse, den Betrag sowie optional Empfängername und Nachricht, um den Gutschein auszustellen, zu versenden und später einzulösen (Art. 6 Abs. 1 lit. b DSGVO). Gutscheindaten bewahren wir bis zum Ablauf der Gültigkeit und der gesetzlichen Aufbewahrungsfristen auf.</p>

      <h2>9. Zahlung mit PayPal</h2>
      <p>Wenn Sie „Jetzt mit PayPal bezahlen“ wählen, wird das PayPal-Skript geladen und Ihre Zahlung über PayPal (Europe) S.à r.l. et Cie, S.C.A., 22–24 Boulevard Royal, L-2449 Luxemburg abgewickelt. Dabei werden Zahlungsdaten und technische Daten an PayPal übermittelt (Art. 6 Abs. 1 lit. b DSGVO). Wählen Sie „Vor Ort bezahlen“, wird PayPal nicht geladen. Details: <a href="https://www.paypal.com/de/legalhub/privacy-full" rel="noopener" target="_blank">Datenschutzerklärung von PayPal</a>.</p>

      <h2>10. Externe Links</h2>
      <p>Links zu Instagram, Google Maps und OpenStreetMap werden erst beim Anklicken geöffnet; vorher werden keine Daten an diese Anbieter übertragen.</p>

      <h2>11. Ihre Rechte</h2>
      <p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie Widerspruch (Art. 15–21 DSGVO). Zudem können Sie sich bei einer Aufsichtsbehörde beschweren, z. B. bei der Landesbeauftragten für den Datenschutz Niedersachsen.</p>
    </div>
  </main>
<?php page_end();
