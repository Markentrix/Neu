# -*- coding: utf-8 -*-
from common import *

JSONLD = '''<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
 {"@type":["EntertainmentBusiness","SportsActivityLocation","LocalBusiness"],"@id":"/#kartbahn",
  "name":"Burnout Celler-Kartbahn","alternateName":"Celler Kartbahn","legalName":"Burnout Celler-Kartbahn GmbH",
  "description":"Indoor-Kartbahn in Celle mit ca. 600 m Strecke, Brücke, Tunnel und zweiter Ebene mit Steilkurve. Sodi-Karts mit 9 PS, Kinderkarts ab 8 Jahren, Doppelsitzer, Kindergeburtstage, Firmenevents, Bistro und Veranstaltungsraum.",
  "image":["/assets/img/og-image.jpg","/assets/img/kartflotte.webp","/assets/img/zweite-ebene.webp"],
  "logo":"/apple-touch-icon.png","url":"/",
  "telephone":"+49 5141 908650","faxNumber":"+49 5141 908652","email":"team@celler-kartbahn.com",
  "address":{"@type":"PostalAddress","streetAddress":"Waldweg 100","postalCode":"29221","addressLocality":"Celle","addressRegion":"Niedersachsen","addressCountry":"DE"},
  "geo":{"@type":"GeoCoordinates","latitude":52.6088,"longitude":10.0614},
  "hasMap":"https://www.openstreetmap.org/?mlat=52.6088&mlon=10.0614#map=17/52.6088/10.0614",
  "areaServed":["Celle","Landkreis Celle","Hannover","Lüneburg","Gifhorn","Uelzen","Niedersachsen"],
  "openingHoursSpecification":[
   {"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday"],"opens":"15:00"},
   {"@type":"OpeningHoursSpecification","dayOfWeek":"Saturday","opens":"13:00"},
   {"@type":"OpeningHoursSpecification","dayOfWeek":"Sunday","opens":"11:00"}],
  "priceRange":"€€","currenciesAccepted":"EUR","paymentAccepted":"Bar, EC-Karte","foundingDate":"2009-01","slogan":"Vollgas auf 600 Metern – mit Brücke, Tunnel und Steilkurve",
  "openingHours":["Mo-Fr 15:00-23:00","Sa 13:00-23:00","Su 11:00-23:00"],
  "contactPoint":[{"@type":"ContactPoint","contactType":"customer service","telephone":"+49 5141 908650","email":"team@celler-kartbahn.com","availableLanguage":"de","areaServed":"DE"},{"@type":"ContactPoint","contactType":"reservations","telephone":"+49 152 31394662","contactOption":"TollFree","availableLanguage":"de"}],
  "knowsAbout":["Kartfahren","Indoor-Kartbahn","Kindergeburtstag","Firmenevent","Teambuilding","Junggesellenabschied","Weihnachtsfeier","Schulausflug"],
  "hasOfferCatalog":{"@type":"OfferCatalog","name":"Angebote der Burnout Celler-Kartbahn","itemListElement":[
   {"@type":"OfferCatalog","name":"Ticketfahrten (10 Minuten, pro Person)","itemListElement":[
    {"@type":"Offer","name":"1 Fahrt Erwachsene Sa/So","price":"15.00","priceCurrency":"EUR"},{"@type":"Offer","name":"1 Fahrt Kinder 8–15 Sa/So","price":"13.50","priceCurrency":"EUR"},
    {"@type":"Offer","name":"1 Fahrt Erwachsene Freitag","price":"14.00","priceCurrency":"EUR"},{"@type":"Offer","name":"1 Fahrt Kinder Freitag","price":"12.00","priceCurrency":"EUR"},
    {"@type":"Offer","name":"Spartag Mo–Do: 3 Fahrten für 2, Erwachsene","price":"30.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Spartag Mo–Do: 5 Fahrten für 3, Erwachsene","price":"43.00","priceCurrency":"EUR"},
    {"@type":"Offer","name":"Doppelsitzer 1 Fahrt (2 Personen)","price":"18.00","priceCurrency":"EUR"}]},
   {"@type":"OfferCatalog","name":"Kindergeburtstag (pro Kind, ab 6 Kindern)","itemListElement":[
    {"@type":"Offer","name":"Kidsparty F1 – 3 × 10 Minuten","price":"40.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Kidsparty F2 – Grand-Prix-Modus 40 Minuten","price":"48.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Pizzapaket","price":"10.50","priceCurrency":"EUR"}]},
   {"@type":"OfferCatalog","name":"Gruppen & Firmen","itemListElement":[
    {"@type":"Offer","name":"Supercup Standard (6–17 Personen, p.P.)","price":"39.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Supercup Premium (p.P.)","price":"59.00","priceCurrency":"EUR"},
    {"@type":"Offer","name":"Bahnmiete 1 Stunde inkl. 10 Karts","price":"650.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Schulklasse Angebot 1 (p.P., ab 20)","price":"20.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Kinderkartführerschein","price":"45.00","priceCurrency":"EUR"}]}]},
  "sameAs":["https://www.facebook.com/BurnoutCellerKartbahn/"],
  "amenityFeature":[{"@type":"LocationFeatureSpecification","name":"Bistro","value":true},{"@type":"LocationFeatureSpecification","name":"Veranstaltungsraum bis 80 Personen","value":true},{"@type":"LocationFeatureSpecification","name":"Terrasse","value":true},{"@type":"LocationFeatureSpecification","name":"Kinderkarts","value":true},{"@type":"LocationFeatureSpecification","name":"Doppelsitzer-Kart","value":true}],
  "makesOffer":[
   {"@type":"Offer","name":"Ticketfahrt 10 Minuten (Erwachsene, Sa/So)","price":"15.00","priceCurrency":"EUR","url":"/preise.html"},
   {"@type":"Offer","name":"Kidsparty F1 – 3 × 10 Minuten","price":"40.00","priceCurrency":"EUR","url":"/kinder.html"},
   {"@type":"Offer","name":"Supercup Standard – Qualifying + 20 Min Rennen","price":"39.00","priceCurrency":"EUR","url":"/firmen.html"},
   {"@type":"Offer","name":"Bahnmiete 1 Stunde inkl. 10 Karts","price":"650.00","priceCurrency":"EUR","url":"/firmen.html"}]
 },
 {"@type":"WebSite","name":"Burnout Celler-Kartbahn","url":"/","inLanguage":"de-DE","publisher":{"@id":"/#kartbahn"}},
 {"@type":"Event","name":"Flatratefahren Oktober 2026","startDate":"2026-10-30T19:00:00+01:00","eventStatus":"https://schema.org/EventScheduled","eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode",
  "location":{"@type":"Place","name":"Burnout Celler-Kartbahn","address":{"@type":"PostalAddress","streetAddress":"Waldweg 100","postalCode":"29221","addressLocality":"Celle","addressCountry":"DE"}},
  "description":"Flatratefahren in 3 Gruppen mit 12-Minuten-Durchgängen im Wechsel. Ab 22 Uhr Discolicht und Nebel auf der Strecke.","organizer":{"@id":"/#kartbahn"},"offers":{"@type":"Offer","url":"/buchen.html?angebot=event","availability":"https://schema.org/InStock"}}
]}
</script>'''

