# Verwaltungsportal – Kurzanleitung

Adresse: `https://www.elbdetail.de/admin`. Anmeldung mit Benutzername und Passwort aus der Server-Konfiguration.

## Übersicht

- **Besucher, Anfragen, WhatsApp- und Anruf-Klicks, Kontaktquote** für 7, 30 oder 90 Tage, jeweils mit Vergleich zum Vorzeitraum.
- **Besucher und Anfragen pro Tag** als Diagramm, darunter die Tageswerte als Tabelle.
- **Nächste Wunschtermine** aus der Online-Buchung.
- **Terminbuchung: Schritte** zeigt, in welchem Schritt Interessierte abbrechen.
- **Herkunft und Kampagnen**: Verweisende Websites und `utm`-Parameter aus Anzeigen (Schema im Anzeigen-Kit).

Die eigene Statistik setzt keine Cookies und speichert keine IP-Adressen. Ein Einwilligungsbanner ist dafür nicht nötig. Google Analytics ist zusätzlich möglich (Grunddaten → Google Analytics, Mess-ID `G-…`): Es lädt erst, wenn ein Besucher im Hinweisfenster zustimmt.

## Anfragen

1. Neue Anfragen erscheinen mit Status **Neu**. Die Zahl steht in der Seitenleiste. Zusätzlich kommt eine E-Mail, wenn SMTP eingerichtet ist.
2. Anfrage anklicken: alle Angaben, Richtpreis laut Website, Kontakt-Knöpfe.
3. **Antwort mit Angebot vorbereiten** erstellt einen Text mit Name, Paket, Wunschtermin und Richtpreis. Platzhalter in eckigen Klammern ergänzen, dann **In WhatsApp öffnen** oder **Als E-Mail öffnen**.
4. Status pflegen: In Bearbeitung → Angebot gesendet → Termin bestätigt → Erledigt (oder Abgelehnt). Notizen sind nur intern sichtbar.
5. Nach dem Termin: **Bewertung anfragen**. Das Portal warnt, wenn die Kundin oder der Kunde der Bewertungsanfrage im Formular nicht zugestimmt hat. Details im Dokument „Bewertungs-Prozess“.
6. **Als CSV exportieren** liefert alle Anfragen für Excel.

**Online-Buchungen:**
- Status „Reserviert“: Der Kunde hat noch nicht bestätigt bzw. angezahlt.
- Nach der Anzahlung oder Bestätigung steht der Termin automatisch auf „Termin bestätigt“.
- „Vom Kunden abgesagt“ und „Reservierung verfallen“ geben die Uhrzeit wieder frei.

In einer Terminanfrage können Sie:
- **Tag und Uhrzeit ändern:** Der Kunde bekommt eine neue Bestätigung, der Google-Termin wird verschoben.
- **Eine PayPal-Anzahlung erstatten.**

Setzen Sie eine klassische Anfrage auf „Termin bestätigt“, bekommt der Kunde ebenfalls die Bestätigung mit dem Hinweis auf Ihren Anruf und Erinnerungen.

## Gutscheine

1. Bestellungen von der Website legen automatisch einen Gutschein mit Status **Offen** an. Die Käuferin oder der Käufer bekommt eine E-Mail mit dem Zahlungshinweis aus den Einstellungen.
2. Nach Zahlungseingang: Gutschein öffnen → **als bezahlt markieren**. Optional geht der Gutschein-Link sofort per E-Mail raus. Der Link führt zu einer druckfertigen Gutscheinseite.
3. Bei der Einlösung: Code oben unter **Code prüfen** eingeben → **Als eingelöst markieren**. Bei Terminanfragen mit Gutscheincode zeigt die Anfrage den Status des Codes direkt an.
4. Gutscheine für Laufkundschaft: **Gutschein manuell anlegen**.

## Kalender

