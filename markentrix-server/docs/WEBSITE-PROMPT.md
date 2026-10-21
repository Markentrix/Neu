# Prompt für Claude Code: Kunden-Website bauen, die bei uns sofort läuft

Diesen Text am Anfang jedes Website-Projekts einfügen. Platzhalter in `<…>` ausfüllen.

```
Baue eine statische Website für <Firma, Branche, Ort>. Sie wird auf dem Server von Markentrix gehostet.
Es gibt KEIN eigenes Backend: keine Python-/Node-Server, keine Datenbank, kein Docker, kein Admin-Bereich.
Formulare, Terminbuchung und Statistik laufen über die Website-API von Markentrix unter /api (Vertrag unten).

ABGABE
- Die fertige Website liegt in einem Ordner "website-fertig/" mit index.html direkt darin.
- Nur statische Dateien: html, css, js, json, xml, txt, Bilder (png, jpg, webp, avif, svg), woff2, pdf, webmanifest.
- Alles relativ verlinken, eigene Schriften lokal, keine Fremd-CDNs. 404.html, sitemap.xml, robots.txt, Impressum, Datenschutz.

WEBSITE-API (gleiche Domain, relative Pfade, JSON):
- GET  /api/verfuegbarkeit   -> {blocked:[ISO-Datum], closedWeekdays:[0-6, 0=So], nextFree:ISO-Datum|null, selfBooking:bool, slotTimes:["08:00",…]}
- GET  /api/slots?tag=JJJJ-MM-TT -> {tag, slots:[{zeit:"08:00", frei:true|false}]}
- POST /api/anfrage (Content-Type: application/json), Felder:
    typ = "kontakt" | "termin" | "gutschein" | "firma" | "widerruf"
    name*, telefon, email, nachricht, einwilligung ("ja", Pflicht) und beliebige weitere Felder (z. B. leistung, paket, fahrzeug)
    bei typ="termin": datum* (JJJJ-MM-TT), uhrzeit (aus slots), telefon*, email* (für die Bestätigung)
    Lockfeld "website" im Formular (unsichtbar, leer lassen)
  Antwort: {ok:true, ref:"…"} -> weiterleiten auf danke.html?typ=<typ>&ref=<ref>
  Fehler: HTTP 422 {ok:false, errors:{feldname:"Text"}} -> Texte am Feld anzeigen
- POST /api/e   {t:"pv"|"ev", u:Pfad, n:Name, w:Breite} per sendBeacon, ohne Cookies (optional, für die Besucherzahlen)
Bei Fehlern oder fehlendem Server immer eine Ausweichmöglichkeit zeigen (Telefon, WhatsApp, E-Mail).
Terminformular: Uhrzeiten nur anbieten, wenn /api/slots frei:true meldet; gesperrte Tage aus /api/verfuegbarkeit sperren.

WEITERE BAUSTEINE (Platzhalter, Skript wird beim Hochladen automatisch eingefügt – nicht selbst einbauen):
- PayPal-Zahlung: <div data-mk="paypal" data-betrag="49,90" data-titel="Gutschein"></div>
- Google-Bewertungen: <div data-mk="bewertungen"></div>
- Cookie-/Statistik-Einstellung im Footer: <span data-mk="cookies"></span>
Baue keine eigene Zahlungsabwicklung, keine eigene Buchungslogik und kein eigenes Analytics.
Fehlt eine Funktion, die der Kunde wünscht, baue sie nicht selbst: Schreibe am Ende, was fehlt.
```
