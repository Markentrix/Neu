# -*- coding: utf-8 -*-
from common import *

def ptable(caption, rows, cols=("Fahrten","Erw. 16+","Kids 8–15")):
    th = "".join(f'<th{" class=price" if i else ""}>{c}</th>' for i,c in enumerate(cols))
    tr = "".join("<tr>"+"".join(f'<td{" class=price" if i else ""}>{c}</td>' for i,c in enumerate(r))+"</tr>" for r in rows)
    return f'<div class="table-wrap"><table><caption>{caption}</caption><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table><p class="price-hint">Preise pro Person. Tickets sind nicht übertragbar und müssen am Kaufdatum verfahren werden.</p></div>'

html = head("Preise Kartfahren Celle ab 12 € | Burnout Kartbahn",
 "Alle Preise der Celler Kartbahn: Ticketfahrten Sa/So, Spartage Mo–Do (3 für 2, 5 für 3), Freitagsspecial, Doppelsitzer, Kidsparty, Supercup, Bahnmiete, Schulklassen und Kinderkartführerschein.",
 breadcrumb("Preise","preise.html") + '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"ItemList","name":"Preisliste Burnout Celler-Kartbahn (Stand Oktober 2026)","itemListOrder":"https://schema.org/ItemListUnordered","numberOfItems":10,"itemListElement":[
{"@type":"ListItem","position":1,"item":{"@type":"Offer","name":"Ticketfahrt 10 Minuten Erwachsene Sa/So","price":"15.00","priceCurrency":"EUR","url":"/preise.html#tickets"}},
{"@type":"ListItem","position":2,"item":{"@type":"Offer","name":"Ticketfahrt 10 Minuten Kinder 8–15 Sa/So","price":"13.50","priceCurrency":"EUR","url":"/preise.html#tickets"}},
{"@type":"ListItem","position":3,"item":{"@type":"Offer","name":"Spartag Mo–Do: 3 Fahrten für 2 (Erwachsene)","price":"30.00","priceCurrency":"EUR","url":"/preise.html#spartage"}},
{"@type":"ListItem","position":4,"item":{"@type":"Offer","name":"Freitag: 1 Fahrt Erwachsene","price":"14.00","priceCurrency":"EUR","url":"/preise.html#freitag"}},
{"@type":"ListItem","position":5,"item":{"@type":"Offer","name":"Doppelsitzer 1 Fahrt (2 Personen)","price":"18.00","priceCurrency":"EUR","url":"/preise.html#doppelsitzer"}},
{"@type":"ListItem","position":6,"item":{"@type":"Offer","name":"Registrierung inkl. Rennlizenz (einmalig)","price":"2.00","priceCurrency":"EUR","url":"/preise.html#neukunden"}},
{"@type":"ListItem","position":7,"item":{"@type":"Offer","name":"Kidsparty F1 pro Kind","price":"40.00","priceCurrency":"EUR","url":"/preise.html#kids"}},
{"@type":"ListItem","position":8,"item":{"@type":"Offer","name":"Supercup Standard pro Person","price":"39.00","priceCurrency":"EUR","url":"/preise.html#supercup"}},
{"@type":"ListItem","position":9,"item":{"@type":"Offer","name":"Bahnmiete 1 Stunde inkl. 10 Karts","price":"650.00","priceCurrency":"EUR","url":"/preise.html#bahnmiete"}},
{"@type":"ListItem","position":10,"item":{"@type":"Offer","name":"Kinderkartführerschein","price":"45.00","priceCurrency":"EUR","url":"/preise.html#fuehrerschein"}}]}</script>''') + header()

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/karts-boxengasse.webp" width="1400" height="933" alt="Rote Sodi-Karts in der Boxengasse der Celler Kartbahn" fetchpriority="high">
  <div class="wrap">
    <span class="eyebrow">Preise &amp; Angebote</span>
    <h1>Preise auf einen Blick</h1>
    <p class="lead">Transparent, pro Person, ohne versteckte Kosten. Bezahlung vor Ort in bar oder mit EC-Karte.</p>
    <div class="hero__actions"><a class="btn btn--primary" href="buchen.html">{ICONS["cal"]}Online buchen</a><a class="btn btn--light" href="gutscheine.html">{ICONS["gift"]}Gutschein kaufen</a></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="toc"><strong>Direkt zu:</strong>
      <ol><li><a href="#tickets">Ticketfahrten Sa/So</a></li><li><a href="#spartage">Spartage Mo–Do</a></li><li><a href="#freitag">Freitagsspecial</a></li><li><a href="#doppelsitzer">Doppelsitzer</a></li><li><a href="#neukunden">Neukunden &amp; Rennlizenz</a></li><li><a href="#kids">Kidsparty</a></li><li><a href="#supercup">Supercup / Rennen</a></li><li><a href="#bahnmiete">Bahnmiete</a></li><li><a href="#schule">Schulklassen</a></li><li><a href="#fuehrerschein">Kinderkartführerschein</a></li><li><a href="#racecam">RaceCam</a></li><li><a href="#siegerehrung">Siegerehrung</a></li></ol>
    </div>
    <p class="notice"><strong>Wer darf fahren?</strong> Kinder ab 8 Jahren und mindestens 1,25 m im Kinderkart. Ins große Kart ab 13 Jahren und 1,55 m (ab 12 Jahren mit Karterfahrung). Kleinere Kids ab 4 Jahren und 1,10 m fahren im <a href="#doppelsitzer">Doppelsitzer</a> mit.</p>

    <h2 id="tickets">Ticketfahrten Samstag &amp; Sonntag</h2>
    {ptable("Normalpreise (Sa/So) – je 10 Minuten", [("1 × 10 Min","15,00 €","13,50 €"),("2 × 10 Min","30,00 €","27,00 €"),("3 × 10 Min","43,00 €","36,00 €"),("4 × 10 Min","52,00 €","43,00 €"),("5 × 10 Min","60,00 €","50,00 €"),("jede weitere 10 Min","9,00 €","7,00 €")])}

    <h2 id="spartage" style="margin-top:2.5rem">Spartage Montag bis Donnerstag</h2>
    <p class="muted">An diesen Tagen bekommt ihr entweder 3 Tickets zum Preis von 2 oder 5 Tickets zum Preis von 3.</p>
    {ptable("Spartage Mo–Do", [("3 für 2 – 3 × 10 Min","30 €","27 €"),("5 für 3 – 5 × 10 Min","43 €","36 €")])}

    <h2 id="freitag" style="margin-top:2.5rem">Freitagsspecial – je öfter, desto günstiger</h2>
    {ptable("Freitag", [("1 × 10 Min","14 €","12 €"),("2 × 10 Min","25 €","21 €"),("3 × 10 Min","34 €","29 €"),("4 × 10 Min","42 €","36 €"),("5 × 10 Min","49 €","41 €"),("jede weitere 10 Min","7 €","6 €")])}

    <h2 id="doppelsitzer" style="margin-top:2.5rem">Doppelsitzer – doppelter Spaß</h2>
    <div class="grid grid-2" style="align-items:start">
      {ptable("Doppelsitzer (Preis für 2 Personen)", [("1 × 10 Min","18 €"),("2 × 10 Min","32 €"),("3 × 10 Min","45 €"),("jede weitere 10 Min","10 €")], cols=("Fahrten","Preis für 2 Personen"))}
      <div class="card">
        <h3>Gut zu wissen</h3>
        <ul class="checks">
          <li>Beifahrer ab 4 Jahren und 1,10 m Mindestgröße</li>
          <li>Am Steuer sitzt eine volljährige Person; bei Beifahrern unter 18 Jahren die erziehungsberechtigte Person</li>
          <li>Unter 18 und zum ersten Mal da? <a href="downloads/haftungsausschluss-minderjaehrige.pdf" target="_blank" rel="noopener">Einverständniserklärung</a> ausgefüllt mitbringen</li>
          <li>Reservierung telefonisch ab 2 Tage vorher: <a href="{TEL_LINK}">{TEL}</a></li>
          <li>Bei Rennen oder Bahnmieten: einmalig 10 € Zusatzgebühr</li>
        </ul>
        <p class="small">Spartage und besondere Angebote gelten nicht für den Doppelsitzer.</p>
      </div>
    </div>

    <h2 id="neukunden" style="margin-top:2.5rem">Neukunden: Registrierung &amp; Rennlizenz</h2>
    <div class="grid grid-3">
      <div class="stat"><strong>2,00 €</strong><span>Registrierung inkl. Rennlizenz (einmalig)</span></div>
      <div class="stat"><strong>3,00 €</strong><span>Sturmhaube inkl. Helmleihe</span></div>
      <div class="stat"><strong>4,00 €</strong><span>Paketpreis Registrierung + Sturmhaube</span></div>
    </div>
    <p class="muted" style="margin-top:1rem">Beim ersten Besuch muss sich jeder Fahrer aus versicherungstechnischen Gründen registrieren. Die Rennlizenz gibt es als Mobillizenz fürs Smartphone: alle Rennen auf einen Blick, Bestzeiten vergleichen, Livetiming und Rennergebnisse direkt aufs Handy. Die Kosten der Rennlizenz entfallen bei Bahnmieten und Kidspartys.</p>

    <h2 id="kids" style="margin-top:2.5rem">Kidsparty &amp; Kindergeburtstag</h2>
    <div class="grid grid-2">
      <div class="card card--accent"><span class="badge">Paket F1</span><h3>40,00 € pro Kind</h3><p>3 × 10 Minuten Fahrspaß</p><ul class="checks"><li>Registrierung und Sturmhaube</li><li>Kleines Geschenk für das Geburtstagskind</li><li>Helmleihe</li><li>Partytisch mit Chips &amp; Süßem</li><li>2 Softdrinks 0,2 l</li></ul></div>
      <div class="card card--accent"><span class="badge">Paket F2</span><h3>48,00 € pro Kind</h3><p>Grand-Prix-Modus – insgesamt 40 Minuten Fahrzeit</p><ul class="checks"><li>10 Min Training, 10 Min Qualifying, 20 Min Rennen mit Formel-1-Start</li><li>Registrierung, Sturmhaube und Helmleihe</li><li>Kleines Geschenk für das Geburtstagskind</li><li>Partytisch mit Chips &amp; Süßem, 2 Softdrinks 0,2 l</li></ul></div>
    </div>
    <div class="table-wrap" style="margin-top:1rem"><table><caption>Extras zur Kidsparty</caption><tbody>
      <tr><td>Pizzapaket (1 Pizza 29 cm nach Wahl + 1 Softdrink 0,2 l)</td><td class="price">10,50 € pro Teilnehmer</td></tr>
      <tr><td>Jede weitere 10 Minuten Fahrspaß</td><td class="price">8,00 € pro Person</td></tr>
      <tr><td>Aufschlag Erwachsene 16–20 Jahre</td><td class="price">5,00 €</td></tr>
      <tr><td>Aufschlag Erwachsene ab 21 Jahren</td><td class="price">7,50 €</td></tr>
    </tbody></table><p class="price-hint">Mindestens 6 Teilnehmer. Bezahlung vor Ort in bar oder per EC. Der Kinderkartführerschein ist in Verbindung mit den Kidsparty-Angeboten nicht gültig.</p></div>
    <p style="margin-top:1rem"><a class="btn btn--ghost" href="kinder.html">Alle Infos zur Kidsparty</a></p>

    <h2 id="supercup" style="margin-top:2.5rem">Supercup / Rennen (6–17 Personen)</h2>
    <p class="muted">Exklusiv – eure Gruppe ist allein auf der Rennstrecke. Mit Qualifying, Ampelstart, Zieleinlauf und Rennauswertung. Bei weniger als 6 Teilnehmern wird der Preis für 6 Teilnehmer berechnet.</p>
    <div class="table-wrap"><table><caption>Supercup</caption><thead><tr><th>Paket</th><th>Qualifying</th><th>Rennen</th><th class="price">Preis p.P.</th></tr></thead><tbody>
      <tr><td>Standard</td><td>10 Min</td><td>20 Min</td><td class="price">39 €</td></tr>
      <tr><td>Professional</td><td>10 Min</td><td>30 Min</td><td class="price">49 €</td></tr>
      <tr><td>Premium</td><td>10 Min</td><td>40 Min</td><td class="price">59 €</td></tr>
      <tr><td>Double Premium</td><td>10 Min</td><td>2 × 20 Min</td><td class="price">59 €</td></tr>
      <tr><td>Double Ultra</td><td>10 Min</td><td>2 × 30 Min</td><td class="price">75 €</td></tr>
      <tr><td>Grand Prix</td><td>10 Min Training + 10 Min Qualifying</td><td>20 Min</td><td class="price">49 €</td></tr>
      <tr><td>Grand Prix Premium</td><td>10 Min Training + 10 Min Qualifying</td><td>30 Min</td><td class="price">59 €</td></tr>
    </tbody></table><p class="price-hint">Nach dem Qualifying kann eine Pause von 15–25 Minuten eingeplant werden – bitte bei der Buchung angeben. Beim Double ist die Startaufstellung im zweiten Rennen der Zieleinlauf des ersten; beim Double Premium ist zwischen den Rennen automatisch eine Pause enthalten. Beim Grand Prix ist immer eine Pause zwischen den Fahrten.</p></div>

    <h2 id="bahnmiete" style="margin-top:2.5rem">Bahnmiete – Firmen &amp; große Gruppen</h2>
    <div class="table-wrap"><table><caption>Exklusive Bahnmiete (Brutto / Netto)</caption><thead><tr><th>Leistung</th><th class="price">pro Stunde</th><th class="price">jede weitere ½ Stunde</th></tr></thead><tbody>
      <tr><td>Bahnmiete inkl. 10 Karts</td><td class="price">650,00 € / 546,22 €</td><td class="price">325,00 € / 273,11 €</td></tr>
      <tr><td>jedes weitere Kart</td><td class="price">65,00 € / 54,62 €</td><td class="price">32,50 € / 27,31 €</td></tr>
    </tbody></table><p class="price-hint">Mindestmietdauer 1 Stunde, Mindestabnahme 10 Karts, maximal 16 Karts gleichzeitig. Weitere Karts können auch spontan am Veranstaltungstag dazugebucht werden.</p></div>

    <h2 id="schule" style="margin-top:2.5rem">Schulklassen (ab 20 Personen, Mo–Fr)</h2>
    <div class="grid grid-2">
      <div class="card"><span class="badge badge--dark">Angebot 1</span><h3>20 € pro Person</h3><p>20 Minuten Fahrzeit</p><ul class="checks"><li>Registrierung der Fahrer</li><li>Sturmhaube</li><li>Einweisung Kart / Strecke / Regeln</li><li>2 × 10 Min auf Bestzeit pro Gruppe</li></ul></div>
      <div class="card"><span class="badge badge--dark">Angebot 2</span><h3>25 € pro Person</h3><p>30 Minuten Fahrzeit</p><ul class="checks"><li>Registrierung der Fahrer</li><li>Sturmhaube</li><li>Einweisung Kart / Strecke / Regeln</li><li>3 × 10 Min auf Bestzeit pro Gruppe</li><li>1 Softgetränk 0,2 l pro Teilnehmer</li></ul></div>
    </div>
    <p class="small" style="margin-top:.8rem">Lehrkräfte nehmen zu den gleichen Konditionen teil. Auch vormittags möglich.</p>

    <h2 id="fuehrerschein" style="margin-top:2.5rem">Kinderkartführerschein – 45,00 €</h2>
    <div class="split">
      <div>
        <p>2–3 Stunden Intensivkurs inkl. Führerscheinlizenz und Sturmhaube: Ideallinie, schwierige Kurven, Hütchenfahren, Bremstest, Flaggentest, Fahrtraining und Theorie. Nach bestandenem Kurs kostet jedes Trainingsticket nur noch 6 € – gültig bis zur Vollendung des 15. Lebensjahres.</p>
        <p><strong>Jeden 1. Samstag im Monat um 10 Uhr</strong>, bitte um 09:30 Uhr im Haus eintreffen. Voranmeldung über die Online-Buchung.</p>
        <a class="btn btn--primary btn--sm" href="buchen.html?angebot=fuehrerschein">Führerschein buchen</a>
      </div>
      <img src="assets/img/kids-start.webp" width="400" height="267" alt="Kind mit rotem Helm im Kinderkart am Start" loading="lazy" decoding="async">
    </div>

    <h2 id="racecam" style="margin-top:2.5rem">RaceCam – dein Rennen auf Video</h2>
    <div class="table-wrap"><table><caption>RaceCam (erhältlich beim Check-in)</caption><tbody>
      <tr><td>1 Durchgang / Rennen</td><td class="price">5 €</td></tr><tr><td>2 Durchgänge / Rennen</td><td class="price">9 €</td></tr><tr><td>3 Durchgänge / Rennen</td><td class="price">12 €</td></tr><tr><td>jeder weitere Durchgang</td><td class="price">3 €</td></tr>
    </tbody></table><p class="price-hint">Ein Durchgang darf maximal 30 Minuten lang sein; bei längeren Rennen 5 € Aufschlag. Download sofort nach dem Rennen per QR-Code.</p></div>

    <h2 id="siegerehrung" style="margin-top:2.5rem">Siegerehrung – Pokale &amp; Medaillen</h2>
    <div class="grid grid-3">
      <div class="card"><h3>Pokalsatz 1</h3><p>10–14 cm, inkl. Standardgravur</p><p><strong style="color:#fff;font-size:1.3rem">30 €</strong></p></div>
      <div class="card"><h3>Pokalsatz 2</h3><p>13–18 cm, inkl. Standardgravur</p><p><strong style="color:#fff;font-size:1.3rem">40 €</strong></p></div>
      <div class="card"><h3>Medaille</h3><p>pro Stück</p><p><strong style="color:#fff;font-size:1.3rem">1,90 €</strong></p></div>
    </div>
    <p class="small" style="margin-top:.8rem">Siegerehrung bei Rennen, Kidspartys oder Bahnmieten ab einer Mindestabnahme von 3 Medaillen oder Pokalen – auf unserem Podest mit Gruppenfoto.</p>
    <p class="small">Alle Preise in Euro inkl. gesetzlicher Umsatzsteuer, Stand Oktober 2026. Änderungen vorbehalten.</p>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("preise.html", html)

# ---------------- BUCHEN ----------------
html = head("Online buchen – Kartbahn Celle | Burnout Kartbahn",
 "Fahrten, Kidsparty, Supercup-Rennen, Bahnmiete, Schulklasse oder Kinderkartführerschein online buchen: Datum und Startzeit wählen, Teilnehmer angeben, Preis sofort sehen.",
 breadcrumb("Online buchen","buchen.html")) + header()

def choice(val, title, sub):
    return f'<div class="choice"><input type="radio" name="angebot" id="a-{val}" value="{val}"><label for="a-{val}"><strong>{title}</strong><small>{sub}</small></label></div>'

html += f'''
<section class="section section--tight">
  <div class="wrap">
    <span class="eyebrow">Online-Buchung</span>
    <h1 id="form-title">Jetzt online buchen</h1>
    <p class="lead">In vier Schritten zur Reservierung. Ihr bekommt sofort eine Eingangsbestätigung mit Vorgangsnummer per E-Mail; verbindlich wird die Buchung mit unserer Buchungsbestätigung (<a href="agb.html">AGB § 2</a>). Bezahlt wird vor Ort in bar oder mit EC-Karte.</p>
    <p id="next-free" class="small"></p>
    <div class="notice" id="self-note" hidden><p>Hinweis: Aktuell nehmen wir Terminwünsche entgegen und melden uns mit einer Bestätigung oder einem Alternativtermin.</p></div>
    <div class="notice">
      <p><strong>Weniger als 5 Personen?</strong> Dann reserviert bitte telefonisch ab 2 Tage vorher: <a href="{TEL_LINK}">{TEL}</a>. Kurzfristige Besuche (innerhalb der nächsten 3 Tage) ebenfalls telefonisch innerhalb der Öffnungszeiten. Doppelsitzer: telefonisch ab 2 Tage vorher.</p>
    </div>
  </div>
