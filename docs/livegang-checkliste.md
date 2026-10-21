# Livegang-Checkliste

## Muss vor dem Livegang erledigt sein

- [ ] **Impressum:** Inhaber:in oder Firmenname, USt-IdNr. oder Kleinunternehmer-Hinweis, Verantwortliche:r nach § 18 MStV (Portal → Inhalte → Grunddaten → Rechtliches).
- [ ] **Datenschutz:** E-Mail-Anbieter eintragen, Auftragsverarbeitungsvertrag mit Hetzner im Hetzner-Konto abschließen (Konsole → Datenschutz), Text rechtlich prüfen lassen.
- [ ] **Preise prüfen:** Richtpreise der vier Pakete (Refresh, Essential, Signature, Excellence) je Fahrzeugklasse in „Pakete & Preise“ (Kleinwagen, Kompaktwagen, Limousinen/Kombis/kleinere SUVs, große SUVs und Vans; Sport- und Luxusfahrzeuge sowie Wohnmobile auf Anfrage) und Keramikpreise (C² CarCeramic).
- [ ] **Aussagen prüfen:** „samstags nach Absprache“, „Abholung nach Absprache“, Firmenkunden-Seite („Abrechnung nach Absprache“), Gutschein-Regeln (Gültigkeit 3 Jahre, Paketgutschein für einen Kleinwagen, Zahlung per Überweisung oder bar).
- [ ] **Zahlungshinweis für Gutscheine** in Einstellungen (Kontoinhaber, IBAN, Verwendungszweck).
- [ ] **SMTP** in `.env` eintragen und Test-E-Mail senden.
- [ ] **PayPal** (Live-App) und **Google Kalender** (OAuth-Client) einrichten, siehe `betrieb-hetzner.md`. Danach eine Testbuchung mit kleinem Paket machen, anzahlen, erstatten.
- [ ] **Storno-Regel für die Anzahlung** festlegen und in den Buchungsbedingungen bzw. AGB nennen.
- [ ] **Testbuchung** über jede Formularart (Kontakt, Termin, Gutschein, Firma) durchführen und im Portal löschen.
- [ ] **Bewertungszahl** aktualisieren, falls sie sich geändert hat.

## Direkt nach dem Livegang

- [ ] Google Search Console: Eigenschaft anlegen, Methode „HTML-Tag“ wählen, nur den Code aus `content="…"` im Portal unter Grunddaten → Bestätigungscodes → Google eintragen, veröffentlichen, bestätigen. Danach `https://www.elbdetail.de/sitemap.xml` einreichen. Bing Webmaster Tools genauso (Feld Bing).
- [ ] Google Analytics 4 (optional): In analytics.google.com eine Property „ElbDetail“ mit Web-Datenstream für `https://www.elbdetail.de` anlegen, Datenaufbewahrung auf 14 Monate stellen, Google-Signale aus lassen, Auftragsverarbeitungsvertrag in der Verwaltung akzeptieren. Die Mess-ID (`G-…`) im Portal unter Grunddaten → Google Analytics eintragen und veröffentlichen. Ab dann erscheint der Einwilligungs-Hinweis, und die Datenschutzerklärung schaltet automatisch auf den Google-Analytics-Abschnitt um. Ohne ID bleibt die Website cookiefrei.
- [ ] Search Console mit Google Analytics verknüpfen (GA4 → Verwaltung → Produktverknüpfungen → Search Console), dann sehen Sie Suchanfragen und Besuche an einem Ort.
- [ ] Wächter per Cron einrichten (`deploy/watchdog.sh`, siehe Betriebsanleitung) und einmal testen: `docker compose run --rm --no-deps app python3 /app/server/app.py alarm "Test"` muss eine E-Mail auslösen.
- [ ] Bing Webmaster Tools: Sitemap einreichen (versorgt auch ChatGPT-Suche und Copilot).
- [ ] Rich-Results-Test für Startseite, eine Leistungsseite und einen Ratgeber-Artikel.
- [ ] Google-Unternehmensprofil: Website-Link auf `https://www.elbdetail.de/` und Termin-Link auf `/termin.html` setzen (Kit in `google-unternehmensprofil.md`).
- [ ] Branchenverzeichnisse mit identischer Schreibweise anlegen (`branchenverzeichnisse.md`).
- [ ] Google-Bewertungslink im Portal hinterlegen, Bewertungsprozess starten (`bewertungs-prozess.md`).
- [ ] Erste echte Vorher/Nachher-Fotos hochladen (`foto-und-video-shotlist.md`).
- [ ] Inhaber-Karte füllen: Portal → Grunddaten → Über uns (Name, Foto aus „Fotos“, 1–2 Sätze in eigenen Worten). Sie erscheint auf der Startseite, sobald Name und Text gefüllt sind.
- [ ] Anzeigen nur mit UTM-Parametern starten (`anzeigen-kit.md`).

## Monatlich

- [ ] Übersicht im Portal ansehen: Herkunft, Abbrüche in der Buchung, Kontaktquote.
- [ ] Ein bis zwei neue Ratgeber-Artikel oder Aktualisierung bestehender (Datum „Aktualisiert“ anpassen).
- [ ] Bewertungsanzahl und neue Zitate pflegen.
- [ ] Sicherungen prüfen (Datei vorhanden, Größe plausibel).
