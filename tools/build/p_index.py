# -*- coding: utf-8 -*-
from common import *

JSONLD = '''<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
 {"@type":["EntertainmentBusiness","SportsActivityLocation","LocalBusiness"],"@id":"{{SITE_URL}}/#kartbahn",
  "name":"Burnout Celler-Kartbahn","alternateName":"Celler Kartbahn","legalName":"Burnout Celler-Kartbahn GmbH",
  "description":"Indoor-Kartbahn in Celle mit ca. 600 m Strecke, Brücke, Tunnel und zweiter Ebene mit Steilkurve in 6 m Höhe. Sodi-Karts mit 9 PS, 13 Kinderkarts ab 8 Jahren, 2 Doppelsitzer, Kindergeburtstage, Firmenevents, Bistro und Veranstaltungsraum.",
  "image":["{{SITE_URL}}/assets/img/og-image.jpg","{{SITE_URL}}/assets/img/strecke-start.webp","{{SITE_URL}}/assets/img/zweite-ebene.webp"],
  "logo":{"@type":"ImageObject","url":"{{SITE_URL}}/assets/img/logo.png","width":329,"height":105},"url":"{{SITE_URL}}/",
  "telephone":"+49 5141 908650","faxNumber":"+49 5141 908652","email":"team@celler-kartbahn.com",
  "address":{"@type":"PostalAddress","streetAddress":"Waldweg 100","postalCode":"29221","addressLocality":"Celle","addressRegion":"Niedersachsen","addressCountry":"DE"},
  "geo":{"@type":"GeoCoordinates","latitude":52.6088,"longitude":10.0614},
  "hasMap":"https://www.openstreetmap.org/?mlat=52.6088&mlon=10.0614#map=17/52.6088/10.0614",
  "areaServed":["Celle","Landkreis Celle","Hannover","Lüneburg","Gifhorn","Uelzen"],
  "openingHoursSpecification":[
   {"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday"],"opens":"15:00"},
   {"@type":"OpeningHoursSpecification","dayOfWeek":"Saturday","opens":"13:00"},
   {"@type":"OpeningHoursSpecification","dayOfWeek":"Sunday","opens":"11:00"}],
  "priceRange":"€€","currenciesAccepted":"EUR","paymentAccepted":"Bar, EC-Karte","foundingDate":"2009-01",
  "contactPoint":[{"@type":"ContactPoint","contactType":"customer service","telephone":"+49 5141 908650","email":"team@celler-kartbahn.com","availableLanguage":"de","areaServed":"DE"},{"@type":"ContactPoint","contactType":"reservations","telephone":"+49 152 31394662","availableLanguage":"de"}],
  "knowsAbout":["Kartfahren","Indoor-Kartbahn","Kindergeburtstag","Firmenevent","Teambuilding","Junggesellenabschied","Weihnachtsfeier","Schulausflug"],
  "sameAs":["https://www.facebook.com/BurnoutCellerKartbahn/"],
  "amenityFeature":[{"@type":"LocationFeatureSpecification","name":"Bistro","value":true},{"@type":"LocationFeatureSpecification","name":"Veranstaltungsraum bis 80 Personen","value":true},{"@type":"LocationFeatureSpecification","name":"Terrasse","value":true},{"@type":"LocationFeatureSpecification","name":"Kinderkarts","value":true},{"@type":"LocationFeatureSpecification","name":"Doppelsitzer-Kart","value":true}],
  "hasOfferCatalog":{"@type":"OfferCatalog","name":"Angebote der Burnout Celler-Kartbahn","itemListElement":[
   {"@type":"OfferCatalog","name":"Ticketfahrten (10 Minuten, pro Person)","itemListElement":[
    {"@type":"Offer","name":"1 Fahrt Erwachsene Sa/So","price":"15.00","priceCurrency":"EUR"},{"@type":"Offer","name":"1 Fahrt Kinder 8–15 Sa/So","price":"13.50","priceCurrency":"EUR"},
    {"@type":"Offer","name":"1 Fahrt Erwachsene Freitag","price":"14.00","priceCurrency":"EUR"},{"@type":"Offer","name":"1 Fahrt Kinder Freitag","price":"12.00","priceCurrency":"EUR"},
    {"@type":"Offer","name":"Spartag Mo–Do: 3 Fahrten für 2, Erwachsene","price":"30.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Spartag Mo–Do: 5 Fahrten für 3, Erwachsene","price":"43.00","priceCurrency":"EUR"},
    {"@type":"Offer","name":"Doppelsitzer 1 Fahrt (2 Personen)","price":"18.00","priceCurrency":"EUR"}]},
   {"@type":"OfferCatalog","name":"Kindergeburtstag (pro Kind, ab 6 Kindern)","itemListElement":[
    {"@type":"Offer","name":"Kidsparty F1 – 3 × 10 Minuten","price":"40.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Kidsparty F2 – Grand-Prix-Modus 40 Minuten","price":"48.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Pizzapaket","price":"10.50","priceCurrency":"EUR"}]},
   {"@type":"OfferCatalog","name":"Gruppen und Firmen","itemListElement":[
    {"@type":"Offer","name":"Supercup Standard (6–17 Personen, p.P.)","price":"39.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Supercup Premium (p.P.)","price":"59.00","priceCurrency":"EUR"},
    {"@type":"Offer","name":"Bahnmiete 1 Stunde inkl. 10 Karts","price":"650.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Schulklasse Angebot 1 (p.P., ab 20)","price":"20.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Kinderkartführerschein","price":"45.00","priceCurrency":"EUR"}]}]}
 },
 {"@type":"WebSite","name":"Burnout Celler-Kartbahn","url":"{{SITE_URL}}/","inLanguage":"de-DE","publisher":{"@id":"{{SITE_URL}}/#kartbahn"}}
]}
</script>'''

