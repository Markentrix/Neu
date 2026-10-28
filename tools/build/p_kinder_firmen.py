# -*- coding: utf-8 -*-
from common import *

# ---------------- KINDER ----------------
html = head("Kindergeburtstag Kartbahn Celle – Kidsparty ab 8 J.",
 "Kindergeburtstag in Celle: Kidsparty ab 6 Kindern exklusiv auf der Kartbahn, Pakete ab 40 € mit Partytisch, Kinderkarts Sodi LR6, Kinderkartführerschein und Schulklassen-Angebote.",
 breadcrumb("Kinder","kinder.html")) + header()

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/kids-siegerehrung.webp" width="400" height="267" alt="Kinder jubeln auf dem Siegerpodest der Celler Kartbahn" fetchpriority="high">
  <div class="wrap">
    <span class="eyebrow">Kinder &amp; Jugend</span>
    <h1>Kindergeburtstag mit Vollgas</h1>
    <p class="lead">Kidsparty exklusiv auf der Strecke, eigener Partytisch, Siegerehrung auf dem Podest – ab 8 Jahren und 1,25 m. Ihr bringt die Kinder, wir den Rest.</p>
    <div class="hero__actions"><a class="btn btn--primary" href="buchen.html?angebot=kidsparty">{ICONS["cal"]}Kidsparty buchen</a><a class="btn btn--ghost" href="#ablauf">So läuft's ab</a></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2 class="sr-only">Kidsparty-Pakete</h2>
    <div class="grid grid-2">
      <div class="card card--accent"><span class="badge">Paket F1</span><h3>40,00 € pro Kind</h3><p>3 × 10 Minuten Fahrspaß</p><ul class="checks"><li>Registrierung und Sturmhaube</li><li>Kleines Geschenk für das Geburtstagskind</li><li>Helmleihe</li><li>Partytisch mit Chips &amp; Süßem</li><li>2 Softdrinks 0,2 l pro Kind</li><li>Jede weitere 10 Minuten 8 €</li></ul><a class="btn btn--primary btn--sm" href="buchen.html?angebot=kidsparty">F1 buchen</a></div>
      <div class="card card--accent"><span class="badge">Paket F2</span><h3>48,00 € pro Kind</h3><p>Grand-Prix-Modus – insgesamt 40 Minuten Fahrzeit</p><ul class="checks"><li>10 Minuten Training</li><li>10 Minuten Qualifying</li><li>20 Minuten Rennen mit Formel-1-Start</li><li>Registrierung, Sturmhaube, Helmleihe, Geschenk</li><li>Partytisch mit Chips &amp; Süßem, 2 Softdrinks 0,2 l</li><li>Jede weitere 10 Minuten 8 €</li></ul><a class="btn btn--primary btn--sm" href="buchen.html?angebot=kidsparty">F2 buchen</a></div>
    </div>
    <div class="grid grid-3" style="margin-top:1.25rem">
      <div class="card"><div class="card__icon">{ICONS["food"]}</div><h3>Pizzapaket 10,50 €</h3><p>Eine Pizza (29 cm) nach Wahl plus ein weiteres Softgetränk 0,2 l – nach der letzten Fahrt. Auch für nur einen Teil der Kinder buchbar.</p></div>
      <div class="card"><div class="card__icon">{ICONS["trophy"]}</div><h3>Siegerehrung</h3><p>Pokalsätze ab 30 €, Medaillen 1,90 € pro Stück (ab 3 Stück). Auf unserem Podest mit Gruppenfoto.</p></div>
      <div class="card"><div class="card__icon">{ICONS["kids"]}</div><h3>Erwachsene fahren mit</h3><p>Aufschlag 16–20 Jahre 5 €, ab 21 Jahren 7,50 €. Mindestteilnehmerzahl: 6 Kinder.</p></div>
    </div>
  </div>
</section>

