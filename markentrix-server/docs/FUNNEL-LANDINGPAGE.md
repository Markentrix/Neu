# Landingpages für den Lead-Funnel

So kommt eine Anmeldung sauber als Lead im Portal an. Stand: Migration 141.

## Zwei Wege

| Weg | Adresse | Aufwand |
|---|---|---|
| **A. Vorlage im Portal** (empfohlen) | `https://portal.markentrix.de/f/<seitenname>` | Nur im Admin anlegen. Kein Caddy, keine eigene Datei. |
| **B. Eigene Landingpage** | z. B. `https://markentrix.de/check-niedersachsen/` | Eigene HTML-Seite plus eine Caddy-Weiterleitung (unten). |

Bei beiden Wegen gilt: Die **Kampagne** im Admin (Admin → Lead-Funnel) ist die Quelle für Einwilligungstext, Mails und Auswertung. Ohne aktive und „rechtlich geprüfte“ Kampagne nimmt das Portal nichts an (404).

## Weg A: Vorlage im Portal

1. Admin → Lead-Funnel → **Neue Seite**.
2. Seitenname (wird Teil der Adresse), Überschrift, Zeile darüber, Vorteile, Knopftext und Einwilligungstext eintragen.
3. Vorlage **Website-Check** wählen. Ergebnis-Mail und Nachfass-Mails nach Wunsch einschalten.
4. Werbekosten eintragen, damit „Kosten pro Lead“ stimmt.
5. Erst nach der Prüfung durch den Anwalt: „Rechtlich geprüft“ und „Seite ist live“.
6. Den Link aus der Liste mit UTM-Angaben in die Anzeige setzen, z. B.
   `https://portal.markentrix.de/f/website-check-ffm?utm_source=meta&utm_campaign=check-ffm&utm_content=A`

Optional, eine kürzere Adresse auf markentrix.de. Diese Zeile in `/srv/caddy-sites/markentrix.de.caddy` leitet weiter und behält die UTM-Angaben:
```
redir /check https://portal.markentrix.de/f/website-check-ffm?{query} 302
```

## Weg B: Eigene Landingpage

### 1. Caddy: Schnittstelle auf derselben Domain

Die Seite darf das Portal nur über **ihre eigene Domain** ansprechen. Fremde Herkunft lehnt das Portal ab, und es gibt kein CORS. In der Caddy-Datei der Domain, vor allen anderen Regeln:
```
handle /api/public/funnel/* {
    reverse_proxy mk-portal:8000
}
```
Als Ziel dieselbe Adresse wie in den Kunden-Dateien unter `/srv/caddy-sites/` nehmen (`mk-portal:8000` oder `127.0.0.1:8090`). Danach Caddy prüfen und neu laden.

Prüfen: `curl -s -o /dev/null -w "%{http_code}" -X POST https://<domain>/api/public/funnel/<seitenname> -H "Content-Type: application/json" -H "X-MK: 1" -d "{}"` muss **422** liefern (nicht 404, nicht 403).

### 2. Seite laden: Texte und Aufrufzähler

`GET /api/public/funnel/<seitenname>` beim Öffnen der Seite **einmal** aufrufen. Der Aufruf zählt die Seitenaufrufe für die Auswertung. Die Antwort:
```json
{"name": "...", "titel": "...", "untertitel": "...", "nutzen": ["..."], "button": "...",
 "einwilligung_text": "...", "danke_titel": "...", "danke_text": "...",
 "telefon_pflicht": true, "website_abfragen": true, "termin_anbieten": true,
 "vorlage": "website_check", "kicker": "...", "check_mail": true,
 "firma": "Markentrix", "kontakt": {"telefon": "...", "email": "..."}}
```
404 heißt: Seite nicht live. Dann statt des Formulars Telefon und E-Mail zeigen.

### 3. Formular absenden

`POST /api/public/funnel/<seitenname>`

Pflicht-Kopfzeilen: `Content-Type: application/json` und **`X-MK: 1`**. Ohne `X-MK` antwortet das Portal mit 403.

