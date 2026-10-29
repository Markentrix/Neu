# Website-API (Vertrag „mk-api v1“)

Jede von uns gebaute Kunden-Website nutzt dieselbe Schnittstelle unter **ihrer eigenen Domain**. Es gibt kein eigenes Backend und keinen eigenen Admin pro Kunde:
Alles läuft im Portal. Caddy leitet nur `/api/*` der Kundendomain an das Portal weiter, das Portal erkennt den Kunden an der Domain.

Der Vertrag bleibt stabil. Es kommen nur neue Felder dazu, bestehende ändern sich nicht. Jede Website, die nach diesem Vertrag gebaut ist, läuft auch nach Updates weiter.

| Aufruf | Zweck |
|---|---|
| `GET /api/verfuegbarkeit` (optional `?leistung=key&mitarbeiter=key`) | `{blocked:[Datum], blockedKeramik:[Datum], closedWeekdays:[0-6, 0=So], nextFree:Datum, selfBooking:bool, slotTimes:["08:00",…], paypalMe:"https://paypal.me/…" oder ""}` (paypalMe = PayPal.Me-Link aus dem Portal, nur wenn PayPal dort eingeschaltet ist; nie fest in die Seite schreiben) |
| `GET /api/slots?tag=JJJJ-MM-TT` (optional `&leistung=key&mitarbeiter=key`) | `{tag, slots:[{zeit:"08:00", frei:bool}]}` |
| `POST /api/anfrage` | JSON oder Formular. Pflicht: `typ` (kontakt, termin, gutschein, firma, widerruf), `name`, `einwilligung`. Weitere Felder beliebig (z. B. `paket`, `fahrzeug`, `nachricht`). Für Terminbuchungen mit Dauer und Personen: `leistung` und `mitarbeiter` (Kurznamen aus den Listen; `mitarbeiter` leer oder „egal“ = beliebige Person). `website` ist das Lockfeld und bleibt leer. Antwort: `{ok:true, ref:"T261021-AB12", status:"neu"}`, bei Fehlern `422 {ok:false, errors:{feld:text}}` |
| `GET /api/leistungen` | `{leistungen:[{key, name, beschreibung, preis, dauer}]}` – die buchbaren Leistungen (im Portal gepflegt) |
| `GET /api/mitarbeiter` | `{mitarbeiter:[{key, name, leistungen:[key]}]}` – leere `leistungen` heißt: bietet alles an |
| `POST /api/e` | Anonyme Statistik `{t:"pv"|"ev", u:Pfad, n:Name, r:Referrer, w:Breite, utm:{s}}`, Antwort 204 |
| `GET /api/health` | `{ok:true}` |

## Was dahinter im Portal passiert (Kundenportal → Website-Dienste)
- **Anfragen** landen unter „Anfragen“, der Inhaber bekommt eine Push-Meldung und eine E-Mail, der Besucher eine Eingangsbestätigung mit Vorgangsnummer.
- **Termine** (`typ=termin` mit `datum` und `uhrzeit`): feste Uhrzeiten oder Raster, Tageslimit, Vorlauf, Ruhetage, Sperrtage (Urlaub), iCal-Kalender des Inhabers, Reservierung mit Haltefrist.
  Mit „Ich bestätige jede Buchung selbst“ wartet die Buchung auf den Inhaber: Bestätigen schickt dem Kunden Einladung, optional mit Anzahlung per PayPal.Me-Link. Ohne Freigabe ist sie sofort gültig.
- **Statistik**: ohne Cookie, ohne IP-Adresse (täglich wechselnder Hash), im Kundenportal sichtbar.
- Ohne eingeschaltete Terminbuchung (`selfBooking:false`) wird `typ=termin` als normale Terminanfrage gespeichert.