</section>
<section class="section section--tight">
  <div class="wrap">
    <form id="buchung" class="form" action="danke.html" method="post" autocomplete="on">
      <fieldset>
        <legend>1. Was möchtet ihr buchen?</legend>
        <div class="choice-grid">
          {choice("tickets","Ticketfahrten","10-Minuten-Fahrten, Spartage, Freitagsspecial – ab 5 Personen")}
          {choice("kidsparty","Kidsparty / Kindergeburtstag","Ab 6 Kindern, exklusiv auf der Strecke, Pakete F1 / F2")}
          {choice("supercup","Supercup / Rennen","6–17 Personen, Qualifying + Rennen, exklusiv")}
          {choice("bahnmiete","Bahnmiete / Firmenevent","Exklusive Strecke ab 10 Karts, Teamrennen, Meisterschaft")}
          {choice("schulklasse","Schulklasse","Ab 20 Personen, Mo–Fr, auch vormittags")}
          {choice("fuehrerschein","Kinderkartführerschein","Jeden 1. Samstag im Monat, 10:00 Uhr, 45 €")}
          {choice("event","Event / Flatratefahren","Plätze für Veranstaltungen wie Flatratefahren oder Nightrace")}
        </div>
      </fieldset>

      <fieldset id="step2" hidden>
        <legend>2. Datum &amp; Startzeit</legend>
        <p class="small" id="fs-note" hidden>Der Kinderkartführerschein findet jeden 1. Samstag im Monat um 10:00 Uhr statt. Bitte um 09:30 Uhr eintreffen.</p>
        <div class="fields-2">
          <div class="field"><label for="datum">Datum *</label><input type="date" id="datum" name="datum" required><span class="error"></span></div>
          <div class="field"><label for="uhrzeit-feld">Startzeit *</label><input type="hidden" name="uhrzeit" id="uhrzeit-feld"><div id="slots" class="slots" role="group" aria-label="Startzeiten"></div><span class="hint" id="slot-hint">Bitte zuerst ein Datum wählen.</span><span class="error"></span></div>
        </div>
        <p class="small">Alle Teilnehmer müssen mindestens 30 Minuten vor der Startzeit bei uns eintreffen (Registrierung, Einweisung).</p>
      </fieldset>

      <fieldset id="step3" hidden>
        <legend>3. Teilnehmer &amp; Details</legend>
        <div class="fields-2">
          <div class="field"><label for="teilnehmer">Anzahl Teilnehmer *</label><input type="number" id="teilnehmer" name="teilnehmer" min="1" max="120" inputmode="numeric" required><span class="hint" id="teil-hint"></span><span class="error"></span></div>
          <div class="field" data-for="tickets kidsparty supercup bahnmiete event"><label for="kinder">davon Kinder 8–15 Jahre</label><input type="number" id="kinder" name="kinder" min="0" max="120" inputmode="numeric" value="0"><span class="hint">Kinderkart ab 8 Jahren und 1,25 m; großes Kart ab 13 Jahren und 1,55 m.</span></div>
        </div>
        <div data-for="tickets">
          <div class="fields-2">
            <div class="field"><label for="fahrten">Fahrten pro Person *</label><select id="fahrten" name="fahrten"><option value="1">1 × 10 Minuten</option><option value="2">2 × 10 Minuten</option><option value="3" selected>3 × 10 Minuten</option><option value="4">4 × 10 Minuten</option><option value="5">5 × 10 Minuten</option></select><span class="hint">Mo–Do: 3 für 2 oder 5 für 3 wird automatisch angewendet.</span></div>
            <div class="field"><label for="kinderalter">Alter der Kinder (falls unter 13)</label><input type="text" id="kinderalter" name="kinderalter" placeholder="z. B. 9, 11, 12"></div>
          </div>
          <div class="fields-2">
            <div class="field"><label for="karterfahrung">Karterfahrung bei den Kindern?</label><select id="karterfahrung" name="karterfahrung"><option value="">bitte auswählen</option><option>Ja</option><option>Nein</option><option>Schon bei uns gefahren</option></select></div>
          </div>
        </div>
        <div data-for="kidsparty">
          <div class="fields-2">
            <div class="field"><label for="kidspaket">Paket *</label><select id="kidspaket" name="kidspaket"><option value="F1">F1 – 3 × 10 Min (40 € pro Kind)</option><option value="F2">F2 – Grand-Prix-Modus 40 Min (48 € pro Kind)</option></select></div>
            <div class="field"><label for="pizza">Pizzapakete (10,50 € je Stück)</label><input type="number" id="pizza" name="pizza" min="0" max="60" value="0" inputmode="numeric"><span class="hint">Nach der letzten Fahrt. Gern auch weniger Pakete als Kinder.</span></div>
          </div>
          <div class="fields-2">
            <div class="field"><label for="erw1620">Mitfahrende Erwachsene 16–20 J. (+5 €)</label><input type="number" id="erw1620" name="erw1620" min="0" max="30" value="0" inputmode="numeric"></div>
            <div class="field"><label for="erw21">Mitfahrende Erwachsene ab 21 J. (+7,50 €)</label><input type="number" id="erw21" name="erw21" min="0" max="30" value="0" inputmode="numeric"></div>
          </div>
          <p class="small">Bitte die <a href="downloads/haftungsausschluss-minderjaehrige.pdf" target="_blank" rel="noopener">Einverständniserklärung der Eltern</a> für jedes Kind mitbringen. Eigene Speisen, Kuchen und Getränke sind nicht gestattet – der Partytisch ist gedeckt.</p>
        </div>
        <div data-for="supercup">
          <div class="fields-2">
            <div class="field"><label for="supercup">Supercup-Paket *</label><select id="supercup" name="supercup"><option value="standard">Standard – 10 Min Quali + 20 Min Rennen (39 €)</option><option value="professional">Professional – 10 + 30 Min (49 €)</option><option value="premium">Premium – 10 + 40 Min (59 €)</option><option value="double_premium">Double Premium – 10 + 2 × 20 Min (59 €)</option><option value="double_ultra">Double Ultra – 10 + 2 × 30 Min (75 €)</option><option value="gp">Grand Prix – Training, Quali, 20 Min Rennen (49 €)</option><option value="gp_premium">Grand Prix Premium – Training, Quali, 30 Min Rennen (59 €)</option></select></div>
            <div class="field"><label for="pause">Pause nach dem Qualifying?</label><select id="pause" name="pause"><option value="nein">Nein, direkt weiter</option><option value="ja">Ja, 15–25 Minuten Pause</option></select></div>
          </div>
        </div>
        <div data-for="bahnmiete">
          <div class="fields-2">
            <div class="field"><label for="stunden">Mietdauer *</label><select id="stunden" name="stunden"><option value="1">1 Stunde</option><option value="1.5">1,5 Stunden</option><option value="2">2 Stunden</option><option value="2.5">2,5 Stunden</option><option value="3">3 Stunden</option><option value="4">4 Stunden</option></select></div>
            <div class="field"><label for="karts">Anzahl Karts (10–16) *</label><input type="number" id="karts" name="karts" min="10" max="16" value="10" inputmode="numeric"><span class="hint">Weitere Karts auch spontan vor Ort buchbar.</span></div>
          </div>
          <div class="field"><label for="firma">Firma / Verein</label><input type="text" id="firma" name="firma" autocomplete="organization"></div>
        </div>
        <div data-for="schulklasse">
          <div class="fields-2">
            <div class="field"><label for="schulangebot">Angebot *</label><select id="schulangebot" name="schulangebot"><option value="a1">Angebot 1 – 20 Min Fahrzeit (20 €)</option><option value="a2">Angebot 2 – 30 Min Fahrzeit + Getränk (25 €)</option></select></div>
            <div class="field"><label for="schule">Schule / Klasse</label><input type="text" id="schule" name="firma" autocomplete="organization" placeholder="z. B. Gymnasium Ernestinum, 9b"></div>
          </div>
        </div>
        <div data-for="event">
          <div class="field"><label for="eventname">Veranstaltung *</label><input type="text" id="eventname" name="eventname" placeholder="z. B. Flatratefahren 30.10.2026"></div>
        </div>
        <div class="field"><label for="nachricht">Wünsche &amp; Hinweise</label><textarea id="nachricht" name="nachricht" placeholder="z. B. Siegerehrung mit Pokalen, Buffet, besondere Wünsche, Wunschuhrzeit falls keine Startzeiten angezeigt werden"></textarea></div>
        <div class="summary" id="summary" hidden>
          <h3 style="margin:0 0 .6rem">Eure Zusammenfassung</h3>
          <dl><dt>Angebot</dt><dd id="sum-angebot"></dd><dt>Termin</dt><dd id="sum-datum"></dd><dt>Teilnehmer</dt><dd id="sum-teil"></dd></dl>
          <ul id="sum-lines" class="hours" style="margin-top:.6rem"></ul>
          <div class="sum"><span>Voraussichtlicher Preis</span><span id="sum-total"></span></div>
          <p class="small" id="sum-note" style="margin:.5rem 0 0"></p>
          <p class="small" style="margin:.3rem 0 0">Unverbindliche Berechnung laut Preisliste. Bezahlung vor Ort. Neukunden: Registrierung 2 € und Sturmhaube 3 € (entfallen bei Kidsparty und Bahnmiete).</p>
        </div>
      </fieldset>

      <fieldset id="step4" hidden>
        <legend>4. Kontaktdaten</legend>
        <div class="fields-2">
          <div class="field"><label for="vorname">Vorname *</label><input type="text" id="vorname" name="vorname" autocomplete="given-name" required><span class="error"></span></div>
          <div class="field"><label for="nachname">Nachname *</label><input type="text" id="nachname" name="nachname" autocomplete="family-name" required><span class="error"></span></div>
        </div>
        <div class="fields-2">
          <div class="field"><label for="telefon">Mobilnummer *</label><input type="tel" id="telefon" name="telefon" autocomplete="tel" inputmode="tel" required><span class="hint">Für Rückfragen am Veranstaltungstag.</span><span class="error"></span></div>
          <div class="field"><label for="email">E-Mail *</label><input type="email" id="email" name="email" autocomplete="email" inputmode="email" required><span class="hint">Dorthin senden wir die Bestätigung.</span><span class="error"></span></div>
        </div>
        <div class="field hp" aria-hidden="true"><label for="website">Website</label><input type="text" id="website" name="website" tabindex="-1" autocomplete="off"></div>
        <div class="field field--check"><input type="checkbox" id="agb" name="agb" value="ja" required><label for="agb">Ich habe die <a href="agb.html">AGB</a> gelesen und akzeptiere sie. Mir ist bekannt, dass alle Teilnehmer 30 Minuten vor Startzeit eintreffen und minderjährige Teilnehmer eine <a href="downloads/haftungsausschluss-minderjaehrige.pdf" target="_blank" rel="noopener">Einverständniserklärung</a> benötigen. *</label><span class="error"></span></div>
        <div class="field field--check"><input type="checkbox" id="einwilligung" name="einwilligung" value="ja" required><label for="einwilligung">Ich bin damit einverstanden, dass meine Angaben zur Bearbeitung der Buchung gespeichert und verarbeitet werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>. *</label><span class="error"></span></div>
        <div class="form-status" role="alert" aria-live="polite"></div>
        {fallback_box("Online-Buchung gerade nicht möglich? Reserviert direkt bei uns:")}
        <button class="btn btn--primary btn--block" type="submit" style="margin-top:1rem">Buchungsanfrage senden</button>
        <p class="small center" style="margin-top:.6rem">* Pflichtfelder · Keine Zahlung online · Eingangsbestätigung mit Vorgangsnummer per E-Mail</p>
      </fieldset>
    </form>
  </div>
