---
name: "markentrix-kundenwebsite"
description: "Erstellt Kunden-Websites und Landingpages auf Agenturniveau für Markentrix-Kunden (lokale Unternehmen): Briefing, Sitemap, Kunden-Design-System, Copy, Umsetzung, Animation, Performance, Barrierefreiheit, DSGVO, SEO, Abnahme und Übergabe."
---

# Markentrix Kundenwebsite – Agentur-Produktionsskill

Für jede Website oder Landingpage, die Markentrix für einen **Kunden** baut. Die Seite trägt die Marke des Kunden, nicht die von Markentrix. Markentrix liefert Prozess, Qualität, Recht und Leistung. Ziel: Ergebnis, das ein Kunde ohne Nachbesserung abnehmen kann und das messbar Anfragen bringt.

Details in `references/`, Startgerüst in `assets/starter/`, automatischer Check in `scripts/audit.sh`.

## 1. Wann
Neue Website, Relaunch, Onepager, Kampagnen-Landingpage, Leistungsseite, Danke-/Rechtsseiten, Website-Audit für Kunden. Für die eigene Markentrix-Seite gilt zusätzlich die Markentrix-CI (Skill `markentrix-werbevideo`, Abschnitt 3).

## 2. Hard Gates
1. **Kunden-CI vor Eigengeschmack.** Farben, Logo, Schrift, Ton kommen vom Kunden. Fehlt eine CI: Mini-CI vorschlagen und vom Kunden freigeben lassen, nicht raten.
2. **Kein erfundener Beweis.** Keine erfundenen Kundenstimmen, Sterne, Referenzen, Zahlen, Auszeichnungen, Teamfotos. Fehlt Material: sichtbarer Platzhalter `[PLATZHALTER – vom Kunden]`, nie live. Stockfotos als solche markieren und nie als „unser Team/Betrieb“ ausgeben.
3. **Keine Heil-, Rechts-, Steuer- oder Ergebnisversprechen** (HWG, UWG, Berufsrecht der Branche). Aussagen vom Kunden schriftlich freigeben lassen.
4. **Kein Tracking, keine Drittanbieter vor Einwilligung.** Standard: alles selbst gehostet (Schriften, Icons, Skripte), Karten/Videos nur per Zwei-Klick.
5. **Barrierefrei:** WCAG 2.2 AA, Tastatur komplett, Kontrast geprüft, Reduced-Motion.
6. **Performance-Budget** (Abschnitt 7) erreicht oder Abweichung begründet.
7. **Rechtliche Pflichtseiten** (Impressum, Datenschutz, AGB, ggf. Barrierefreiheitserklärung): Der **Kunde** erstellt und liefert die Texte samt Anschrift, Register und USt-IdNr.; Markentrix bindet sie ein und prüft nur Vollständigkeit der Pflichtangaben und Passung zu den genutzten Diensten (keine Rechtsberatung, im Hand-off so benennen). Nie Rechtsdaten erfinden, ohne gelieferte Texte kein Livegang. Den **AV-Vertrag erstellt Markentrix** (`assets/dokumente/avv.html`).
8. **Nach außen nur Markentrix als Agentur:** nie Tool-/Modellnamen (Claude, Higgsfield, n8n …) im Code, Footer, Meta, Übergabe. Credit-Link „Website von Markentrix“ nur wenn vertraglich vereinbart, dezent, `rel` passend.
9. **Kundeneigentum & Hosting:** Die Domain wird auf den Kunden registriert. In der Pflege hostet Markentrix (Preisliste: Hosting, Updates, Sicherung inklusive), daher AV-Vertrag und transparente Regelung für Export/Umzug des Codes. Keine versteckte Abhängigkeit, die nur Markentrix lösen kann.
10. **Kein Dark-Pattern:** Ablehnen = Akzeptieren, keine Fake-Verknappung, keine vorangekreuzten Haken.
11. **Demo für jeden Kunden, aber sauber:** Jede Anfrage bekommt eine eigene Demo (Phase 1b) als gekennzeichneter Entwurf: `noindex`, passwortgeschützt, keine erfundenen Inhalte, keine fremden Rechte, kein Tracking, Löschfrist. Regeln in `demo-website.md`.
12. **Dokumente für den Kunden** (Briefing, Angebot) stehen in **Markentrix-CI**, die Website in **Kunden-CI**. Preise nur aus der aktuellen Preisliste, nie erfunden.
13. **AGB von Markentrix** liefert der Inhaber, nie selbst formulieren. **Preise und Pakete** nur laut Preisliste (`pakete-preise.md`), in Angeboten, nie auf Kundenseiten, nie rabattiert ohne Freigabe. Paketumfang (LANDING START/LANDING/BUSINESS WEB/WEB + FUNNEL) bestimmt die Tiefe, nicht die Qualitätsstandards.

