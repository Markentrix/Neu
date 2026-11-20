# -*- coding: utf-8 -*-
from common import *

html = head("Strecke, Karts & Bistro | Burnout Celler-Kartbahn",
 "Indoor-Kartbahn Celle: ca. 600 m Strecke mit Brücke, Tunnel und Steilkurve in 6 m Höhe, Sodi SR5 mit 9 PS, 13 Kinderkarts LR6, Doppelsitzer, Rennlizenz-App, RaceCam, Bistro mit Terrasse und das Team seit 2009.",
 breadcrumb("Die Kartbahn","kartbahn.html")) + header()

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/strecke-boxengasse.webp" width="1400" height="934" alt="Boxengasse und Reifenstapel der Indoor-Strecke in Celle" fetchpriority="high">
  <div class="wrap">
    <div>
      <h1>Die Strecke in Celle</h1>
      <p class="lead">Ca. 600 Meter Asphalt in der Halle, mit Brücke, Tunnel und seit 2023 der zweiten Ebene mit Steilkurve in 6 Metern Höhe. Dazu Sodi-Karts, die seit 2009 schon die fünfte neue Flotte sind.</p>
      <div class="hero__actions"><a class="btn btn--primary" href="buchen.html">Fahrten reservieren</a><a class="link" href="#tipps">Tipps für schnellere Runden</a></div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap">
    <ul class="daten" aria-label="Streckendaten">
      <li><strong>600 m</strong><span>Streckenlänge indoor</span></li>
      <li><strong>6 m</strong><span>Höhe der Steilkurve</span></li>
      <li><strong>9 PS</strong><span>Sodi SR5 Rennkarts</span></li>
      <li><strong>13</strong><span>Kinderkarts Sodi LR6</span></li>
    </ul>
  </div>
</section>

<section class="ebene" id="strecke" aria-labelledby="strecke-h">
  <img src="assets/img/zweite-ebene.webp" width="1600" height="595" alt="Rampe und Steilkurve der zweiten Ebene" loading="lazy" decoding="async">
  <div class="ebene__text">
    <div class="wrap">
      <p class="hoehe">+100 m<small>mehr Strecke seit 2023, Rampe, Steilkurve, Zuschauerplattform</small></p>
      <div>
        <h2 id="strecke-h">Zweite Ebene seit 2023</h2>
        <p>Vollgas die Rampe hoch, die Steilkurve in 6 Metern Höhe nehmen und mit Rückenwind bergab in den Tunnel. Rundenzeiten laufen live auf der Großbildleinwand und am Zeitenmonitor an der Strecke. Vor jeder ersten Fahrt gibt es die Einweisung mit Flaggenkunde und Ampelstart.</p>
        <p class="small">Kidskonzept: Für Kinder von 8 bis 12 Jahren ohne Karterfahrung wird die zweite Ebene mit wenigen Handgriffen umfahren. Das entscheidet nur das Streckenpersonal.</p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="karts">
  <div class="wrap">
    <h2>Die Karts</h2>
    <p class="lead">Sodi aus Frankreich, seit September 2023 die fünfte neue Flotte seit 2009. Tägliche Checks, Sitz und Pedale verstellbar, LED-Licht und Bremslicht.</p>
    <div class="grid grid-2" style="align-items:start">
      <figure style="margin:0">
        <img src="assets/img/kart-sodi-front.webp" width="1260" height="430" alt="Sodi SR5 Rennkart von vorn mit Startnummer 4" loading="lazy" decoding="async" class="bank-img">
        <figcaption><h3 style="margin:1rem 0 .4rem">Sodi SR5, 9 PS, ab 13 Jahren und 1,55 m</h3></figcaption>
        <div class="table-wrap"><table><tbody>
          <tr><td>Motor</td><td>9 PS Honda GX 270 mit LPG-Betrieb</td></tr>
          <tr><td>Bremse</td><td>Hydraulische Zweikreis-Bremse, selbstnachstellend</td></tr>
          <tr><td>Reifen, Antrieb</td><td>BEBA Rot, Zahnriemen</td></tr>
          <tr><td>Gewicht</td><td>165 kg</td></tr>
          <tr><td>Ausstattung</td><td>Sitz- und Pedalverstellung, gepolstertes Lenkrad, Überrollbügel, Gas-Brems-System, LED-Lichtpaket mit Bremslicht, E-Starter, Easy-Drive-Lenkung</td></tr>
        </tbody></table></div>
      </figure>
      <figure style="margin:0">
        <img src="assets/img/karts-boxengasse.webp" width="1400" height="933" alt="Kinderkarts und Rennkarts in der Boxengasse" loading="lazy" decoding="async" class="bank-img" style="aspect-ratio:1260/430;object-fit:cover">
        <figcaption><h3 style="margin:1rem 0 .4rem">Sodi LR6, 6,5 PS, ab 8 Jahren und 1,25 m</h3></figcaption>
        <div class="table-wrap"><table><tbody>
          <tr><td>Motor</td><td>6,5 PS Honda GX 200</td></tr>
          <tr><td>Bremse</td><td>Hydraulische Bremse</td></tr>
          <tr><td>Reifen, Antrieb</td><td>Beba Rot, Zahnriemen</td></tr>
          <tr><td>Gewicht</td><td>124 kg</td></tr>
          <tr><td>Ausstattung</td><td>3-Punkt-Sicherheitsgurt, Gas-Brems-System, LED-Beleuchtung mit Bremslicht, Sitz-, Lenkrad- und Pedalverstellung, Überrollbügel</td></tr>
        </tbody></table></div>
      </figure>
    </div>
    <p style="margin-top:1.5rem">Dazu kommen <strong>2 Doppelsitzer</strong>: Kinder ab 4 Jahren und 1,10 m fahren auf dem Beifahrersitz mit, am Steuer sitzt eine volljährige Person. <a href="preise.html#doppelsitzer">Doppelsitzer-Preise</a> ab 18 € für zwei Personen, Reservierung telefonisch ab 2 Tage vorher. Mehr zum Hersteller: <a href="https://www.sodikart.com/de-de/" rel="noopener" target="_blank">sodikart.com</a>.</p>
  </div>
