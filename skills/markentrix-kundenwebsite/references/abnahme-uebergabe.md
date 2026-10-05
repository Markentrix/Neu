# Abnahme, Livegang, Übergabe (Phase 6–8)

## Staging & Feedback
Staging-Link mit Passwortschutz und `noindex`. Ein Ansprechpartner beim Kunden bündelt Feedback, Korrekturrunden laut Angebot (typisch 2). Feedback sammeln als nummerierte Liste (Seite, Element, Wunsch). Änderungen außerhalb Scope als Zusatzauftrag benennen.
Vor Versand an Kunden: Qualitäts-Gate (SKILL Abschnitt 8) komplett.

## Freigabe
Schriftliche Freigabe (E-Mail genügt) für: Design, Texte/Claims, Bilder/Rechte (inkl. Lizenznachweis-Liste), vom Kunden gelieferte Rechtstexte, Tracking-Entscheidung. Ohne gelieferte Rechtstexte und unterschriebenen AV-Vertrag kein Livegang. Erst danach Livegang.

## Livegang-Checkliste
(Details zu DNS/Umzug: `domain-hosting-umzug.md`)
0. Domain-Checkliste und Vollmacht liegen vor, Zonenstand gesichert, Rollback-Plan, altes Hosting bleibt bis nach der Beobachtungszeit aktiv.
1. Backup, DNS-TTL vorher senken, Zielhosting prüfen (HTTPS, HSTS, Header).
2. Relaunch: Redirect-Map (301) aktiv, alte URLs getestet.
3. `noindex` entfernen, `robots.txt` und `sitemap.xml` live, Search Console + Bing verifizieren, Sitemap einreichen.
4. Formular live testen (Zustellung beim Kunden), E-Mail-Authentifizierung (SPF/DKIM/DMARC).
5. Google-Unternehmensprofil: URL, NAP-Abgleich, Leistungen.
6. Monitoring: Uptime, Zertifikatsablauf, Core-Web-Vitals-Feld, Formular-Eingang.
7. Lighthouse/Feldwerte nach Livegang erneut messen und dokumentieren.

## Übergabe-Paket
- Zugänge/Eigentum: Domain, Hosting, Repo/Export, CMS-Logins (Übergabe sicher, Passwort-Manager).
- Doku (1–3 Seiten): Struktur, Tokens, wie Inhalte geändert werden, genutzte Dienste und AVV-Liste, Consent-Einstellungen, Wartungsintervalle.
- Schulung/Video-Anleitung für Inhaltspflege (falls CMS).
- Messwerte und Prüfprotokoll (Lighthouse, A11y).
- Offene Punkte: z. B. anwaltliche Prüfung, fehlende Texte, empfohlene nächste Schritte.
- Empfehlung Pflege/Optimierung (Updates, Monitoring, Content, SEO, Reporting) als Angebot, ohne Druck.

## Haftung/Ehrlichkeit
Keine Rankingversprechen, keine Garantie auf Anfragezahlen. Rechtstexte „zur Prüfung durch Kunden/Anwalt“ kennzeichnen. Fehler transparent melden und beheben.