<section class="section section--alt" id="ablauf">
  <div class="wrap">
    <span class="eyebrow">Ablauf</span>
    <h2>So läuft eure Kidsparty ab</h2>
    <ol class="steps">
      <li><h3>Registrierung</h3><p class="muted">Alle Kids registrieren sich bei der Ankunft (falls noch nicht geschehen). Bitte 30 Minuten vor der gebuchten Startzeit da sein.</p></li>
      <li><h3>Zum Partytisch</h3><p class="muted">Der eingedeckte Tisch im Bistro ist euer Treffpunkt. Von hier verfolgen die Kids das Rennen auf den Livemonitoren.</p></li>
      <li><h3>Einweisung</h3><p class="muted">Sturmhauben verteilen, dann in den Einweisungsraum: Bedienung des Karts, Regeln und Flaggenkunde – kindgerecht erklärt.</p></li>
      <li><h3>Auf die Strecke</h3><p class="muted">Die Gruppe fährt exklusiv – ohne andere Teilnehmer. Ob die 2. Ebene befahren wird, entscheidet das Streckenpersonal je nach Fahrkönnen.</p></li>
      <li><h3>Pause</h3><p class="muted">Zwischen den Fahrten 15–25 Minuten: ausruhen, Rennergebnisse anschauen, trinken und knabbern.</p></li>
      <li><h3>Siegerehrung</h3><p class="muted">Nach der letzten Fahrt organisieren wir gern eine Siegerehrung mit Medaillen oder Pokalen. Der Tisch steht euch danach noch bis zu 45 Minuten (mit Snackpaket 60 Minuten) zur Verfügung.</p></li>
    </ol>
    <div class="gallery" style="margin-top:1.5rem">
      <figure><img src="assets/img/kids-registrierung.webp" width="400" height="267" alt="Kinder registrieren sich am Check-in-Terminal" loading="lazy"><figcaption>Registrierung</figcaption></figure>
      <figure><img src="assets/img/kids-einweisung.webp" width="400" height="267" alt="Kinder mit Sturmhauben bei der Einweisung" loading="lazy"><figcaption>Einweisung</figcaption></figure>
      <figure><img src="assets/img/kids-start.webp" width="400" height="267" alt="Kind mit rotem Helm im Kinderkart am Start" loading="lazy"><figcaption>Start</figcaption></figure>
      <figure><img src="assets/img/kids-pause.webp" width="400" height="267" alt="Kinder schauen sich die Rennergebnisse an" loading="lazy"><figcaption>Rennergebnisse</figcaption></figure>
      <figure><img src="assets/img/kids-bistro.webp" width="400" height="267" alt="Geburtstagstisch im Bistro mit jubelnden Kindern" loading="lazy"><figcaption>Partytisch</figcaption></figure>
      <figure><img src="assets/img/kids-siegerehrung.webp" width="400" height="267" alt="Siegerehrung auf dem Podest" loading="lazy"><figcaption>Siegerehrung</figcaption></figure>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2>Wichtig für Eltern</h2>
    <div class="grid grid-2">
      <div class="notice notice--warn">
        <p><strong>Einverständniserklärung:</strong> Eltern haften für ihre Kinder. Für jedes minderjährige Kind bitte die <a href="downloads/haftungsausschluss-minderjaehrige.pdf">Einverständniserklärung (PDF)</a> ausgefüllt mitbringen – sonst kann das Kind leider nicht teilnehmen.</p>
      </div>
      <div class="notice">
        <p><strong>Essen &amp; Trinken:</strong> Durch unsere Gastronomie sind eigene Speisen, Kuchen, Gebäck und Getränke nicht gestattet. Der Geburtstagstisch ist ausreichend mit Süßigkeiten und Chips gedeckt und wird bei Bedarf aufgefüllt.</p>
      </div>
    </div>
    <ul class="checks" style="margin-top:1rem">
      <li>Verbindliche Buchung online – am besten mit vorheriger Terminabsprache per Mail oder Telefon</li>
      <li>Bezahlung vor Ort in bar oder per EC-Karte</li>
      <li>Kinderkartführerschein gilt nicht in Verbindung mit den Kidsparty-Angeboten</li>
      <li>Kinder 8–12 Jahre ohne Karterfahrung fahren die verkürzte Strecke ohne 2. Ebene</li>
    </ul>
  </div>
</section>

