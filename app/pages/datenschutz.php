<?php
$s = cfg()['salon'];

page_start([
    'title' => 'Datenschutz | AJ Atelier – Friseur in Burgwedel-Wettmar',
    'description' => 'Datenschutzerklärung von AJ Atelier: Kontaktformular, Online-Terminbuchung, Gutscheine, PayPal, Besucherstatistik und Ihre Rechte nach DSGVO.',
    'path' => '/datenschutz',
    'robots' => 'noindex, follow',
]);
?>
  <main id="main" class="page">
    <div class="container narrow card prose-legal">
      <h1>Datenschutzerklärung</h1>

      <h2>1. Verantwortliche Stelle</h2>
      <p><span class="placeholder">[Vor- und Nachname der Inhaberin / des Inhabers]</span>, <?= e($s['legalName']) ?>, <?= e($s['street']) ?>, <?= e("{$s['zip']} {$s['city']}") ?><br>
        Telefon: <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a> · E-Mail: <span class="placeholder">[E-Mail-Adresse]</span></p>

      <h2>2. Hosting bei Markentrix und Server-Logfiles</h2>
      <p>Diese Website wird von Markentrix, <span class="placeholder">[Anschrift Markentrix]</span>, betrieben und auf Servern der Hetzner Online GmbH, Industriestr. 25, 91710 Gunzenhausen, in Deutschland gehostet. Mit Markentrix besteht ein Vertrag zur Auftragsverarbeitung (Art. 28 DSGVO). Beim Aufruf werden technisch notwendige Daten (IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, Browser) in Server-Logfiles verarbeitet, um die Website sicher und stabil auszuliefern (Art. 6 Abs. 1 lit. f DSGVO).</p>

      <h2>3. Schriftarten, Cookies und Besucherstatistik</h2>
      <p>Schriftarten werden lokal von unserem Server geladen, es werden keine Inhalte von Google Fonts oder anderen Schriftanbietern abgerufen. Für Formulare, Bewertungen und Statistik lädt die Website ein Skript der Markentrix-Website-Dienste von deren Server.</p>
      <p>Wir zählen Seitenaufrufe anonym, ohne Cookies und ohne Speicherung Ihrer IP-Adresse. Dazu wird ein täglich wechselnder, nicht rückrechenbarer Hashwert gebildet; die Zahlen werden höchstens 400 Tage aufbewahrt (Art. 6 Abs. 1 lit. f DSGVO, Interesse an einer bedarfsgerechten Website).</p>
      <p>Weitere Statistik-Werkzeuge wie Google Analytics werden nur geladen, wenn Sie über das Hinweisfenster ausdrücklich zustimmen (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG). Ihre Auswahl wird im Speicher Ihres Browsers abgelegt. Über „Statistik-Einstellungen“ im Fuß jeder Seite können Sie die Einwilligung jederzeit widerrufen.</p>

      <h2>4. Kontaktformular und Anfragen</h2>
      <p>Wenn Sie uns über ein Formular schreiben, verarbeiten wir Name, E-Mail-Adresse, optional Telefonnummer und Ihre Nachricht, um Ihre Anfrage zu beantworten (Art. 6 Abs. 1 lit. b DSGVO bei Anfragen zu unseren Leistungen, sonst lit. f). Die Anfrage wird im Kundenportal von Markentrix gespeichert, wir werden per E-Mail benachrichtigt und Sie erhalten eine Eingangsbestätigung mit Vorgangsnummer. Ein unsichtbares Feld und eine Begrenzung der Anfragen pro Zeit schützen vor Spam. Anfragen löschen wir, sobald sie erledigt sind und keine Aufbewahrungspflichten bestehen.</p>

      <h2>5. Online-Terminbuchung</h2>
      <p>Für eine Buchung verarbeiten wir Name, Telefonnummer, E-Mail-Adresse, gewählte Leistung, gegebenenfalls die gewünschte Mitarbeiterin oder den gewünschten Mitarbeiter, Datum, Uhrzeit und Ihre Anmerkung. Zweck ist die Vereinbarung und Durchführung des Termins (Art. 6 Abs. 1 lit. b DSGVO). Ihre E-Mail-Adresse nutzen wir für die Bestätigung, für Erinnerungen vor dem Termin und für den Link zum Absagen. Diese E-Mails gehören zum gebuchten Termin und enthalten keine Werbung. Buchungsdaten werden gelöscht, sobald sie nicht mehr benötigt werden, spätestens nach Ablauf gesetzlicher Aufbewahrungsfristen.</p>

      <h2>6. Gutscheine und Zahlung mit PayPal</h2>
      <p>Für eine Gutschein-Anfrage verarbeiten wir Ihren Namen, Ihre E-Mail-Adresse, optional Telefonnummer, den Betrag sowie optional Empfängername und Widmung, um den Gutschein auszustellen, zuzusenden und einzulösen (Art. 6 Abs. 1 lit. b DSGVO). Gutscheindaten bewahren wir bis zum Ablauf der Gültigkeit und der gesetzlichen Aufbewahrungsfristen auf.</p>
      <p>Bezahlen können Sie über einen PayPal-Link, den wir Ihnen per E-Mail senden. Erst wenn Sie diesen Link öffnen, werden Daten an PayPal (Europe) S.à r.l. et Cie, S.C.A., 22–24 Boulevard Royal, L-2449 Luxemburg übermittelt. Die Zahlung geht direkt an uns; es gelten die <a href="https://www.paypal.com/de/legalhub/privacy-full" rel="noopener" target="_blank">Datenschutzbestimmungen von PayPal</a>.</p>

      <h2>7. Google-Bewertungen</h2>
      <p>Auf der Startseite zeigen wir Bewertungen aus unserem Google-Unternehmensprofil. Die Texte werden von den Markentrix-Website-Diensten bereitgestellt; beim Anzeigen werden keine Daten von Ihnen an Google übertragen. Erst wenn Sie den Link „Jetzt bei Google bewerten“ anklicken, öffnet sich Google; dort gelten die Datenschutzbestimmungen der Google Ireland Limited.</p>

      <h2>8. Externe Links</h2>
      <p>Links zu Instagram, Google Maps und OpenStreetMap werden erst beim Anklicken geöffnet; vorher werden keine Daten an diese Anbieter übertragen.</p>

      <h2>9. Ihre Rechte</h2>
      <p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie Widerspruch (Art. 15–21 DSGVO). Eine erteilte Einwilligung können Sie jederzeit mit Wirkung für die Zukunft widerrufen. Zudem können Sie sich bei einer Aufsichtsbehörde beschweren, zum Beispiel bei der Landesbeauftragten für den Datenschutz Niedersachsen.</p>
    </div>
  </main>
<?php page_end();
