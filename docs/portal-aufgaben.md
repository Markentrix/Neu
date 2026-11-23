# Aufgaben im Markentrix-Portal (aus dem Prüfbericht vom 21.11.2026)

Diese Punkte liegen nicht in der ElbDetail-Website, sondern im gemeinsamen Portal-Skript `portal.markentrix.de/static/js/site.js` oder in der Portal-Verarbeitung. **Änderungen am Skript wirken auf alle Kundenwebsites**, die es einbinden. Vorher auf einer Testseite prüfen.

## 1. Analytics-Widerruf technisch wirksam machen (A04, P1)

**Befund im ausgelieferten Skript (Stand 21.11.2026):**
- `banner()` → „Ablehnen“ ruft nur `merke('nein')` auf und schließt das Fenster. Wurde vorher „Erlauben“ geklickt (auch über „Statistik-Einstellungen“ auf derselben Seite), ist `gtag.js` schon geladen und sendet in diesem Seitenaufruf weiter.
- Die Cookies `_ga` und `_ga_<ID>` bleiben nach dem Widerruf stehen.
- Es gibt kein Consent Mode (`gtag('consent', …)`) und kein `window['ga-disable-<ID>']`.
- `anonymize_ip` wirkt in Google Analytics 4 nicht. Der Bannertext „Wir möchten anonym zählen“ trifft auf GA4 nicht zu.
- Das Fenster nennt keine Speicherdauer, keinen Anbieter und keine Drittlandübermittlung.
- `data-datenschutz` ist auf allen Seiten `/datenschutz.html`, auch auf den englischen Seiten unter `/en/`.

**Vorschlag (Kern, im Portal-Skript):**

```js
function gaAus(id) {
  window['ga-disable-' + id] = true;                       // gtag sendet nichts mehr
  if (window.gtag) window.gtag('consent', 'update', { analytics_storage: 'denied' });
  var host = location.hostname.split('.'), domains = [];
  for (var i = 0; i < host.length - 1; i++) domains.push(host.slice(i).join('.'));
  document.cookie.split(';').forEach(function (c) {
    var n = c.split('=')[0].trim();
    if (n === '_ga' || n.indexOf('_ga_') === 0) domains.concat(['']).forEach(function (d) {
      document.cookie = n + '=; Max-Age=0; path=/' + (d ? '; domain=.' + d : '');
    });
  });
}
function gaLaden(id) {
  if (window.__mkGa) { window['ga-disable-' + id] = false; window.gtag('consent', 'update', { analytics_storage: 'granted' }); return; }
  window.__mkGa = true;
  window.dataLayer = window.dataLayer || []; window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag('consent', 'default', { analytics_storage: 'granted', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });
  window.gtag('js', new Date()); window.gtag('config', id);
  document.head.appendChild(el('script', { async: true, src: 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id) }));
}
// im Banner: nein.addEventListener('click', function () { merke('nein'); gaAus(id); b.remove(); });
// in „Statistik-Einstellungen“: vor dem erneuten Fragen gaAus(a.id) aufrufen, nicht nur den Speicher leeren.
```

**Bannertext ohne „anonym“, mit Pflichtangaben**, z. B.: „Wir möchten mit Google Analytics (Google Ireland Limited) auswerten, wie unsere Website genutzt wird. Dabei setzt Google Cookies (bis zu 2 Jahre) und Daten können in die USA übermittelt werden. Nur mit Ihrer Zustimmung, jederzeit widerrufbar über „Statistik-Einstellungen“.“ Die englische Fassung zeigt das Portal auf Seiten mit `<html lang="en">`, dort mit Link auf `/en/datenschutz.html`.

