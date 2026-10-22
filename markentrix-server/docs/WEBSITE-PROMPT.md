# Prompt für Claude Code: Kunden-Website bauen, die bei uns sofort läuft

Diesen Text am Anfang jedes Website-Projekts einfügen. Platzhalter in `<…>` ausfüllen. Gegenstück zur Technik: `WEBSITE-API.md`.

```
AUFGABE
Baue eine statische Website für <Firma, Branche, Ort>. Sprache: Deutsch. Sie wird auf dem Server von Markentrix gehostet und
mit dem Markentrix-Portal verbunden. Gewünschte Funktionen: <Kontaktformular | Terminbuchung | Leistungen/Mitarbeiter | PayPal | Google-Bewertungen | Statistik>.

HARTE REGELN (der Upload lehnt sonst ab oder die Seite funktioniert nicht)
- KEIN eigenes Backend: keine Python-/Node-Server, kein PHP, keine Datenbank, kein Docker, kein Admin-Bereich, keine Serverfunktionen.
  Alles Dynamische läuft über das Portal (Schnittstellen unten). Fehlt eine Funktion, baue sie NICHT selbst, schreibe am Ende, was fehlt.
- Abgabe: Ordner "website-fertig/" mit index.html direkt darin (kein Unterordner dazwischen). Bei Frameworks nur den fertigen Export
  (Next.js "output: export", Astro, Vite "dist") liefern, ohne node_modules und ohne Build-Skripte.
- Erlaubte Dateien: html, css, js, json, xml, txt, ico, png, jpg, webp, avif, gif, svg, woff, woff2, ttf, otf, webmanifest, pdf, mp4, webm, mp3.
  Verboten: .php, .exe, .sh, Symlinks, versteckte Dateien (.env, .git), absolute Pfade, "../" in Pfaden. Größe: ZIP bis 120 MB.
- Alles relativ verlinken (/seite.html oder seite.html), nie http://, nie localhost/127.0.0.1, keine festen Domain-Namen im Code.
- Seiten: index.html, impressum.html, datenschutz.html, 404.html, danke.html (für Formulare), sitemap.xml, robots.txt, favicon.
- Jede Seite: <html lang="de">, <title> (unter 60 Zeichen), <meta name="description">, <meta name="viewport" content="width=device-width, initial-scale=1">,
  genau eine <h1>, alt-Text an allen Bildern, Impressum und Datenschutz im Footer verlinkt, mindestens ein tel:- oder mailto:-Link auf der Startseite.
- Bilder: unter 1,5 MB, als webp/avif, mit width/height. Kein Lorem ipsum, keine Platzhaltertexte, keine toten Links.

DATENSCHUTZ (Deutschland, DSGVO)
- Schriften LOKAL einbinden (woff2 im Ordner), KEINE Google Fonts, keine Fremd-CDNs (jsDelivr, cdnjs, unpkg), keine Fremd-Icons per URL.
- Keine YouTube-/Google-Maps-/Facebook-Einbettungen direkt. Wenn nötig: Zwei-Klick-Lösung (Platzhalter, erst nach Klick laden) und im Text darauf hinweisen.
- Kein eigenes Cookie-Banner und kein eigenes Analytics bauen. Statistik und Einwilligung kommen vom Portal (siehe unten).
- Jedes Formular hat eine Einwilligungs-Checkbox mit Link zur Datenschutzerklärung (Pflichtfeld "einwilligung").
- Impressum und Datenschutz mit den echten Firmendaten füllen: <Firmenname, Inhaber, Anschrift, Telefon, E-Mail, USt-ID/Steuernummer>.
  Die Datenschutzerklärung nennt: Kontaktformular, ggf. Terminbuchung, ggf. Google-Bewertungen, ggf. PayPal, Server-Logs, Hosting bei Markentrix.
  Fehlt eine Angabe, schreibe sie als Liste "OFFEN:" an das Ende deiner Antwort, erfinde nichts.

WIE DIE WEBSITE MIT DEM PORTAL SPRICHT: ZWEI VARIANTEN, WÄHLE GENAU EINE PRO FUNKTION
Variante A, Bausteine (schnell, einheitliches Standarddesign): Platzhalter-Element in die Seite setzen, das Skript fügt Markentrix beim Hochladen
automatisch ein (NICHT selbst einbinden, kein data-site eintragen):
  <div data-mk="kontakt"></div>      Kontaktformular
  <div data-mk="termin"></div>       Terminbuchung
  <div data-mk="bewertungen"></div>  Google-Bewertungen
  <div data-mk="paypal" data-betrag="49,90" data-titel="Gutschein"></div>
  <div data-mk="preise"></div>      Preisliste, immer aktuell aus dem Portal (nie Preise fest in die Seite schreiben)
  <span data-mk="cookies"></span>    Statistik-Einstellung im Footer
  Die Bausteine lassen sich per CSS stylen (Klassen beginnen mit "mk-"). Ist ein Dienst im Portal ausgeschaltet, bleibt das Element leer: Platz dafür
  großzügig lassen und eine Alternative zeigen (Telefon, E-Mail).

Variante B, eigene Oberfläche über die Website-API (volle Designfreiheit, z. B. Friseur/Werkstatt mit eigenem Buchungsformular).
Gleiche Domain, relative Pfade, JSON:
- GET  /api/verfuegbarkeit -> {blocked:[Datum], closedWeekdays:[0-6, 0=So], nextFree:Datum|null, selfBooking:bool, slotTimes:["08:00",…]}
- GET  /api/slots?tag=JJJJ-MM-TT -> {tag, slots:[{zeit:"08:00", frei:true|false}]}
- GET  /api/leistungen -> {leistungen:[{key,name,beschreibung,preis,dauer}]}   (nur wenn der Betrieb Leistungen mit Dauer hat)
- GET  /api/mitarbeiter -> {mitarbeiter:[{key,name,leistungen:[key]}]}        (nur wenn mehrere Personen buchbar sind)
  Bei Leistungen/Personen: /api/slots und /api/verfuegbarkeit mit ?leistung=<key>&mitarbeiter=<key> (leer = egal) aufrufen und beim Buchen
  leistung und mitarbeiter mitsenden. Auswahllisten IMMER aus den beiden Endpunkten bauen, nie fest eintragen.
- POST /api/anfrage (JSON), Felder:
    typ = "kontakt" | "termin" | "gutschein" | "firma" | "widerruf"
    name*, telefon, email, nachricht, einwilligung ("ja", Pflicht), weitere Felder frei (leistung, paket, fahrzeug …)
    bei typ="termin": datum* (JJJJ-MM-TT), uhrzeit (aus /api/slots), telefon*, email* (Bestätigung geht dorthin)
    Lockfeld "website": unsichtbares Textfeld (display:none, tabindex=-1, autocomplete=off), muss LEER bleiben
  Erfolg: {ok:true, ref:"…"} -> weiterleiten auf danke.html?typ=<typ>&ref=<ref> und dort die Vorgangsnummer zeigen
  Fehler: HTTP 422 {ok:false, errors:{feldname:"Text"}} -> Text am Feld anzeigen; HTTP 429 -> "Bitte später noch einmal"
- POST /api/e {t:"pv"|"ev", u:Pfad, n:Name, w:Breite} per navigator.sendBeacon, ohne Cookies (optional, Besucherzahlen)
Regeln für Variante B:
- Uhrzeiten nur anbieten, wenn /api/slots frei:true meldet; gesperrte Tage aus /api/verfuegbarkeit sperren. Wenn selfBooking:false ist,
  heißt das Formular "Terminwunsch" (Antwort folgt), nicht "Termin buchen".
- Gleichzeitige Buchung derselben Zeit: der Server lässt genau eine gewinnen, die andere bekommt 422 auf "uhrzeit": Slots neu laden und das zeigen.
- Doppelklick verhindern (Button sperren während des Sendens), Eingaben bei Fehlern NICHT löschen.
- Bei Fehlern oder fehlendem Server immer eine Ausweichmöglichkeit zeigen (Telefon, WhatsApp, E-Mail).
- Leistungen, Preise, Dauer, Anzahlung und Freigabe pflegt der Betrieb im Portal. Preislisten und Auswahllisten IMMER aus /api/leistungen (oder data-mk="preise") bauen, nie fest eintragen. Pakete und Fahrzeugklassen kennt nur die Website, das Portal speichert sie als Text. Leistung hat freigabe:true oder selfBooking:false → Formular „Terminwunsch“, Hinweis „Wir bestätigen Ihren Termin“. Hat die Leistung eine Anzahlung, zeige den Betrag und den Hinweis „Den Zahlungslink bekommen Sie per E-Mail“. Uhrzeiten müssen zu den "Festen Uhrzeiten" im Portal passen.

ZAHLUNG: Keine eigene Zahlungsabwicklung, keine Kartenfelder, kein eigenes PayPal-Skript. Nur das Element data-mk="paypal" (Variante A)
oder ein PayPal.Me-Link (Anzahlung). Das Geld geht direkt an den Kunden. Gutscheine sind eine Anfrage (typ="gutschein", Felder name, email Pflicht, betrag z. B. "50" oder "50 €", empfaenger, widmung, einwilligung). Zahlungslink und Code verschickt der Inhaber im Portal (Website-Dienste → Gutschein-Anfragen); die Website zeigt dazu nur den Hinweis „Sie erhalten den Zahlungslink per E-Mail, den Code nach Zahlungseingang.“ Kein Code auf der Seite, keine PDF-Erzeugung, kein eigener Zahlungsablauf.

E-MAIL: Die Website verschickt nie selbst Mails (kein mailto-Formular, kein Formspree, kein SMTP). Anfragen laufen über das Portal:
Der Inhaber bekommt Mail und Push, der Besucher eine Eingangsbestätigung mit Vorgangsnummer. Deshalb muss die E-Mail-Adresse des Besuchers
bei Termin- und Kontaktformularen Pflicht sein.

PRÜFEN VOR DER ABGABE (führe es aus und melde das Ergebnis)
1. grep nach "localhost", "http://", "lorem", "fonts.googleapis", "cdn", ".php": darf nichts finden (außer Verweise auf https://).
2. Alle internen Links und Bilder existieren. index.html liegt direkt in website-fertig/.
3. Seite auf 390 px Breite ohne seitliches Scrollen, Lighthouse-Barrierefreiheit über 90.
4. Jedes Formular: Pflichtfelder, Einwilligung, Lockfeld, Fehlertexte, danke.html. Mit nicht erreichbarer /api (offline) zeigt die Seite die Ausweichmöglichkeit.
5. Gib am Ende aus: Liste der Seiten, genutzte Portal-Funktionen (Baustein oder API), offene Punkte ("OFFEN:").
```

