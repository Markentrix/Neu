# -*- coding: utf-8 -*-
from common import *

html = head("Strecke, Karts & Bistro | Burnout Celler-Kartbahn",
 "Indoor-Kartbahn Celle: ca. 600 m Strecke mit Brücke, Tunnel und Steilkurve in 6 m Höhe, Sodi SR5 mit 9 PS, Kinderkarts LR6, Doppelsitzer, Bistro mit Terrasse, RaceCam, Rennlizenz-App und Tipps für schnellere Rundenzeiten.",
 breadcrumb("Die Kartbahn","kartbahn.html")) + header()

html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/hero-strecke.webp" width="1260" height="430" alt="Kart in der Kurve der Indoor-Strecke mit Brücke" fetchpriority="high">
  <div class="wrap">
    <span class="eyebrow">Die Kartbahn</span>
    <h1>600 Meter Indoor-Rennstrecke</h1>
    <p class="lead">Brücke, Tunnel und seit 2023 die zweite Ebene mit Steilkurve in 6 Metern Höhe: Unsere Strecke in Celle ist in Norddeutschland einzigartig.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid grid-4">
      <div class="stat"><strong>600 m</strong><span>Streckenlänge</span></div>
      <div class="stat"><strong>6 m</strong><span>Höhe der Steilkurve</span></div>
      <div class="stat"><strong>9 PS</strong><span>Sodi SR5 Rennkarts</span></div>
      <div class="stat"><strong>13</strong><span>Kinderkarts Sodi LR6</span></div>
    </div>
  </div>
</section>

<section class="section section--alt" id="strecke">
  <div class="wrap split">
    <img src="assets/img/zweite-ebene.webp" width="1600" height="595" alt="Rampe und Steilkurve der zweiten Ebene" loading="lazy" decoding="async">
    <div>
      <span class="eyebrow">Strecke</span>
      <h2>Rampe hoch, Steilkurve, Rückenwind bergab</h2>
      <p>Seit Januar 2009 führt ein neues Team die Indoor-Kartbahn in Celle. Auf ca. 600 Metern Asphalt mit Brücke und Tunnel kam 2023 ein neuer Streckenabschnitt dazu: 100 Meter mehr Strecke mit Rampe, Steilkurve und einer Zuschauerplattform, von der ihr hautnah dabei seid.</p>
      <ul class="checks">
        <li>Live-Zeiten auf der Großbildleinwand und dem Zeitenmonitor an der Strecke</li>
        <li>Ampelstart, Flaggenkunde und Einweisung vor jeder ersten Fahrt</li>
        <li>Kidskonzept: Für Kinder 8–12 Jahre ohne Erfahrung wird die 2. Ebene mit wenigen Handgriffen umfahren</li>
      </ul>
    </div>
  </div>
</section>

