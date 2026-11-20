# -*- coding: utf-8 -*-
from common import *

# ---------------- KINDER ----------------
html = head("Kindergeburtstag Kartbahn Celle – Kidsparty ab 8 J.",
 "Kindergeburtstag in Celle: Kidsparty ab 6 Kindern exklusiv auf der Kartbahn, Pakete ab 40 € mit Partytisch, 13 Kinderkarts Sodi LR6, Kinderkartführerschein und Schulklassen-Angebote.",
 breadcrumb("Kinder","kinder.html") + '''<script type="application/ld+json">{"@context":"https://schema.org","@graph":[
{"@type":"HowTo","name":"So läuft die Kidsparty auf der Celler Kartbahn ab","totalTime":"PT2H","supply":[{"@type":"HowToSupply","name":"Einverständniserklärung der Eltern"}],
 "step":[{"@type":"HowToStep","name":"Registrierung","text":"Alle Kinder registrieren sich bei der Ankunft, 30 Minuten vor der gebuchten Startzeit."},{"@type":"HowToStep","name":"Partytisch","text":"Der eingedeckte Tisch im Bistro ist Treffpunkt; von dort verfolgen die Kids das Rennen auf Livemonitoren."},{"@type":"HowToStep","name":"Einweisung","text":"Sturmhauben verteilen, dann Erklärung von Kart, Regeln und Flaggen im Einweisungsraum."},{"@type":"HowToStep","name":"Fahrten","text":"Die Gruppe fährt exklusiv; zwischen den Fahrten 15 bis 25 Minuten Pause."},{"@type":"HowToStep","name":"Siegerehrung","text":"Nach der letzten Fahrt Siegerehrung mit Medaillen oder Pokalen auf dem Podest."}]},
{"@type":"Service","name":"Kindergeburtstag auf der Kartbahn (Kidsparty)","serviceType":"Kindergeburtstag","provider":{"@id":"{{SITE_URL}}/#kartbahn"},"areaServed":"Celle und Region Hannover","audience":{"@type":"PeopleAudience","suggestedMinAge":8,"suggestedMaxAge":15},
 "offers":[{"@type":"Offer","name":"Paket F1 – 3 × 10 Minuten","price":"40.00","priceCurrency":"EUR","eligibleQuantity":{"@type":"QuantitativeValue","minValue":6}},{"@type":"Offer","name":"Paket F2 – Grand-Prix-Modus","price":"48.00","priceCurrency":"EUR","eligibleQuantity":{"@type":"QuantitativeValue","minValue":6}},{"@type":"Offer","name":"Kinderkartführerschein","price":"45.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Schulklasse Angebot 1","price":"20.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Schulklasse Angebot 2","price":"25.00","priceCurrency":"EUR"}]}]}</script>''') + header()

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/kartflotte.webp" width="1400" height="934" alt="Die Kartflotte der Celler Kartbahn, bereit für die Kidsparty" fetchpriority="high">
  <div class="wrap">
    <div>
      <h1>Kidsparty ab 8 Jahren</h1>
      <p class="lead">Kindergeburtstag exklusiv auf der Strecke, mit Partytisch, Geschenk und Siegerehrung auf dem Podest. Ab 6 Kindern, ab 8 Jahren und 1,25 m. Ihr bringt die Kinder, wir machen den Rest.</p>
      <div class="hero__actions"><a class="btn btn--primary" href="buchen.html?angebot=kidsparty">Kidsparty buchen</a><a class="link" href="#ablauf">So läuft die Party ab</a></div>
    </div>
  </div>
</section>

