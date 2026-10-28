# -*- coding: utf-8 -*-
from common import *
import json, html as H

FAQ = [
 ("Ab welchem Alter darf man auf der Celler Kartbahn fahren?", "Ab dem 8. Lebensjahr und einer Mindestgröße von 1,25 m im Kinderkart. Unter 1,25 m lässt sich das Bremspedal nicht vollständig bedienen; das Mindestalter ist aus versicherungstechnischen Gründen nicht zu umgehen. Kinder ab 4 Jahren und 1,10 m dürfen im Doppelsitzer bei Mama oder Papa mitfahren."),
 ("Wann darf mein Kind im großen Kart fahren?", "Ab 13 Jahren und 1,55 m Mindestgröße, mit Karterfahrung ab 12 Jahren und 1,55 m. Ausnahmen gibt es nur für Kinder, die regelmäßig und sicher bei uns fahren (mindestens 3 Turns mit 39er-Zeiten im Kinderkart innerhalb eines Jahres, mindestens 1,50 m und 10 Jahre). Diese Entscheidung trifft ausschließlich das Bahnpersonal."),
 ("Was kostet Kartfahren in Celle?", "Eine 10-Minuten-Fahrt kostet am Wochenende 15 € für Erwachsene und 13,50 € für Kinder, freitags 14 € bzw. 12 €. Montag bis Donnerstag gibt es 3 Fahrten zum Preis von 2 (30 € / 27 €) oder 5 zum Preis von 3 (43 € / 36 €). Neukunden zahlen einmalig 2 € Registrierung inkl. Rennlizenz; die Sturmhaube inkl. Helmleihe kostet 3 €."),
 ("Kann ich Fahrten online buchen oder Tickets vorab kaufen?", "Ja. Ab 5 Personen reserviert ihr Fahrten, Kidspartys, Supercup-Rennen, Bahnmieten und Schulklassen-Events online über unsere Buchungsseite. Gutscheine und Fahrt-Tickets könnt ihr auf der Gutschein-Seite vorab kaufen und per E-Mail erhalten. Unter 5 Personen reserviert ihr telefonisch ab 2 Tage vorher."),
 ("Muss ich reservieren?", "Nein, ihr könnt auch spontan vorbeikommen. Unter 5 Personen ist eine Reservierung telefonisch ab 2 Tage vorher möglich. Ab 5 Personen reserviert ihr online weit im Voraus; bei kurzfristigen Besuchen innerhalb der nächsten 3 Tage bitte telefonisch innerhalb der Öffnungszeiten."),
 ("Wie sind die Öffnungszeiten?", "Montag bis Freitag ab 15 Uhr (in den niedersächsischen Schulferien ab 13 Uhr), Samstag ab 13 Uhr, Sonntag ab 11 Uhr – jeweils Open End. Je nach Auslastung schließen wir unter der Woche zum Beispiel gegen 21 Uhr. Vor einem spontanen Besuch bitte kurz anrufen."),
 ("Ist Kartfahren gefährlich?", "Solange ihr euch an die Regeln der Einweisung und die Anweisungen des Personals haltet, ist es nicht gefährlich – garantieren kann man aber nie etwas, so wie beim Fahrradfahren auch. Bei uns ist noch nie etwas Schwerwiegendes passiert. Wir sichern uns durch einen Haftungsausschluss ab; Fragen dazu beantworten wir gern per Mail oder Telefon."),
 ("Was muss ich zum ersten Besuch mitbringen?", "Beim ersten Besuch registriert sich jeder Fahrer (2 € inkl. Rennlizenz als Mobillizenz fürs Smartphone). Minderjährige bringen die ausgefüllte Einverständniserklärung der Eltern mit (Download auf unserer Website). Festes Schuhwerk ist empfehlenswert; Helme leihen wir, Sturmhauben gibt es für 3 €."),
 ("Wie lange dauert eine Fahrt und wie viele Karts sind gleichzeitig auf der Strecke?", "Eine Ticketfahrt dauert 10 Minuten. Bei Bahnmieten können maximal 16 Karts gleichzeitig fahren. Plant mindestens 30 Minuten vor der Startzeit für Registrierung und Einweisung ein."),
 ("Was kostet ein Kindergeburtstag?", "Die Kidsparty gibt es ab 6 Kindern: Paket F1 mit 3 × 10 Minuten für 40 € pro Kind oder Paket F2 im Grand-Prix-Modus (40 Minuten Fahrzeit) für 48 € pro Kind – jeweils mit Partytisch, 2 Softdrinks, Geschenk für das Geburtstagskind, Sturmhaube und Helmleihe. Pizzapaket 10,50 €, jede weitere 10 Minuten 8 €."),
 ("Darf ich eigene Speisen, Kuchen oder Getränke mitbringen?", "Nein. Durch unsere Gastronomie sind eigene Speisen, Kuchen, Gebäck und Getränke nicht gestattet. Bei Kidspartys ist der Geburtstagstisch mit Süßigkeiten und Chips gedeckt; für Schulklassen gibt es Softdrinks für 1,50 € pro Glas."),
 ("Was kostet die Bahnmiete für Firmenevents?", "Die exklusive Bahnmiete kostet 650 € pro Stunde inkl. 10 Karts (546,22 € netto), jede weitere halbe Stunde 325 €. Jedes weitere Kart kostet 65 € pro Stunde. Mindestmietdauer 1 Stunde, maximal 16 Karts gleichzeitig. Für 6–17 Personen bieten wir Supercup-Rennen ab 39 € pro Person."),
 ("Wie bezahle ich?", "Vor Ort in bar oder mit EC-Karte. Online wird bei der Buchung nichts bezahlt. Gutscheine könnt ihr online per PayPal kaufen oder per Überweisung bestellen."),
 ("Wie komme ich zur Celler Kartbahn?", "Burnout Celler-Kartbahn, Waldweg 100, 29221 Celle. Vom Bahnhof Celle sind es maximal 20 Minuten zu Fuß; Parkplätze gibt es direkt am Haus. Aus Hannover, Lüneburg, Gifhorn und Uelzen seid ihr schnell bei uns."),
 ("Gibt es Live-Zeiten und ein Video vom Rennen?", "Ja. Rundenzeiten seht ihr auf der Großbildleinwand, am Zeitenmonitor an der Strecke und in der Rennlizenz-App auf dem Smartphone. Mit der RaceCam bekommt ihr euer Rennen direkt nach dem Fahren per QR-Code aufs Handy (ab 5 €, erhältlich beim Check-in)."),
]