## 3. Arbeitsablauf (Agentur-Pipeline)
| Phase | Ergebnis | Referenz |
|---|---|---|
| 0 Intake | ausgefülltes Briefing (Markentrix-CI-Dokument), Asset-/Zugangsliste | `briefing-intake.md`, `angebot-briefing-dokumente.md` |
| 1 Strategie | Ziel, Zielgruppe, USP, Wettbewerbs-Check, Sitemap, KPI | `briefing-intake.md`, `branchen.md` |
| 1b **Demo (Pflicht)** | individuelle Demo-Website für diesen Kunden, vor/mit Angebot | `demo-website.md` |
| 1c Angebot | Angebot in Markentrix-CI mit Paket, Demo-Link, Preisliste | `angebot-briefing-dokumente.md`, `pakete-preise.md` |
| 2 Design-System | Kunden-Tokens, Typo, Komponenten, Bildsprache | `design-system-kunde.md` |
| 3 Copy | Texte pro Seite, SEO-Keywords, CTAs, freigegeben | `conversion-landingpage.md` |
| 4 Umsetzung | Code aus Starter, Animation, Formulare, Consent | `animation.md`, `dsgvo-recht.md` |
| 5 Qualität | Audit, Lighthouse, A11y-Test, Gerätetest | `barrierefreiheit.md`, `performance.md` |
| 6 Abnahme | Staging-Link, Feedbackrunde(n), schriftliche Freigabe | `abnahme-uebergabe.md` |
| 7 Livegang | DNS/Redirects, Search Console, Monitoring | `abnahme-uebergabe.md`, `seo.md` |
| 8 Übergabe | Doku, Schulung, Pflegevertrag-Angebot | `abnahme-uebergabe.md` |

Nur fehlende Angaben beim Auftraggeber erfragen, den Rest mit begründeten Defaults entscheiden und im Hand-off nennen. Eine Version pro Phase freigeben lassen, nicht fünf Varianten zur Auswahl.

## 4. Standard-Stack
- Statische Seiten ≤ 10 Seiten: reines HTML/CSS/JS aus `assets/starter/` oder Astro. Mehr Seiten/Redakteursbedarf: Astro + Markdown/Headless-CMS (EU-Hosting) oder WordPress nur auf Kundenwunsch (dann Hardening, Caching, kein Page-Builder-Ballast, Plugin-Minimum, DSGVO-Plugins prüfen).
- Kein SPA-Zwang, Inhalte im HTML ausgeliefert. Progressive Enhancement.
- Hosting: Hetzner, Serverstandort Nürnberg, HTTPS, AVV, Backup, Security-Header (`performance.md`). Formularversand serverseitig/über AVV-Dienst, Spam-Schutz ohne reCAPTCHA.
- Versionskontrolle (Git), Staging getrennt von Live, `noindex` auf Staging.

## 5. Agentur-Qualitätsmerkmale (Unterschied zu Baukasten-Seiten)
- **Konzept vor Pixeln:** ein Seitenziel, ein Hauptkunde, ein Primär-CTA, Sitemap aus Suchintention.
- **Eigenes Design-System** je Kunde (Tokens, Skalen, Komponenten) statt Template-Optik.
- **Echte Inhalte** statt Lorem ipsum, Bildsprache konsistent, eigene Fotos bevorzugt, Retusche/Zuschnitt einheitlich.
- **Micro-Interaktionen und Scroll-Motion** ruhig und markengerecht (`animation.md`), nie auf Kosten von LCP/INP.
- **Messbar:** Ziele definiert (Anfragen, Anrufe, Terminbuchungen), datenschutzkonform gemessen, Reporting-Vorschlag.
- **Lokale Sichtbarkeit** eingebaut: NAP, Google-Profil-Abgleich, LocalBusiness-Daten, Leistungs-/Ortsseiten wo sinnvoll.
- **Wartbar:** saubere Struktur, Doku, Pflegeanleitung, Tokens an einer Stelle.