<section class="section section--alt" id="kinderkarts">
  <div class="wrap split">
    <img src="assets/img/kartflotte.webp" width="1400" height="934" alt="Die Kartflotte der Celler Kartbahn in Reihe aufgestellt" loading="lazy">
    <div>
      <span class="eyebrow">Junior Racing</span>
      <h2>13 Kinderkarts Sodi LR6</h2>
      <p>Bahn frei für die Nachwuchs-Piloten: Ab 8 Jahren und 1,25 m geht es im Kinderkart mit 6,5-PS-Honda-Motor, hydraulischer Bremse und 3-Punkt-Sicherheitsgurt auf die Strecke. Sitz, Lenkrad und Pedale sind verstellbar, LED-Beleuchtung und Überrollbügel inklusive.</p>
      <p>Unser geschultes Personal erklärt die Rennregeln, weist in die Bedienung ein und trifft alle Sicherheitsvorkehrungen. Tägliche Checks garantieren Sicherheit, Power und Fahrspaß.</p>
      <a class="btn btn--ghost" href="kartbahn.html#karts">Technische Daten</a>
    </div>
  </div>
</section>

<section class="section" id="fuehrerschein">
  <div class="wrap grid grid-2" style="align-items:start">
    <div>
      <span class="eyebrow">Kinderkartführerschein</span>
      <h2>Der Intensivkurs für 45 €</h2>
      <p>2–3 Stunden Training inkl. Führerscheinlizenz und Sturmhaube: Ideallinie und schwierige Kurven, Hütchenfahren, Bremstest, Flaggentest, Fahrtraining und ein intensiver Theoriekurs.</p>
      <ul class="checks">
        <li>Jeden 1. Samstag im Monat um 10 Uhr – um 09:30 Uhr im Haus eintreffen</li>
        <li>Nach bestandenem Kurs kostet jedes Trainingsticket nur noch 6 €</li>
        <li>Gültig bis zur Vollendung des 15. Lebensjahres</li>
      </ul>
      <a class="btn btn--primary" href="buchen.html?angebot=fuehrerschein">Kurs buchen</a>
    </div>
    <div>
      <span class="eyebrow">Schulklassen</span>
      <h2>Unterricht mal anders</h2>
      <p>Für Schulklassen ab 20 Personen, Montag bis Freitag und auch vormittags. Nach der Begrüßung teilen wir die Klasse in Fahrergruppen von 10–15 Fahrern ein (Wünsche werden berücksichtigt), dann folgen Einweisung und Fahrten auf Bestzeit.</p>
      <div class="grid grid-2">
        <div class="card"><h3>Angebot 1 · 20 €</h3><p>20 Min Fahrzeit: Registrierung, Sturmhaube, Einweisung, 2 × 10 Min pro Gruppe. Dauer ca. 2 Stunden.</p></div>
        <div class="card"><h3>Angebot 2 · 25 €</h3><p>30 Min Fahrzeit: wie Angebot 1 plus 3 × 10 Min und 1 Softgetränk 0,2 l. Dauer ca. 2,5–3 Stunden.</p></div>
      </div>
      <p class="small" style="margin-top:.8rem">Lehrkräfte fahren zu den gleichen Konditionen. Vom Bahnhof Celle sind es max. 20 Minuten zu Fuß. Eigene Speisen und Getränke sind nicht gestattet – für Schulklassen gibt es Softdrinks für 1,50 € pro Glas und Eis für den kleinen Geldbeutel.</p>
      <a class="btn btn--ghost" href="buchen.html?angebot=schulklasse">Schulklasse anfragen</a>
    </div>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("kinder.html", html)