## Leistungen und Mitarbeiter (Friseur, Kosmetik, Praxis, Werkstatt …)
- **Leistungen** haben eine Dauer und optional eine Pause danach. Ein Termin wird nur angeboten, wenn die ganze Dauer (plus Pause) vor die nächste Buchung passt.
- **Mitarbeiter** haben eigene Arbeitstage, Arbeitszeiten, feste Uhrzeiten, einen eigenen Kalender (iCal) und eigenen Urlaub, und bieten alle oder bestimmte Leistungen an.
- Ohne Wunschperson ist ein Termin frei, sobald irgendjemand Zeit hat. Die Zuordnung geht an die Person mit den wenigsten Terminen an dem Tag. Die Antwort auf `anfrage` bleibt unverändert, die Zuordnung steht im Portal und in der Bestätigung.
- Ohne angelegte Mitarbeiter bucht der Betrieb als eine Einheit. Sind Mitarbeiter angelegt, aber alle pausiert, ist nichts buchbar.
- Gleichzeitige Buchungen derselben Zeit werden serverseitig serialisiert: genau eine gewinnt, die anderen bekommen `422 {errors:{uhrzeit}}`.
- Unbekannte `leistung` oder `mitarbeiter` ergeben `422 {errors:{leistung|mitarbeiter}}`.

## Betrieb
- `GET /api/health` (über Caddy: `/siteapi/api/health`) antwortet `{"ok":true}` und wird vom Wachdienst alle 5 Minuten je Domain abgefragt. Wer die Weiterleitung `/api/*` in der Caddy-Datei entfernt, löst dadurch einen Alarm aus.
- Besucher bekommen 24 h und 2 h vor einer Buchung eine Erinnerungs-Mail mit Absage-Link (je Kunde einstellbar). Ergebnis „erschienen / nicht erschienen“ trägt der Kunde im Portal ein.

## Grenzen (bewusst)
- Pakete, Preise und Fahrzeugklassen kennt nur die Website. Das Portal prüft sie nicht, es speichert sie als Text in der Anfrage.
- Uhrzeiten auf der Website müssen zu den „Festen Uhrzeiten“ im Portal passen. Mit Raster (ohne feste Uhrzeiten) baut die Website die Auswahl aus den `slots` der Antwort auf.
- Keine eigene Zahlungsabwicklung: Anzahlung über PayPal.Me, der Inhaber prüft den Eingang.
- Leistungen mit Anzahlung und Freigabe: `GET /api/leistungen` liefert je Leistung zusätzlich `freigabe` (true = der Betrieb bestätigt Termine dieser Leistung selbst, sie kommen als „reserviert“) und `anzahlung` (Betrag in Euro als Text, leer = keine). Bei `POST /api/anfrage` mit `typ=termin` und `leistung` geht der PayPal-Link über die Anzahlung sofort per Mail an den Besucher. `GET /api/verfuegbarkeit?leistung=<key>` meldet `selfBooking:false`, wenn der Betrieb jede Buchung (oder diese Leistung) selbst bestätigt: dann heißt das Formular „Terminwunsch“. Preise, Dauer und Anzahlung pflegt der Betrieb im Portal; sie stehen automatisch auch in der Wissensdatenbank des Assistenten. Preislisten nie fest in die Seite schreiben: Baustein `<div data-mk="preise"></div>` oder `GET /api/leistungen`.
- Gutscheine: `typ=gutschein` mit `name`, `email` (Pflicht, sonst kann das Portal nichts senden), `betrag` oder `wunschbetrag` ("50", "50 €", "49,90 EUR" werden gelesen), optional `empfaenger`, `widmung`. Die Anfrage landet unter „Anfragen“ und in der Karte **Website-Dienste → Gutschein-Anfragen**. Dort sendet der Inhaber mit einem Klick den PayPal.Me-Zahlungslink (`{me-link}/{betrag}{waehrung}`, Betrag aus der Anfrage) an den Käufer und nach dem Zahlungseingang den selbst vergebenen Code („Gutschein senden“). Beide Mails gehen im Namen des Betriebs raus. Das Portal sieht PayPal-Zahlungen nicht und erzeugt deshalb keinen Code. Die Website braucht dafür nichts weiter als das Formular. Anfragen werden nach 400 Tagen gelöscht.