- Tag anklicken sperrt ihn (z. B. Urlaub, ausgebucht). Nochmal klicken gibt ihn frei. Gesperrte Tage und Ruhetage sind in der Online-Buchung nicht wählbar.
- Die Zahl im Tag zeigt Terminwünsche, „best.“ die bestätigten.
- **Ruhetage** (Standard: Sonntag) rechts festlegen.
- **Auslastung:** „Fahrzeuge pro Tag“ (Standard 2). Hat ein Tag so viele Anfragen mit Status „Termin bestätigt“, gilt er automatisch als ausgebucht. „Vorlauf“ (Standard 1) legt fest, ab wann frühestens gebucht werden kann. „Keramikversiegelung belegt den Platz exklusiv“ (Standard an) und „Standzeit Keramik in Tagen“ (Standard 3): Eine bestätigte Keramik sperrt ihre ganze Standzeit für andere Termine, und eine neue Keramik kann nur beginnen, wenn in diesen Tagen nichts bestätigt ist.
- **Nächster freier Tag:** Startseite, Kontaktblock und Buchung zeigen automatisch den nächsten Tag, der weder Ruhetag noch gesperrt noch ausgebucht ist. Ein Klick übernimmt ihn in die Terminanfrage. Damit die Anzeige stimmt: Termine nach Zusage auf „Termin bestätigt“ setzen und Urlaub sperren.

## Inhalte

- **Grunddaten & Kontakt:** Telefon, Adresse, Bewertungsanzahl, Google-Links, Einzugsgebiet, Angaben für Impressum und Datenschutz, Gutscheinbeträge, „Über uns“ (Inhaber-Karte), Bestätigungscodes für Google und Bing.
- **Bewertungen:** `heroQuote` ist das kurze Zitat im Startbereich. Nur echte Sätze aus einer Google-Bewertung verwenden, Name abgekürzt.
- **Pakete & Preise:** Paketnamen, Leistungen, Richtpreise je Fahrzeugklasse, Einzelleistungen, Vergleichstabelle. Preise ändern sich überall gleichzeitig (Startseite, Rechner, Buchung, Leistungsseiten, strukturierte Daten, llms.txt).
- **Bewertungen, Häufige Fragen, Vorher/Nachher-Galerie, Leistungsseiten.**
- **Ratgeber:** Artikel bearbeiten mit Live-Vorschau, neue Artikel anlegen. Neue Artikel starten als Entwurf (Häkchen „Entwurf“ entfernen, um sie zu veröffentlichen).
- Jede Speicherung legt eine Sicherung der vorherigen Fassung auf dem Server an (die letzten 30 je Datei).
- **Speichern & veröffentlichen** baut die Website in wenigen Sekunden neu.

## Fotos

1. Vorher- und Nachher-Fotos im Format 4:3 hochladen (JPG, PNG oder WebP, bis 15 MB). Gleiches Motiv, gleicher Standpunkt, siehe Foto-Shotlist.
2. Unter Inhalte → Vorher/Nachher-Galerie die Dateinamen bei „Foto vorher“ und „Foto nachher“ eintragen (Vorschlagsliste erscheint beim Tippen).
3. Veröffentlichen. Die Website erzeugt automatisch AVIF- und WebP-Versionen in mehreren Größen.

## Veröffentlichen

Zeigt den letzten Stand, die Dauer und offene Hinweise (z. B. fehlender Inhaber im Impressum, fehlende Fotos).


## Angebote

Unter **Angebote** legen Sie Aktionen selbst an: Titel, Etikett, kurze Beschreibung, Preisangabe, Laufzeit, Button-Ziel und optional ein Bild (Querformat 16:9). Eine Vorschau zeigt die Karte so, wie sie auf der Website erscheint.

- **Speichern = live.** Jede Änderung wird sofort veröffentlicht, ein zusätzlicher Klick auf „Veröffentlichen“ ist nicht nötig.
- **Startseite:** Bis zu drei Live-Angebote erscheinen direkt unter der Vertrauensleiste. „Auf der Startseite ganz vorn zeigen“ setzt ein Angebot an den Anfang und hebt es dunkel hervor. Alle Live-Angebote stehen auf `/angebote.html`.
- **Laufzeit:** Mit „Gültig ab“ und „Gültig bis“ geht ein Angebot automatisch online und wieder offline. Der Server prüft das stündlich und veröffentlicht bei Bedarf selbst neu. Abgelaufene Karten blendet die Website zusätzlich sofort aus.
- **Reihenfolge** mit ↑ und ↓ ändern, **Ausblenden** nimmt ein Angebot von der Website, ohne es zu löschen.
- **Rechtlich:** Endpreise angeben, keine erfundenen „statt“-Preise. Bilder nur mit Nutzungsrecht (eigene Fotos oder ausdrücklich freigegebenes Herstellermaterial).