</section>

<section class="section section--flaeche" id="lizenz">
  <div class="wrap split split--rev">
    <img src="assets/img/anmeldung-theke.webp" width="1260" height="430" alt="Anmeldung und Check-in der Celler Kartbahn" loading="lazy" decoding="async">
    <div>
      <h2>Rennlizenz auf dem Handy</h2>
      <p>Beim ersten Besuch registriert sich jeder Fahrer aus versicherungstechnischen Gründen, einmalig 2 € inklusive Rennlizenz. Die Lizenz gibt es als Mobillizenz auf dem Smartphone:</p>
      <ul class="checks">
        <li>Alle deine Rennen auf einen Blick</li>
        <li>Bestzeiten mit Freunden vergleichen</li>
        <li>Livetiming und Rennergebnisse sofort auf dem Handy</li>
        <li>Streckenverlauf, Infos und Bestenlisten</li>
      </ul>
      <p class="small">Sturmhaube inklusive Helmleihe 3 €, Paketpreis Registrierung und Sturmhaube 4 €. Bei Bahnmieten und Kidspartys entfällt die Rennlizenz-Gebühr.</p>
    </div>
  </div>
</section>

<section class="section" id="racecam">
  <div class="wrap grid grid-2" style="align-items:start">
    <div>
      <h2>RaceCam: dein Rennen als Video</h2>
      <p>Direkt nach dem Fahren bekommt ihr euer Rennen per QR-Code aufs Smartphone, in voller Qualität zum Teilen. Erhältlich beim Check-in.</p>
      <div class="table-wrap"><table><tbody>
        <tr><td>1 Durchgang</td><td class="price">5 €</td></tr><tr><td>2 Durchgänge</td><td class="price">9 €</td></tr><tr><td>3 Durchgänge</td><td class="price">12 €</td></tr><tr><td>jeder weitere Durchgang</td><td class="price">3 €</td></tr>
      </tbody></table><p class="price-hint">Ein Durchgang maximal 30 Minuten, bei längeren Rennen 5 € Aufschlag.</p></div>
    </div>
    <div id="bistro">
      <h2>Boxenstopp im Bistro</h2>
      <p>Im Bistro verfolgt ihr den Rennablauf auf den Livemonitoren, mit Erfrischungsgetränken, Red Bull für Rennfahrer und kleinen Snacks. An sonnigen Tagen ist die 2018 neu gestaltete Terrasse geöffnet. Eigene Speisen und Getränke sind nicht gestattet.</p>
      <img src="assets/img/bistro-lounge.webp" width="1400" height="934" alt="Lounge-Bereich im Bistro der Celler Kartbahn" loading="lazy" decoding="async" class="bank-img">
    </div>
  </div>