html = head("Indoor-Kartbahn in Celle | Burnout Celler-Kartbahn",
 "Indoor-Kartbahn in Celle: 600 m Strecke mit Brücke, Tunnel und Steilkurve in 6 m Höhe, Sodi-Karts mit 9 PS, Kinderkarts ab 8 Jahren. Fahrten online reservieren, Kidsparty, Firmenevents, Gutscheine.",
 JSONLD) + header()

html += f'''
<section class="hero">
  <img class="hero__img" src="assets/img/strecke-start.webp" width="1400" height="934" alt="Startaufstellung der Sodi-Karts vor der Rennleitung in der Halle der Burnout Celler-Kartbahn" fetchpriority="high">
  <div class="wrap">
    <div>
      <p class="etikett" data-open-status><span class="dot"></span><span>Celle, Waldweg 100</span><span aria-hidden="true">·</span><span data-text>Mo–Fr ab 15 Uhr, Sa ab 13, So ab 11</span></p>
      <h1>600 Meter Vollgas in Celle</h1>
      <p class="lead">Indoor-Kartbahn mit Brücke, Tunnel und Steilkurve in 6 Metern Höhe. 9-PS-Sodi-Karts für Erwachsene, 13 Kinderkarts ab 8 Jahren. Ab 5 Personen reserviert ihr eure Fahrten online, bezahlt wird vor Ort.</p>
      <div class="hero__actions">
        <a class="btn btn--primary" href="buchen.html">{ICONS["cal"]}Fahrten reservieren</a>
        <a class="link" href="preise.html">Preise ab 12 € ansehen</a>
      </div>
    </div>
    <a class="vorschau" href="kartbahn.html#strecke">
      <img src="assets/img/zweite-ebene.webp" width="1600" height="595" alt="Die zweite Ebene mit Rampe und Steilkurve" loading="lazy" decoding="async">
      <span class="vorschau__body"><small>Neu seit 2023</small><strong>Die 2. Ebene</strong><span>100 Meter mehr Strecke, Rampe hoch, Steilkurve in 6 Metern Höhe, Zuschauerplattform.</span></span>
    </a>
  </div>
  <div class="hero__bar">
    <div class="wrap">
      <ul>
        <li>{ICONS["flag"]}Familienbetrieb seit 2009</li>
        <li>{ICONS["ruler"]}ca. 600 m Strecke</li>
        <li>{ICONS["speed"]}Sodi SR5 mit 9 PS</li>
      </ul>
      <ul>
        <li><a href="{WA_LINK}" rel="noopener" target="_blank">{ICONS["wa"]}WhatsApp</a></li>
        <li><a href="https://www.facebook.com/BurnoutCellerKartbahn/" rel="noopener" target="_blank">Facebook</a></li>
      </ul>
    </div>
  </div>
</section>

<section class="section" id="angebote">
  <div class="wrap">
    <h2>Startliste: Was ihr bei uns fahren könnt</h2>
    <p class="lead">Von der 10-Minuten-Fahrt bis zur exklusiven Bahnmiete für 80 Gäste. Alle Preise pro Person, bezahlt wird vor Ort in bar oder mit EC-Karte.</p>
    <table class="startliste">
      <thead><tr><th scope="col">Angebot</th><th scope="col">Für wen</th><th scope="col" class="preis">Preis</th><th scope="col"><span class="sr-only">Aktion</span></th></tr></thead>
      <tbody>
        <tr><td class="name"><a href="preise.html#tickets">Ticketfahrten</a><small>10 Minuten pro Fahrt. Mo–Do 3 Fahrten zum Preis von 2, freitags Special, Sa/So Normalpreis.</small></td><td class="fuer">Ab 8 Jahren und 1,25 m. Spontan oder ab 5 Personen online.</td><td class="preis">ab 12 €<small>Kids, pro Fahrt</small></td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=tickets">Reservieren</a></td></tr>
        <tr><td class="name"><a href="kinder.html">Kidsparty</a><small>Kindergeburtstag exklusiv auf der Strecke, Partytisch, Geschenk, Siegerehrung auf dem Podest.</small></td><td class="fuer">Ab 6 Kindern, 8–15 Jahre.</td><td class="preis">40 €<small>pro Kind, 3 × 10 Min</small></td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=kidsparty">Kidsparty buchen</a></td></tr>
        <tr><td class="name"><a href="firmen.html#supercup">Supercup</a><small>Qualifying, Ampelstart, Rennen mit Auswertung. Eure Gruppe ist allein auf der Bahn.</small></td><td class="fuer">6 bis 17 Personen. Firmen, Vereine, JGA.</td><td class="preis">39 €<small>pro Person, Standard</small></td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=supercup">Rennen buchen</a></td></tr>
        <tr><td class="name"><a href="firmen.html#meisterschaft">Bahnmiete</a><small>Strecke exklusiv, Teamrennen oder Meisterschaftsmodus, danach Buffet im Clubraum.</small></td><td class="fuer">Ab 18 Personen bis ca. 80 Gäste.</td><td class="preis">650 €<small>pro Stunde, 10 Karts</small></td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=bahnmiete">Event anfragen</a></td></tr>
        <tr><td class="name"><a href="gutscheine.html">Gutscheine</a><small>Wertgutschein oder Fahrten vorab kaufen, kommt per E-Mail, wird an der Anmeldung eingelöst.</small></td><td class="fuer">Für alle ab 8 Jahren. Zum Verschenken.</td><td class="preis">ab 25 €<small>Wertgutschein</small></td><td class="aktion"><a class="btn btn--primary btn--sm" href="gutscheine.html">Gutschein kaufen</a></td></tr>
      </tbody>
    </table>
    <p class="small" style="margin-top:1rem">Unter 5 Personen reserviert ihr telefonisch ab 2 Tage vorher, Doppelsitzer ebenfalls telefonisch: <a href="{TEL_LINK}">{TEL}</a>.</p>
  </div>
</section>

<section class="ebene" id="ebene" aria-labelledby="ebene-h">
  <img src="assets/img/zweite-ebene.webp" width="1600" height="595" alt="Rampe und Steilkurve der zweiten Ebene in der Halle" loading="lazy" decoding="async">
  <div class="ebene__text">
    <div class="wrap">
      <p class="hoehe">+6 m<small>Steilkurve der 2. Ebene, seit 2023</small></p>
      <div>
        <h2 id="ebene-h">Rampe, Steilkurve, Rückenwind</h2>
        <p>100 Meter mehr Strecke auf der zweiten Ebene, dazu Brücke, Tunnel und eine Zuschauerplattform. Kinder von 8 bis 12 Jahren ohne Karterfahrung fahren die verkürzte Strecke ohne die Steilkurve, das entscheidet das Streckenpersonal.</p>
        <a class="btn btn--light" href="kartbahn.html#strecke">Strecke und Karts ansehen</a>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <ul class="daten" aria-label="Streckendaten">
      <li><strong>600 m</strong><span>Streckenlänge indoor</span></li>
      <li><strong>9 PS</strong><span>Sodi SR5, seit 09/2023</span></li>
      <li><strong>13</strong><span>Kinderkarts Sodi LR6 ab 8 Jahren</span></li>
      <li><strong>80</strong><span>Plätze im Veranstaltungsraum</span></li>
    </ul>
  </div>
</section>

<section class="section section--flaeche" id="preise-kurz">
  <div class="wrap grid grid-2" style="align-items:start">
    <div>
      <h2>Preise pro Fahrt, Tag für Tag</h2>
      <p>10 Minuten pro Fahrt. Kinder 8–15 Jahre ab 1,25 m, Erwachsene ab 16 Jahren. Tickets gelten am Kauftag und sind nicht übertragbar. Neukunden zahlen einmalig 2 € Registrierung mit Rennlizenz und 3 € für die Sturmhaube mit Helmleihe.</p>
      <div class="table-wrap">
        <table>
          <caption>Ticketfahrten</caption>
          <thead><tr><th>Tag</th><th>Angebot</th><th class="price">Erw.</th><th class="price">Kids</th></tr></thead>
          <tbody>
            <tr><td>Mo–Do</td><td>3 Fahrten zum Preis von 2</td><td class="price">30 €</td><td class="price">27 €</td></tr>
            <tr><td>Mo–Do</td><td>5 Fahrten zum Preis von 3</td><td class="price">43 €</td><td class="price">36 €</td></tr>
            <tr><td>Freitag</td><td>1 Fahrt, je öfter desto günstiger</td><td class="price">14 €</td><td class="price">12 €</td></tr>
            <tr><td>Sa/So</td><td>1 Fahrt</td><td class="price">15 €</td><td class="price">13,50 €</td></tr>
            <tr><td>Sa/So</td><td>3 Fahrten</td><td class="price">43 €</td><td class="price">36 €</td></tr>
          </tbody>
        </table>
      </div>
      <p style="margin-top:1.25rem"><a class="btn btn--primary" href="preise.html#preis-check">Preis-Check starten</a></p>
    </div>
    <div class="tafel">
      <h3>Öffnungszeiten</h3>
      <ul class="hours">
        <li><span>Montag bis Freitag</span><span>ab 15:00</span></li>
        <li><span>Mo–Fr in den Schulferien</span><span>ab 13:00</span></li>
        <li><span>Samstag</span><span>ab 13:00</span></li>
        <li><span>Sonntag</span><span>ab 11:00</span></li>
      </ul>
      <p class="small" style="margin:1rem 0 0">Open End heißt: Wir schließen je nach Auslastung, unter der Woche zum Beispiel gegen 21 Uhr. Vor einem spontanen Besuch bitte kurz anrufen: <a href="{TEL_LINK}">{TEL}</a>.</p>
      <p class="small" style="margin:.5rem 0 0">Reservierung unter 5 Personen telefonisch ab 2 Tage vorher. Ab 5 Personen online, bei Besuchen innerhalb der nächsten 3 Tage telefonisch.</p>
    </div>
  </div>
</section>

<section class="aktuell section" id="aktuell">
  <div class="wrap grid grid-2">
    <div>
      <h2>Weihnachtsfeier auf der Rennstrecke</h2>
      <p>Von 6 bis ca. 80 Personen: Supercup bis 17 Teilnehmer, Rennpakete und Meisterschaftsmodus ab 18. Danach Buffet im festlich dekorierten Clubraum, auf Wunsch weiter in den Dartraum nebenan. Dezember-Termine werden knapp.</p>
      <a class="btn btn--light" href="firmen.html">Rennpakete für Gruppen</a>
    </div>
    <div>
      <h3>Flatratefahren und Nightrace</h3>
      <p>Unsere Flatrate-Abende: drei Gruppen fahren im Wechsel 12-Minuten-Durchgänge, ab 22 Uhr mit Discolicht und Nebel. Die nächsten Termine geben wir hier und auf Facebook bekannt.</p>
      <a class="link" style="color:#fff;text-decoration-color:#fff" href="buchen.html?angebot=event">Platz für ein Event anfragen</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split split--rev">
    <img src="assets/img/bistro-theke.webp" width="1400" height="934" alt="Bistro-Theke der Celler Kartbahn mit Livemonitoren" loading="lazy" decoding="async">
    <div>
      <h2>Bistro, Clubraum, Dartraum</h2>
      <p>Im Bistro verfolgt ihr den Rennablauf auf Livemonitoren, mit Erfrischungen, Snacks und bei Sonne auf der Terrasse. Der Veranstaltungsraum bietet bis zu 80 Personen Platz und ist bei Buffetbestellung kostenfrei. Für Firmen: erst Kartfahren, dann Darten im <a href="https://www.dartraum-celle.de" rel="noopener" target="_blank">Dartraum Celle</a>.</p>
      <a class="link" href="firmen.html#buffet">Buffet und Clubraum ansehen</a>
    </div>
  </div>
</section>

<section class="section section--flaeche">
  <div class="wrap">
    <h2>Das sagen unsere Gäste</h2>
    <div data-mk="bewertungen" class="mk-slot"></div>
    <p class="small">Ihr wart bei uns? Wir freuen uns über eure Bewertung bei Google und über Feedback per <a href="{WA_LINK}" rel="noopener" target="_blank">WhatsApp</a>.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid grid-2">
    <div>
      <h2>Waldweg 100, Celle</h2>
      <p>Vom Bahnhof Celle in maximal 20 Minuten zu Fuß, kostenlose Parkplätze direkt am Haus. Aus Hannover, Lüneburg, Gifhorn und Uelzen seid ihr in unter einer Stunde bei uns.</p>
      <address style="font-style:normal;margin-bottom:1.25rem"><strong>Burnout Celler-Kartbahn GmbH</strong><br>Waldweg 100<br>29221 Celle</address>
      <div class="pill-row">
        <a class="btn btn--primary" href="https://www.google.com/maps/dir/?api=1&amp;destination=Waldweg+100,+29221+Celle" rel="noopener" target="_blank">Route planen</a>
        <a class="link" href="kontakt.html">Kontakt und Anfahrt</a>
      </div>
    </div>
    <div class="map" data-map="https://www.openstreetmap.org/export/embed.html?bbox=10.0514%2C52.6038%2C10.0714%2C52.6138&amp;layer=mapnik&amp;marker=52.6088%2C10.0614">
      <div class="map__consent">
        <strong>Karte anzeigen</strong>
        <p>Mit Klick wird die Karte von OpenStreetMap geladen. Dabei werden Daten wie eure IP-Adresse an die OpenStreetMap Foundation übertragen. Details in der <a href="datenschutz.html#karte">Datenschutzerklärung</a>.</p>
        <button class="btn btn--primary btn--sm" type="button">Karte laden</button>
      </div>
    </div>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("index.html", html)