</section>
''' + footer() + end('<script src="assets/js/buchen.js" defer></script>')
write("buchen.html", html)

# ---------------- GUTSCHEINE ----------------
html = head("Gutscheine & Tickets vorab | Burnout Kartbahn Celle",
 "Kart-Gutscheine für Celle online kaufen: Wertgutscheine und Fahrt-Tickets per PayPal, Gutschein per E-Mail. Das Geschenk für Rennfahrer ab 8 Jahren.",
 breadcrumb("Gutscheine","gutscheine.html") + '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Gutschein Burnout Celler-Kartbahn","description":"Wertgutschein oder Fahrt-Ticket für die Indoor-Kartbahn in Celle, per E-Mail als PDF, 3 Jahre gültig, einlösbar für alle Fahrten, Pakete und im Bistro.","brand":{"@type":"Brand","name":"Burnout Celler-Kartbahn"},"image":"/assets/img/og-image.jpg","category":"Gutschein",
"offers":[{"@type":"Offer","name":"Wertgutschein 25 €","price":"25.00","priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"/gutscheine.html","seller":{"@id":"/#kartbahn"}},{"@type":"Offer","name":"Wertgutschein 50 €","price":"50.00","priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"/gutscheine.html"},{"@type":"Offer","name":"Wertgutschein 100 €","price":"100.00","priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"/gutscheine.html"},{"@type":"Offer","name":"3 Fahrten Wochenende Erwachsene","price":"43.00","priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"/gutscheine.html"},{"@type":"Offer","name":"3 Fahrten Kids","price":"36.00","priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"/gutscheine.html"},{"@type":"Offer","name":"Supercup Premium","price":"59.00","priceCurrency":"EUR","availability":"https://schema.org/InStock","url":"/gutscheine.html"}]}</script>''') + header()