<section class="section" id="pakete">
  <div class="wrap">
    <h2>Zwei Pakete, ein Partytisch</h2>
    <p class="lead">Beide Pakete enthalten Registrierung, Sturmhaube, Helmleihe, ein kleines Geschenk für das Geburtstagskind, den gedeckten Partytisch mit Chips und Süßem und zwei Softdrinks pro Kind.</p>
    <div class="table-wrap">
      <table class="vergleich">
        <caption>Kidsparty-Pakete, Preis pro Kind</caption>
        <thead><tr><th scope="col"></th><th scope="col">Paket F1</th><th scope="col">Paket F2</th></tr></thead>
        <tbody>
          <tr><th scope="row">Preis pro Kind</th><td data-label="Paket F1" class="price">40,00 €</td><td data-label="Paket F2" class="price">48,00 €</td></tr>
          <tr><th scope="row">Fahrzeit</th><td data-label="Paket F1">3 × 10 Minuten</td><td data-label="Paket F2">40 Minuten im Grand-Prix-Modus</td></tr>
          <tr><th scope="row">Ablauf</th><td data-label="Paket F1">Drei freie Fahrten auf Bestzeit</td><td data-label="Paket F2">10 Min Training, 10 Min Qualifying, 20 Min Rennen mit Formel-1-Start</td></tr>
          <tr><th scope="row">Jede weitere 10 Minuten</th><td data-label="Paket F1" class="price">8,00 €</td><td data-label="Paket F2" class="price">8,00 €</td></tr>
          <tr><th scope="row">Mindestteilnehmer</th><td data-label="Paket F1">6 Kinder</td><td data-label="Paket F2">6 Kinder</td></tr>
          <tr><th scope="row"></th><td data-label="Paket F1"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=kidsparty">F1 buchen</a></td><td data-label="Paket F2"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=kidsparty">F2 buchen</a></td></tr>
        </tbody>
      </table>
    </div>
    <div class="table-wrap" style="margin-top:1rem"><table><caption>Extras</caption><tbody>
      <tr><td>Pizzapaket: eine Pizza 29 cm nach Wahl plus ein Softdrink 0,2 l, nach der letzten Fahrt, auch für einen Teil der Kinder</td><td class="price">10,50 €</td></tr>
      <tr><td>Mitfahrende Erwachsene 16 bis 20 Jahre</td><td class="price">+ 5,00 €</td></tr>
      <tr><td>Mitfahrende Erwachsene ab 21 Jahren</td><td class="price">+ 7,50 €</td></tr>
      <tr><td>Siegerehrung: Pokalsatz ab 30 €, Medaille 1,90 € pro Stück, ab 3 Stück</td><td class="price">ab 5,70 €</td></tr>
    </tbody></table><p class="price-hint">Bezahlung vor Ort in bar oder per EC-Karte. Der Kinderkartführerschein gilt nicht in Verbindung mit den Kidsparty-Paketen.</p></div>
  </div>
</section>

<section class="section section--flaeche" id="ablauf">
  <div class="wrap">
    <h2>So läuft eure Kidsparty ab</h2>
    <ol class="steps steps--foto">
      <li><img src="assets/img/kids-registrierung.webp" width="400" height="267" alt="Kinder registrieren sich am Check-in-Terminal" loading="lazy" decoding="async"><h3>Registrierung</h3><p>Alle Kinder registrieren sich bei der Ankunft, falls noch nicht geschehen. Bitte 30 Minuten vor der gebuchten Startzeit da sein.</p></li>
      <li><img src="assets/img/kids-bistro.webp" width="400" height="267" alt="Geburtstagstisch im Bistro mit jubelnden Kindern" loading="lazy" decoding="async"><h3>Partytisch</h3><p>Der eingedeckte Tisch im Bistro ist euer Treffpunkt. Von hier verfolgen die Kids das Rennen auf den Livemonitoren.</p></li>
      <li><img src="assets/img/kids-einweisung.webp" width="400" height="267" alt="Kinder mit Sturmhauben bei der Einweisung" loading="lazy" decoding="async"><h3>Einweisung</h3><p>Sturmhauben verteilen, dann in den Einweisungsraum: Bedienung des Karts, Regeln und Flaggenkunde, kindgerecht erklärt.</p></li>
      <li><img src="assets/img/kids-start.webp" width="400" height="267" alt="Kind mit rotem Helm im Kinderkart am Start" loading="lazy" decoding="async"><h3>Auf die Strecke</h3><p>Die Gruppe fährt exklusiv, ohne andere Teilnehmer. Ob die 2. Ebene befahren wird, entscheidet das Streckenpersonal je nach Fahrkönnen.</p></li>
      <li><img src="assets/img/kids-pause.webp" width="400" height="267" alt="Kinder schauen sich die Rennergebnisse an" loading="lazy" decoding="async"><h3>Pause</h3><p>Zwischen den Fahrten 15 bis 25 Minuten: ausruhen, Rennergebnisse anschauen, trinken und knabbern.</p></li>
      <li><img src="assets/img/kids-siegerehrung.webp" width="400" height="267" alt="Siegerehrung auf dem Podest" loading="lazy" decoding="async"><h3>Siegerehrung</h3><p>Nach der letzten Fahrt mit Medaillen oder Pokalen auf dem Podest. Der Tisch steht euch danach noch bis zu 45 Minuten zur Verfügung, mit Pizzapaket 60 Minuten.</p></li>
    </ol>
  </div>