## Absage, Umbuchen, Quittung, Zusatzfragen, mehrere Leistungen (Paket B)
- **Absagelink** in den Mails (`/site/<id>/termin/absagen?t=…`): zeigt zuerst die Regel und fragt nach; abgesagt wird erst nach dem Klick (POST). Bis `storno_std` Stunden vor dem Termin (Standard 24, im Portal einstellbar) ist die Absage kostenlos, die Anzahlung wird erstattet. Später ist der volle Betrag fällig. Der Betrieb sieht „Anzahlung zurückzahlen“ im Portal und klickt danach „Erstattet“.
- **Umbuchen** (`/site/<id>/termin/verschieben?t=…`): Besucher wählt selbst eine neue freie Zeit (gleiche Leistung und Person), nur solange die Frist nicht abgelaufen ist. Betrieb und Besucher bekommen eine Mail, die Erinnerung läuft neu.
- **Quittung:** Betrieb erzeugt im Portal beim Termin mit erhaltener Anzahlung ein PDF („Quittung“, keine Rechnung mit Umsatzsteuer) und kann sie per Mail senden. Steuerliche Einordnung bitte mit der Steuerberatung klären.
- **Zusatzfragen je Leistung:** `GET /api/leistungen` liefert `felder:[{key,label,pflicht}]`. Die Website zeigt sie als Eingabefelder mit dem Namen `key`. Fehlt eine Pflichtangabe, antwortet `POST /api/anfrage` mit `422 {errors:{key:text}}`.
- **Mehrere Leistungen in einem Termin:** `leistung` als Liste oder `a,b,c` (Kurznamen). Dauer, Preis und Anzahlung werden addiert, die Person muss alle anbieten, Freigabe gilt, wenn eine Leistung sie braucht. Gilt auch für `/api/slots` und `/api/verfuegbarkeit` (`?leistung=a,b`).
- Datenschutz-Textbausteine für Zahlung, Anzahlung und Gutschein: `docs/DATENSCHUTZ-BAUSTEIN-ZAHLUNG.md`.

## Wochenplan, Personenzahl, Warteliste (Ergänzung)
- `/leistungen` und `/slots` richten sich nach dem **Wochenplan** (Zeiten je Wochentag mit Pausen); `personen` (Parameter bei `/slots`, `/verfuegbarkeit` und der Buchung) vervielfacht Dauer, Preis und Anzahlung.
- Neuer Anfragetyp **`warteliste`** (Pflicht: E-Mail und Datum). Wird ein Termin frei, benachrichtigt das Portal bis zu 3 Wartende mit den freien Zeiten.
- Termin-Links in Mails: absagen, verschieben und **„Ich komme“** (Bestätigung), alle als Seiten mit Bestätigungsschritt.

## Fotos zu Anfragen und Terminen (optional, pro Betrieb einzuschalten)
Der Betrieb schaltet das im Kundenportal unter Website-Dienste → „Fotos von Besuchern“ ein und legt die **Löschfrist** fest (Standard 90 Tage, 7 bis 365). Ohne Schalter antwortet der Upload mit 409.
- `GET /api/foto` → `{aktiv, max, tage, max_mb, hinweis}`. Den `hinweis` (Löschfrist!) direkt beim Foto-Feld anzeigen.
- `POST /api/foto` mit dem Foto als **Rohdaten im Body** (JPG, PNG oder WebP, höchstens 6 MB) → `{ok:true, token:"…"}`. Am besten im Browser vorher auf höchstens 1600 Pixel verkleinern (Canvas, JPEG 0,82), das spart Datenvolumen und entfernt Standort und Kameradaten schon beim Besucher. Der Server prüft den Inhalt (nicht den Dateinamen) und entfernt Metadaten selbst noch einmal. Mit `Content-Type: text/plain` senden, dann entfällt die Vorabfrage (CORS).
- `POST /api/anfrage` mit dem Zusatzfeld **`fotos`** (Liste der Kennungen, bis 5; bei einem normalen Formular mehrere Felder `fotos=…`). Gilt für alle Anfragetypen, auch Termin. Eine Kennung kann nur einmal verwendet werden.
- Nicht abgeschickte Uploads löscht das Portal nach 24 Stunden. Abgeschickte Fotos löscht es nach der Frist des Betriebs automatisch (Eintrag im Löschprotokoll). Der Betrieb sieht sie bei Anfragen, Terminen und Buchungen und im Anhang der Mail (bis 8 MB zusammen, sonst nur im Portal) und kann sie vorher selbst löschen.
- Der Baustein `site.js` (Kontaktformular und Terminbuchung) bringt das Foto-Feld mit Verkleinern und Löschhinweis automatisch mit, sobald der Betrieb es eingeschaltet hat.