<section class="section" id="karts">
  <div class="wrap">
    <span class="eyebrow">Kartflotte</span>
    <h2>Die Karts</h2>
    <div class="grid grid-2">
      <div class="card card--img">
        <img src="assets/img/kart-sodi-front.webp" width="1260" height="430" alt="Sodi SR5 Rennkart von vorn mit Startnummer 4" loading="lazy" decoding="async">
        <div class="card__body">
          <h3>Sodi SR5 – seit 09/2023 im Einsatz</h3>
          <p>Die fünfte neue Kartflotte seit 2009. Diesmal Sodi aus Frankreich – geniales Handling, volle Ausstattung.</p>
          <div class="table-wrap" style="margin-top:.8rem"><table><tbody>
            <tr><td>Motor</td><td>9 PS Honda GX 270 mit LPG-Betrieb</td></tr>
            <tr><td>Bremse</td><td>Hydraulische Zweikreis-Bremse, selbstnachstellend</td></tr>
            <tr><td>Reifen / Antrieb</td><td>BEBA Rot / Zahnriemen</td></tr>
            <tr><td>Gewicht</td><td>165 kg</td></tr>
            <tr><td>Rahmen</td><td>ø 31,8 mm Speziallegierung</td></tr>
            <tr><td>Ausstattung</td><td>Sitz- und Pedalverstellung, gepolstertes 4-Speichen-Lenkrad, Überrollbügel, Gas-Brems-System (Kupplungsschutz), LED-Lichtpaket inkl. Bremslicht, E-Starter, Easy-Drive-Lenkung</td></tr>
          </tbody></table></div>
        </div>
      </div>
      <div class="card card--img">
        <img src="assets/img/karts-boxengasse.webp" width="1400" height="933" alt="Kinderkarts und Rennkarts in der Boxengasse" loading="lazy" decoding="async">
        <div class="card__body">
          <h3>Sodi LR6 (2025) – 13 Kinderkarts</h3>
          <p>Für die kleinen Piloten ab 8 Jahren und 1,25 m. Jeder fängt klein an.</p>
          <div class="table-wrap" style="margin-top:.8rem"><table><tbody>
            <tr><td>Motor</td><td>6,5 PS Honda GX 200</td></tr>
            <tr><td>Bremse</td><td>Hydraulische Bremse</td></tr>
            <tr><td>Reifen / Antrieb</td><td>Beba Rot / Zahnriemen</td></tr>
            <tr><td>Gewicht</td><td>124 kg</td></tr>
            <tr><td>Rahmen</td><td>ø 31,8 mm Speziallegierung</td></tr>
            <tr><td>Ausstattung</td><td>3-Punkt-Sicherheitsgurt, Gas-Brems-System, LED-Beleuchtung, Bremslicht, Sitz-, Lenkrad- und Pedalverstellung, Überrollbügel</td></tr>
          </tbody></table></div>
        </div>
      </div>
    </div>
    <div class="grid grid-2" style="margin-top:1.25rem">
      <div class="card"><h3>2 Doppelsitzer</h3><p>Kinder ab 4 Jahren und 1,10 m schnuppern auf dem Beifahrersitz Rennluft – am Steuer eine volljährige Person. Preise für 2 Personen ab 18 €, Reservierung telefonisch ab 2 Tage vorher.</p><a class="more" href="preise.html#doppelsitzer">Doppelsitzer-Preise →</a></div>
      <div class="card"><h3>Herstellerinfos</h3><p>Mehr über unsere Sodi-Karts beim Hersteller: <a href="https://www.sodikart.com/de-de/" rel="noopener" target="_blank">www.sodikart.com</a>. Tägliche, regelmäßige Checks und jahrelange Erfahrung sorgen für ein Höchstmaß an Sicherheit.</p></div>
    </div>
  </div>
</section>

<section class="section section--alt" id="lizenz">
  <div class="wrap split split--rev">
    <img src="assets/img/anmeldung-theke.webp" width="1260" height="430" alt="Anmeldung und Check-in der Celler Kartbahn" loading="lazy" decoding="async">
    <div>
      <span class="eyebrow">Neukunden</span>
      <h2>Registrierung &amp; Rennlizenz fürs Smartphone</h2>
      <p>Beim ersten Besuch muss sich jeder Fahrer aus versicherungstechnischen Gründen registrieren (2 € inkl. Rennlizenz). Die Rennlizenz gibt es nur noch als Mobillizenz auf dem Smartphone – mit vielen Vorteilen:</p>
      <ul class="checks">
        <li>Alle deine Rennen auf einen Blick</li>
        <li>Bestzeiten mit Freunden vergleichen</li>
        <li>Livetiming und Rennergebnisse sofort auf dem Handy</li>
        <li>Streckenverlauf, Infos und Bestenlisten</li>
      </ul>
      <p class="small">Sturmhaube inkl. Helmleihe 3 €, Paketpreis Registrierung + Sturmhaube 4 €. Die Kosten der Rennlizenz entfallen bei Bahnmieten und Kidspartys. Einfach registrieren und startklar fürs Rennen.</p>
    </div>
  </div>
</section>

