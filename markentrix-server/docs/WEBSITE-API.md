# Website-API (Vertrag „mk-api v1“)

Jede von uns gebaute Kunden-Website nutzt dieselbe Schnittstelle unter **ihrer eigenen Domain**. Es gibt kein eigenes Backend und keinen eigenen Admin pro Kunde:
Alles läuft im Portal. Caddy leitet nur `/api/*` der Kundendomain an das Portal weiter, das Portal erkennt den Kunden an der Domain.

Der Vertrag bleibt stabil. Es kommen nur neue Felder dazu, bestehende ändern sich nicht. Jede Website, die nach diesem Vertrag gebaut ist, läuft auch nach Updates weiter.

| Aufruf | Zweck |
|---|---|
| `GET /api/verfuegbarkeit` (optional `?leistung=key&mitarbeiter=key`) | `{blocked:[Datum], blockedKeramik:[Datum], closedWeekdays:[0-6, 0=So], nextFree:Datum, selfBooking:bool, slotTimes:["08:00",…]}` |
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
- Gutscheine: als Anfrage mit Zahlung per PayPal.Me, der Code wird vom Inhaber vergeben.