</section>

<section class="section">
  <div class="wrap grid grid-2" style="align-items:start">
    <div>
      <h2>Checkliste für Eltern</h2>
      <ul class="checks">
        <li><strong>Einverständniserklärung</strong> für jedes minderjährige Kind ausgefüllt mitbringen, sonst kann das Kind nicht fahren: <a href="downloads/haftungsausschluss-minderjaehrige.pdf" target="_blank" rel="noopener">PDF herunterladen</a>.</li>
        <li><strong>Verbindlich online buchen</strong>, am besten nach kurzer Terminabsprache per Telefon oder Mail.</li>
        <li><strong>30 Minuten vor der Startzeit</strong> mit allen Kindern im Haus sein.</li>
        <li><strong>Keine eigenen Speisen, Kuchen oder Getränke:</strong> Der Partytisch ist gedeckt und wird aufgefüllt. Unsere Gastronomie erlaubt nichts Mitgebrachtes.</li>
        <li><strong>Bezahlung vor Ort</strong> in bar oder per EC-Karte.</li>
        <li><strong>Festes Schuhwerk</strong>, Helme leihen wir, Sturmhauben sind im Paket.</li>
      </ul>
    </div>
    <div class="tafel">
      <h3>Wer darf ins Kinderkart?</h3>
      <ul class="hours">
        <li><span>Kinderkart Sodi LR6</span><span>ab 8 J., 1,25 m</span></li>
        <li><span>Rennkart Sodi SR5</span><span>ab 13 J., 1,55 m</span></li>
        <li><span>Rennkart mit Karterfahrung</span><span>ab 12 J., 1,55 m</span></li>
        <li><span>Doppelsitzer, Beifahrer</span><span>ab 4 J., 1,10 m</span></li>
      </ul>
      <p class="small" style="margin:1rem 0 0">Kinder von 8 bis 12 Jahren ohne Karterfahrung fahren die verkürzte Strecke ohne die 2. Ebene. Ausnahmen entscheidet nur das Bahnpersonal.</p>
    </div>
  </div>
</section>

<section class="section section--flaeche" id="kinderkarts">
  <div class="wrap">
    <figure class="stanz">
      <img src="assets/img/karts-boxengasse.webp" width="1400" height="933" alt="Kinderkarts und Rennkarts in der Boxengasse" loading="lazy" decoding="async">
      <figcaption class="stanz__etikett"><strong>13 Kinderkarts Sodi LR6</strong><span>6,5 PS, 3-Punkt-Gurt, ab 8 Jahren und 1,25 m</span></figcaption>
    </figure>
    <div class="grid grid-2" style="margin-top:1.5rem;align-items:start">
      <p>Sitz, Lenkrad und Pedale sind verstellbar, LED-Beleuchtung und Überrollbügel inklusive. Unser Personal erklärt die Regeln, weist in die Bedienung ein und prüft die Karts täglich.</p>
      <p><a class="link" href="kartbahn.html#karts">Technische Daten der Karts</a></p>
    </div>
  </div>
</section>

<section class="section" id="fuehrerschein">
  <div class="wrap grid grid-2" style="align-items:start">
    <div class="tafel">
      <h3>Kinderkartführerschein</h3>
      <ul class="hours">
        <li><span>Wann</span><span>jeden 1. Samstag, 10:00</span></li>
        <li><span>Eintreffen</span><span>09:30 im Haus</span></li>
        <li><span>Dauer</span><span>2 bis 3 Stunden</span></li>
        <li><span>Preis</span><span>45,00 €</span></li>
        <li><span>Danach pro Trainingsticket</span><span>6,00 €</span></li>
      </ul>
      <p style="margin:1rem 0">Intensivkurs mit Führerscheinlizenz und Sturmhaube: Ideallinie, schwierige Kurven, Hütchenfahren, Bremstest, Flaggentest, Fahrtraining und Theorie. Die Lizenz gilt bis zur Vollendung des 15. Lebensjahres.</p>
      <a class="btn btn--primary" href="buchen.html?angebot=fuehrerschein">Kurs buchen</a>
    </div>
    <div>
      <h2>Schulklassen ab 20</h2>
      <p>Montag bis Freitag, auch vormittags. Nach der Begrüßung teilen wir die Klasse in Fahrergruppen von 10 bis 15 Fahrern ein, Wünsche werden berücksichtigt. Dann Einweisung und Fahrten auf Bestzeit. Lehrkräfte fahren zu denselben Konditionen.</p>
      <div class="table-wrap"><table><thead><tr><th>Angebot</th><th>Leistung</th><th class="price">p. P.</th></tr></thead><tbody>
        <tr><td>Angebot 1</td><td>Registrierung, Sturmhaube, Einweisung, 2 × 10 Min auf Bestzeit pro Gruppe, ca. 2 Stunden</td><td class="price">20 €</td></tr>
        <tr><td>Angebot 2</td><td>wie Angebot 1 plus 3 × 10 Min und ein Softgetränk 0,2 l, ca. 2,5 bis 3 Stunden</td><td class="price">25 €</td></tr>
      </tbody></table><p class="price-hint">Vom Bahnhof Celle maximal 20 Minuten zu Fuß. Eigene Speisen und Getränke sind nicht gestattet; Softdrinks für Schulklassen 1,50 € pro Glas.</p></div>
      <a class="btn btn--primary" href="buchen.html?angebot=schulklasse">Schulklasse anfragen</a>
    </div>
  </div>