def pp(betrag, titel, desc):
    return f'''<div class="card card--accent">
      <h3>{titel}</h3><p>{desc}</p>
      <p><strong style="color:#fff;font-size:1.5rem">{betrag} €</strong></p>
      <div data-mk="paypal" data-betrag="{betrag}" data-titel="Gutschein {titel} – Burnout Celler-Kartbahn" class="mk-slot"></div>
      <a class="btn btn--ghost btn--sm" href="#bestellen">Ohne PayPal bestellen</a>
    </div>'''

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/hero-duell.webp" width="1260" height="430" alt="Kartfahrer im Rennen auf der Celler Kartbahn – das Motiv für den Gutschein" fetchpriority="high">
  <div class="wrap">
    <span class="eyebrow">Gutscheine &amp; Vorverkauf</span>
    <h1>Adrenalin verschenken</h1>
    <p class="lead">Kauft Wertgutscheine oder Fahrt-Tickets bequem vorab. Der Gutschein kommt per E-Mail und wird an der Anmeldung eingelöst – für alle ab 8 Jahren.</p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>Direkt kaufen mit PayPal</h2>
    <p class="muted">Nach der Zahlung per PayPal erhaltet ihr den Gutschein mit Gutscheincode per E-Mail von uns. Einlösbar für alle Ticketfahrten, Pakete und im Bistro. Ihr seht hier keine Schaltfläche? Dann nutzt bitte die Bestellung weiter unten.</p>
    <div class="grid grid-4">
      {pp("25,00","Wertgutschein 25 €","Zum Beispiel eine Fahrt am Wochenende plus Registrierung.")}
      {pp("50,00","Wertgutschein 50 €","Reicht für 3 Fahrten am Wochenende – oder 5 am Spartag.")}
      {pp("100,00","Wertgutschein 100 €","Für zwei Rennfahrer oder ein ganzes Supercup-Ticket plus Extras.")}
      {pp("43,00","3 Fahrten Wochenende","3 × 10 Minuten für Erwachsene (Sa/So) – der Klassiker.")}
    </div>
    <div class="grid grid-4" style="margin-top:1.25rem">
      {pp("36,00","3 Fahrten Kids","3 × 10 Minuten für Kinder 8–15 Jahre (Sa/So) im Kinderkart.")}
      {pp("45,00","Doppelsitzer 3 Fahrten","3 × 10 Minuten im Doppelsitzer für 2 Personen (Reservierung telefonisch).")}
      {pp("45,00","Kinderkartführerschein","Intensivkurs mit Lizenz, jeden 1. Samstag im Monat.")}
      {pp("59,00","Supercup Premium","Qualifying + 40 Minuten Rennen pro Person (Gruppe 6–17).")}
    </div>
    <p class="small" style="margin-top:1rem">Gutscheine sind nicht an einen Tag gebunden; Ticketpreise gelten je nach Wochentag (siehe <a href="preise.html">Preise</a>). Ein Wertgutschein wird mit dem jeweils gültigen Preis verrechnet. Für Online-Käufe gilt das <a href="widerruf.html">Widerrufsrecht</a>.</p>
  </div>