ld = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ]}
jsonld = '<script type="application/ld+json">'+json.dumps(ld, ensure_ascii=False)+'</script>' + breadcrumb("FAQ","faq.html")

html = head("FAQ Kartfahren in Celle | Burnout Celler-Kartbahn",
 "Antworten auf die häufigsten Fragen: Mindestalter und Größe, Preise, Reservierung, Öffnungszeiten, Kindergeburtstag, Firmenevents, Bezahlung, Anfahrt und Sicherheit auf der Celler Kartbahn.",
 jsonld) + header()
items = "".join(f'<details{" open" if i==0 else ""}><summary>{H.escape(q)}</summary><div class="faq__body"><p>{H.escape(a)}</p></div></details>' for i,(q,a) in enumerate(FAQ))
html += f'''
<section class="section">
  <div class="wrap">
    <span class="eyebrow">FAQ</span>
    <h1>Häufige Fragen</h1>
    <p class="lead">Alles, was ihr vor dem ersten Besuch wissen wollt – kurz und klar. Eure Frage ist nicht dabei? Ruft an unter <a href="{TEL_LINK}">{TEL}</a> oder schreibt per <a href="{WA_LINK}" rel="noopener" target="_blank">WhatsApp</a>.</p>
    <div class="faq" style="max-width:860px">{items}</div>
    <div class="pill-row" style="margin-top:1.5rem">
      <a class="btn btn--primary" href="buchen.html">Jetzt buchen</a>
      <a class="btn btn--ghost" href="preise.html">Preise</a>
      <a class="btn btn--ghost" href="kontakt.html">Kontakt</a>
    </div>
  </div>
</section>
''' + footer() + end()
write("faq.html", html)

# ---------------- KONTAKT ----------------
html = head("Kontakt & Anfahrt | Burnout Celler-Kartbahn Celle",
 "Kontakt zur Celler Kartbahn: Telefon 05141 908650, WhatsApp, E-Mail und Kontaktformular. Anfahrt Waldweg 100, 29221 Celle – 20 Minuten vom Bahnhof, Parkplätze am Haus. Öffnungszeiten.",
 breadcrumb("Kontakt","kontakt.html")) + header()