</section>

<section class="section section--flaeche" id="tipps">
  <div class="wrap">
    <h2>Schneller auf der Strecke</h2>
    <p class="lead">Vier Dinge, die bei uns Rundenzeit bringen. Der Unterschied zwischen zwei Karts liegt bei etwa 0,3 Sekunden pro Runde, der zwischen einer guten und einer schlechten Kurve bei deutlich mehr.</p>
    <div class="grid grid-2">
      <div><h3>Die Ideallinie</h3><p>Von außen an den Scheitelpunkt innen und wieder nach außen herausbeschleunigen. Die Ideallinie ist der kürzeste und schnellste Weg und für jeden Fahrer etwas anders.</p></div>
      <div><h3>Vor der Kurve bremsen</h3><p>Rutschen oder Driften kostet Zeit, weil das Kart Geschwindigkeit verliert. Wer gleichzeitig bremst und lenkt, rutscht. Also vorher bremsen, langsam rein, schnell raus. In den scharfen Kurven gewinnt oder verliert ihr am meisten.</p></div>
      <div><h3>Mein Kart ist langsamer?</h3><p>Meist war die Kurve davor das Problem, dann fehlt am Ausgang Geschwindigkeit. Das Fahrergewicht macht etwa 0,3 Sekunden pro 10 kg und Runde aus. Gewichtsausgleich gibt es bei Rennen und Bahnmieten.</p></div>
      <div><h3>Von Schnelleren lernen</h3><p>Überholen lassen und der Linie des schnelleren Fahrers folgen. Am Zeitenmonitor an der Strecke verschiedene Kurven ausprobieren und die Sektoren vergleichen.</p></div>
    </div>
  </div>
</section>

<section class="section" id="team">
  <div class="wrap">
    <h2>Familienbetrieb seit 2009</h2>
    <p class="lead">Seit Januar 2009 führen wir die Indoor-Kartbahn in Celle. Jede Anfrage bekommt eine persönliche Antwort von einem von uns.</p>
    <ul class="team" aria-label="Das Team">
      <li><img src="assets/img/team-chris.webp" srcset="assets/img/team-chris-480.webp 480w, assets/img/team-chris.webp 960w" sizes="(min-width: 720px) 25vw, 50vw" width="960" height="720" alt="Chris, Geschäftsführer der Celler Kartbahn" loading="lazy" decoding="async"><strong>Chris</strong><span>Geschäftsführer. Strecke, Karts, Marketing, Einkauf, Planung.</span></li>
      <li><img src="assets/img/team-conny.webp" srcset="assets/img/team-conny-480.webp 480w, assets/img/team-conny.webp 960w" sizes="(min-width: 720px) 25vw, 50vw" width="960" height="720" alt="Conny an der Zapfanlage im Bistro" loading="lazy" decoding="async"><strong>Conny</strong><span>Finanzen, Event-Organisation, Buchhaltung, Service.</span></li>
      <li><img src="assets/img/team-susi.webp" srcset="assets/img/team-susi-480.webp 480w, assets/img/team-susi.webp 960w" sizes="(min-width: 720px) 25vw, 50vw" width="960" height="720" alt="Susi am Tresen des Bistros" loading="lazy" decoding="async"><strong>Susi</strong><span>Service im Bistro und Ticketverkauf.</span></li>
      <li><img src="assets/img/team-speedy.webp" srcset="assets/img/team-speedy-480.webp 480w, assets/img/team-speedy.webp 960w" sizes="(min-width: 720px) 25vw, 50vw" width="960" height="720" alt="Speedy, der Hund der Kartbahn, auf einem Kart" loading="lazy" decoding="async"><strong>Speedy</strong><span>Maskottchen. Klein, aber laut.</span></li>
    </ul>
    <p class="small" style="margin-top:1rem">Danke an alle freiwilligen Helfer für die Stunden, Tage und Wochen des Umbaus im Bistro und auf der Strecke.</p>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("kartbahn.html", html)