</section>
''' + contact_strip("kinder") + footer() + end()
write("kinder.html", html)

# ---------------- FIRMEN ----------------
html = head("Firmenevents & Gruppen | Burnout Celler-Kartbahn Celle",
 "Firmenevent, Weihnachtsfeier, Junggesellenabschied oder Vereinsfeier auf der Celler Kartbahn: Supercup für 6–17 Personen, Bahnmiete und Meisterschaftsmodus bis 80 Gäste, Buffet im Clubraum.",
 breadcrumb("Firmen & Gruppen","firmen.html") + '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"Service","name":"Firmenevents und Gruppenrennen auf der Celler Kartbahn","serviceType":"Firmenevent, Teambuilding, Weihnachtsfeier, Junggesellenabschied","provider":{"@id":"{{SITE_URL}}/#kartbahn"},"areaServed":["Celle","Hannover","Niedersachsen"],
"hasOfferCatalog":{"@type":"OfferCatalog","name":"Rennpakete","itemListElement":[
{"@type":"Offer","name":"Supercup Standard – 10 Min Qualifying + 20 Min Rennen","price":"39.00","priceCurrency":"EUR","eligibleQuantity":{"@type":"QuantitativeValue","minValue":6,"maxValue":17}},
{"@type":"Offer","name":"Supercup Professional – 10 + 30 Min","price":"49.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Supercup Premium – 10 + 40 Min","price":"59.00","priceCurrency":"EUR"},
{"@type":"Offer","name":"Supercup Double Premium – 10 + 2 × 20 Min","price":"59.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Supercup Double Ultra – 10 + 2 × 30 Min","price":"75.00","priceCurrency":"EUR"},
{"@type":"Offer","name":"Grand Prix – Training, Qualifying, 20 Min Rennen","price":"49.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Grand Prix Premium – 30 Min Rennen","price":"59.00","priceCurrency":"EUR"},
{"@type":"Offer","name":"Bahnmiete 1 Stunde inkl. 10 Karts (exklusiv)","price":"650.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Bahnmiete jede weitere halbe Stunde","price":"325.00","priceCurrency":"EUR"},{"@type":"Offer","name":"Jedes weitere Kart pro Stunde","price":"65.00","priceCurrency":"EUR"}]}}</script>''') + header()

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/strecke-start.webp" width="1400" height="934" alt="Startaufstellung der Karts vor der Rennleitung der Celler Kartbahn" fetchpriority="high">
  <div class="wrap">
    <div>
      <h1>Rennen für euer Team</h1>
      <p class="lead">Weihnachtsfeier, Firmenevent, Vereinsfeier oder Junggesellenabschied: von 6 bis ca. 80 Personen ist die Strecke exklusiv für euch. Danach Buffet im Clubraum für bis zu 80 Gäste, oder weiter in den Dartraum nebenan.</p>
      <div class="hero__actions"><a class="btn btn--primary" href="buchen.html?angebot=bahnmiete">Event anfragen</a><a class="link" href="#supercup">Rennpakete vergleichen</a></div>
    </div>
  </div>
</section>

