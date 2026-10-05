# Angebots- und Briefing-Dokumente (in Markentrix-CI)

Diese Dokumente sind **Markentrix-Dokumente** und stehen in Markentrix-CI (Soft White, Graphite Navy, Cyan→Blue, Space Grotesk/Inter, Logo nach CI-Regeln). Das Kundenprojekt selbst bleibt in Kunden-CI.

Vorlagen (A4, druckfertig, als PDF aus Browser exportierbar): `assets/dokumente/briefing.html`, `assets/dokumente/angebot.html`. Alternativ als Word/Google Doc/PDF erzeugen, gleiche Struktur und CI.

## Briefing-Dokument (vom Kunden auszufüllen)
Struktur = `briefing-intake.md`: Unternehmen/Impressumsdaten, Ziel/KPI, Zielgruppe, Angebot/USP, Wettbewerb, Marke/CI, Inhalte, Technik/Zugänge, Pflege, Freigaben. Kurz halten (3–4 Seiten), Ausfüllhilfen und Beispiele, Pflichtfelder markiert. Hinweis zum Datenschutz (Verarbeitung der Angaben zur Projektbearbeitung). Rückgabe an info@markentrix.de.

## Domain-&-Technik-Checkliste (Anlage, Pflicht)
`assets/dokumente/domain-checkliste.html` geht mit Angebot und Briefing an **jeden** Kunden: Domain/Registrar/Inhaber, DNS-Zugang und -Stand, DNSSEC/CAA, E-Mail (MX/SPF/DKIM), bisherige Website, Vollmacht, Wunschtermin, plus was wir liefern (Server-IP v4/v6, www, ggf. Nameserver). Prozess intern: `domain-hosting-umzug.md`.

## Angebot
Inhalt in dieser Reihenfolge:
1. **Deckblatt:** Titel „Angebot Website [Kunde]“, Datum, Angebotsnummer, Gültigkeit (z. B. 30 Tage), Ansprechpartner.
2. **Ausgangslage & Ziel** (aus Briefing, in 3–5 Sätzen, kundenbezogen).
3. **Unser Vorschlag:** Seitenstruktur (Sitemap), Kernbotschaft, Primär-CTA, Verweis auf Demo-Link und Screenshot.
4. **Leistungsumfang:** je Phase (Konzept, Design-System, Copy/Textservice ja/nein, Umsetzung, Animation, Formulare/Consent, SEO-Basis, Barrierefreiheit, Performance-Garantie nur als Messziel, Tests, Livegang, Schulung). Was **nicht** enthalten ist (Fotoshooting, Texterstellung, Logoentwicklung, Fremdlizenzen, laufende Pflege) klar benennen.
5. **Qualitätsstandard:** Ziel-Werte Lighthouse/CWV (als Messziel, nicht Garantie), WCAG 2.2 AA, DSGVO-konforme Umsetzung (selbst gehostete Schriften, Consent), Browser-/Gerätetest.
6. **Zeitplan:** Meilensteine mit Kundenmitwirkung (Inhalte liefern, Feedback, Freigabe). Verzug durch fehlende Mitwirkung verschiebt Termine.
7. **Investition:** Genau ein Website-Paket (LANDING START / LANDING / BUSINESS WEB / WEB + FUNNEL) mit Projektpreis und monatlicher Pflege aus `pakete-preise.md`, netto zzgl. USt. Kombivorteile (500 € bei Website + KI-Kommunikation ab BUSINESS bzw. CI + Website) nur wenn die Bedingung erfüllt ist. Zusatzleistungen (CI, LOCAL VISIBILITY, SOCIAL MEDIA …) als Option. Nie Preise erfinden oder rabattieren ohne Freigabe; Abweichungen vorab schriftlich vereinbaren.
8. **Rahmenbedingungen:** Korrekturrunden (z. B. 2), Nutzungsrechte nach Zahlung, Domain auf den Kunden registriert, Hosting in der Pflege durch Markentrix (AV-Vertrag), Export/Umzug des Codes geregelt, Mitwirkungspflichten, Zahlung 50 % Anzahlung bei Auftragserteilung, 50 % bei Abnahme; Pflege monatlich per SEPA-Lastschrift zu Monatsbeginn; Zahlungsziel 7–14 Tage, Gewährleistung/Haftung laut AGB, **AV-Vertrag** bei Hosting/Wartung, Verweis auf AGB und Datenschutzhinweis.
9. **Nächste Schritte & Unterschriftenfeld** (Annahme per Unterschrift/E-Mail).
10. **Absender:** Markentrix, Celle, Niedersachsen, markentrix.de, info@markentrix.de (weitere Daten nur aus Projektdatei, nicht erfinden).

## Regeln
- Keine Ergebnis-/Ranking-/Anfragegarantien, keine „spart X Stunden“, keine erfundenen Referenzen/Zahlen (Allowlist `markentrix-werbevideo` Abschnitt 5).
- Preise immer gegen aktuelle Preisliste prüfen, Stand im Dokument nennen.
- AGB, AV-Vertrag, Haftungs-/Gewährleistungsklauseln stammen vom Anwalt/aus der Markentrix-Vertragsvorlage; Platzhalter, keine selbst erfundene Rechtssprache.
- CI-Regeln für Sales-Dokumente (CI-Master S. 16): Cover mit klarer Nutzenbotschaft, max. 1 primärer CTA pro Seite, helle großzügige Tabellen, Charts in Blue/Cyan mit Violet als Highlight, konsistenter Footer, Beweis statt Floskel (nur echte, freigegebene Cases).
- Kontrast vor CI-Mockup: Der CI-Master zeigt weißen Text auf Cyan-Button (≈ 1,9:1). In Dokumenten und Websites setzen wir Navy-Text auf Cyan→Blue, damit Lesbarkeit und WCAG erfüllt sind.
- Das Original-Logo (`assets/dokumente/logo-light.png`, `bildmarke.png`) wird unverändert verwendet: Light-Variante auf Weiß, Schutzraum = Höhe „M“, nie verzerrt/umgefärbt, Dokument min. 30 mm Breite, Bildmarke min. 8 mm.
- Nach außen nur Markentrix, keine Tool-/Modellnamen.
- Dokument vor Versand: Rechtschreibung, Zahlen, Summen (netto/USt/brutto), Gültigkeitsdatum, Kundendaten, Demo-Link prüfen.
- Versand als PDF mit sprechendem Dateinamen: `Markentrix_Angebot_[Kunde]_[JJJJ-MM-TT].pdf`.