<section class="section" id="racecam">
  <div class="wrap grid grid-2" style="align-items:start">
    <div>
      <span class="eyebrow">Neu</span>
      <h2>RaceCam – dein Rennen. Für immer.</h2>
      <p>Direkt nach dem Fahren bekommt ihr euer Rennen per QR-Code zum Download aufs Smartphone: schnell, unkompliziert, in bester Qualität. Teilt euer Rennen mit Freunden und Familie. Erhältlich beim Check-in.</p>
      <div class="table-wrap"><table><tbody>
        <tr><td>1 Durchgang / Rennen</td><td class="price">5 €</td></tr><tr><td>2 Durchgänge</td><td class="price">9 €</td></tr><tr><td>3 Durchgänge</td><td class="price">12 €</td></tr><tr><td>jeder weitere Durchgang</td><td class="price">3 €</td></tr>
      </tbody></table><p class="price-hint">Ein Durchgang maximal 30 Minuten, bei längeren Rennen 5 € Aufschlag.</p></div>
    </div>
    <div id="bistro">
      <span class="eyebrow">Bistro &amp; Terrasse</span>
      <h2>Boxenstopp mit Aussicht</h2>
      <p>Im Bistro findet jeder einen gemütlichen Platz, um Wartezeiten zu überbrücken oder den Rennablauf auf den Livemonitoren zu verfolgen. Neben Erfrischungsgetränken (bis zum Red Bull für Rennfahrer) gibt es kleine Snacks für den kleinen Hunger. An sonnigen Tagen ist die 2018 neu gestaltete Terrasse geöffnet.</p>
      <img src="assets/img/bistro-lounge.webp" width="1400" height="934" alt="Lounge-Bereich im Bistro der Celler Kartbahn" loading="lazy" style="border-radius:14px">
    </div>
  </div>
</section>

<section class="section section--alt" id="tipps">
  <div class="wrap">
    <span class="eyebrow">Tipps &amp; Tricks</span>
    <h2>Schneller werden auf der Strecke</h2>
    <div class="grid grid-2">
      <div class="card"><h3>Die Ideallinie</h3><p>Der kürzeste und schnellste Weg zur Bestzeit – und für jeden Fahrer etwas anders. Grundprinzip jeder Kurve: von außen nach innen zum Scheitelpunkt und wieder nach außen herausbeschleunigen.</p></div>
      <div class="card"><h3>Wie fahre ich eine Kurve?</h3><p>Rutschen oder Driften kostet Zeit, weil das Kart Geschwindigkeit verliert. Vor der Kurve bremsen, damit ihr in der Kurve nicht mehr bremsen müsst: langsam rein, schnell raus. In den scharfen Kurven gewinnt oder verliert ihr die meiste Zeit.</p></div>
      <div class="card"><h3>Mein Kart beschleunigt schlechter?</h3><p>Meist wurde nur die Kurve davor schlechter genommen – dann fehlt am Ausgang Geschwindigkeit. Der Unterschied zwischen den Karts liegt bei nur ca. 0,3 Sekunden pro Runde; das Fahrergewicht macht etwa 0,3 Sekunden pro 10 kg aus. Gewichtsausgleich gibt es bei Rennen und Bahnmieten.</p></div>
      <div class="card"><h3>Wie werde ich besser?</h3><p>Schnellere Fahrer überholen lassen und ihrer Linie folgen. Am Zeitenmonitor an der Strecke verschiedene Kurven ausprobieren und vergleichen.</p></div>
    </div>
  </div>
</section>

<section class="section" id="team">
  <div class="wrap">
    <span class="eyebrow">Über uns</span>
    <h2>Ein Familienbetrieb mit starkem Serviceteam</h2>
    <p class="muted">Seit Januar 2009 führen wir die Indoor-Kartbahn in Celle. Ob Kindergeburtstag, Firmenevent oder Vereinsfeier – wir erstellen jederzeit ein exklusives Angebot und setzen eure Wünsche schnell um. Ein großes Dankeschön an alle freiwilligen Helfer für die harten Stunden, Tage und Wochen des Umbaus im Bistro und auf der Strecke.</p>
    <div class="grid grid-4">
      <div class="card"><h3>Chris</h3><p><strong>Geschäftsführer</strong> – der Mann für alles, was Strecke, Karts, Marketing, Einkauf, Erneuerung und Planung angeht.</p></div>
      <div class="card"><h3>Conny</h3><p><strong>Finanzministerin</strong> – Mama der Kartbahn: Sauberkeit, Event-Organisation, Buchhaltung und Service.</p></div>
      <div class="card"><h3>Susi</h3><p><strong>Servicekraft</strong> – sorgt mit langer Erfahrung für das leibliche Wohl im Bistro und verkauft euch die Tickets.</p></div>
      <div class="card"><h3>Speedy</h3><p><strong>Hund &amp; Maskottchen</strong> der Kartbahn Burnout – klein, aber laut.</p></div>
    </div>
  </div>
</section>
''' + contact_strip() + footer() + end()
write("kartbahn.html", html)