<section class="section" id="supercup">
  <div class="wrap">
    <ul class="fakten-zeile" aria-label="Gruppengrößen"><li><strong>6 bis 17</strong> Personen: Supercup</li><li><strong>ab 18</strong> Personen: Rennpakete und Meisterschaft</li><li><strong>16</strong> Karts gleichzeitig</li><li><strong>80</strong> Gäste im Clubraum</li></ul>
    <h2>Supercup: euer Rennen</h2>
    <p class="lead">Qualifying, Ampelstart, Zieleinlauf und Rennauswertung auf der Großbildleinwand. Eure Gruppe ist allein auf der Strecke. Anfänger und erfahrene Fahrer starten nach einer ausführlichen Einweisung gemeinsam.</p>
    <table class="startliste">
      <thead><tr><th scope="col">Paket</th><th scope="col">Ablauf</th><th scope="col" class="preis">Preis p. P.</th><th scope="col"><span class="sr-only">Aktion</span></th></tr></thead>
      <tbody>
        <tr><td class="name">Standard<small>Der Klassiker für Gruppen bis 17.</small></td><td class="fuer">10 Min Qualifying, 20 Min Rennen</td><td class="preis">39 €</td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=supercup">Buchen</a></td></tr>
        <tr><td class="name">Professional<small>Mehr Rennen, gleiche Startaufstellung.</small></td><td class="fuer">10 Min Qualifying, 30 Min Rennen</td><td class="preis">49 €</td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=supercup">Buchen</a></td></tr>
        <tr><td class="name">Premium<small>40 Minuten Renndistanz am Stück.</small></td><td class="fuer">10 Min Qualifying, 40 Min Rennen</td><td class="preis">59 €</td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=supercup">Buchen</a></td></tr>
        <tr><td class="name">Double Premium<small>Zwei Rennen, Startaufstellung im zweiten ist der Zieleinlauf des ersten, Pause dazwischen.</small></td><td class="fuer">10 Min Qualifying, 2 × 20 Min Rennen</td><td class="preis">59 €</td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=supercup">Buchen</a></td></tr>
        <tr><td class="name">Double Ultra<small>Die lange Doppelrunde.</small></td><td class="fuer">10 Min Qualifying, 2 × 30 Min Rennen</td><td class="preis">75 €</td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=supercup">Buchen</a></td></tr>
        <tr><td class="name">Grand Prix<small>Mit Training, immer Pause zwischen den Fahrten. Premium: 30 Min Rennen für 59 €.</small></td><td class="fuer">10 Min Training, 10 Min Qualifying, 20 Min Rennen</td><td class="preis">49 €</td><td class="aktion"><a class="btn btn--primary btn--sm" href="buchen.html?angebot=supercup">Buchen</a></td></tr>
      </tbody>
    </table>
    <p class="small" style="margin-top:1rem">Mindestens 6, maximal 17 Personen; bei weniger als 6 wird der Preis für 6 berechnet. Pause von 15 bis 25 Minuten nach dem Qualifying bitte bei der Buchung angeben. Doppelsitzer beim Rennen einmalig 10 € Zusatzgebühr.</p>
  </div>
</section>

<section class="section section--flaeche" id="meisterschaft">
  <div class="wrap split">
    <img src="assets/img/strecke-boxengasse.webp" width="1400" height="934" alt="Boxengasse und Reifenstapel der Celler Kartbahn" loading="lazy" decoding="async">
    <div>
      <h2>Meisterschaft und Bahnmiete</h2>
      <p><strong>Wer ist der Schnellste in eurer Gruppe?</strong> Alle fahren ihr Qualifying, die persönliche Bestzeit zählt. Danach teilen wir in möglichst gleichstarke Gruppen ein, jede Gruppe fährt ihr eigenes Rennen, am Ende wird der Gesamtsieger ermittelt. Lohnend ab 18 Personen.</p>
      <p>Bei der <strong>Bahnmiete</strong> bestimmt ihr das Programm. Am beliebtesten: das Teamrennen mit 2 bis 4 Fahrern pro Team, Wechsel während des Rennens, Rundenzeiten live auf der Leinwand, danach Siegerehrung auf dem Podest.</p>
      <div class="table-wrap"><table><caption>Bahnmiete, brutto / netto</caption><tbody>
        <tr><td>1 Stunde inkl. 10 Karts</td><td class="price">650 € / 546,22 €</td></tr>
        <tr><td>jede weitere halbe Stunde</td><td class="price">325 € / 273,11 €</td></tr>
        <tr><td>jedes weitere Kart pro Stunde</td><td class="price">65 € / 54,62 €</td></tr>
      </tbody></table><p class="price-hint">Mindestens 1 Stunde und 10 Karts, maximal 16 Karts gleichzeitig. Weitere Karts auch spontan am Veranstaltungstag. Rechnung mit Netto-Ausweis auf Wunsch.</p></div>
      <p style="margin-top:1rem"><a class="btn btn--primary" href="buchen.html?angebot=bahnmiete">Bahnmiete anfragen</a></p>
    </div>
  </div>
