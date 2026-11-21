# Livegang-Checkliste

Die Website läuft beim Markentrix-Portal. Abgegeben wird nur der Ordner `website-fertig/` (siehe `portal-upload.md`).

## Muss vor dem Livegang erledigt sein

- [ ] **Prüfbericht vom 21.11.2026:** offene Punkte in `pruefbericht-2026-11-umsetzung.md` (A03 Vertragsablauf entscheiden, A10 Ausfallpauschale belegen, A13/A14 Nachweise) und Portal-Aufgaben in `portal-aufgaben.md` (Analytics-Widerruf, Widerruf ohne Einwilligung, Bestätigungsmail) erledigen.
- [ ] **Datenschutz-Schalter** in `content/site.json → legal` setzen, sobald belegt: `avContract`, `analyticsDpa`, `analyticsRetentionMonths`.

- [ ] **Impressum:** Inhaber, Kleinunternehmer-Hinweis, Verantwortlicher nach § 18 MStV prüfen (`content/site.json` → `legal`). Steuernummer fehlt noch.
- [ ] **Datenschutz:** Auftragsverarbeitungsvertrag mit Markentrix abschließen (Hetzner Online GmbH, Rechenzentrum Nürnberg, als Unterauftragsverarbeiter darin aufführen). Anschrift von Markentrix ist eingetragen (Heinrich-Hüdig-Straße 1, 29227 Celle). Text anwaltlich prüfen lassen.
- [ ] **Markentrix-Portal einrichten:** Termine an, feste Uhrzeiten wie auf der Website (8, 9, 10 Uhr; mittwochs ab 9 Uhr), Sonntag geschlossen. Kalender verbinden, falls gewünscht.
- [ ] **Bausteine im Portal einschalten:** Bewertungen (Google-Profil verknüpfen), Statistik und Cookie-Hinweis (Google Analytics Mess-ID `G-LTV65F8GKJ` dort hinterlegen).
- [ ] **Foto-Upload im Markentrix-Portal** einschalten, falls gewünscht (Anzahl und Löschfrist dort festlegen). Abschnitt „Fotos vom Fahrzeug“ in der Datenschutzerklärung anwaltlich prüfen lassen.
- [ ] **PayPal.me-Namen im Markentrix-Portal** hinterlegen (z. B. `elbdetail`). Die Website liest ihn aus `/api/verfuegbarkeit` (Feld `paypalMe`) und zeigt dann in der Buchung und auf der Danke-Seite den PayPal-Link mit dem Betrag der Anzahlung. Ist das Feld leer, gibt es keinen Zahlungslink.
- [ ] **Preise prüfen:** Richtpreise der vier Pakete je Fahrzeugklasse und Keramikpreise (C² CarCeramic, Felgen, Scheiben).
- [ ] **Aussagen prüfen:** Öffnungszeiten (Mo bis Sa 8 bis 17 Uhr, Mi ab 9 Uhr), „Abholung nach Absprache“, Firmenkunden-Seite, Gutschein-Regeln (Gültigkeit 3 Jahre, Paketgutschein für einen Kleinwagen).
- [x] **AGB mit Widerrufsbelehrung, Muster-Widerrufsformular und Seite „Vertrag widerrufen“** sind eingebaut. Selbst erstellter Entwurf, **noch anwaltlich prüfen lassen**. Die geprüfte Fassung ersetzt den Text in `build/agb.py`.
- [x] **Storno-Regel** in den AGB (§ 6): Verschieben kostenlos, Absage innerhalb der 14-tägigen Widerrufsfrist = volle Erstattung, danach Anzahlung als Ausfallpauschale mit Nachweis-Möglichkeit.
- [x] **Domain:** www.elbdetail.de.
- [x] **Referenzen:** Freigabe aller 5 Firmen für Logo und Namen liegt bei René vor.
- [x] **Foto von René** auf der Startseite und unter „Über uns“.
- [ ] **Englische Fassung** (`/en/`) einmal durchklicken. Englische Rechtstexte (Impressum, Datenschutz, AGB, Widerruf) sind Übersetzungen mit Hinweis auf die verbindliche deutsche Fassung. Beim Anwalt mitprüfen lassen.
- [ ] **Testanfrage** über jedes Formular (Kontakt, Termin, Gutschein, Firma, Widerruf) schicken und prüfen, dass Mail, Push und Eingangsbestätigung ankommen.

## Direkt nach dem Livegang

- [ ] Google Search Console: Eigenschaft anlegen, Methode „HTML-Tag“, Code in `content/site.json` → `verification.google` eintragen, neu bauen und hochladen. Danach `https://www.elbdetail.de/sitemap.xml` einreichen. Bing Webmaster Tools genauso.
- [ ] Rich-Results-Test für Startseite, eine Leistungsseite und einen Ratgeber-Artikel.
- [ ] Google-Unternehmensprofil: Website-Link auf `https://www.elbdetail.de/` und Termin-Link auf `/termin.html` setzen (`google-unternehmensprofil.md`).
- [ ] Branchenverzeichnisse mit identischer Schreibweise anlegen (`branchenverzeichnisse.md`).
- [x] Google-Bewertungslink eingetragen (Place-ID aus dem Portal), Kurzadresse `elbdetail.de/bewerten.html` mit QR-Karte. Einmal selbst antippen und prüfen, dass sich das Bewertungsfenster von ElbDetail öffnet. Dann den Bewertungsprozess starten (`bewertungs-prozess.md`).
- [ ] **Buchungszeitraum im Portal** von 3 Wochen auf mindestens 3 Monate stellen. Bis dahin zeigt die Buchung nach der Grenze einen Hinweis auf Telefon und WhatsApp.
- [ ] Erste echte Vorher/Nachher-Fotos einbauen (`foto-und-video-shotlist.md`).
- [ ] Anzeigen nur mit UTM-Parametern starten (`anzeigen-kit.md`).

## Termine im Kalender

- [ ] **28.02.2027:** Winterangebot und Winter-Aktion Scheibenkeramik laufen aus. Website neu bauen und hochladen, damit die Aktionspreise verschwinden. Angebotskarten blenden sich am Ablaufdatum von selbst aus.

## Monatlich

- [ ] Statistik im Markentrix-Portal ansehen: Herkunft, Abbrüche in der Buchung, Kontaktquote.
- [ ] Ein bis zwei neue Ratgeber-Artikel oder Aktualisierung bestehender.
- [ ] Bewertungsanzahl in `content/site.json` → `rating` und neue Zitate pflegen.