</section>

<section class="section section--alt" id="bestellen">
  <div class="wrap grid grid-2" style="align-items:start">
    <div>
      <span class="eyebrow">Individuell</span>
      <h2>Gutschein bestellen</h2>
      <p class="muted">Wunschbetrag oder bestimmtes Paket, persönlicher Text, Zahlung per Überweisung oder vor Ort. Wir senden euch die Zahlungsinfos per E-Mail und nach Zahlungseingang den Gutschein als PDF. Den Gutscheincode vergeben wir persönlich.</p>
      <ul class="checks">
        <li>Jeder Betrag ab 10 € möglich</li>
        <li>Mit Widmung – ideal zum Geburtstag, Weihnachten oder Vatertag</li>
        <li>Abholung vor Ort während der Öffnungszeiten möglich</li>
      </ul>
      <img src="assets/img/kart-detail.webp" width="1400" height="934" alt="Nahaufnahme der Startnummer eines Sodi-Karts" loading="lazy" style="border-radius:14px">
    </div>
    <form class="form" data-mk-form="gutschein" action="danke.html" method="post">
      <fieldset>
        <legend>Gutschein-Bestellung</legend>
        <div class="fields-2">
          <div class="field"><label for="g-betrag">Betrag oder Paket *</label><input type="text" id="g-betrag" name="betrag" required placeholder="z. B. 50 € oder Supercup Premium"><span class="error"></span></div>
          <div class="field"><label for="g-anzahl">Anzahl</label><input type="number" id="g-anzahl" name="anzahl" min="1" max="50" value="1" inputmode="numeric"></div>
        </div>
        <div class="field"><label for="g-fuer">Gutschein für (Name, optional)</label><input type="text" id="g-fuer" name="beschenkter"></div>
        <div class="field"><label for="g-text">Persönlicher Text</label><textarea id="g-text" name="nachricht" placeholder="z. B. Alles Gute zum 40. – Vollgas, Papa!"></textarea></div>
        <div class="field"><label for="g-zustellung">Zustellung *</label><select id="g-zustellung" name="zustellung"><option>Per E-Mail als PDF</option><option>Abholung vor Ort</option></select></div>
        <div class="fields-2">
          <div class="field"><label for="g-name">Dein Name *</label><input type="text" id="g-name" name="name" autocomplete="name" required><span class="error"></span></div>
          <div class="field"><label for="g-tel">Telefon</label><input type="tel" id="g-tel" name="telefon" autocomplete="tel" inputmode="tel"></div>
        </div>
        <div class="field"><label for="g-email">E-Mail *</label><input type="email" id="g-email" name="email" autocomplete="email" required><span class="error"></span></div>
        <div class="field hp" aria-hidden="true"><label for="g-website">Website</label><input type="text" id="g-website" name="website" tabindex="-1" autocomplete="off"></div>
        <div class="field field--check"><input type="checkbox" id="g-einw" name="einwilligung" value="ja" required><label for="g-einw">Ich bin damit einverstanden, dass meine Angaben zur Bearbeitung der Bestellung verarbeitet werden. Es gelten die <a href="agb.html">AGB</a> und das <a href="widerruf.html">Widerrufsrecht</a>. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>. *</label><span class="error"></span></div>
        <div class="form-status" role="alert" aria-live="polite"></div>
        {fallback_box("Bestellung gerade nicht möglich? Schreibt uns direkt:")}
        <button class="btn btn--primary btn--block" type="submit" style="margin-top:1rem">Zahlungspflichtig bestellen</button>
        <p class="small center" style="margin-top:.6rem">Der Vertrag kommt mit unserer Bestätigung zustande; die Zahlung erfolgt per Überweisung oder vor Ort.</p>
      </fieldset>
    </form>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("gutscheine.html", html)
