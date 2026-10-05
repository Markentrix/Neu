# DSGVO, TDDDG, Impressum, BFSG – Umsetzung für Websites

Keine Rechtsberatung. **Rechtstexte der Kundenseite (Impressum, Datenschutz, AGB) erstellt der Kunde** (Generator/Anwalt) und liefert sie an Markentrix; Markentrix bindet ein, prüft Vollständigkeit der Pflichtangaben und ob die Datenschutzerklärung die tatsächlich genutzten Dienste abdeckt (Hosting, Formular, Buchungstool, Consent, Karten …) und meldet Lücken an den Kunden; im Hand-off als „zur Prüfung“ markieren. Stand der Rechtslage vor Livegang prüfen.

## 1. Grundprinzip
Datensparsamkeit: Was nicht erhoben wird, braucht keine Einwilligung. Beste Lösung = **Seite ohne Drittanbieter und ohne Cookies**, dann entfällt der Banner. Banner nur, wenn ein einwilligungspflichtiger Dienst wirklich gebraucht wird.

## 2. Einwilligung (§ 25 TDDDG, Art. 6/7 DSGVO)
Einwilligungspflichtig: alles, was Informationen auf dem Endgerät speichert/ausliest, die nicht unbedingt erforderlich sind (Marketing-/Analyse-Cookies, Pixel, Local Storage für Tracking, Fingerprinting) sowie Drittinhalte, die IP-Adressen an Dritte übertragen (YouTube, Google Maps, Social-Embeds).
Ohne Einwilligung zulässig: technisch zwingend notwendige Speicherung (Session, Warenkorb, Consent-Status selbst, Sicherheit).

Banner-Anforderungen:
- Erscheint vor jedem nicht notwendigen Request; Skripte werden erst **nach** Opt-in geladen (kein „laden und blockieren“).
- „Alle akzeptieren“ und „Nur notwendige / Ablehnen“ gleichwertig (gleiche Ebene, Größe, Kontrast).
- Granular nach Zweck/Dienst, jeder Dienst einzeln nennbar, nichts vorausgewählt.
- Widerruf jederzeit so einfach wie Erteilung (Footer-Link „Cookie-Einstellungen“).
- Consent-Nachweis (Zeitpunkt, Version, Entscheidung) speichern; Banner erneut bei Dienständerung.
- Banner selbst barrierefrei (Fokus-Management, Escape/Tastatur, Screenreader-Rolle `dialog`), blockiert nicht den Zugang zu Impressum/Datenschutz.
- Bei Drittinhalten: **Zwei-Klick-Lösung** (Platzhalter mit Hinweis, Inhalt erst nach Klick), Karten bevorzugt als statisches Bild + Link.
Consent-Lösung: selbst gehostet/einfach (z. B. Klaro, Orestbida CookieConsent) oder zertifizierte CMP. Kein Dienst, der selbst vor Consent Daten an Dritte sendet.

## 3. Tracking & Marketing
- Standard Markentrix-Seiten: kein Tracking oder cookielose, selbst gehostete Messung (Matomo/Plausible EU-/Self-Hosting). „Einwilligungsfrei“ nur annehmen, wenn die Konfiguration das nachweislich hergibt (keine Geräte-Speicherung, keine Profile, Datenschutzerklärung nennt es) und im Hand-off als „zur Prüfung“ markieren.
- Meta-Pixel/Conversions API, Google Ads/GA4/GTM, TikTok-Pixel: nur nach Opt-in, in Datenschutzerklärung benannt, AVV/Drittlandtransfer-Grundlage geprüft (EU-US Data Privacy Framework Status des Anbieters prüfen).
- Server-seitiges Tracking ersetzt die Einwilligung **nicht**.
- UTM-Parameter ohne Personenbezug sind unkritisch; keine E-Mail-Adressen in URLs.

## 4. Formulare & Lead-Erfassung
- Nur Pflichtfelder, die wirklich nötig sind (Name, E-Mail oder Telefon, Anliegen). Kein Telefon als Pflicht ohne Grund.
- Hinweis direkt am Formular: Zweck, Verantwortlicher, Link zur Datenschutzerklärung (Art. 13). **Keine** vorangekreuzte Checkbox. Einwilligungs-Checkbox nur, wenn Einwilligung die Rechtsgrundlage ist (z. B. Newsletter, Werbung); Anfragebearbeitung läuft auf Art. 6 Abs. 1 lit. b/f.
- Newsletter/Werbe-Mail: Double-Opt-In, Protokoll, Abmelde-Link, getrennte Einwilligung (§ 7 UWG).
- Übertragung per HTTPS, Daten nur an AVV-gebundene Empfänger (Hoster, E-Mail-Dienst, CRM, n8n-Instanz). Speicherdauer und Löschkonzept festlegen.
- Bestätigungsseite/Danke-Seite ohne Tracking-Zwang; Conversion-Messung nur mit Consent.
- Spam-Schutz ohne Google reCAPTCHA (Honeypot, Zeitprüfung, Rate-Limit).