## 6. Technische Standards
- Semantisches HTML5, ein `<h1>`, Skip-Link, `lang="de"`, eindeutiger `<title>` und Description je Seite, Canonical, OG/Twitter, Favicon-Set, 404, `robots.txt`, `sitemap.xml`.
- Mobile-first (320 px bis 1920 px), 400 % Zoom nutzbar, Touch-Ziele ≥ 44 px.
- CSS: Custom Properties, `clamp()`, Grid/Flex, `:focus-visible`, kein Framework-Ballast. JS minimal, `defer`.
- Bilder: AVIF/WebP, `srcset`, Maße gesetzt, LCP-Bild `fetchpriority="high"`, Rest lazy, sinnvolle `alt`.
- Formulare: native Elemente, sichtbare Labels, `autocomplete`, Fehlertexte per ARIA, Datenschutz-Hinweis am Formular, Erfolgs-/Fehlerzustand getestet. Kunden-Mailzustellung (SPF/DKIM/DMARC) prüfen.
- Click-to-Call und Terminbuchung bei lokalen Betrieben prominent (Mobile). Öffnungszeiten, Anfahrt, Notdienst je Branche.

## 7. Performance-Budget (mobil, 4G, Mittelklasse-Gerät)
LCP ≤ 2,0 s · INP ≤ 150 ms · CLS ≤ 0,05 · TTFB ≤ 0,6 s · Lighthouse Mobil Perf ≥ 95 / A11y 100 / BP 100 / SEO 100 · initial ≤ 500 KB, JS ≤ 60 KB gzip, ≤ 20 Requests, 0 Drittanbieter vor Consent. Lab- und Feldwerte getrennt berichten, Lab ist kein Feldbeweis.

## 8. Qualitäts-Gate vor Abnahme
- [ ] `bash scripts/audit.sh <ordner>` ohne FAIL
- [ ] Lighthouse mobil im Budget, Werte dokumentiert
- [ ] axe/WAVE ohne Fehler, Tastaturdurchlauf, Screenreader-Stichprobe
- [ ] Geräte/Browser: iOS Safari, Android Chrome, Desktop Chrome/Firefox/Safari; 320/768/1280/1920 px
- [ ] Reduced-Motion und 200/400 % Zoom getestet
- [ ] Netzwerk-Tab: 0 Drittanbieter vor Consent
- [ ] Formular Ende-zu-Ende (Zustellung beim Kunden, Bestätigung, Fehlerfall, Spam-Test)
- [ ] Alle Texte/Claims/Bilder vom Kunden freigegeben, keine Platzhalter, keine Lorem-Texte
- [ ] Vom Kunden gelieferte Rechtstexte eingebunden und auf Vollständigkeit/Passung zu den Diensten geprüft; Consent-Lösung passend; AV-Vertrag unterschrieben (bei Hosting/Pflege)
- [ ] Lizenznachweise für alle Bilder und Schriften dokumentiert
- [ ] Redirect-Map (Relaunch), Sitemap, robots, OG-Bilder, Favicons, 404
- [ ] Backup, Staging `noindex` entfernt erst beim Livegang

## 9. Hand-off an Kunde und intern
Kurz und ehrlich: Umfang, Messwerte (Lab/Feld getrennt), offene Punkte (z. B. anwaltliche Prüfung, fehlende Inhalte), Zugänge/Eigentum, Pflegehinweise, Empfehlung Pflegepaket. Absender „Ihr Markentrix-Team“. Vorlagen: `assets/dokumente/angebot.html`, `briefing.html`, `avv.html` (A4, Markentrix-CI, als PDF exportierbar). Siehe `abnahme-uebergabe.md`.

## 10. Referenzen
`briefing-intake.md` · `branchen.md` · `pakete-preise.md` · `demo-website.md` · `angebot-briefing-dokumente.md` · `design-system-kunde.md` · `conversion-landingpage.md` · `animation.md` · `performance.md` · `barrierefreiheit.md` · `dsgvo-recht.md` · `seo.md` · `abnahme-uebergabe.md`