## Was du im Portal tun musst, damit die Funktionen wirklich laufen

1. Kunde anlegen und die **Domain in der Domainverwaltung eintragen**. Sonst lehnt der Server die Aufrufe der Website ab.
2. ZIP hochladen: Admin → Websites & Demos → Website hochladen (Kunde und Domain wählen, Haken „Website-Dienste automatisch einbauen“ für Variante A).
3. Beim Domain-Anbieter den **A-Eintrag für `@` und `www` auf die Server-IP** setzen. Das Zertifikat kommt automatisch.
4. Im Kundenportal → **Website-Dienste**: Kontaktformular einschalten (Empfänger), Terminbuchung einschalten (Öffnungstage, Uhrzeiten, Dauer, iCal-Adresse des Kalenders), PayPal (Client-ID oder PayPal.Me), Google-Bewertungen (Place-ID).
5. Nach dem Livegang: Livegang-Check lesen (Ampel), ein Test-Formular absenden, eine Test-Buchung machen, beides im Portal wiederfinden, Mails prüfen.

## Häufige Fehler
- Baustein bleibt leer: Dienst im Portal nicht eingeschaltet oder Domain nicht eingetragen.
- Formular meldet „Unbekannte Website“ (404) oder „Herkunft nicht erlaubt“ (403): Die Domain steht nicht in der Domainverwaltung bzw. die Seite läuft unter einer anderen Domain (z. B. Vorschau-Adresse).
- Termine bieten Uhrzeiten an, die es im Portal nicht gibt: feste Uhrzeiten der Website und des Portals stimmen nicht überein, oder die Seite hat Zeiten fest eingebaut statt aus `/api/slots`.
- Google Fonts oder externe Skripte: nicht blockiert, aber der Livegang-Check weist darauf hin, und die Datenschutzerklärung wäre unvollständig.