## 5. Lead-Ad-Landingpages (Meta/TikTok)
Ad-Versprechen und Seite müssen übereinstimmen (Wortlaut, Angebot, CTA). Kein Pop-up-Zwang, schnelle Ladezeit (Budget Abschnitt 6 im SKILL), Impressum/Datenschutz im Footer sichtbar, Preise nur laut aktueller Preisliste mit „netto“. Pixel nur nach Consent; Meta-Lead-Formulare in der Plattform haben eigene Datenschutz-URL, die auf diese Seite zeigen darf.

## 6. Impressum (§ 5 DDG) und Pflichtseiten
Impressum: Name/Firma und Rechtsform, vertretungsberechtigte Person, ladungsfähige Anschrift (kein Postfach), E-Mail und eine weitere schnelle Kontaktmöglichkeit, Register und Registernummer, USt-IdNr. falls vorhanden, ggf. Aufsichtsbehörde/Kammer/Berufsbezeichnung. Daten (Anschrift, Register, USt-IdNr.) liefert der Kunde, **nie erfinden**. Erreichbar mit einem Klick von jeder Seite, als echter Link `Impressum` im Footer. Medienrechtlich Verantwortlicher (§ 18 MStV) bei redaktionellen Inhalten.
Datenschutzerklärung: Verantwortlicher, Datenschutzbeauftragter falls bestellt, alle Verarbeitungen mit Zweck/Rechtsgrundlage/Empfänger/Dauer, Hosting + Server-Logs, Kontaktformular, Tracking/Dienste, Drittlandübermittlung, Betroffenenrechte (Auskunft, Löschung, Widerspruch …), Beschwerderecht bei der Aufsichtsbehörde (Niedersachsen: LfD Niedersachsen).
Kein Rechtstext-Copy-Paste von fremden Seiten. Der **AV-Vertrag** (Markentrix als Auftragsverarbeiter bei Hosting/Pflege) kommt von Markentrix: `assets/dokumente/avv.html`, vor Einsatz anwaltlich prüfen lassen. Terminbuchungs-/Mail-Tools des Kunden brauchen dessen eigenen AVV mit dem Anbieter.

## 7. Barrierefreiheitsstärkungsgesetz (BFSG, seit 28.06.2025)
Betrifft u. a. Verbraucher-E-Commerce/Online-Shops und bestimmte Dienstleistungen im elektronischen Geschäftsverkehr; Kleinstunternehmen (< 10 Beschäftigte und ≤ 2 Mio. € Umsatz/Bilanzsumme) sind für Dienstleistungen ausgenommen. Ob ein Projekt erfasst ist, im Briefing klären (Shop/Buchung/Vertragsabschluss online?). Wenn erfasst: Erfüllung nach EN 301 549 (WCAG 2.1 AA als Mindestmaß, wir bauen 2.2 AA), **Barrierefreiheitserklärung** auf der Seite, Feedback-Kontakt. Unabhängig davon bleibt AA unser Standard.

## 8. Weitere Pflichten und Fallen
- Keine Google Fonts per Link, keine CDN-Bibliotheken (IP-Übertragung).
- Bildrechte: nur Material mit Lizenz/Nutzungsrecht; Personenfotos mit Einwilligung; KI-Bilder kennzeichnen, wenn sie echt wirken und Menschen zeigen.
- Server-Logs: Aufbewahrung kurz (z. B. 7 Tage), IP anonymisieren wo möglich.
- Cookie-Liste/Verarbeitungsverzeichnis bei Kundenprojekten für den Kunden vorbereiten.
- Online-Streitbeilegung/Widerrufsbelehrung/Preisangaben (PAngV) nur bei Shop/Verbrauchervertrag ergänzen.
- Werbeaussagen: UWG (keine irreführenden Alleinstellungs-/Garantieversprechen, Testimonial-Echtheit, Kennzeichnung von Werbung).
- Checkliste für Hand-off: Banner ja/nein, genutzte Dienste, AVV-Liste, offene Rechtsfragen.