## Online-Shop (Modul „shop“, Migration 147)
Das Portal führt Artikel, Farben, Kategorien, Bilder und Bestellungen. Die Website bleibt statisch und holt alles über dieselben relativen Pfade wie bisher. Der Shop liefert erst aus, wenn das Modul „Online-Shop“ beim Kunden gebucht **und** im Kundenportal (Online-Shop → Einstellungen) eingeschaltet ist. Sonst antworten alle Shop-Pfade mit `404 {"ok":false}`: Die Website nimmt dann ihre eingebaute Liste als Rückfall.

| Aufruf | Antwort |
|---|---|
| `GET /api/produkte` | `{stand, versand:{pauschale, versandfreiAb, abholung, produktionszeit, lieferzeit}, kategorien:[{key,name,sort}], farben:[{key,name,hex}], produkte:[…]}`. Nur aktive Artikel in Anzeigereihenfolge. Leere Kategorien fehlen. |
| `GET /api/produkte/{id}` | Ein Artikel, zusätzlich `verwandt:[id]` (nur aktive). 404 `{ok:false}`, wenn inaktiv oder unbekannt. |
| `GET /api/farben`, `GET /api/kategorien` | Die zentralen Listen. |
| `GET /api/gutschein` | `{aktiv:true, einloesen:true, betraege:[10,20,…], min, max, gueltigkeitMonate, zustellung:[…]}` oder `{aktiv:false}`. |
| `POST /api/gutschein/pruefen` `{code}` | `{ok:true, gueltig:true, rest:20.0, ablauf:"2029-10-29"}` oder `{ok:true, gueltig:false, message}`. Für die Kasse (Feld „Gutscheincode“). Stark begrenzt (10 Versuche je 10 Minuten und IP, dann `429`); die Meldung verrät nicht, ob es den Code gibt. |
| `GET /api/medien/{bild-id}.webp` | Das Bild (nur von aktiven Artikeln), `Cache-Control: public, max-age=86400`. |

Artikel: `{id, name, kategorie, preis (Euro, Zahl), kurz, lang, material, masse, gewicht, farben:[key], tags, personalisierbar, textlabel, textmax, bilder:[{url,w,h,alt}], sort, aktiv, geaendert}`. Bild-URLs sind relativ und liegen unter `/api/medien/…` (nicht `/media/…`), damit die bestehende Caddy-Weiterleitung `/api/*` ausreicht. Die Kataloge sind cachebar: `Cache-Control: public, max-age=300` und `ETag` (Antwort 304 bei `If-None-Match`). Das ist die einzige Ausnahme vom allgemeinen `no-store` des Portals.