| Feld | Pflicht | Hinweis |
|---|---|---|
| `name` | ja | 2 bis 200 Zeichen |
| `email` | ja | gültige Adresse |
| `telefon` | wenn in der Kampagne so eingestellt | |
| `website` | bei Vorlage Website-Check | „www.beispiel.de“ reicht, `https://` ergänzt das Portal |
| `firma` | nein | sonst nimmt das Portal den Namen der Website |
| `einwilligung` | ja, `true` | Haken neben dem **Einwilligungstext der Kampagne** |
| `utm` | nein | Objekt mit `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `gclid`, `fbclid` aus der Adresse der Seite |
| `ref` | nein | nur Empfehlungsprogramm |
| `zweitfeld` | leer lassen | Roboterfalle: unsichtbares Textfeld, Menschen füllen es nicht aus |

Antworten:
- **200** `{"ok": true, "termin": true, "neu": true, "check": "<kennzeichen>"}`. `check` gibt es nur bei der Vorlage Website-Check.
- **400** `{"detail": "Text für den Besucher"}`: Text direkt am Formular zeigen, Eingaben stehen lassen.
- **422**: Feld hat ein falsches Format (z. B. `einwilligung` kein true/false).
- **404**: Seite nicht live. **403**: `X-MK` fehlt oder falsche Herkunft. **429**: zu viele Anmeldungen (20 je Stunde und Anschluss).

Bei jedem Fehler und ohne Verbindung immer Telefon und E-Mail als Ausweg anzeigen. Den Knopf während des Sendens sperren.

### 4. Ampel auf der Danke-Ansicht (nur Website-Check)

`GET /api/public/funnel/<seitenname>/check/<kennzeichen>` alle 3 Sekunden, höchstens 2 Minuten lang:
```json
{"status": "laeuft" | "fertig" | "fehler", "mail": true,
 "ampel": "gruen" | "gelb" | "rot", "score": 85, "zusammenfassung": "...", "website": "beispiel.de",
 "punkte": [{"titel": "...", "status": "gut" | "mittel" | "schlecht", "text": "..."}]}
```
Die Antwort enthält keine persönlichen Daten. Das Kennzeichen kennt nur der Besucher.

### 5. Termin

Knopf auf `https://portal.markentrix.de/buchen`. Bucht der Besucher mit derselben E-Mail-Adresse, ordnet das Portal den Termin dem Lead zu. Damit enden die Nachfass-Mails.

### 6. Regeln für die Seite

- Den **Einwilligungstext genau so** zeigen wie in der Kampagne. Das Portal protokolliert beim Lead den Text der Kampagne.
- Impressum und Datenschutz verlinken. Die Datenschutzerklärung nennt den Website-Check und bei eingeschaltetem PageSpeed die Übermittlung der Website-Adresse an Google.
- Kein Tracking (Pixel, Analytics) ohne Einwilligung.
- Skripte als eigene Datei einbinden, nicht im HTML. Die Sicherheitsregeln (CSP) von markentrix.de und dem Portal sperren eingebettete Skripte.
- Handy zuerst, ohne Menü, schnell. Keine Schriften oder Bibliotheken von fremden Servern.

## Was im Portal ankommt

- **Lead**: heiß, Quelle „website“, Kampagne, UTM-Angaben, Website. Der Einwilligungs-Vermerk steht im Verlauf.
- **Aufgabe** „Neuer Funnel-Lead, bitte innerhalb einer Stunde anrufen“, dazu Push und Mail an das Team.
- **Website-Check**: Ampel, Punktzahl und 9 Prüfpunkte beim Lead, das PDF per Knopf. Der Score steht im Lead.
- **Ergebnis-Mail mit PDF** an den Interessenten, wenn in der Kampagne eingeschaltet.
- **Nachfass-Mails** nach den eingestellten Tagen, wenn eingeschaltet.
- **Auswertung** (Admin → Lead-Funnel): Aufrufe, Leads, Termine, Kunden, Kosten pro Lead und pro Kunde.

## Testen vor dem Start

1. Admin → Lead-Funnel → Karte „Website-Check“ → **Probe-Check** mit einer echten Website. Das PDF ansehen.
2. Seite live schalten und selbst einmal mit eigener E-Mail-Adresse ausfüllen. Ampel, Mail mit PDF, Lead, Aufgabe und Push prüfen.
3. Den Test-Lead danach löschen oder auf „verloren“ setzen.