# ---------------- FIRMEN ----------------
html = head("Firmenevents & Gruppen | Burnout Celler-Kartbahn Celle",
 "Firmenevent, Weihnachtsfeier, Junggesellenabschied oder Vereinsfeier auf der Celler Kartbahn: Supercup für 6–17 Personen, Bahnmiete und Meisterschaftsmodus bis 80 Gäste, Buffet im Clubraum.",
 breadcrumb("Firmen & Gruppen","firmen.html")) + header()

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/strecke-start.webp" width="1400" height="934" alt="Startaufstellung der Karts vor der Rennleitung der Celler Kartbahn" fetchpriority="high">
  <div class="wrap">
    <span class="eyebrow">Firmen, Vereine &amp; Gruppen</span>
    <h1>Rennfeeling für euer Team</h1>
    <p class="lead">Weihnachtsfeier, Firmenevent, Vereinsfeier oder Junggesellenabschied: von 6 bis ca. 80 Personen ist die Strecke exklusiv für euch. Danach Buffet im Clubraum – oder weiter in den Dartraum.</p>
    <div class="hero__actions"><a class="btn btn--primary" href="buchen.html?angebot=bahnmiete">{ICONS["cal"]}Event anfragen</a><a class="btn btn--ghost" href="#supercup">Pakete vergleichen</a></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid grid-3">
      <div class="stat"><strong>6–17</strong><span>Personen: Supercup-Rennen</span></div>
      <div class="stat"><strong>ab 18</strong><span>Personen: Rennpakete &amp; Meisterschaft</span></div>
      <div class="stat"><strong>bis 80</strong><span>Gäste im Veranstaltungsraum</span></div>
    </div>
    <p class="muted" style="margin-top:1.25rem">Anfänger und erfahrene Fahrer kommen gleichermaßen auf ihre Kosten. Nach einer ausführlichen Einweisung geht es auf die Rennstrecke: Überholmanöver, Vollgas durch den Tunnel und über die zweite Ebene – Motorsport-Feeling hautnah.</p>
  </div>
</section>

<section class="section section--alt" id="supercup">
  <div class="wrap">
    <span class="eyebrow">6–17 Personen</span>
    <h2>Supercup – euer exklusives Rennen</h2>
    <p class="muted">Qualifying, Ampelstart, Zieleinlauf und Rennauswertung. Eure Gruppe ist allein auf der Strecke. Bei weniger als 6 Teilnehmern wird der Preis für 6 Teilnehmer berechnet. Maximal 17 Personen.</p>
    <div class="grid grid-3">
      <div class="card"><span class="badge badge--dark">Standard</span><h3>39 € p.P.</h3><p>10 Min Qualifying + 20 Min Rennen</p></div>
      <div class="card"><span class="badge badge--dark">Professional</span><h3>49 € p.P.</h3><p>10 Min Qualifying + 30 Min Rennen</p></div>
      <div class="card"><span class="badge badge--dark">Premium</span><h3>59 € p.P.</h3><p>10 Min Qualifying + 40 Min Rennen</p></div>
      <div class="card"><span class="badge">Double Premium</span><h3>59 € p.P.</h3><p>10 Min Qualifying + 2 Rennen à 20 Min. Startaufstellung im 2. Rennen = Zieleinlauf des 1. Pause zwischen den Rennen inklusive.</p></div>
      <div class="card"><span class="badge">Double Ultra</span><h3>75 € p.P.</h3><p>10 Min Qualifying + 2 Rennen à 30 Min.</p></div>
      <div class="card"><span class="badge">Grand Prix</span><h3>49 € / 59 € p.P.</h3><p>10 Min Training + 10 Min Qualifying + 20 Min Rennen (Premium: 30 Min). Immer mit Pause zwischen den Fahrten.</p></div>
    </div>
    <p class="small" style="margin-top:1rem">Wunsch nach einer Pause von 15–25 Minuten nach dem Qualifying bitte bei der Buchung angeben. Doppelsitzer beim Rennen: einmalig 10 € Zusatzgebühr.</p>
    <a class="btn btn--primary" href="buchen.html?angebot=supercup">Supercup buchen</a>
  </div>
</section>