### Bestellung: `POST /api/anfrage` mit `typ="bestellung"` (nur JSON)
Felder: `name`, `email` (Pflicht), `telefon`, `einwilligung`, `agb` (beide `"ja"`), `lieferart` (`versand`|`abholung`), `adresse:{strasse,plz,ort,land}` (nur bei Versand), `zahlungsart` (`paypal`|`abholung`; Zahlung bei Abholung nur mit Abholung), `positionen:[{id,name,farbe,text,menge,einzelpreis}]`, `zwischensumme`, `versand`, `summe`, `anmerkung`, `website` (Lockfeld).
- Das **Portal rechnet mit seinen eigenen Preisen nach**. Artikelnamen und Preise der Website werden nie übernommen. Weicht `einzelpreis`, `zwischensumme`, `versand` oder `summe` ab (zum Beispiel nach einer Preisänderung), antwortet es `422 {errors:{summe:…}}`. Fehlen die Summenfelder, rechnet das Portal ohne Vergleich.
- Prüfungen: Artikel aktiv, Menge 1 bis 99, Farbe aus der Auswahl des Artikels, Wunschtext Pflicht und höchstens `textmax` Zeichen bei `personalisierbar` (sonst ignoriert), Adresse bei Versand. Fehler je Feld als `422 {errors:{…}}`.
- Versand: bei Abholung 0, ab `versandfreiAb` 0, sonst die Pauschale.
- Antwort wie bisher `{ok:true, ref:"SA-2026-0001", status:"neu"}`, bei PayPal und eingetragenem PayPal.Me-Link zusätzlich `paypalUrl` (Betrag und Währung eingebaut). Die Nummer ist fortlaufend je Kunde und Jahr, das Präfix stellt der Kunde ein.
- Danach: Push und Mail an den Betrieb, Bestätigungs-Mail mit Positionen, Summe und Zahlhinweis an die Kundin bzw. den Kunden. **Keine Rechnung (PDF) und keine Umsatzsteuer-Ausweisung**: das ist bewusst nicht gebaut (steuerliche Einordnung, siehe Anwalts-Checkliste).
- **Gutschein einlösen:** Feld `gutscheincode` in der Bestellung. Das Portal zieht höchstens den Rest des Gutscheins ab (nie mehr als die Summe aus Waren und Versand) und bucht ihn ab. `summe` bleibt Waren plus Versand (ohne Gutschein), die Antwort enthält zusätzlich `gutschein:{abgezogen, rest, zuZahlen}`. `paypalUrl` gilt nur für `zuZahlen`, ist es 0, gibt es keinen PayPal-Link und die Bestellung steht sofort auf „Bezahlt“. Ungültiger, abgelaufener oder aufgebrauchter Code: `422 {errors:{gutscheincode:…}}`. Bei Stornierung der Bestellung im Portal wird der Betrag zurückgebucht. Ein Gutschein gilt nur im Shop des Kunden, der ihn gesendet hat, und nur nach dem Versand des Codes (Portal → Website-Dienste → Gutscheine). Ablauf: die im Shop eingestellten Monate (Standard 36) ab Versand.
- `typ="gutschein"` prüft den Betrag zusätzlich gegen `min` und `max` aus dem Shop (nur wenn die Gutschein-Einstellung des Shops eingeschaltet ist).

### Kundenportal: Online-Shop (nur Inhaber, Modul „shop“)
Bestellungen (Status eingegangen, bestätigt, bezahlt, in Produktion, versendet, abholbereit, abgeholt, storniert; Sendungsnummer, Abholtermin, interne Notiz; optional Mail an die Kundschaft bei Statuswechsel), Artikel (Entwurf oder aktiv, Farben, Tags, Wunschtext, „oft zusammen bestellt“), Bilder (der Browser schneidet auf 4:3 zu, 1200 × 900, und wandelt in WebP um; bis 600 KB, bis 8 je Artikel, 100 MB je Kunde), zentrale Farben und Kategorien, Einstellungen (Versand, Abholung, Zeiten, Bestellnummer-Präfix, Gutschein-Vorgaben).

### Noch nicht gebaut
Freistellen von Bildern; automatisch erzeugte Artikelseiten `produkt/<id>.html` mit `sitemap.xml` (die Website nutzt dafür bis auf Weiteres ihre eigenen Seiten oder `produkt.html?id=…`); Rechnung/Quittung zur Bestellung; Einlösen von Gutscheinen an der Ladenkasse außerhalb des Shops (Restguthaben wird nur bei Online-Bestellungen abgebucht, im Geschäft trägt der Inhaber nichts ein); automatische Zahlungsprüfung (der Inhaber setzt „Bezahlt“ selbst nach Blick ins PayPal-Konto).
