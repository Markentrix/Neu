# Website-API (Vertrag „mk-api v1“)

Jede von uns gebaute Kunden-Website nutzt dieselbe Schnittstelle unter **ihrer eigenen Domain**. Es gibt kein eigenes Backend und keinen eigenen Admin pro Kunde:
Alles läuft im Portal. Caddy leitet nur `/api/*` der Kundendomain an das Portal weiter, das Portal erkennt den Kunden an der Domain.

Der Vertrag bleibt stabil. Es kommen nur neue Felder dazu, bestehende ändern sich nicht. Jede Website, die nach diesem Vertrag gebaut ist, läuft auch nach Updates weiter.

| Aufruf | Zweck |
|---|---|
| `GET /api/verfuegbarkeit` | `{blocked:[Datum], blockedKeramik:[Datum], closedWeekdays:[0-6, 0=So], nextFree:Datum, selfBooking:bool, slotTimes:["08:00",…]}` |
| `GET /api/slots?tag=JJJJ-MM-TT` | `{tag, slots:[{zeit:"08:00", frei:bool}]}` |
| `POST /api/anfrage` | JSON oder Formular. Pflicht: `typ` (kontakt, termin, gutschein, firma, widerruf), `name`, `einwilligung`. Weitere Felder beliebig (z. B. `paket`, `fahrzeug`, `leistung`, `nachricht`). `website` ist das Lockfeld und bleibt leer. Antwort: `{ok:true, ref:"T261021-AB12", status:"neu"}`, bei Fehlern `422 {ok:false, errors:{feld:text}}` |
| `POST /api/e` | Anonyme Statistik `{t:"pv"|"ev", u:Pfad, n:Name, r:Referrer, w:Breite, utm:{s}}`, Antwort 204 |
| `GET /api/health` | `{ok:true}` |

## Was dahinter im Portal passiert (Kundenportal → Website-Dienste)
- **Anfragen** landen unter „Anfragen“, der Inhaber bekommt eine Push-Meldung und eine E-Mail, der Besucher eine Eingangsbestätigung mit Vorgangsnummer.
- **Termine** (`typ=termin` mit `datum` und `uhrzeit`): feste Uhrzeiten oder Raster, Tageslimit, Vorlauf, Ruhetage, Sperrtage (Urlaub), iCal-Kalender des Inhabers, Reservierung mit Haltefrist.
  Mit „Ich bestätige jede Buchung selbst“ wartet die Buchung auf den Inhaber: Bestätigen schickt dem Kunden Einladung, optional mit Anzahlung per PayPal.Me-Link. Ohne Freigabe ist sie sofort gültig.
- **Statistik**: ohne Cookie, ohne IP-Adresse (täglich wechselnder Hash), im Kundenportal sichtbar.
- Ohne eingeschaltete Terminbuchung (`selfBooking:false`) wird `typ=termin` als normale Terminanfrage gespeichert.

## Grenzen (bewusst)
- Pakete, Preise und Fahrzeugklassen kennt nur die Website. Das Portal prüft sie nicht, es speichert sie als Text in der Anfrage.
- Uhrzeiten auf der Website müssen zu den „Festen Uhrzeiten“ im Portal passen.
- Keine eigene Zahlungsabwicklung: Anzahlung über PayPal.Me, der Inhaber prüft den Eingang.
- Gutscheine: als Anfrage mit Zahlung per PayPal.Me, der Code wird vom Inhaber vergeben.