<section class="section" id="meisterschaft">
  <div class="wrap split">
    <img src="assets/img/strecke-boxengasse.webp" width="1400" height="934" alt="Boxengasse und Reifenstapel der Celler Kartbahn" loading="lazy">
    <div>
      <span class="eyebrow">ab 18 Personen</span>
      <h2>Meisterschaftsmodus &amp; Bahnmiete</h2>
      <p><strong>Wer ist der Schnellste in eurer Gruppe?</strong> Zunächst fahren alle Teilnehmer ihr Qualifying – die persönliche Bestzeit zählt. Danach teilen wir die Fahrer in möglichst gleichstarke Gruppen ein. Jede Gruppe fährt ihr eigenes Rennen mit Startaufstellung und direktem Kampf um die Platzierungen. Am Ende werden alle Ergebnisse ausgewertet und der Gesamtsieger ermittelt.</p>
      <p>Bei der <strong>Bahnmiete</strong> bestimmt ihr das Programm selbst – am beliebtesten ist das <strong>Teamrennen</strong>: 2–4 Fahrer pro Team wechseln sich während des Rennens ab, alle verfolgen Rundenzeiten und Ergebnis auf der Großbildleinwand. Anschließend Siegerehrung mit Pokalen und Medaillen – nur die Besten kommen aufs Podest.</p>
      <div class="table-wrap"><table><caption>Bahnmiete (Brutto / Netto)</caption><tbody>
        <tr><td>1 Stunde inkl. 10 Karts</td><td class="price">650 € / 546,22 €</td></tr>
        <tr><td>jede weitere ½ Stunde</td><td class="price">325 € / 273,11 €</td></tr>
        <tr><td>jedes weitere Kart pro Stunde</td><td class="price">65 € / 54,62 €</td></tr>
      </tbody></table><p class="price-hint">Mindestens 1 Stunde und 10 Karts, maximal 16 Karts gleichzeitig. Zusätzliche Karts auch spontan am Veranstaltungstag.</p></div>
      <p style="margin-top:1rem"><a class="btn btn--primary" href="buchen.html?angebot=bahnmiete">Bahnmiete anfragen</a></p>
    </div>
  </div>
</section>

<section class="section section--alt" id="buffet">
  <div class="wrap split split--rev">
    <img src="assets/img/veranstaltungsraum.webp" width="1400" height="933" alt="Festlich eingedeckter Veranstaltungsraum der Celler Kartbahn" loading="lazy">
    <div>
      <span class="eyebrow">Nach dem Rennen</span>
      <h2>Buffet &amp; Clubraum</h2>
      <p>Lasst euren Renntag bei einem leckeren Buffet und Getränken ausklingen. In unserem Veranstaltungsraum finden bis zu 80 Personen Platz; bei einer Buffetbestellung steht der Raum kostenfrei zur Verfügung, und unser Servicepersonal kümmert sich um euer leibliches Wohl. In der Weihnachtszeit ist der Raum passend dekoriert.</p>
      <ul class="checks">
        <li>Buffet möglich ab 20 Personen</li>
        <li>Eigener Servicebereich mit Servicekraft</li>
        <li>Kombination mit dem <a href="https://www.dartraum-celle.de" rel="noopener" target="_blank">Dartraum Celle</a>: erst Kart, dann Dart</li>
      </ul>
      <div class="pill-row">
        <a class="btn btn--ghost" href="downloads/buffet-2026-2027.jpg">Buffetangebot 2026/2027 ansehen</a>
        <a class="btn btn--primary" href="kontakt.html">Individuelles Angebot anfragen</a>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2>Siegerehrung</h2>
    <div class="grid grid-3">
      <div class="card"><div class="card__icon">{ICONS["trophy"]}</div><h3>Pokalsatz 1 · 30 €</h3><p>10–14 cm, inkl. Standardgravur</p></div>
      <div class="card"><div class="card__icon">{ICONS["trophy"]}</div><h3>Pokalsatz 2 · 40 €</h3><p>13–18 cm, inkl. Standardgravur</p></div>
      <div class="card"><div class="card__icon">{ICONS["trophy"]}</div><h3>Medaille · 1,90 €</h3><p>pro Stück, ab 3 Stück</p></div>
    </div>
    <p class="small" style="margin-top:.8rem">Die Siegerehrung findet auf unserem Podest statt – perfekt für das Gruppenfoto. Ihr seid eine Firma und braucht eine Rechnung mit Netto-Ausweis? Kein Problem, einfach bei der Buchung angeben.</p>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("firmen.html", html)