</section>

<section class="ebene ebene--band" id="buffet" aria-labelledby="buffet-h">
  <img src="assets/img/veranstaltungsraum.webp" width="1400" height="933" alt="Festlich eingedeckter Veranstaltungsraum der Celler Kartbahn" loading="lazy" decoding="async">
  <div class="ebene__text">
    <div class="wrap">
      <p class="hoehe">80<small>Plätze im Clubraum, bei Buffetbestellung kostenfrei</small></p>
      <div>
        <h2 id="buffet-h">Buffet und Clubraum</h2>
        <p>Nach dem Rennen bleibt ihr: Buffet ab 20 Personen, eigener Servicebereich mit Servicekraft, in der Weihnachtszeit dekoriert. Wer danach noch nicht nach Hause will: der <a href="https://www.dartraum-celle.de" rel="noopener" target="_blank">Dartraum Celle</a> liegt nebenan.</p>
        <div class="pill-row"><a class="btn btn--light" href="buffet.html">Buffetangebot 2026/2027</a></div>
      </div>
    </div>
  </div>
</section>

<section class="section section--flaeche">
  <div class="wrap grid grid-2" style="align-items:start">
    <div>
      <h2>Siegerehrung</h2>
      <p>Auf unserem Podest, mit Gruppenfoto. Ab einer Mindestabnahme von 3 Medaillen oder Pokalen, bei Rennen, Kidspartys und Bahnmieten.</p>
    </div>
    <div class="table-wrap"><table><tbody>
      <tr><td>Pokalsatz 1, 10 bis 14 cm, mit Standardgravur</td><td class="price">30 €</td></tr>
      <tr><td>Pokalsatz 2, 13 bis 18 cm, mit Standardgravur</td><td class="price">40 €</td></tr>
      <tr><td>Medaille, pro Stück</td><td class="price">1,90 €</td></tr>
    </tbody></table></div>
  </div>
</section>
''' + contact_strip("firmen") + footer() + end()
write("firmen.html", html)

# ---------------- BUFFET ----------------
html = head("Buffetangebot 2026/2027 | Burnout Celler-Kartbahn", "Buffetauswahl für Firmenevents, Weihnachtsfeiern und Gruppen ab 20 Personen im Veranstaltungsraum der Celler Kartbahn – der Raum ist bei Buffetbestellung kostenfrei.", breadcrumb("Buffet","buffet.html")) + header()
html += f'''
<section class="section section--tight">
  <div class="wrap">
    <p><a class="link" href="firmen.html#buffet">Zurück zu Firmen und Gruppen</a></p>
    <h1>Buffetangebot 2026/2027</h1>
    <p class="lead">Für Gruppen ab 20 Personen. Bei einer Buffetbestellung steht euch der Veranstaltungsraum für bis zu 80 Personen kostenfrei zur Verfügung, unser Servicepersonal kümmert sich um euch.</p>
    <figure style="margin:0 0 1.5rem">
      <img src="downloads/buffet-2026-2027.jpg" width="1400" height="933" alt="Buffetangebot 2026/2027 der Burnout Celler-Kartbahn mit allen Speisen und Preisen" style="width:100%;height:auto" decoding="async" class="bank-img">
      <figcaption class="small" style="margin-top:.5rem">Auf dem Handy mit zwei Fingern zoomen. <a class="link" href="downloads/buffet-2026-2027.jpg" target="_blank" rel="noopener">Bild in voller Größe öffnen</a>. Die Speisen und Preise nennen wir auf Wunsch auch telefonisch oder per E-Mail.</figcaption>
    </figure>
    <div class="pill-row">
      <a class="btn btn--primary" href="buchen.html?angebot=bahnmiete">Event mit Buffet anfragen</a>
      <a class="link" href="firmen.html">Rennpakete ansehen</a>
    </div>
    <p class="small" style="margin-top:1rem">Angebot gültig für die Saison 2026/2027, Änderungen vorbehalten. Buffet bitte spätestens bei der Buchung angeben.</p>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("buffet.html", html)