html = head("Burnout Celler-Kartbahn – Indoor-Kartbahn in Celle",
 "Indoor-Kartbahn in Celle: 600 m Strecke mit Brücke, Tunnel und Steilkurve, 9-PS-Sodi-Karts, Kinderkarts ab 8 Jahren. Online buchen, Kindergeburtstage, Firmenevents, Gutscheine.",
 JSONLD) + header()

html += f'''
<section class="hero">
  <img class="hero__img" src="assets/img/hero-rennen.webp" width="1260" height="430" alt="Zwei Sodi-Karts im Duell auf der Indoor-Kartbahn Burnout in Celle" fetchpriority="high">
  <div class="wrap">
    <span class="eyebrow">Indoor-Kartbahn · Celle</span>
    <h1>Vollgas auf 600 Metern – mit Brücke, Tunnel und Steilkurve</h1>
    <p class="lead">Die Burnout Celler-Kartbahn ist die Indoor-Kartbahn für Celle, Hannover und die Region: 9-PS-Sodi-Karts, Kinderkarts ab 8 Jahren, zweite Ebene mit Steilkurve in 6 Metern Höhe. Jetzt Fahrten online reservieren oder Gutschein sichern.</p>
    <div class="hero__actions">
      <a class="btn btn--primary" href="buchen.html">{ICONS["cal"]}Jetzt online buchen</a>
      <a class="btn btn--light" href="gutscheine.html">{ICONS["gift"]}Gutscheine &amp; Tickets</a>
      <a class="btn btn--ghost" href="preise.html">Preise ansehen</a>
    </div>
    <ul class="hero__facts">
      <li>{ICONS["ruler"]}ca. 600 m Strecke</li>
      <li>{ICONS["speed"]}9 PS Sodi SR5</li>
      <li>{ICONS["kids"]}Kinder ab 8 Jahren</li>
      <li>{ICONS["clock"]}Mo–Fr ab 15 Uhr · Sa ab 13 · So ab 11</li>
    </ul>
  </div>
</section>

<section class="section section--tight" id="fakten">
  <div class="wrap">
    <h2 class="sr-only">Auf einen Blick</h2>
    <dl class="facts">
      <div><dt>Adresse</dt><dd>Burnout Celler-Kartbahn GmbH, Waldweg 100, 29221 Celle (Niedersachsen)</dd></div>
      <div><dt>Öffnungszeiten</dt><dd>Mo–Fr ab 15 Uhr (Ferien ab 13 Uhr), Sa ab 13 Uhr, So ab 11 Uhr – Open End</dd></div>
      <div><dt>Preise</dt><dd>10-Minuten-Fahrt ab 12 € (Kids) bzw. 14 € (Erwachsene), Kidsparty ab 40 € pro Kind, Supercup ab 39 € p.P.</dd></div>
      <div><dt>Alter</dt><dd>Kinderkart ab 8 Jahren und 1,25 m, Rennkart ab 13 Jahren und 1,55 m, Doppelsitzer-Beifahrer ab 4 Jahren</dd></div>
      <div><dt>Strecke</dt><dd>ca. 600 m indoor mit Brücke, Tunnel und Steilkurve in 6 m Höhe, Sodi SR5 mit 9 PS, 13 Kinderkarts</dd></div>
      <div><dt>Kontakt</dt><dd><a href="{TEL_LINK}">05141 908650</a>, <a href="mailto:{MAIL}">{MAIL}</a>, WhatsApp +49 152 31394662</dd></div>
    </dl>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2 class="sr-only">Unsere Angebote</h2>
    <div class="grid grid-4">
      <a class="card card--link" href="buchen.html?angebot=tickets"><div class="card__icon">{ICONS["ticket"]}</div><h3>Ticketfahrten</h3><p>10-Minuten-Fahrten für Erwachsene und Kids, Spartage Mo–Do, Freitagsspecial. Ab 5 Personen online reservieren.</p><span class="more">Fahrten buchen →</span></a>
      <a class="card card--link" href="kinder.html"><div class="card__icon">{ICONS["kids"]}</div><h3>Kindergeburtstage</h3><p>Kidsparty ab 6 Kindern, exklusiv auf der Strecke, Partytisch inklusive. Pakete ab 40 € pro Kind.</p><span class="more">Kidsparty planen →</span></a>
      <a class="card card--link" href="firmen.html"><div class="card__icon">{ICONS["building"]}</div><h3>Firmen &amp; Gruppen</h3><p>Supercup-Rennen für 6–17 Personen, Bahnmiete und Meisterschaftsmodus für bis zu 80 Gäste – mit Buffet im Clubraum.</p><span class="more">Event anfragen →</span></a>
      <a class="card card--link" href="gutscheine.html"><div class="card__icon">{ICONS["gift"]}</div><h3>Gutscheine</h3><p>Das Geschenk für Adrenalin-Fans: Wertgutscheine und Fahrt-Tickets vorab online kaufen und per E-Mail erhalten.</p><span class="more">Gutschein kaufen →</span></a>
    </div>
  </div>
</section>

<section class="section section--alt">
  <div class="wrap split">
    <img src="assets/img/zweite-ebene.webp" width="1600" height="595" alt="Die zweite Ebene der Celler Kartbahn mit Rampe und Steilkurve in sechs Metern Höhe" loading="lazy" decoding="async">
    <div>
      <span class="eyebrow">Neu: 2. Ebene</span>
      <h2>Bist du bereit für das nächste Level?</h2>
      <p>100 Meter mehr Strecke: Vollgas die Rampe hoch, die Steilkurve in 6 Metern Höhe meistern und mit Rückenwind bergab. Mit Brücke, Tunnel und neuer Zuschauerplattform ist die Strecke in Norddeutschland einzigartig.</p>
      <ul class="checks">
        <li>ca. 600 m Streckenlänge inkl. Brücke, Tunnel und Steilkurve</li>
        <li>Neue Kartflotte Sodi SR5 mit 9 PS (seit 09/2023)</li>
        <li>13 Kinderkarts Sodi LR6 und 2 Doppelsitzer</li>
        <li>Live-Zeiten auf der Großbildleinwand und in der App</li>
      </ul>
      <p class="small">Kidskonzept: Für Kinder von 8–12 Jahren ohne Karterfahrung wird die zweite Ebene umfahren. Bei Kindergeburtstagen entscheidet das Streckenpersonal je nach Fahrkönnen.</p>
      <a class="btn btn--ghost" href="kartbahn.html">Strecke &amp; Karts entdecken</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid grid-2" style="align-items:start">
      <div>
        <span class="eyebrow">Preise</span>
        <h2>Fahrspaß ab 12 €</h2>
        <p class="muted">Alle Preise pro Person und 10-Minuten-Fahrt. Kinder 8–15 Jahre (ab 1,25 m), Erwachsene ab 16 Jahren. Tickets sind nicht übertragbar und werden am Kauftag gefahren.</p>
        <div class="table-wrap">
          <table>
            <caption>Ticketfahrten im Überblick</caption>
            <thead><tr><th>Tag</th><th>Angebot</th><th class="price">Erw.</th><th class="price">Kids</th></tr></thead>
            <tbody>
              <tr><td>Mo–Do</td><td>Spartage: 3 Fahrten für 2</td><td class="price">30 €</td><td class="price">27 €</td></tr>
              <tr><td>Mo–Do</td><td>Spartage: 5 Fahrten für 3</td><td class="price">43 €</td><td class="price">36 €</td></tr>
              <tr><td>Freitag</td><td>1 Fahrt (je öfter, desto günstiger)</td><td class="price">14 €</td><td class="price">12 €</td></tr>
              <tr><td>Sa/So</td><td>1 Fahrt</td><td class="price">15 €</td><td class="price">13,50 €</td></tr>
              <tr><td>Sa/So</td><td>3 Fahrten</td><td class="price">43 €</td><td class="price">36 €</td></tr>
            </tbody>
          </table>
          <p class="price-hint">Neukunden: einmalige Registrierung inkl. Rennlizenz 2 €, Sturmhaube inkl. Helmleihe 3 € (Paket 4 €).</p>
        </div>
        <p style="margin-top:1rem"><a class="btn btn--ghost" href="preise.html">Alle Preise &amp; Pakete</a></p>
      </div>
      <div>
        <span class="eyebrow">Öffnungszeiten</span>
        <h2>Wann ihr fahren könnt</h2>
        <div class="card">
          <h3>Normal</h3>
          <ul class="hours">
            <li><span>Montag – Freitag</span><span>15:00 – Open End</span></li>
            <li><span>Samstag</span><span>13:00 – Open End</span></li>
            <li><span>Sonntag</span><span>11:00 – Open End</span></li>
          </ul>
          <h3 style="margin-top:1rem">Niedersächsische Schulferien</h3>
          <ul class="hours">
            <li><span>Montag – Freitag</span><span>13:00 – Open End</span></li>
            <li><span>Samstag</span><span>13:00 – Open End</span></li>
            <li><span>Sonntag</span><span>11:00 – Open End</span></li>
          </ul>
          <p class="small" style="margin-top:.8rem">Open End heißt: Wir schließen je nach Auslastung (unter der Woche z.&nbsp;B. gegen 21 Uhr). Vor einem spontanen Besuch bitte kurz anrufen: <a href="{TEL_LINK}">{TEL}</a>.</p>
        </div>
        <div class="notice" style="margin-top:1rem">
          <p><strong>Reservierung:</strong> Unter 5 Personen telefonisch ab 2 Tage vorher. Ab 5 Personen weit im Voraus online – kurzfristig (innerhalb 3 Tagen) bitte telefonisch.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section--alt">
  <div class="wrap">
    <span class="eyebrow">Aktuell</span>
    <h2>News &amp; Events</h2>
    <div class="grid grid-3">
      <article class="news">
        <time datetime="2026-10-30">Freitag, 30.10.2026</time>
        <h3>Flatratefahren Oktober 2026</h3>
        <p class="muted">Unser beliebtes Flatratefahren: gefahren wird in 3 Gruppen in 12-Minuten-Durchgängen im Wechsel. Ab 22 Uhr gehen die Lichter aus – Discobeleuchtung und Nebel an!</p>
        <a class="btn btn--primary btn--sm" href="buchen.html?angebot=event">Platz sichern</a>
      </article>
      <article class="news">
        <time datetime="2026-12">Weihnachtsfeiern 2026</time>
        <h3>Firmen, Vereine &amp; Gruppen</h3>
        <p class="muted">Von 6 bis ca. 80 Personen: Supercup bis 17 Teilnehmer, Rennpakete und Meisterschaftsmodus ab 18. Danach Buffet im festlich dekorierten Clubraum.</p>
        <a class="btn btn--ghost btn--sm" href="firmen.html">Pakete ansehen</a>
      </article>
      <article class="news">
        <time>Neu</time>
        <h3>RaceCam – dein Rennen auf Video</h3>
        <p class="muted">Für kleines Geld bekommt ihr euer Rennen direkt nach der Fahrt per QR-Code aufs Smartphone. 1 Durchgang 5 €, 2 Durchgänge 9 €, 3 Durchgänge 12 €. Erhältlich beim Check-in.</p>
        <a class="btn btn--ghost btn--sm" href="kartbahn.html#racecam">Mehr erfahren</a>
      </article>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split split--rev">
    <img src="assets/img/bistro-theke.webp" width="1400" height="934" alt="Bistro-Theke der Celler Kartbahn mit Livemonitoren und roter Beleuchtung" loading="lazy" decoding="async">
    <div>
      <span class="eyebrow">Erst Kart, dann Dart?</span>
      <h2>Bistro, Clubraum &amp; Dartraum</h2>
      <p>Im Bistro verfolgt ihr den Rennablauf auf Livemonitoren – mit Erfrischungen, Snacks und bei Sonne auf der Terrasse. Der Veranstaltungsraum bietet bis zu 80 Personen Platz und steht bei Buffetbestellung kostenfrei zur Verfügung.</p>
      <p>Für die perfekte Firmenveranstaltung: erst Kartfahren, dann Darten im <a href="https://www.dartraum-celle.de" rel="noopener" target="_blank">Dartraum Celle</a>, dazu ein deftiges Buffet.</p>
      <a class="btn btn--ghost" href="firmen.html#buffet">Buffet &amp; Clubraum</a>
    </div>
  </div>
</section>

<section class="section section--alt">
  <div class="wrap">
    <span class="eyebrow">Bewertungen</span>
    <h2>Das sagen unsere Gäste</h2>
    <div data-mk="bewertungen" class="mk-slot"></div>
    <p class="small">Ihr wart bei uns? Wir freuen uns über eure Bewertung bei Google – und über Feedback direkt per <a href="{WA_LINK}" rel="noopener" target="_blank">WhatsApp</a>.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid grid-2">
      <div>
        <span class="eyebrow">Anfahrt</span>
        <h2>Mitten in Celle, gut erreichbar</h2>
        <address style="font-style:normal">
          <strong>Burnout Celler-Kartbahn GmbH</strong><br>Waldweg 100<br>29221 Celle
        </address>
        <ul class="checks">
          <li>Vom Bahnhof Celle in max. 20 Minuten zu Fuß</li>
          <li>Kostenlose Parkplätze direkt am Haus</li>
          <li>Aus Hannover, Lüneburg, Gifhorn und Uelzen gut erreichbar</li>
        </ul>
        <div class="pill-row">
          <a class="btn btn--primary btn--sm" href="https://www.google.com/maps/dir/?api=1&amp;destination=Waldweg+100,+29221+Celle" rel="noopener" target="_blank">Route planen (Google Maps)</a>
          <a class="btn btn--ghost btn--sm" href="kontakt.html">Kontakt &amp; Karte</a>
        </div>
      </div>
      <div class="map" data-map="https://www.openstreetmap.org/export/embed.html?bbox=10.0514%2C52.6038%2C10.0714%2C52.6138&amp;layer=mapnik&amp;marker=52.6088%2C10.0614">
        <div class="map__consent">
          <strong>Karte anzeigen</strong>
          <p>Mit Klick wird die Karte von OpenStreetMap geladen. Dabei werden Daten (z.&nbsp;B. eure IP-Adresse) an die OpenStreetMap Foundation übertragen. Details in der <a href="datenschutz.html#karte">Datenschutzerklärung</a>.</p>
          <button class="btn btn--primary btn--sm" type="button">Karte laden</button>
        </div>
      </div>
    </div>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("index.html", html)
