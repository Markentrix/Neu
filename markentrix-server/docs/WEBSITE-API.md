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