html += f'''
<section class="section">
  <div class="wrap">
    <span class="eyebrow">Kontakt &amp; Anfahrt</span>
    <h1>Wir freuen uns auf euch</h1>
    <p class="lead">Fragen zu Terminen, Gruppen oder Angeboten? Ruft an, schreibt per WhatsApp oder nutzt das Formular – ihr bekommt eine Eingangsbestätigung mit Vorgangsnummer.</p>
    <div class="grid grid-3">
      <a class="card card--link" href="{TEL_LINK}"><div class="card__icon">{ICONS["phone"]}</div><h3>Telefon</h3><p>{TEL}<br><span class="small">während der Öffnungszeiten · Fax 05141 908652</span></p></a>
      <a class="card card--link" href="{WA_LINK}" rel="noopener" target="_blank"><div class="card__icon">{ICONS["wa"]}</div><h3>WhatsApp</h3><p>+49 152 31394662<br><span class="small">Nachricht schreiben, wir antworten schnell</span></p></a>
      <a class="card card--link" href="mailto:{MAIL}"><div class="card__icon">{ICONS["mail"]}</div><h3>E-Mail</h3><p>{MAIL}<br><span class="small">Terminanfragen, Angebote, Rechnungen</span></p></a>
    </div>
  </div>
</section>

<section class="section section--alt">
  <div class="wrap grid grid-2" style="align-items:start">
    <form class="form" data-mk-form="kontakt" action="danke.html" method="post">
      <fieldset>
        <legend>Nachricht senden</legend>
        <div class="field"><label for="k-anliegen">Anliegen</label><select id="k-anliegen" name="anliegen"><option>Allgemeine Frage</option><option>Firmenevent / Weihnachtsfeier</option><option>Kindergeburtstag</option><option>Schulklasse</option><option>Buffet / Veranstaltungsraum</option><option>Gutschein</option><option>Rechnung</option><option>Sonstiges</option></select></div>
        <div class="fields-2">
          <div class="field"><label for="k-name">Name *</label><input type="text" id="k-name" name="name" autocomplete="name" required><span class="error"></span></div>
          <div class="field"><label for="k-firma">Firma / Verein</label><input type="text" id="k-firma" name="firma" autocomplete="organization"></div>
        </div>
        <div class="fields-2">
          <div class="field"><label for="k-email">E-Mail *</label><input type="email" id="k-email" name="email" autocomplete="email" required><span class="error"></span></div>
          <div class="field"><label for="k-tel">Telefon</label><input type="tel" id="k-tel" name="telefon" autocomplete="tel" inputmode="tel"></div>
        </div>
        <div class="fields-2">
          <div class="field"><label for="k-datum">Wunschtermin (optional)</label><input type="date" id="k-datum" name="wunschtermin"></div>
          <div class="field"><label for="k-personen">Personenzahl (optional)</label><input type="number" id="k-personen" name="personen" min="1" max="200" inputmode="numeric"></div>
        </div>
        <div class="field"><label for="k-nachricht">Nachricht *</label><textarea id="k-nachricht" name="nachricht" required placeholder="Personenzahl, Datum und Wünsche bitte erwähnen"></textarea><span class="error"></span></div>
        <div class="field hp" aria-hidden="true"><label for="k-website">Website</label><input type="text" id="k-website" name="website" tabindex="-1" autocomplete="off"></div>
        <div class="field field--check"><input type="checkbox" id="k-einw" name="einwilligung" value="ja" required><label for="k-einw">Ich bin damit einverstanden, dass meine Angaben zur Beantwortung meiner Anfrage verarbeitet werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>. *</label><span class="error"></span></div>
        <div class="form-status" role="alert" aria-live="polite"></div>
        {fallback_box()}
        <button class="btn btn--primary btn--block" type="submit" style="margin-top:1rem">Nachricht senden</button>
      </fieldset>
    </form>
    <div>
      <h2>Anfahrt</h2>
      <address style="font-style:normal;margin-bottom:1rem"><strong>Burnout Celler-Kartbahn GmbH</strong><br>Waldweg 100<br>29221 Celle<br>Niedersachsen</address>
      <div class="map" data-map="https://www.openstreetmap.org/export/embed.html?bbox=10.0514%2C52.6038%2C10.0714%2C52.6138&amp;layer=mapnik&amp;marker=52.6088%2C10.0614" style="margin-bottom:1rem">
        <div class="map__consent">
          <strong>Karte anzeigen</strong>
          <p>Mit Klick wird die Karte von OpenStreetMap geladen. Dabei werden Daten (z.&nbsp;B. eure IP-Adresse) an die OpenStreetMap Foundation übertragen. Details in der <a href="datenschutz.html#karte">Datenschutzerklärung</a>.</p>
          <button class="btn btn--primary btn--sm" type="button">Karte laden</button>
        </div>
      </div>
      <div class="pill-row">
        <a class="btn btn--ghost btn--sm" href="https://www.google.com/maps/dir/?api=1&amp;destination=Waldweg+100,+29221+Celle" rel="noopener" target="_blank">Route mit Google Maps</a>
        <a class="btn btn--ghost btn--sm" href="https://www.openstreetmap.org/directions?to=52.6088%2C10.0614" rel="noopener" target="_blank">Route mit OpenStreetMap</a>
      </div>
      <ul class="checks" style="margin-top:1rem">
        <li><strong>Zu Fuß:</strong> vom Bahnhof Celle in maximal 20 Minuten</li>
        <li><strong>Mit dem Auto:</strong> kostenlose Parkplätze direkt am Haus</li>
        <li><strong>Aus der Region:</strong> Hannover, Lüneburg, Gifhorn, Uelzen, Soltau, Wolfsburg</li>
      </ul>
      <h2 style="margin-top:1.5rem">Öffnungszeiten</h2>
      <div class="card">
        <ul class="hours">
          <li><span>Montag – Freitag</span><span>15:00 – Open End</span></li>
          <li><span>Mo – Fr in den Ferien</span><span>13:00 – Open End</span></li>
          <li><span>Samstag</span><span>13:00 – Open End</span></li>
          <li><span>Sonntag</span><span>11:00 – Open End</span></li>
        </ul>
        <p class="small" style="margin:.8rem 0 0">Open End: Wir schließen je nach Auslastung, unter der Woche z.&nbsp;B. gegen 21 Uhr. Bitte vor einem spontanen Besuch kurz anrufen.</p>
      </div>
    </div>
  </div>
</section>
''' + footer() + end()
write("kontakt.html", html)