**Abnahme mit Netzwerkprotokoll** (Browser-Entwicklertools, Filter `google-analytics.com` und `googletagmanager.com`):
1. Frischer Besuch ohne Auswahl → keine Anfrage an Google.
2. „Ablehnen“ → keine Anfrage, kein `_ga`-Cookie.
3. „Erlauben“ → `gtag/js` und `collect`-Anfragen.
4. „Statistik-Einstellungen“ → „Ablehnen“ auf derselben Seite → keine weiteren `collect`-Anfragen, `_ga`-Cookies gelöscht.
5. Seitenwechsel und Neuladen → weiterhin nichts.

## 2. Widerruf ohne Einwilligungsfeld annehmen (A06, P1)

Die Website sendet beim Widerruf (`typ: "widerruf"`) **kein Feld `einwilligung` mehr**. Rechtsgrundlage ist Art. 6 Abs. 1 lit. c DSGVO, eine Einwilligung darf keine Hürde sein. Pflicht sind `name`, `email` und **entweder** `vorgang` **oder** `nachricht` (Beschreibung des Vertrags).

- Das Portal muss `typ=widerruf` ohne `einwilligung` annehmen. **Solange es das nicht tut, scheitert der Widerruf mit 422**. Die Website zeigt dann WhatsApp, E-Mail und Telefon als Ausweg, aber das darf live nicht so bleiben.
- Die Eingangsbestätigung per E-Mail muss beim Widerruf **den Inhalt des Widerrufs** (Name, E-Mail, Vorgangsnummer bzw. Beschreibung) **sowie Datum und Uhrzeit des Eingangs** enthalten (§ 356a BGB), nicht nur die Vorgangsnummer.

## 3. Einwilligungsfeld der übrigen Formulare (A07)

Kontakt, Termin, Gutschein und Firmenkunden senden weiter `einwilligung: "ja"`. Das Häkchen bedeutet jetzt „Datenschutzhinweise zur Kenntnis genommen“, keine Einwilligung (Rechtsgrundlage Vertrag bzw. Vertragsanbahnung). Im Portal den Feldnamen bzw. die Anzeige entsprechend lesen und nicht als Marketing-Einwilligung verwenden.

## 4. Weitere Portal-Einstellungen

- **Empfänger für Anfragen** eintragen (bisher „Kein Empfänger eingetragen“).
- **Google-Bewertungen**: Abfrage scheitert („Google lehnt die Abfrage ab“). Places API (New), Abrechnung und Schlüssel-Beschränkung prüfen, Ergebnis zwischenspeichern.
- **Buchungszeitraum** von 3 Wochen auf mindestens 3 Monate.
- **Eine Hauptadresse (Prüfbericht vom 21.11.2026, „HTTPS und einheitliche Hauptadresse“):** `https://elbdetail.de/` und `http://…` per 301 auf `https://www.elbdetail.de/` leiten (gleicher Pfad). Canonical, Sitemap und hreflang der Website nennen bereits `https://www.elbdetail.de/`.
- **Suchbegriffe im Prüf-Profil:** „Fahrzeugaufbereitung & Autoaufbereitung Celle“ ist der Seitentitel, kein Suchbegriff. Besser als zwei Einträge „Fahrzeugaufbereitung Celle“ und „Autoaufbereitung Celle“ führen. Die Website erfüllt seit dem 23.11.2026 trotzdem beide Schreibweisen (Titel und H1 der Startseite).

## 5. Hinweise zum automatischen Prüfbericht

- **„Keine überholten Angaben: Google Maps“** ist ein Fehlalarm. Die Karte steht auf `/kontakt.html` und wird erst nach Klick auf „Karte laden“ eingebunden, deshalb findet der Prüfer sie beim Abruf nicht. Die Datenschutzerklärung nennt jetzt ausdrücklich die Kontaktseite.
- **„Preise mit Hinweis zur Umsatzsteuer“** betraf nur die englischen Seiten: Der Prüfer erkennt „VAT“ nicht. Seit dem 23.11.2026 steht dort „no VAT (Umsatzsteuer) is charged“ (§ 19 Abs. 1 UStG) im Fußbereich jeder Seite und an den Preisen.
