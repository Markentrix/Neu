---
name: "website-mit-portal"
description: "Statische Kundenwebsite für das Markentrix-Portal bauen, relaunchen, ändern oder prüfen (Kontakt, Termin, Gutschein über Portal-API). Nutzen bei Website-, Landingpage- und Relaunch-Aufträgen für Kunden. Nicht für die eigene Markentrix-Website."
---

MARKENTRIX – MASTER-PROMPT V4.3
KUNDENWEBSITE · PORTAL-INTEGRATION · CONVERSION · QUALITÄT

GELTUNG
Dieser Skill baut neue, STATISCHE Kundenwebsites, die über den Markentrix-Uploader und das Markentrix-Portal betrieben werden. Für die eigene Markentrix-Website (Hetzner/Docker-Stack) gilt der Skill "markentrix-eigene-website", nicht dieser.

PRIORITÄTEN BEI WIDERSPRÜCHEN
1. Datensicherheit, DSGVO, verifizierte API-Verträge und die konkreten Vorgaben des Kundenauftrags.
2. HARTE REGELN, Exportvorgaben und Portal-Schnittstellen dieses Skills.
3. Echte Kunden-CI (Logo, Farben, Schrift, Bildsprache) vor stilistischen Verboten. Verlangt die CI etwas von der VERBOTEN-Liste, ist es zulässig und wird in DESIGN.md begründet.
4. Conversion, Lesbarkeit, Barrierefreiheit und Performance vor Animation und Dekoration.
5. Stil-Beispiele, Richtwerte und externe Design-Skills sind nachrangig.

WEGWEISER (welcher Abschnitt wann)
- Vor dem Start: 1 Abfrage und Auftragsart. Immer gültig: 2 Harte Regeln, 3 Datenschutz.
- Planen und Bauen: 4 Ablauf (Schritte 1–7). Dazu 5 Design-Regeln (Verbote, Typografie und Farbe, Bewegung, Gestaltungssysteme, Hero-Kompositionen), 6 Branchenprofile mit Farb-Bibliothek, 7 Lokales SEO, 8 Performance und Barrierefreiheit, 9 Portal-Schnittstellen.
- Testen (Schritte 6 und 7): 11 Mock-Server, 14 Härtetest, 15 Handy, 16 Design-Kritik, 17 Bewegungs-Review, 18 Prüfskript, 21 Formulartest, zum Schluss 12 Prüfliste.
- Abgeben: 13 Bericht, danach 22 Kundenübergabe.
- Nur bei Bedarf: 19 Relaunch, 20 Änderungsauftrag, 10 externe Design-Skills, Skill "website-mit-portal-shop".
Die Abschnittsnummern bleiben fest, weil Prüfliste, Bericht und der Shop-Zusatz darauf verweisen. Neue Regeln kommen in den passenden Abschnitt, nicht ans Ende.

======================================================================
1. ABFRAGE VOR DEM START
======================================================================
Prüfe, was aus Auftrag, Anhängen und bestehender Website schon vorliegt. Fehlt etwas davon, frage es EINMAL gesammelt ab, bevor du Material sammelst oder entwirfst:
- Firma, Branche, Ort, bestehende Website/Google-Profil
- gewünschte Funktionen: <Kontaktformular | Terminbuchung | Leistungen/Mitarbeiter | PayPal | Google-Bewertungen | Statistik | Online-Shop | Gutschein>
- Impressumsdaten: Firmenname, Inhaber, Anschrift, Telefon, E-Mail, USt-ID/Steuernummer
- Öffnungszeiten, Einsatzgebiet, Logo, Fotos, Preise, vorhandene CI
- bei Shop: AGB, Widerrufsbelehrung, Kleinunternehmer ja/nein, Lieferzeit

FARBFRAGE (bei Neubau und Relaunch IMMER stellen, zusammen mit der Abfrage oben; entfällt nur, wenn der Auftrag die Farben nennt oder eine verbindliche Kunden-CI vorliegt)
Die drei Kombinationen der Branche aus der FARB-BIBLIOTHEK (Abschnitt 6) zeigen, jede mit Grund, Text und Akzent als Hex-Wert. Die Empfehlung steht zuerst, ist als "Empfehlung" markiert und bekommt einen Satz Begründung aus Logo, Fotos, Material und Ort dieses Betriebs. Dann fragen: "A, B, C oder eigene Farben?" Gibt es ein Werkzeug für Auswahlfragen, die drei als antippbare Optionen anbieten. Liegt außer den Farben schon alles vor, ist das die einzige Frage vor dem Start. Ist niemand erreichbar (geplanter Lauf), die Empfehlung nehmen und im Bericht nennen.
Ist niemand erreichbar (geplanter Lauf), arbeite mit dem Vorhandenen und führe alles Fehlende unter "OFFEN:".

AUFTRAGSART ZUERST BESTIMMEN
- NEUBAU: Betrieb ohne Website oder ausdrücklich neue Seite. Voller Ablauf (Abschnitt 4).
- RELAUNCH: Es gibt eine alte Website, die ersetzt wird. Voller Ablauf, zusätzlich Abschnitt 19.
- ÄNDERUNG: Eine mit diesem Skill gebaute Seite wird angepasst (Preise, Texte, Bilder, neue Unterseite). Nur Abschnitt 20, kein neues Design.
- Shop, Gutscheinverkauf oder bezahlte Online-Buchung gewünscht: zusätzlich den Skill "website-mit-portal-shop" laden (Pflicht).

GRUNDSATZ "NICHTS ERFINDEN" (gilt überall): keine erfundenen Kennzahlen, Preise, Öffnungszeiten, Kundenstimmen, Kundenlogos, Siegel, Auszeichnungen, Personen, Superlative ("Nr. 1", "garantiert", "preisgekrönt") oder Beispieldaten. Was fehlt, steht als Liste "OFFEN:" am Ende der Antwort.

======================================================================
2. HARTE REGELN (der Upload lehnt sonst ab oder die Seite funktioniert nicht)
======================================================================
KEIN eigenes Backend: keine Python-/Node-Server, kein PHP, keine Datenbank, kein Docker, kein Admin-Bereich, keine Serverfunktionen. Alles Dynamische läuft über das Portal (Abschnitt 9). Fehlt eine Funktion, baue sie NICHT selbst, schreibe am Ende, was fehlt.
Abgabe: Ordner "website-fertig/" mit index.html direkt darin (kein Unterordner dazwischen). Bei Frameworks nur den fertigen Export (Next.js "output: export", Astro, Vite "dist") liefern, ohne node_modules und ohne Build-Skripte. Build-Tools, Mock-Server und Arbeitsordner liegen NEBEN website-fertig/, nie darin.
Erlaubte Dateien: html, css, js, json, xml, txt, ico, png, jpg, webp, avif, gif, svg, woff, woff2, ttf, otf, webmanifest, pdf, mp4, webm, mp3. Verboten: .php, .exe, .sh, Symlinks, versteckte Dateien (.env, .git), absolute Pfade, "../" in Pfaden. Größe: ZIP bis 120 MB.
Alles relativ verlinken (/seite.html oder seite.html), nie http://, nie localhost/127.0.0.1, keine festen Domain-Namen im Code. Wo eine absolute Adresse technisch nötig ist (sitemap.xml, Sitemap-Zeile in robots.txt, Canonical, og:url, JSON-LD), den Platzhalter {{SITE_URL}} setzen (ohne Slash am Ende, z. B. {{SITE_URL}}/leistungen.html); der Uploader ersetzt ihn durch die Live-Adresse. Den Platzhalter nirgends sonst verwenden und im Bericht nennen, in welchen Dateien er steht.
Seiten: index.html, impressum.html, datenschutz.html, 404.html, danke.html (für Formulare), sitemap.xml, robots.txt, favicon. 404.html und danke.html bekommen <meta name="robots" content="noindex"> und stehen nicht in der Sitemap. Werte aus der URL (ref, typ, id) nur per textContent ausgeben, nie per innerHTML.
Jede Seite: <html lang="de">, <title> (unter 60 Zeichen), <meta name="description">, <meta name="viewport" content="width=device-width, initial-scale=1">, genau eine <h1>, alt-Text an allen Bildern, Impressum und Datenschutz im Footer verlinkt, mindestens ein tel:- oder mailto:-Link auf der Startseite.
Bilder: unter 1,5 MB, als webp/avif, mit width/height. Kein Lorem ipsum, keine Platzhaltertexte, keine toten Links.

======================================================================
3. DATENSCHUTZ (Deutschland, DSGVO)
======================================================================
Schriften LOKAL einbinden (woff2 im Ordner, z. B. aus dem npm-Paket @fontsource/<schrift> kopieren, nur benötigte Schnitte), KEINE Google Fonts, keine Fremd-CDNs (jsDelivr, cdnjs, unpkg), keine Fremd-Icons per URL.
Keine YouTube-/Google-Maps-/Facebook-Einbettungen direkt. Wenn nötig: Zwei-Klick-Lösung (Platzhalter, erst nach Klick laden) und im Text darauf hinweisen.
Kein eigenes Cookie-Banner und kein eigenes Analytics bauen. Statistik und Einwilligung kommen vom Portal.
Jedes Formular hat eine Einwilligungs-Checkbox mit Link zur Datenschutzerklärung (Pflichtfeld "einwilligung") und fragt nur ab, was der Vorgang braucht.
Impressum und Datenschutz mit den echten Firmendaten füllen.
Pflichtlinks: Impressum und Datenschutz sind auf JEDER Seite verlinkt, auch auf Beispiel-, Danke- und Einbettungsseiten, nicht nur auf der Startseite. Direkt am Absenden-Knopf jedes Formulars steht ein Satz mit Link zur Datenschutzerklärung. Beispielformulare, die nichts senden, sagen das.
Zielgruppe VOR dem Bau klären (B2B oder B2C; Teil der Abfrage). B2B (nur Unternehmen): Pflicht-Checkbox "Ich handle als Unternehmer im Sinne des § 14 BGB", nicht vorangekreuzt, und Preise mit "netto" direkt am Preis. Lässt das Portal die Prüfung nicht zu, ist das ein "OFFEN:". B2C: Bruttopreise, Widerruf und bei Verkauf über die Seite die Barrierefreiheitspflichten (BFSG) prüfen lassen; im Bericht als "OFFEN: rechtliche Prüfung".
Keine pauschale "Haftung für Links" und keine Haftungsausschluss-Texte. Keine Zusagen wie "rechtssicher", "abmahnsicher", "DSGVO-konform", "rund um die Uhr", "24/7", "garantiert" oder "jederzeit"; Leistungs-, Datenschutz- und Barrierefreiheitsaussagen nur mit dem tatsächlichen Umfang. Aussagen zu Datenspeicherung (Cookie-Laufzeit, Aufbewahrung, Standort) nur, wenn gemessen oder belegt; nie schätzen.
Bewertungen und Kundenstimmen nur echt, mit Quelle und Hinweis zur Herkunft (zum Beispiel "von Google, von uns nicht bearbeitet") und ehrlicher Angabe, ob die Echtheit geprüft wird. Zahlen, die von Hand gepflegt werden (Anzahl Bewertungen), mit Stand ("Stand November 2026"). Referenzen, Logos und erkennbare Personen nur mit dokumentierter Zustimmung, Bilder nur mit belegter Lizenz: im Bericht unter "OFFEN:" führen, wenn der Nachweis fehlt.
Befristete Angebote bekommen ein Ablaufdatum im HTML (data-bis) und im Skript; im Bericht steht "Nach Fristende neu ausliefern", denn eine statische Seite versteckt sonst nur im Browser.
Wortlaut der Rechtstexte: Liegt neben website-fertig/ ein Ordner rechtstexte/ mit geprüften Bausteinen (oder liefert der Auftrag welche), deren Wortlaut UNVERÄNDERT übernehmen und nur die Platzhalter füllen; Absätze zu nicht genutzten Funktionen weglassen, nichts umformulieren. Fehlen Bausteine, einen Entwurf schreiben und im Bericht unter "OFFEN:" als "Rechtstext-ENTWURF, nicht geprüft: <Seite>" führen (kein Hinweis darauf auf der Seite selbst).
Impressum, Pflichtangaben (§ 5 DDG): Name und Rechtsform, bei Einzelunternehmen Vor- und Nachname des Inhabers, ladungsfähige Anschrift, E-Mail und Telefon, USt-IdNr. falls vorhanden, Register und Nummer falls eingetragen, bei Handwerk und anderen geregelten Berufen zuständige Kammer und Berufsbezeichnung, Aufsichtsbehörde falls genehmigungspflichtig. Kein Hinweis und kein Link auf die EU-Streitbeilegungsplattform (seit 20.07.2025 eingestellt); der Hinweis nach § 36 VSBG nur nach Angabe des Betriebs. Jede fehlende Angabe ist "OFFEN:". Die Datenschutzerklärung nennt: Kontaktformular, ggf. Terminbuchung, ggf. Google-Bewertungen, ggf. PayPal, ggf. Online-Shop (Bestelldaten, Versand, Aufbewahrung), Server-Logs, Hosting bei Markentrix.

======================================================================
4. ABLAUF (Reihenfolge einhalten)
======================================================================
Ziel ist Agentur-Niveau: Die Seite soll aussehen, als hätte eine Spitzenagentur sie für 50.000 € gebaut, unverwechselbar für genau diesen Betrieb. Ein Fremder darf sie nicht für eine KI-Seite halten. KI-Seiten erkennt man an Standardwerten, die niemand bewusst gewählt hat; jede sichtbare Entscheidung muss für DIESEN Betrieb getroffen sein.

SCHRITT 1 – MATERIAL UND BRIEFING
Echte Fotos (Betrieb, Team, Werkstatt, Arbeitsergebnisse, Produkte, Ort) von der bestehenden Website, dem Google-Profil, Social Media oder vom Kunden; Logo; echte Texte, Preise, Bewertungen, Zahlen.
Briefing festhalten: Hauptziel, Zielgruppe, Zielregion, Kontaktweg, Nutzenversprechen, wichtigste Einwände, vorhandene Vertrauensbeweise (jeweils mit Quelle), kaufrelevante Leistungs- und Preisinformationen. Genau EINE Haupt-Conversion pro Seite; Nebenaktionen ordnen sich sichtbar unter. Branchenprofil aus Abschnitt 6 als Startpunkt nehmen.
Inventar: 8–12 Dinge, die nur dieser Betrieb hat (Name und Bedeutung, Straße/Ort und wie sie aussieht, Zahlen aus dem Auftrag, Einschränkung ("nur 1 Charge im Monat"), Material, Rituale/Zeiten, Gedrucktes seiner Welt: Schild, Karte, Etikett).
Flächen-Modus: Kundenwebsite = "Persuade" (Besucher entscheidet und handelt). Shop-/Buchungsflächen = "Operate" (Klarheit, Wiedererkennbarkeit vor Ausdruck). Rechtstexte/FAQ = "Read" (Lesbarkeit zuerst).

SCHRITT 2 – ARGUMENT
Seite als Behauptungen mit Beleg planen, eine Zeile pro Abschnitt: Bedarf → konkret belegbares Angebot → Unterschied → Risikoabbau/Vertrauen → Handlung. Reihenfolge nach dem, was die Kundschaft dieses Betriebs zur Entscheidung braucht. Abschnitt ohne Behauptung streichen.

SCHRITT 3 – RICHTUNG, IDEE, DESIGN.md (bevor Code entsteht)
Drei Richtungen aus dem Inventar skizzieren und die wählen, die etwas trägt, das nur dieser Betrieb hat. Hat der Kunde Farben/Schriften, bleiben sie. Sonst gilt die in der FARBFRAGE gewählte Kombination; alle drei Richtungen arbeiten mit ihr. Palette gegen das Material des Betriebs prüfen (Pastell bei Torf-Whisky = falsch).
Ideensatz, beide Lücken aus dem Inventar: "Auf dieser Seite wird [etwas, das nur dem Betrieb gehört] zu [Gestaltungsmittel der Richtung]." Austauschtest: Funktioniert der Satz (oder später die Seite mit getauschtem Namen und Logo) auch für den Betrieb zwei Straßen weiter? Dann ist es Kategorie, nicht Idee. Neu.
Eine "lebendige Sache" pro Seite, aus der Idee gebaut, mit echtem Inhalt, am Handy mit dem Daumen bedienbar, mit Ausweichlösung ohne Skript (z. B. Öffnungs-Status live, Holzart wählen, Preisrechner mit echten Preisen, Terminübersicht aus /api/verfuegbarkeit). Nur über Portal-API/Bausteine, nie mit eigenem Backend.
Plan gegen die VERBOTEN-Liste (Abschnitt 5) prüfen: Würde ich für einen ähnlichen Betrieb dasselbe bauen? Wenn ja, ist es Standard: überarbeiten und festhalten, was geändert wurde und warum.
DESIGN.md NEBEN website-fertig/ speichern (.md ist im Upload nicht erlaubt). Inhalt:
- Kernidee in einem Satz, Ideensatz, Live-Element, verworfene Richtungen mit Grund.
- Farben: 4–6 benannte Hex-Werte mit Rolle (Grund, Text, Fläche, Akzent …), abgeleitet aus Logo, Material, Ort und Branche. Verteilung 60/30/10. Ohne Kunden-CI sind Grund, Text und Akzent die gewählte Kombination aus der FARB-BIBLIOTHEK (Buchstabe nennen); weitere Werte sind nur Tonstufen dieser drei.
- Schriften: eine charaktervolle Display-Schrift (sparsam), eine gut lesbare Textschrift, höchstens zwei Schriftfamilien insgesamt. Zahlen/Daten über Tabellenziffern der Textschrift (font-variant-numeric: tabular-nums). Feste Typo-Skala mit deutlichen Sprüngen.
- Layout-Konzept als kurze Beschreibung plus ASCII-Skizze, Hierarchie für Desktop und Handy mit klarem Fokus im ersten Bildschirm. Der Hero eröffnet mit dem Typischsten aus der Welt des Betriebs (echtes Foto, Werkstück, Ergebnis, eine echte Zahl), nicht mit dem Standard-Hero.
- Signatur: genau ein unverwechselbares Element, an das man sich erinnert. Alles drumherum ruhig und diszipliniert.
- Hero-Komposition (Buchstabe A–G aus Abschnitt 5 oder eigene, mit Grund) und die Gestaltungssysteme: Schattenwerte, Radien, Bildform, Belege im ersten Bildschirm.
- Haupt-Conversion, Button-Text und Rückmeldung nach der Aktion.
- Vertrauensbelege mit tatsächlicher Quelle. Bewegungs-Entscheidungen mit Zweck.
- Jede begründete Ausnahme von der VERBOTEN-Liste.

SCHRITT 4 – TEXTE VOR DEM MARKUP
Ganzen Textentwurf zuerst. Jede Überschrift höchstens zwei Zeilen bei JEDER Breite (ca. 32 Zeichen sind überall sicher) und mit konkretem Nutzen oder Fakt, nicht bloß Atmosphäre.
Erster Bildschirm beantwortet GROSS: wer, was, wo, für wen, wann/wie viel, was jetzt zu tun ist. Ein Stützsatz direkt unter der Headline, eine Hauptaktion als echter Button.
Jeder Bereich, wegen dem Leute kommen (Karte, Leistungen, Preise, Zeiten), hat eigene Überschrift und eigenen Navigationspunkt. Inhalte vollständig, keine dünnen Abschnitte. Preise erklären Umfang, Unterschiede und Folgekosten.
Konkret, in der Sprache des Betriebs und der Region, mit echten Namen, Orten, Leistungen und Preisen. Buttons nennen die Handlung ("Termin für Reifenwechsel wählen"). Fehlertexte sagen, was zu tun ist.

SCHRITT 5 – BAUEN
Tokens zuerst: jede Farbe und Schrift als CSS-Variable auf :root aus DESIGN.md, keine losen Hex-Werte. Alle Unterseiten nutzen dieselben Tokens, dieselbe Navigation und denselben Footer (kein Design-Drift).
Hero zuerst in Desktop- und Handybreite, groß was groß ist, klein was klein ist. Anordnung aus den HERO-KOMPOSITIONEN (Abschnitt 5) wählen oder bewusst davon abweichen. Anordnung aus den HERO-KOMPOSITIONEN (Abschnitt 5) wählen oder bewusst davon abweichen. Jede Sektion eine andere Komposition als ihre Nachbarn; die Idee zieht sich bis Preise, FAQ und Footer durch (häufigster Fehler: starker Hero, dann Standardblöcke).
Bilder in dieser Reihenfolge: Kundenfotos > echte Bilder aus offenen Sammlungen (passende Lizenz, lokal als webp, Credit im Footer) > im Code gezeichnet (Material/Fliesen/Schild des Betriebs) > nur Typografie/Farbfläche. Erzeugte (KI-)Bilder nur für Material, Textur und Gegenstände und nur nach Freigabe des Kunden; nie für Personen, Räume, Arbeitsergebnisse oder Referenzen des Betriebs (das wäre erfunden). Einheitliche Bildsprache (Zuschnitt, Licht, Farbwirkung). Mindestens 4 echte Bilder pro Seite als Ziel; fehlen sie, als "OFFEN:" melden statt auffüllen. Ein dominantes Bild schlägt sechs kleine.
Fülle: Jeder Desktop-Bildschirm wirkt wie ein Plakat (ein dominantes Ding plus Inhalt). Leere Flächen nur einmal pro Seite bewusst.
Rahmen und Rhythmus: gleiche äußere Ränder links/rechts, Abschnittsabstand 120–240 px (Desktop), Abschnitte unterschiedlich dicht und breit, mindestens ein Vollbreite-Moment, Asymmetrie nur innerhalb des Rasters, nie leere Hälfte ohne Gegengewicht.
Zustände: Hover, sichtbarer Fokus, Laden, Fehler, leer. Alles per Tastatur bedienbar, Icons mit aria-label, Formularfelder mit sichtbarem Label.
Portal-Bausteine (Variante A) über die mk-Klassen an DESIGN.md anpassen, damit sie nicht wie Fremdkörper wirken. Für volle Designfreiheit Variante B.
Lokales SEO (Abschnitt 7) und Performance-Grenzen (Abschnitt 8) gleich mitbauen.

SCHRITT 6 – VEREDELN
Der Reihe nach durchgehen: Kritik (Stärken, größte Schwächen) → Typografie → Layout → Farbe (mutiger oder ruhiger) → UX-Texte → Handy/Tablet → Härten (Fehler, Leerzustände, lange Texte, API-Ausfall) → Feinschliff → Ladezeit. Screenshots ALLER Breiten wirklich ansehen, Top 3 Probleme beheben, neu prüfen, höchstens 3 Runden. Pflicht in diesem Schritt: Härtetest (Abschnitt 14), Handy-Feinheiten (15), Design-Kritik mit Wertung (16), Bewegungs-Review (17), Prüfskript (18).
Bei jeder Animation und Zier fragen: dient sie einer Entscheidung des Besuchers? Sonst raus. Vor der Abgabe mindestens ein Deko-Element entfernen. Entfernte Zier nicht durch neue Zier ersetzen: Platz füllen mit Maßstab, echtem Inhalt, Bild für dieses Thema oder einer Farbfläche.

SCHRITT 7 – PRÜFEN (Abschnitt 12) und BERICHT (Abschnitt 13).

======================================================================
5. DESIGN-REGELN
======================================================================
VERBOTEN (nur erlaubt, wenn Kunde oder Marke es ausdrücklich verlangt oder wenn es nach den GESTALTUNGSSYSTEMEN weiter unten als System festgelegt ist; dann in DESIGN.md begründen)
Farbe: Lila-/Indigo-/Violett-Verläufe und -Buttons (Tailwind indigo/violet/purple, z. B. #6366F1, #8B5CF6, #7C3AED, #A855F7), Verlaufstext in Überschriften, Pink→Lila-Kacheln, Neon-Glow, Dauer-Dark-Mode ohne Grund, grauer Fließtext auf Dunkel, unveränderte Tailwind-/shadcn-Grautöne (zinc, slate), Standard-blue-600, schüchterne Palette ohne Hauptfarbe. Verläufe generell (Ausnahme: neutraler Scrim unter Text auf Foto).
Zweite KI-Welle: cremefarbener oder beiger Seitengrund (der Grund ist Reinweiß oder eine klare Farbe aus der CI); Creme um #F4F1EA + Terrakotta um #D97757 + Serif; Fast-Schwarz + ein Neongrün oder Zinnober; Smaragd #10B981 als Ausweichakzent; "Broadsheet-Kostüm" (Haarlinien, Radius 0, Zeitungsspalten) bei Inhalt, der keine Zeitung ist.
Schrift: Inter, Roboto, Arial oder System-Stack als einzige Schrift; Geist, Space Grotesk, Instrument Serif, Syne, Sora, Fraunces, Cal Sans oder Montserrat + Open Sans als Reflexwahl; ein einzelnes hervorgehobenes Wort in der Headline (kursiv, farbig, fett, unterstrichen); Eyebrows ohne eigene Information (ALL-CAPS-Label, Pill-Badge, "Neu ·"-Chip über Überschriften); Monospace außer für echten Code; durchgehend Title Case; flache Skala.
Layout: zentrierter Hero mit Pill-Badge, zwei Buttons und Glow-Orb; drei oder vier identische Icon-Karten oder Reihen identischer Karten; Statistik-Leiste mit runden Zahlen; Nummern 01 / 02 / 03 ohne echte Reihenfolge; Standard-Reihenfolge Hero → Logos → Features → Testimonials → Zahlen → Preise → FAQ → CTA; Vier-Spalten-Footer mit Newsletter; alles zentriert (Zentrierung höchstens einmal); überall gleiche Abstände und Sektionshöhen; fake Fenster mit macOS-Ampelpunkten; Fake-Dashboards; schwebende Pillen-Navigation.
Komponenten: rounded-2xl mit demselben weichen Schatten überall; Schatten an Elementen, die flach auf der Fläche liegen (Schatten nur nach dem EBENENSYSTEM unten); Haarlinien und graue 1-px-Rahmen als Trenner oder um jede Karte (stattdessen Abstand, Tonstufe, Maßstab, gefüllte Fläche); farbiger Streifen links/oben an Karten; Karten in Karten; Glassmorphism/backdrop-blur; Icon in getöntem Rundquadrat; Pfeil "→" an jedem Link; Meta-Zeilen "A · B · C"; Effekt-Bibliotheken (Spotlight, Beams, Meteors, Shimmer-Button, Marquee nur als Deko); Status-Chips ohne echten Zustand.
Icons und Bilder: Emojis als Icons; Standard-Lucide-Set (Sparkles, Zap, Rocket, Shield, Check, ArrowRight) aus Reflex; Stock-"Team am Laptop"; 3D-Blobs, Mesh-Gradients, Partikel, Deko-Formen; KI-generierte Personenfotos; Platzhalter-Avatare; leere Demo-Flächen.
Bewegung: dasselbe Fade-up an jeder Sektion; Bounce-/Elastic-Easing; hochzählende Zahlen; Zoom auf jedem Bild-Hover; transition: all.
Text: "Ihr Partner für …", "Qualität, die überzeugt", "In der heutigen Zeit", "auf das nächste Level", "maßgeschneiderte Lösungen", "innovativ", "ganzheitlich", "nahtlos"; "Nicht nur X, sondern auch Y"; Dreier-Slogans ("Schnell. Sauber. Zuverlässig."); Gedankenstriche (—) im Fließtext; "Jetzt starten", "Mehr erfahren", "Absenden" als Button-Text; FAQ, die nur die Seite wiederholt.

TYPOGRAFIE UND FARBE
Zwei bis drei Größen tragen die Wirkung: eine sehr große, eine kleine, wenig dazwischen. Headline zu Fließtext mindestens 3×, Spitzenseiten 4–8×. Höchstens 5 Größen insgesamt.
Display: Laufweite -0,02 bis -0,05em, Zeilenhöhe 0,85–1,05. Linksbündig als Standard.
Fließtext in voller Tinte, 16–20 px, Zeilenhöhe 1,45–1,6, 45–75 Zeichen je Zeile, Kontrast mind. 4,5:1. Grau nur für Nebennotizen.
Statements (große Einleitungssätze) als <p>/<blockquote>, höchstens 36 px Desktop / 24 px Handy, ca. 25 Wörter; länger = Headline und Zwei-Zeilen-Regel gilt.
Eine Grundfarbe, eine Tinte, ein Akzent (nur für Aktion und ein weiteres Ding). Flächen durch kleine Tonstufen trennen. Ein Abschnitt darf die ganze Feldfarbe wechseln.
Buttons: eine Füllfarbe, einmal entscheiden: eckig ODER voll rund (weicher 9–16-px-Radius ist der Schwäche-Standard). Radius und Rahmen sonst nach Hierarchie variieren.
Navigation: Wortmarke, 3–5 Links, eine Aktion. Footer = gestalteter Abschluss (Name groß zurück), keine Sitemap; Pflichtlinks (Impressum, Datenschutz, ggf. Widerruf, Barrierefreiheit, Statistik-Einstellung) bleiben.

BEWEGUNG
Ein orchestrierter Moment (z. B. Seitenaufbau) plus Rückmeldung auf Aktionen. Staffel nur 30–80 ms Abstand, blockiert nie die Bedienung, nicht in jeder Sektion wiederholen.
Entscheidung vor jeder Animation: a) Häufigkeit: 100×/Tag oder Tastatur-Aktion = keine; Dutzende/Tag (Hover, Listen) = weglassen oder stark reduzieren; gelegentlich (Menü, Dialog, Toast) = normal; selten (Erstbesuch, Bestätigung) = darf Freude machen. b) Zweck nennen: Raumbezug, Zustand, Erklären, Rückmeldung, harten Wechsel abfedern. "Sieht cool aus" = nein. c) Easing: Ein-/Ausblenden = ease-out; Bewegung auf dem Schirm = ease-in-out; Hover/Farbe = ease; Dauerbewegung = linear. NIE ease-in für UI. Eigene Kurven: --ease-out: cubic-bezier(0.23, 1, 0.32, 1); --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1); --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1). d) Dauer: Button-Feedback 100–160 ms, Tooltips 125–200 ms, Dropdowns 150–250 ms, Modale/Drawer 200–500 ms. UI unter 300 ms. Austritt schneller als Eintritt. e) Nur transform und opacity animieren, nie width/height/margin/padding.
Details:
- Pressbare Elemente: :active { transform: scale(0.97) } (0,95–0,98), transition transform 160 ms ease-out.
- Nie aus scale(0) starten: ab scale(0.95) plus opacity 0. Popover von ihrem Auslöser aus skalieren (transform-origin), Modale bleiben mittig.
- Unterbrechbare UI mit CSS-Transitions statt Keyframes (Keyframes starten bei 0 neu). Einblenden neuer Elemente mit @starting-style, Fallback data-mounted.
- Weicher Übergang, der trotz Easing falsch wirkt: kurz filter: blur(2px) (unter 20 px, in Safari teuer).
- clip-path: inset() für Reveals (Bild aufdecken, Vorher/Nachher-Schieber, Tabs mit sauberem Farbwechsel). Auf Scroll via IntersectionObserver, einmalig.
- Hover-Effekte nur in @media (hover: hover) and (pointer: fine), sonst falsche Treffer auf Touch.
- prefers-reduced-motion: Bewegung und Position raus, Opazität/Farbe darf bleiben.
- Nur CSS, WAAPI (element.animate) oder kleines lokales JS; keine Animations-Bibliotheken. CSS-Variablen auf Elternelementen vermeiden, wenn viele Kinder reagieren (transform direkt setzen).
- Tooltips: Verzögerung beim ersten, danach sofort und ohne Animation beim Nachbarn.
- Gesten (Drawer/Slider): Geschwindigkeit zählt (ab ca. 0,11 px/ms schließen), Dämpfung statt harter Wand, Pointer-Capture, Multi-Touch ignorieren. Federn nur bei Gesten mit Schwung (Bounce 0,1–0,3), per WAAPI mit linear()-Easing oder weglassen.
- Passung: spielerischer Betrieb = etwas mehr Federn, Kanzlei/Handwerk = knapp und schnell.
- Prüfen in Zeitlupe (2–5× Dauer) und Bild für Bild, am nächsten Tag noch einmal; Touch-Gesten auf echtem Gerät. Review-Tabelle: transition all → genaue Eigenschaften; scale(0) → 0.95+opacity; ease-in → ease-out; Dauer >300 ms → 150–250 ms; Keyframes auf schnell auslösbarem Element → Transition; Hover ohne Media-Query → mit; Animation auf Tastaturaktion → entfernen.

GESTALTUNGSSYSTEME (so regeln es Agenturen: ein Mittel ist erlaubt, wenn es einmal als System entschieden ist)
Die VERBOTEN-Liste sperrt Reflexe, nicht Mittel. Tiefe, Etiketten, Zahlen und Bildformen sind zulässig, wenn sie in DESIGN.md einmal als System mit Tokens festgelegt und überall gleich angewendet werden. Nie verhandelbar bleiben: nichts Erfundenes, keine KI-Personen oder Stockpersonen, kein Lila/Indigo ohne Kunden-CI, kein Glas-Effekt, keine Emojis als Icons, keine Floskeltexte.
- EBENENSYSTEM: höchstens drei Ebenen. Ebene 0 = Fläche, nie Schatten. Ebene 1 = Element, das ein Foto oder eine Abschnittskante sichtbar überlappt (Belegkarte am Hero-Bild): ein Schattenwert --shadow-1. Ebene 2 = Schwebendes (Menü, Dialog): --shadow-2. Schatten zweilagig (nah und weit), aus der Tintenfarbe getönt, nie reines Schwarz. Karten, die im Raster auf einfarbigem Grund liegen, bleiben Ebene 0 und trennen sich über Tonstufe.
- RADIEN: ein Satz aus höchstens drei Werten (klein für Etiketten, mittel für Karten, groß für Bilder), verschachtelt gilt innen = außen minus Abstand. Voll runde Buttons und Kapselbilder zählen nicht mit.
- BILDFORM: genau eine Formsprache je Website (Kapsel ODER ausgesparte Ecke ODER eingestanztes Etikett ODER Rechteck), auf allen Unterseiten dieselbe.
- BELEGE: höchstens drei im ersten Bildschirm, genau so wie geliefert und mit Quelle im Bericht ("seit 1987", "4,8 bei 212 Google-Bewertungen"). Keine gerundeten Schätzwerte, kein Hochzählen. Fehlt der Beleg, entfällt das Element.
- ETIKETT ÜBER DER HEADLINE: nur wenn es etwas sagt, das die Headline nicht sagt (Ort, Leistungsbereich, Öffnungsstatus live), in der Textschrift, ohne Punkt-Deko, auf der ganzen Seite gleich gebaut.
- SCHNITTWECHSEL IN DER HEADLINE: eine ganze Zeile im zweiten Schnitt derselben oder der zweiten Schriftfamilie ist erlaubt, ein einzelnes Wort nicht.
- RUNDES AKTIONSELEMENT: höchstens eines je Seite, immer klickbar und mit echter Aktion oder echtem Angebot.
Prüfung in Schritt 6: mehr als zwei Schattenwerte, mehr als drei Radien oder gemischte Bildformen im CSS = System gebrochen, beheben.

HERO-KOMPOSITIONEN (Anordnungs-Bibliothek für den ersten Bildschirm)
Vom Auftraggeber als Vorbild für professionelle Seiten vorgegeben. Übernommen wird die ANORDNUNG (was steht wo, was ist groß); Farben, Schriften, Texte, Bilder und Zahlen kommen aus DESIGN.md und dem echten Material. In Schritt 3 zwei Kompositionen als ASCII-Skizze gegeneinanderstellen, die wählen, die zur Idee und zum vorhandenen Bildmaterial passt, und in DESIGN.md mit Buchstabe und Grund nennen. Zwei Kundenseiten hintereinander nie mit derselben Komposition.
A Wort hinter dem Motiv: Vollbild-Foto, ein einzelnes riesiges Wort (Ort, Leistung, Material) liegt halb hinter dem Hauptmotiv. Unten links Belege und die Hauptaktion mit einem Satz, unten rechts kleine Bildkarte mit Zähler (z. B. 01/10) für weitere Arbeiten. Braucht ein ruhiges Foto mit klarer Silhouette.
B Text links, Werkstück rechts: links Headline, Stützsatz, Button, darunter ein kleines zweites Bild mit Namen und einer Zeile. Rechts ein großes Foto in der Bildform der Seite. Zwischen beiden das runde Aktionselement, unter dem Bild eine Fortschrittsmarke bei mehreren Bildern. Gut für Produkte, Werkstücke, Arbeitsergebnisse.
C Mitte mit Belegen am Bild: Headline und Stützsatz mittig, darunter ein breites Foto, an dessen Rändern Belegkarten überlappen (Ebene 1): eine Zahl, die Google-Bewertung, die Leistungen als Wortliste. Hauptaktion mittig unter dem Bild. Zählt als die eine erlaubte Zentrierung der Seite.
D Farbfläche mit Person: ganze Fläche in der Hauptfarbe des Betriebs, Headline mittig, darunter eine freigestellte echte Person (Inhaber, Mitarbeiter) am unteren Rand, links und rechts davon je eine helle Belegkarte. Nur mit echtem Personenfoto. Zählt wie C als die eine erlaubte Zentrierung der Seite.
E Dunkles Vollbild, Text links: Foto füllt alles, Headline, Stützsatz und Button links. Rechts eine kleine Vorschaukarte zum nächsten Bild oder zur nächsten Leistung mit Titel und Kurztext. Unterkante als ruhige Leiste: links Beleg, rechts Social-Links.
F Zeile oben, Bild unten: Headline links und Stützsatz rechts in einer Reihe, darunter ein Bild fast über die volle Breite. In zwei Bildecken sind Etiketten eingestanzt (Ecke in Hintergrundfarbe ausgespart): z. B. Name und Rolle der Person, Leistung und Datum der Arbeit.
G Drei Spalten mit Kapselbild: links zweizeilige Headline mit Schnittwechsel in der zweiten Zeile, Button, kurzer Text, kleine Bildreihe. Mitte ein Foto in Hochoval- oder Kapselform mit dem runden Aktionselement am Rand. Rechts eine echte Kundenstimme mit Namen, darunter zwei Belege.
Navigation bei allen: Wortmarke links, Links mittig, eine Aktion rechts.
Am Handy wird jede Komposition einspaltig: Headline, Stützsatz, Button, dann Bild, Belege darunter als ruhige Zeile; die Hauptaktion bleibt im ersten Bildschirm sichtbar.

REFERENZEN (nur Prinzipien, nie Layouts, Texte, Animationen oder Assets kopieren): Emil Kowalski (Micro-Interaktion, Timing, direkte Rückmeldung), Rauno Freiberg (Interaktionsdetails, Navigation), Paco Coursey (reduzierte Typografie, konsistente Komponenten), Bruno Simon (ein memorabler Markenmoment, nur mit kommunikativem Zweck), Jeffrey Zeldman (semantisches HTML, Webstandards, langlebige Architektur).

======================================================================
6. BRANCHENPROFILE (Startpunkt, nie Ersatz für echtes Material)
======================================================================
Je Branche: erste Frage des Besuchers → Hauptaktion → Abschnitte, die nicht fehlen dürfen. Inhalte nur mit echten Angaben des Betriebs füllen; was fehlt, ist "OFFEN:".
- Kfz-Werkstatt / Reifen: "Wann bekomme ich einen Termin und was kostet es?" → Termin wählen (Leistung zuerst). Leistungen mit Preisen, Fahrzeugarten/Marken, HU/AU-Tage, Öffnungszeiten, Anfahrt, Ersatzwagen/Wartebereich falls vorhanden.
- Friseur / Kosmetik: "Was kostet es, wann ist frei, wer macht es?" → Termin buchen mit Leistung und Mitarbeiter aus der API. Vollständige Preisliste, Team mit echten Fotos, Öffnungszeiten.
- SHK / Elektro: "Kommt ihr zu mir und wie schnell?" → Anruf, danach Anfrage. Einsatzgebiet mit Ortsnamen, Notdienst nur wenn real (mit Zeiten), Leistungen, Ablauf in echter Reihenfolge, Arbeitsproben.
- Maler / Tischler / Bau / GaLaBau: "Können die das und wie sieht ihre Arbeit aus?" → Besichtigung oder Angebot anfragen. Arbeitsproben mit Ort und Jahr, Leistungen, Einsatzgebiet, Weg bis zum Angebot.
- Gastronomie / Laden: "Wann ist offen, was gibt es, wo ist das?" → Anrufen, Reservieren oder Route. Karte/Sortiment mit Preisen, Öffnungszeiten, Anfahrt.
Am Handy bleibt bei allen Branchen der Anruf oder die Hauptaktion ständig erreichbar: flache Leiste über die volle Breite am unteren Rand (keine schwebende Pille), verdeckt nie Inhalte oder Formularknöpfe, beachtet env(safe-area-inset-bottom), Ziel mind. 44 px hoch. Keine blockierenden Overlays.

FARB-BIBLIOTHEK (drei Kombinationen je Branche, Grundlage der FARBFRAGE in Abschnitt 1)
Reihenfolge der Werte: Grund, Text, Akzent. Grund trägt die Fläche, Text ist Überschrift und Fließtext, Akzent nur für die Hauptaktion und ein weiteres Element. Alle Kombinationen sind gemessen: Text auf Grund mindestens 4,5:1, Akzent auf Grund mindestens 3:1. Sie gelten als begründete Wahl im Sinne der VERBOTEN-Liste. Knopftext auf dem Akzent ist Weiß oder Fast-Schwarz, je nachdem, was mehr Kontrast hat.
Empfehlung bestimmen: A ist der Standard. Davon abweichen, wenn Logo, Schild, Fahrzeug oder Arbeitskleidung des Betriebs eine andere Kombination tragen, wenn die Fotos des Betriebs auf dem Grund von A schlecht stehen (dunkle Werkstattfotos brauchen einen ruhigen dunklen oder weißen Grund), oder wenn ein Mitbewerber im selben Ort oder die letzte Markentrix-Seite derselben Branche schon so aussieht. Die Begründung nennt immer etwas Konkretes aus dem Material des Betriebs.
Branche nicht in der Liste: die nächstverwandte nehmen oder drei Kombinationen nach denselben Regeln ableiten (eine mit dunklem, eine mit weißem, eine mit farbigem Grund; Kontraste messen; kein cremefarbener Grund, kein Lila).
- Kfz-Werkstatt: A #23272B #D9DCDE #FFC400 | B #FFFFFF #12305A #D9261C | C #0F3B66 #FFFFFF #FF8A1F
- Reifenservice: A #101820 #FFFFFF #E2231A | B #FFFFFF #18191B #1565C0 | C #ECEFF1 #263238 #C2410C
- Elektriker: A #0B1F3A #FFFFFF #FFD60A | B #FFFFFF #14181F #0A66D8 | C #EEF1F4 #102A4C #D4500A
- Heizung und Sanitär: A #E6F1F5 #0E4C5A #E4572E | B #0C2D48 #FFFFFF #FF7A1A | C #FFFFFF #0B4F8A #D63A2A
- Dachdecker: A #2F3A44 #C9D1D6 #E8743B | B #FFFFFF #1F262D #B5432B | C #A63A24 #FFFFFF #FFD27A
- Tischler: A #FFFFFF #4A2F1D #B46A00 | B #1E3A2B #FFFFFF #E0A63A | C #3E2616 #FFFFFF #F28C28
- Maler: A #FFFFFF #1D1D1F #E63B2E | B #1746A2 #FFFFFF #FFD23F | C #F0F2F4 #23272B #0B7F7F
- Garten- und Landschaftsbau: A #12372A #F4F6F2 #F2C230 | B #FFFFFF #3B2A1E #2E7D32 | C #2F6B3A #FFFFFF #FFD54A
- Umzug und Transport: A #F26A1B #14213D #FFFFFF | B #FFFFFF #14213D #D9480F | C #123A6B #FFFFFF #FFC533
- Friseur: A #FFFFFF #1E1614 #B5532D | B #24332E #ECEDEA #C9A24A | C #EBD5D2 #5A1E2B #1F4D3A
- Kosmetikstudio: A #DDE5DC #1F3B2E #C8402F | B #FFFFFF #2B2B2E #B2475A | C #0F3A40 #FFFFFF #FFB38A
- Barbershop: A #10241C #EDEDED #C9A24A | B #FFFFFF #111111 #C8102E | C #14233A #FFFFFF #F0445A
- Tattoostudio: A #FAFAFA #0A0A0A #FF4B1F | B #1E2124 #F5F5F5 #E5B323 | C #7A1F1F #FFFFFF #EADFCB
- Fitnessstudio: A #1B2A41 #E8ECF0 #FF5A1F | B #FFFFFF #121212 #E0201B | C #1338BE #FFFFFF #FFE14D
- Hundesalon: A #44583C #F2F5EF #FFB066 | B #FFFFFF #3A2A20 #0B7F7F | C #D6EAF5 #17324D #C9401F
- Italienisches Restaurant: A #FFFFFF #1E5B3A #C2331D | B #B62A18 #FFFFFF #FFD84D | C #2C3A1E #FFFFFF #F0553A
- Café: A #3A241A #CFE6F5 #FFD25A | B #FFFFFF #2B1D14 #C2253A | C #CFE3C4 #3A241A #B81F52
- Bäckerei: A #FFFFFF #5A3A22 #3F6FD8 | B #4A2C17 #FFFFFF #F2B93B | C #24459A #FFFFFF #FFCB57
- Bar: A #0D1321 #BFC8D6 #FF6B1A | B #4A1020 #FFFFFF #D4A84B | C #0F3326 #FFFFFF #FF5A4D
- Imbiss und Markt: A #D62818 #FFFFFF #FFD400 | B #FFFFFF #161616 #D62818 | C #1E6B3C #FFFFFF #FFD400
- Blumenladen: A #FFFFFF #2E6B3E #D81E6F | B #17382A #FFFFFF #FF8FB1 | C #F6D6DF #1C4332 #B8145A
- Reitverein: A #1F5A36 #FFFFFF #F2C14E | B #FFFFFF #5A3420 #1F7A44 | C #152A45 #FFFFFF #F0504A
- Physiotherapie: A #0F5C63 #FFFFFF #F6B93B | B #FFFFFF #14324F #0B7F85 | C #E3F0F7 #14324F #C94A12
- Zahnarztpraxis: A #0A3D62 #EEF7F5 #2EC4A6 | B #FFFFFF #0A3D62 #0A858F | C #EAF6F3 #12423A #D2452F
- Steuerberater: A #0F3D2E #FFFFFF #C99A2E | B #FFFFFF #0F1E3D #C8372D | C #0F1E3D #FFFFFF #37C2B5
- Anwaltskanzlei: A #5B1A2B #F1F1F1 #C9A24A | B #FFFFFF #0E1726 #8A1C32 | C #0E1726 #FFFFFF #C9A24A
- Immobilien: A #FFFFFF #2A2D31 #0B6B4B | B #12263F #FFFFFF #D0A85C | C #EEF0F2 #12263F #B8402A
- IT-Service: A #FFFFFF #0A1A2F #0077CC | B #0A1A2F #FFFFFF #2CC4F0 | C #EDF1F5 #0A1A2F #C94A12
- Gebäudereinigung: A #123C69 #FFFFFF #7AC74F | B #FFFFFF #123C69 #0A858F | C #E1F0FA #123C69 #1E7D3C
- Fahrschule: A #FFD100 #111111 #0057B8 | B #FFFFFF #111111 #D9261C | C #0B4EA2 #FFFFFF #FFD100

======================================================================
7. LOKALES SEO (Pflicht)
======================================================================
- <title> nach dem Muster "Leistung in Ort | Firma", H1 nennt Leistung und Ort in natürlicher Sprache.
- H1: der Suchbegriff (Leistung, Ort) steht am Anfang, höchstens 70 Zeichen. Eine Unterzeile oder ein Claim gehört NICHT ins H1-Element (eigener Absatz), sonst klebt der Text ohne Leerzeichen zusammen und die H1 wird zu lang; auch vor einem <br> in der H1 ein Leerzeichen setzen. Keine Überschriftenebene überspringen. Zwischenüberschriften tragen ein Themenwort ("Leistungen in Celle"), nicht "Mehr erfahren" oder "Passend dazu".
- Suchbegriffe festlegen (5 bis 10, mit Ort): je Begriff genau eine Zielseite, der Begriff steht dort in Title, H1 und im ersten Absatz; nicht zwei Seiten auf denselben Begriff. Tabelle "Begriff → Seite" in den Bericht. Description 70 bis 160 Zeichen und je Seite eindeutig. Die Startseite steht in Canonical, og:url und Sitemap gleich geschrieben (mit Schrägstrich).
- Name, Adresse, Telefon überall identisch: Seite, Impressum, JSON-LD und Google-Profil. Abweichungen zum Google-Profil als "OFFEN:" melden.
- JSON-LD auf der Startseite: LocalBusiness mit passendem Untertyp (z. B. AutoRepair, HairSalon, Plumber, Electrician, HousePainter, Restaurant) und name, address, telephone, url ({{SITE_URL}}), image, openingHoursSpecification; geo, priceRange und areaServed nur mit echten Angaben. Kein aggregateRating, keine erfundenen Felder.
- Öffnungszeiten stehen als sichtbarer Text auf der Seite und stimmen mit dem JSON-LD überein. Fehlen sie: "OFFEN:", nicht schätzen.
- Einsatzgebiet als echter Text mit Ortsnamen. Keine Serien fast gleicher Ortsseiten.
- URL- und Indexierungs-Matrix im Bericht: je Seite Indexierung ja/nein, Meta-Robots, Canonical ({{SITE_URL}}/pfad), Sitemap-Aufnahme. hreflang nur bei echter Mehrsprachigkeit. Jede Seite in höchstens zwei Klicks erreichbar.

======================================================================
8. PERFORMANCE UND BARRIEREFREIHEIT
======================================================================
Ziele (Felddaten, 75. Perzentil): LCP <= 2,5 s, INP <= 200 ms, CLS <= 0,1. Ohne Felddaten Laborwerte nennen und als solche kennzeichnen.
Feste Grenzen (Richtwerte von Markentrix; Überschreitung im Bericht begründen):
- Höchstens 2 Schriftfamilien mit zusammen 4 Schnitten, woff2, font-display: swap; nur die Display-Schrift des ersten Bildschirms per preload.
- Hero-Bild: nicht lazy, fetchpriority="high", per <link rel="preload" as="image">, Ziel unter 250 KB. Übrige Bilder Ziel unter 150 KB, srcset mit mindestens zwei Breiten, loading="lazy" und decoding="async" unterhalb des ersten Bildschirms.
- JavaScript gesamt unter 50 KB (mit Shop unter 120 KB), ungepackt, mit defer geladen. CSS unter 60 KB.
- Startseite beim ersten Aufruf unter 1 MB Übertragung. Kein Layout-Sprung durch nachladende Schriften, Bilder oder Portal-Bausteine (Platz reservieren).
Barrierefreiheit: Ziel WCAG 2.2 AA. Prüfen: nur Tastatur, sichtbarer Fokus, Formular-Labels, Kontraste, Screenreader-Semantik, Touch-Ziele, reduced motion, Zoom bis 200 %. Ein Lighthouse-Wert allein ist kein Nachweis. Ist Playwright vorhanden, zusätzlich axe-core (WCAG 2.2 AA und Best Practice) auf jeder Seite bei 390 und 1440 px: kein Verstoß.
Links und Bilder: Karten, die als Ganzes klickbar sind, verlinken nur ihre Überschrift (Link auf der H3, die Fläche per ::after über die Karte ziehen); so bleibt der Linktext kurz (höchstens 70 Zeichen) und aussagekräftig. Gleicher Linktext nie mit verschiedenen Zielen ("Mehr erfahren" dreimal): jeder Link nennt sein Ziel. Interne Links mit Parametern (?x=) mit rel="nofollow". Externe Verweise (Hilfeseiten, Gesetze) vor der Abgabe auf Erreichbarkeit prüfen, sie ändern sich. Jedes Bild mit alt, width und height; reine Zierbilder als CSS-Hintergrund statt <img alt="">. Keine role auf Links, die der Link nicht erlaubt (kein role="listitem" auf <a>; Liste und Listenelement außen herum). Jede eigenständige Seite, auch eine eingebettete, hat <main>.

======================================================================
9. PORTAL-SCHNITTSTELLEN (verbindlicher Vertrag, nichts daran ändern)
======================================================================
ZWEI VARIANTEN, WÄHLE GENAU EINE PRO FUNKTION
Variante A, Bausteine (schnell, einheitliches Standarddesign): Platzhalter-Element in die Seite setzen, das Skript fügt Markentrix beim Hochladen automatisch ein (NICHT selbst einbinden, kein data-site eintragen):
<div data-mk="kontakt"></div> Kontaktformular
<div data-mk="termin"></div> Terminbuchung
<div data-mk="bewertungen"></div> Google-Bewertungen
<div data-mk="paypal" data-betrag="49,90" data-titel="Gutschein"></div>
<span data-mk="cookies"></span> Statistik-Einstellung im Footer
Bewertungszahlen im Text (Kopfbereich, Fakten, Siegel, Kontaktseite) NIE nur fest schreiben, sondern live ersetzen lassen; der feste Text bleibt als Rückfall: <span data-mk-bew="anzahl">22</span> · <span data-mk-bew="sterne">5,0</span> · <span data-mk-bew="symbole">★★★★★</span> · <span data-mk-bew="stand">(Stand Oktober 2026)</span>. "stand" wird ausgeblendet, sobald Live-Zahlen da sind. Voraussetzung: Google-Bewertungen beim Kunden aktiv und Place-ID hinterlegt; ohne Place-ID bleibt der feste Text. JSON-LD aggregateRating bleibt weiter verboten (Abschnitt 7).
Lokal bleiben die Baustein-Elemente leer, weil erst der Uploader das Skript einfügt: ihr Aussehen ist vor dem Hochladen "NICHT TESTBAR" und wird nach dem Upload geprüft (im Bericht als offenen Prüfschritt nennen). Liegt ein Baustein-Skript zum lokalen Testen vor, nur neben website-fertig/ verwenden, nie mit ausliefern.
Die Bausteine lassen sich per CSS stylen (Klassen beginnen mit "mk-"). Ist ein Dienst im Portal ausgeschaltet, bleibt das Element leer: Platz dafür großzügig lassen und eine Alternative zeigen (Telefon, E-Mail).

Variante B, eigene Oberfläche über die Website-API (volle Designfreiheit, z. B. Friseur/Werkstatt mit eigenem Buchungsformular). Gleiche Domain, relative Pfade, JSON:
GET /api/verfuegbarkeit -> {blocked:[Datum], closedWeekdays:[0-6, 0=So], nextFree:Datum|null, selfBooking:bool, slotTimes:["08:00",…]}
GET /api/slots?tag=JJJJ-MM-TT -> {tag, slots:[{zeit:"08:00", frei:true|false}]}
GET /api/leistungen -> {leistungen:[{key,name,beschreibung,preis,dauer}]} (nur wenn der Betrieb Leistungen mit Dauer hat)
GET /api/mitarbeiter -> {mitarbeiter:[{key,name,leistungen:[key]}]} (nur wenn mehrere Personen buchbar sind)
Bei Leistungen/Personen: /api/slots und /api/verfuegbarkeit mit ?leistung=<key>&mitarbeiter=<key> (leer = egal) aufrufen und beim Buchen leistung und mitarbeiter mitsenden. Auswahllisten IMMER aus den beiden Endpunkten bauen, nie fest eintragen.
POST /api/anfrage (JSON), Felder:
- typ = "kontakt" | "termin" | "gutschein" | "firma" | "widerruf" | "bestellung"
- name*, telefon, email (im Formular IMMER als Pflichtfeld bauen, auch bei typ="kontakt", wegen der Eingangsbestätigung; die API erzwingt sie nur bei termin/bestellung), nachricht, einwilligung ("ja", Pflicht), weitere Felder frei (leistung, paket, fahrzeug …)
- bei typ="termin": datum* (JJJJ-MM-TT), uhrzeit (aus /api/slots), telefon*, email* (Bestätigung geht dorthin)
- Lockfeld "website": unsichtbares Textfeld (display:none, tabindex=-1, autocomplete=off), muss LEER bleiben
- Erfolg: {ok:true, ref:"…"} -> weiterleiten auf danke.html?typ=<typ>&ref=<ref> und dort die Vorgangsnummer zeigen
- Fehler: HTTP 422 {ok:false, errors:{feldname:"Text"}} -> Text am Feld anzeigen; HTTP 429 -> "Bitte später noch einmal"
POST /api/e {t:"pv"|"ev", u:Pfad, n:Name, w:Breite} per navigator.sendBeacon, ohne Cookies (optional, Besucherzahlen). Aus dem Geschäftsmodell 3–5 Conversions ableiten und als "ev" mit festem Namen senden (z. B. termin_gesendet, anruf_klick), je Ereignis genau einmal. Keine Conversion-Rate ohne echte Daten behaupten.
Regeln für Variante B:
- Uhrzeiten nur anbieten, wenn /api/slots frei:true meldet; gesperrte Tage aus /api/verfuegbarkeit sperren. Wenn selfBooking:false ist, heißt das Formular "Terminwunsch" (Antwort folgt), nicht "Termin buchen".
- Gleichzeitige Buchung derselben Zeit: der Server lässt genau eine gewinnen, die andere bekommt 422 auf "uhrzeit": Slots neu laden und das zeigen.
- Doppelklick verhindern (Button sperren während des Sendens), Eingaben bei Fehlern NICHT löschen.
- Bei Fehlern oder fehlendem Server immer eine Ausweichmöglichkeit zeigen (Telefon, WhatsApp, E-Mail).
- Preise, Pakete und Fahrzeugklassen kennt nur die Website, das Portal speichert sie als Text. Uhrzeiten müssen zu den "Festen Uhrzeiten" im Portal passen.

ONLINE-SHOP, GUTSCHEINVERKAUF, BEZAHLTE ONLINE-BUCHUNG: Der vollständige Vertrag (Katalog, Bestellung, Gutschein, Widerrufsfunktion, Bestellknopf, Barrierefreiheitserklärung, Pflichtangaben) steht im Skill "website-mit-portal-shop". Vor jeder Arbeit an diesen Funktionen laden; ohne ihn keinen Shop bauen.

ZAHLUNG: Keine eigene Zahlungsabwicklung, keine Kartenfelder, kein eigenes PayPal-Skript. Nur das Element data-mk="paypal" (Variante A), der paypalUrl aus der Bestellantwort oder ein PayPal.Me-Link (Anzahlung). Das Geld geht direkt an den Kunden. Gutscheine sind eine Anfrage (typ="gutschein"), den Code vergibt der Inhaber.

E-MAIL: Die Website verschickt nie selbst Mails (kein mailto-Formular, kein Formspree, kein SMTP). Anfragen laufen über das Portal: Der Inhaber bekommt Mail und Push, der Besucher eine Eingangsbestätigung mit Vorgangsnummer. Deshalb ist die E-Mail-Adresse des Besuchers bei Termin-, Kontakt- und Bestellformularen Pflicht.

======================================================================
10. EXTERNE DESIGN-SKILLS (optional, nie Voraussetzung)
======================================================================
Dieser Skill ist ohne sie vollständig. Ihr Kernwissen ist fest eingebaut: Bewegung in Abschnitt 5, Härtetest in 14, Handy-Feinheiten in 15, Design-Kritik in 16, Bewegungs-Review in 17, automatische Messung in 18. Die Abschnitte 14–18 laufen IMMER, mit oder ohne externe Skills. Sind die externen Skills installiert, dienen sie zusätzlich als Nachschlagewerk und zweites Prüfwerkzeug. ZUERST PRÜFEN: ls ~/.claude/skills/ . Was fehlt, wird im Bericht als "NICHT TESTBAR (Skill fehlt)" geführt; nie Skript-Ergebnisse, Seeds oder Wertungen erfinden.

taste-skill (github: Leonxlnx/taste-skill)
Version prüfen: liegt scripts/gate.mjs vor, ist es 2.5.x (Befehle unten). Liegt stattdessen scripts/draw.mjs vor, ist es die alte 2.1.x: aktualisieren oder ohne Skripte arbeiten.
Nur als PRÜFWERKZEUG nutzen, aus dem Arbeitsordner, mit kind = service (Handwerk, Dienstleister) oder place (Laden, Salon, Gastronomie):
  node <skill>/scripts/copy-lint.mjs website-fertig/index.html --kind <kind>
  node <skill>/scripts/consistency.mjs website-fertig/index.html --widths 1440,1024,768,390 --profile .taste-skill/chrome-check --page <kind> --category "<was verkauft wird>" --primary "<Hauptaktion>"
  node <skill>/scripts/shoot.mjs --url website-fertig/index.html --w 1440 --out shots/1440.png --profile .taste-skill/chrome-check   (ebenso 768 und 390)
  node <skill>/scripts/perf.mjs website-fertig/index.html --profile .taste-skill/chrome-check
Jedes FAIL beheben oder begründen. Meldungen, die nur den Aufbau des taste-skill-Baukastens betreffen (dessen Klassen, starter.html), sind hier "nicht anwendbar". Bricht ein Skript ab oder fehlt Chrome: Screenshots von Hand, im Bericht sagen. Ordner .taste-skill/ und shots/ gehören NICHT in website-fertig/.
Zum Nachlesen: references/copy.md, copy-voice.md, copy-tells.md, system.md, photos.md.

impeccable (github: pbakaus/impeccable): nur reference/*.md lesen: craft-floor (vor dem Bauen), critique, typeset, layout, colorize, bolder, quieter, clarify, adapt, harden, polish, optimize.

Emil Kowalski (github: emilkowalski/skill): emil-design-eng, break-ui, mobile-native, apple-design, review-animations, find-animation-opportunities, remove-animations. Konzepte übernehmen, Code als CSS/WAAPI neu schreiben.

DIESER SKILL GEWINNT IMMER. Die externen Skills ändern nie die Portal-Schnittstellen. Aus ihnen gilt NICHT:
- taste-skill Baukasten (assets/starter.html, system.css, layout/deal.mjs, moments.mjs, effects.mjs): nicht als Grundlage nehmen, die Seite entsteht aus DESIGN.md.
- taste-skill start.mjs deal/css: liefert Google-Fonts-Paare. Schriften bleiben lokal (woff2), Auswahl nach DESIGN.md.
- taste-skill photos.mjs search / Ersatzfotos von Unsplash oder Wikimedia als Platzhalter für fehlende Kundenbilder: nicht erlaubt. Offene Sammlungen nur mit passender Lizenz, lokal gespeichert, Credit im Footer, nie als angebliches Bild des Betriebs, nie Fremd-URLs im Code.
- taste-skill "angenommene" Öffnungszeiten und Preise (data-assumed), erfundene Markennamen, Beispieldaten: nicht erlaubt, stattdessen "OFFEN:".
- taste-skill "jede Seite bewegt sich", Einstiegsanimation an jedem Hero, Momente/Effekte/Szenen: es gilt "ein orchestrierter Moment".
- taste-skill gate.mjs --start und seine Hooks: nicht scharf schalten.
- impeccable "live", "generate", "init", Hooks, nachgeladene Binaries, PRODUCT.md/DESIGN.md im Projektordner: nicht benutzen; DESIGN.md liegt neben website-fertig/.
- emil-design-eng "antworte beim ersten Aufruf nur mit einem Satz", Framer Motion, Sonner, npm-/CDN-Bibliotheken, Tailwind-CDN: ignorieren.
- Nicht anwenden: write-swift, animate-expo, ask-sonner, pick-ui-library.

======================================================================
11. MOCK-SERVER ZUM TESTEN (liegt NEBEN website-fertig/, nie im Export)
======================================================================
Als mock.mjs neben website-fertig/ speichern, mit "node mock.mjs" starten, Seite unter http://localhost:8787 testen. Liefert die Seite aus und beantwortet die API nach Vertrag: 10:00 Uhr ist belegt (422 auf uhrzeit), eine gebuchte Zeit ist danach belegt, fehlende Pflichtfelder geben 422, "?fail=429" an einer API-Adresse gibt 429, /api/produkte gibt 404 (Fallback prüfen). Für Shop-Tests die Katalog-Antwort nach dem Skill "website-mit-portal-shop" ergänzen. Mock-Daten gelangen nie in die Seite.

```js
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = path.resolve('website-fertig'), taken = new Set(['10:00']);
const mime = {html:'text/html',css:'text/css',js:'text/javascript',json:'application/json',svg:'image/svg+xml',webp:'image/webp',woff2:'font/woff2',xml:'application/xml',txt:'text/plain'};
const json = (res, code, o) => { res.writeHead(code, {'content-type':'application/json'}); res.end(JSON.stringify(o)); };
http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x'), p = u.pathname;
  if (u.searchParams.get('fail') === '429') return json(res, 429, {ok:false});
  if (p === '/api/verfuegbarkeit') return json(res, 200, {blocked:[], closedWeekdays:[0], nextFree:null, selfBooking:true, slotTimes:['08:00','10:00','14:00']});
  if (p === '/api/slots') return json(res, 200, {tag:u.searchParams.get('tag'), slots:['08:00','10:00','14:00'].map(z => ({zeit:z, frei:!taken.has(z)}))});
  if (p === '/api/leistungen') return json(res, 200, {leistungen:[{key:'a', name:'Testleistung', beschreibung:'', preis:'', dauer:30}]});
  if (p === '/api/mitarbeiter') return json(res, 200, {mitarbeiter:[{key:'m1', name:'Testperson', leistungen:['a']}]});
  if (p === '/api/gutschein/pruefen') return json(res, 200, {ok:true, gueltig:false});
  if (p.startsWith('/api/produkte') || p === '/api/gutschein') return json(res, 404, {ok:false});
  if (p === '/api/e') { res.writeHead(204); return res.end(); }
  if (p === '/api/anfrage' && req.method === 'POST') {
    let b = ''; req.on('data', c => b += c); req.on('end', () => {
      let d = {}; try { d = JSON.parse(b); } catch {}
      const e = {};
      if (!d.name) e.name = 'Bitte Namen angeben.';
      if (d.einwilligung !== 'ja') e.einwilligung = 'Bitte der Datenschutzerklärung zustimmen.';
      if (d.typ === 'termin' && !d.datum) e.datum = 'Bitte einen Tag wählen.';
      if (d.typ === 'termin' && taken.has(d.uhrzeit)) e.uhrzeit = 'Diese Uhrzeit ist gerade vergeben.';
      if (d.website) return json(res, 200, {ok:true, ref:'MOCK-0000'});
      if (Object.keys(e).length) return json(res, 422, {ok:false, errors:e});
      if (d.uhrzeit) taken.add(d.uhrzeit);
      json(res, 200, {ok:true, ref:'MOCK-2026-0001'});
    }); return;
  }
  const f = path.join(ROOT, p === '/' ? 'index.html' : p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404, {'content-type':'text/html'}); return res.end(fs.existsSync(path.join(ROOT,'404.html')) ? fs.readFileSync(path.join(ROOT,'404.html')) : '404'); }
  res.writeHead(200, {'content-type': mime[path.extname(f).slice(1)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(res);
}).listen(8787, () => console.log('Mock: http://localhost:8787'));
```

======================================================================
12. PRÜFLISTE VOR DER ABGABE (ausführen, Ergebnis melden)
======================================================================
Jeder Punkt bekommt genau einen Status: PASS, FAIL, NICHT TESTBAR oder BEWUSST AUSGENOMMEN (mit Grund). Nie Ungetestetes als PASS melden. Messwerte dazuschreiben.
1. Export: index.html direkt in website-fertig/, nur erlaubte Dateitypen, keine versteckten Dateien, kein DESIGN.md, AENDERUNGEN.md, WEITERLEITUNGEN.md, mock.mjs, pruefe.mjs, formtest.mjs, rechtstexte/, node_modules/, .taste-skill/ oder shots/ im Ordner, ZIP unter 120 MB.
2. Fremdabrufe: grep -rniE "localhost|127\.0\.0\.1|lorem ipsum|fonts\.(googleapis|gstatic)|jsdelivr|cdnjs|unpkg|\.php" und grep -rn "http://" in website-fertig/: darf nichts finden. Zulässig bei "http://": XML-/SVG-Namensräume (www.w3.org, www.sitemaps.org). Jede https://-Adresse einzeln prüfen: erlaubt sind nur Links zum Anklicken (z. B. PayPal.Me, Social Media), schema.org in JSON-LD und {{SITE_URL}}; nichts, was beim Laden fremde Server abruft.
3. Links und Dateien: alle internen Links, Bilder und Schriften existieren; Pflichtseiten vorhanden; 404.html und danke.html mit noindex und nicht in der Sitemap; {{SITE_URL}} nur in sitemap.xml, robots.txt, Canonical, og:url, JSON-LD.
4. Jede Seite: lang="de", Title unter 60 Zeichen, Description (70 bis 160), Viewport, genau eine H1 (Suchbegriff vorn, höchstens 70 Zeichen, Unterzeile nicht im H1), alt-Texte, Footer-Pflichtlinks, tel:/mailto: auf der Startseite.
5. Breiten 1440, 768, 390 und 320 px: kein seitliches Scrollen, Headlines höchstens zwei Zeilen, Handy-Aktionsleiste verdeckt nichts. Screenshots gemacht (z. B. Playwright/headless Chrome) UND angesehen.
6. Formulare gegen den Mock-Server (Abschnitt 11): Erfolg mit Weiterleitung auf danke.html und Vorgangsnummer, 422 am richtigen Feld mit erhaltenen Eingaben, 429-Meldung, Doppelklick-Sperre, Lockfeld, Einwilligung, E-Mail als Pflichtfeld. Bei Terminen: belegte Zeit nicht wählbar, 422 auf uhrzeit lädt Slots neu, selfBooking:false heißt "Terminwunsch".
7. API nicht erreichbar (Mock aus): Seite zeigt Ausweichmöglichkeit (Telefon, E-Mail), nichts sieht kaputt aus. Leere Variante-A-Bausteine haben eine Alternative.
8. Shop (falls vorhanden, Vertrag im Skill "website-mit-portal-shop"): Katalog aus /api/produkte, Fallback bei 404, Warenkorb rechnet Versand/Abholung/Gutschein korrekt, Wunschtext-Pflicht, AGB-Checkbox, Knopf "Zahlungspflichtig bestellen", 422 summe wird abgefangen, danke.html zeigt ref und paypalUrl, Link "Vertrag widerrufen" auf jeder Seite, widerruf.html zweistufig, barrierefreiheit.html verlinkt.
9. Barrierefreiheit: nur mit Tastatur bedienbar, sichtbarer Fokus, Labels, Kontrast mind. 4,5:1, Touch-Ziele, reduced motion, Zoom 200 %, Lighthouse-Barrierefreiheit über 90 (nur Indikator).
10. Performance: Grenzen aus Abschnitt 8 gemessen (Dateigrößen, Schriftschnitte, Hero-Preload, lazy), LCP/CLS als Laborwert.
11. Lokales SEO: Punkte aus Abschnitt 7, JSON-LD syntaktisch gültig, Angaben identisch zu Impressum, Indexierungs-Matrix erstellt.
12. Bewegung: genau ein orchestrierter Moment, Review-Tabelle aus Abschnitt 5 durchgegangen, in Zeitlupe angesehen.
13. KI-Look, grep: ohne Groß-/Kleinschreibung, als ganze Wörter (grep -wi); Schriftnamen nur in font-family, @font-face und Dateinamen werten, damit "Winter" oder "hinter" keinen Fehlalarm geben. Suchen in html/css/js nach: "Inter", "Geist", "Space Grotesk", "Instrument Serif", "indigo", "violet", "purple", "#6366f1", "#8b5cf6", "#7c3aed", "#a855f7", "#f4f1ea", "#d97757", "#10b981", "bg-clip-text", "background-clip: text", "backdrop-filter", "backdrop-blur", "rounded-2xl", "fade-up", "fadeInUp", "animate-bounce", "transition: all", "—", "✨", "🚀", "Mehr erfahren", "Jetzt starten", "Ihr Partner", "nächste Level", "maßgeschneidert", "innovativ", "nahtlos". Jeder Treffer ist in DESIGN.md begründet oder wird entfernt.
14. KI-Look, Blick: Screenshots gegen die VERBOTEN-Liste halten; bei 3 oder mehr Treffern überarbeiten. Austauschtest (Schritt 3) an der fertigen Seite wiederholen: passt sie mit anderem Namen und Logo genauso gut, Kernidee und Signatur stärken.
15. Einheitlichkeit: alle Unterseiten mit denselben Tokens, Schriften, Navigation und Footer; keine losen Hex-Werte. Gestaltungssysteme (Abschnitt 5) eingehalten: per grep nach box-shadow und border-radius im CSS höchstens zwei Schattenwerte und drei Radien, dazu eine Bildform und höchstens ein rundes Aktionselement je Seite.
16. Externe Skills (Abschnitt 10): was lief, was fehlte, offene FAILs.
17. Härtetest (Abschnitt 14): Tabelle der Brüche mit Schwere und Fix; alles "Kaputt" behoben.
18. Handy-Feinheiten (Abschnitt 15): Grundausstattung eingebaut, "Nie ausliefern"-Liste sauber; was nur am echten Gerät prüfbar ist, benannt.
19. Design-Kritik (Abschnitt 16): Spezifitäts-Urteil, Wertung von 40, kognitive Last, beide Personas; alle P0/P1 behoben.
20. Bewegungs-Review (Abschnitt 17): Tabelle Vorher/Nachher/Warum, gestrichene und behaltene Animationen.
21. Prüfskript (Abschnitt 18): gelaufen auf jeder Seite, Zahl der Funde, jeder verbliebene Fund begründet.
22. Formulartest (Abschnitt 21): auf jeder Seite mit Formular gelaufen, alle acht Punkte PASS oder begründet.
23. Relaunch (nur bei Relaunch, Abschnitt 19): jede alte Adresse zugeordnet, WEITERLEITUNGEN.md vollständig, fremde Pflichtlinks erhalten.
24. Kundenübergabe (Abschnitt 22): Mail-Entwurf erstellt, nichts versendet.
25. Qualitäts-Gate (Abschnitt 18, Skript qa-statisch.py): auf website-fertig/ gelaufen, 0 FEHLER; jeden HINWEIS gesichtet und behoben oder begründet.

======================================================================
13. BERICHT (in dieser Reihenfolge, knapp)
======================================================================
A. Auftrag, Hauptziel, Haupt-Conversion, verwendeter Stack/Export.
B. Liste der Seiten und Dateien mit Indexierungs-Matrix; Dateien, in denen {{SITE_URL}} steht.
C. Genutzte Portal-Funktionen je Funktion (Baustein oder API) und gesendete Ereignisse.
D. Design-Richtung: Kernidee, Ideensatz, Farben, Schriften, Signatur, Live-Element, Hero-Komposition, Gestaltungssysteme, verworfene Richtungen, Ausnahmen von der VERBOTEN-Liste.
E. Prüfliste 1–25 mit Status und Messwerten; subjektive Gestaltungsqualität und gemessene Werte getrennt bewerten.
F. Verwendete fremde Bilder mit Titel, Urheber, Lizenz und Quelle; erzeugte Bilder mit Freigabe.
G. Ehrliche Einschätzung: was Agentur-Niveau erreicht und was noch fehlt (oft Fotos und Texte vom Kunden). Keine pauschale Perfektion behaupten, nichts melden, was nicht geprüft wurde.
H. Nächste 3 Maßnahmen nach erwarteter Geschäftswirkung.
I. "OFFEN:" als Liste: fehlende Angaben, Material, Rechtstexte, Freigaben, Funktionen, die das Portal noch nicht bietet; dazu Nachweise, die nur der Kunde hat (Verträge zur Auftragsverarbeitung, Bildlizenzen, Zustimmungen von Personen und Referenzkunden, tatsächliche Löschfristen, Konto-Einstellungen von Statistikdiensten) und die Zielgruppen-Entscheidung B2B oder B2C.

======================================================================
14. HÄRTETEST: DIE SEITE MIT ECHTEN SCHLIMMSTFÄLLEN BRECHEN
======================================================================
Demo-Daten sind unbewusst so gewählt, dass alles gut aussieht. Hier wird das rückgängig gemacht. Gilt für alles, was Daten anzeigt: Leistungen, Mitarbeiter, Slots, Produkte, Bewertungen, Preise, Formulareingaben, danke.html.
Regeln:
- Nur plausible Werte, kein Unsinn ("aaaaaaa"). Jeder Wert könnte von einem echten Kunden oder aus dem Portal kommen.
- Die Daten ändern, nicht die Seite: Schlimmstfälle über mock.mjs (Abschnitt 11) einspielen, nie Markup oder CSS von Hand verbiegen. Danach die Mock-Daten zurücksetzen.
- Erst alle Brüche auflisten, dann beheben. Nach dem Beheben auch die Normaldaten erneut prüfen.
Schlimmstfall-Werte (verteilt über die ersten Zeilen, nicht alle in eine):
- Namen: "Dr. Maximiliane von Hohenlohe-Schillingsfürst", "Jo", "Özgür Şimşek", Name mit Emoji, Name mit Leerzeichen vorn und hinten, fehlender Name.
- Texte: langes Wort ohne Trennstelle ("Kraftfahrzeughaftpflichtversicherung"), Leistungsname über 60 Zeichen, leere Beschreibung, Bewertung mit 900 Zeichen, Bewertung mit einem Wort.
- E-Mail/Links: "maximiliane.hohenlohe-schillingsfuerst@autohaus-musterstadt-gmbh.example", "a@b.de".
- Zahlen: Preis leer, 0, "ab 1.249,00 €", Dauer 5 und 480 Minuten, Menge 99, Summe über 10.000 €.
- Mengen: 0 Einträge (Leerzustand), genau 1 ("1 Termine" ist ein Fehler), 60+ Einträge, alle Slots belegt, kein freier Tag.
- Bilder: fehlendes Bild, sehr hohes und sehr breites Seitenverhältnis.
- Ablauf: langsames Netz, Abbruch mitten im Senden, Doppelklick, Zurück-Knopf nach dem Absenden, Seite ohne JavaScript (Telefon und E-Mail müssen sichtbar bleiben).
Prüfen bei 320 px, der echten Breite und 200 % Zoom.
Fehlerbild → Ursache → Fix:
- Bild oder Icon zur Ellipse gequetscht → Flex-Kind schrumpft → flex-shrink: 0.
- Text läuft aus der Box → min-width: auto im Flex/Grid → min-width: 0 auf der Textspalte (im Grid minmax(0, 1fr)).
- E-Mail oder Link ragt über den Rand → keine Umbruchstelle → overflow-wrap: anywhere.
- Knopf am Zeilenende weggedrückt → Mitte nimmt allen Platz → min-width: 0 auf der Mitte, flex-shrink: 0 auf dem Knopf.
- Badge bricht zweizeilig um → white-space: nowrap; flex-shrink: 0.
- Bild hängt neben dreizeiligem Text in der Luft → align-items: flex-start, sobald Text umbrechen kann.
- Wort mitten zerhackt → word-break: break-all → overflow-wrap: anywhere, für deutsche Komposita hyphens: auto mit lang="de".
- Leere Zeile oder verwaister Strich bei fehlendem Wert → Zeile weglassen.
- "1 Termine", "0 Artikel" → Intl.PluralRules oder eigene Texte für 0, 1, viele.
- Zahlen springen oder stehen schief → font-variant-numeric: tabular-nums.
- "1249", "NaN", "undefined" → Intl.NumberFormat('de-DE', {style:'currency', currency:'EUR'}), null abfangen.
- Knopftext läuft über → feste Breite → Breite aus dem Inhalt mit min-width.
- Kaputtes Bild-Symbol → onerror-Ausweichbild oder Farbfläche, object-fit: cover.
- Abgeschnittener Text ohne Ausweg → title-Attribut oder volle Fassung an anderer Stelle.
- Rohes "<b>" oder "&amp;" im Text → Daten nur per textContent einsetzen.
Umbrechen, Kürzen oder Klemmen, je Feld entscheiden: Namen und Leistungen umbrechen (zwei Zeilen sind in Ordnung); Nebenangaben am Ende kürzen; Dateinamen und E-Mails in der Mitte kürzen; Vorschautexte in Karten auf zwei Zeilen klemmen (line-clamp); Preise, Daten und Uhrzeiten NIE kürzen.
Weiter härten: Ladezustände sagen, was lädt; Leerzustände nennen den nächsten Schritt; jeder Netzfehler hat einen "Noch einmal"-Knopf und die Telefonnummer; Zeitüberschreitung nach spätestens 10 Sekunden behandeln.
Ergebnis als Tabelle: Schwere (Kaputt = unlesbar, Aktion unerreichbar, falsche Daten; Unschön = lesbar, aber sichtbar falsch; Wackelig = ein realistischer Schritt vom Bruch), Feld, Wert, was passiert, Fix. Dazu: was gehalten hat.

======================================================================
15. HANDY: WIE EINE APP, NICHT WIE EINE WEBSITE
======================================================================
Symptom → Fix:
- Hover bleibt nach dem Tippen kleben → Hover nur in @media (hover: hover) and (pointer: fine); Druck-Rückmeldung über :active.
- Grauer/blauer Blitz beim Tippen → -webkit-tap-highlight-color: transparent, dafür eigener :active-Zustand an jedem Tippziel.
- Höhe stimmt nicht, Knopf unter der Adressleiste → nie 100vh; Hero 100svh, App-artige Flächen 100dvh.
- Seite zoomt ins Eingabefeld → Eingabefelder mindestens 16 px Schrift. Zoom nie sperren.
- Tippen wirkt träge → touch-action: manipulation, Rückmeldung beim Drücken (:active, pointerdown), nicht erst beim Loslassen.
- Liste zieht die ganze Seite mit → overscroll-behavior: contain auf inneren Scrollbereichen (Slot-Liste, Warenkorb, Menü).
- Langes Drücken markiert den Knopftext → user-select: none nur auf Bedienelementen, nie auf Inhalt (Adresse, Vorgangsnummer bleiben kopierbar).
- Bildleiste ruckelt beim Wischen → scroll-snap-type: x mandatory statt eigenem Wisch-Skript, sonst touch-action: pan-y.
- Statusleiste in falscher Farbe → <meta name="theme-color"> passend zur obersten Fläche, je Farbschema einer.
- Falsche Tastatur → type="tel", type="email", inputmode="numeric" für PLZ, autocomplete (name, email, tel, street-address, postal-code), enterkeyhint="send" am letzten Feld.
Grundausstattung, vor der ersten Komponente einbauen:

```css
html { -webkit-text-size-adjust: 100%; }
a, button, [role="button"], label, summary { -webkit-tap-highlight-color: transparent; touch-action: manipulation; }
button, [role="button"] { -webkit-user-select: none; user-select: none; }
input, select, textarea { font-size: max(16px, 1rem); }
.aktionsleiste { padding-bottom: env(safe-area-inset-bottom); }
@media (hover: hover) and (pointer: fine) { /* alle Hover-Stile hier */ }
```

Der Viewport-Tag bleibt exakt wie in den HARTEN REGELN. Nie ausliefern: user-scalable=no oder maximum-scale=1; Hover ohne Media-Query; 100vh; Rückmeldung nur auf click; touchmove mit preventDefault gegen Überscrollen; user-select: none auf body; Geräteerkennung über User-Agent.
Ehrlich bleiben: klebender Hover, Tipp-Blitz, Adressleiste, Eingabe-Zoom, Tastatur und Sicherheitsränder zeigen sich nur am echten Gerät, nicht in der Geräte-Simulation. Im Bericht trennen: aus dem Code geprüft / braucht ein echtes Handy.

======================================================================
16. DESIGN-KRITIK MIT WERTUNG
======================================================================
A. Spezifitäts-Urteil zuerst: Wirkt die Seite für diesen Betrieb gemacht oder passt sie auf jeden der Branche? Ein Satz Begründung, dazu was gut funktioniert.
B. Zehn Heuristiken, je 0–4 Punkte (0 = fehlt, 4 = vorbildlich), Summe von 40. Punkte 7 und 10 dürfen auf einer Werbeseite "entfällt" sein (dann anteilig rechnen):
1. Zustand sichtbar (Laden, gesendet, gewählter Tag, aktiver Menüpunkt)
2. Sprache der Kundschaft statt Fachjargon
3. Kontrolle und Rückweg (zurück, ändern, abbrechen)
4. Einheitlichkeit (gleiches sieht gleich aus und verhält sich gleich)
5. Fehler vermeiden (gesperrte Tage, klare Pflichtfelder, passende Tastatur)
6. Erkennen statt Erinnern (Auswahl bleibt sichtbar, nichts merken müssen)
7. Abkürzungen für Geübte
8. Reduzierte Gestaltung (nichts lenkt von der Hauptaktion ab)
9. Hilfe bei Fehlern (was ist passiert, was jetzt tun)
10. Hilfe und Erklärung, wo nötig
Richtwert von Markentrix: ab 32 gut, 24–31 nacharbeiten, unter 24 grundlegend überarbeiten.
C. Kognitive Last, acht Fragen (jedes Nein ist ein Fehler; 0–1 gut, 2–3 beheben, ab 4 kritisch):
- Ist je Bildschirm genau eine Hauptaktion erkennbar?
- Höchstens vier Wahlmöglichkeiten je Entscheidung, sonst gruppiert?
- Muss niemand etwas aus Schritt 1 für Schritt 3 im Kopf behalten?
- Ist immer sichtbar, wo man ist?
- Kommt die Seite ohne Fachwörter aus oder erklärt sie sie sofort?
- Gibt es eine klare Rangfolge (ein Hauptelement, zwei bis drei Nebenelemente, Rest zurückgenommen)?
- Funktionieren gleiche Aktionen überall gleich?
- Steht alles, was man für eine Entscheidung braucht, an einer Stelle (Preis, Dauer, Zeit, Ort)?
D. Zwei Personas gehen den Weg bis zur Haupt-Conversion; notieren, wo sie abbrechen würden:
- Eilig am Handy: eine Hand, draußen, 30 Sekunden Zeit, will Termin oder Anruf.
- Selten online: unsicher mit Formularen, liest alles, fürchtet Fehler und versteckte Kosten.
E. Qualitätsboden, am gebauten Ergebnis prüfen:
- Abstände: eng innerhalb einer Gruppe, großzügig zwischen Gruppen, über einer Überschrift mehr Platz als darunter.
- Kontrast: Fließtext und Platzhalter mind. 4,5:1, großer Text mind. 3:1; auf farbigen Flächen Nebentext aus dem Farbton ableiten, nicht Grau.
- Echte Texte bei jeder Breite durchlaufen lassen und beheben, was überläuft; Überschriften ausbalanciert (text-wrap: balance).
- Browser-Flächen gehören zum Design: ::selection, caret-color, Fokusring, Scrollleiste, text-underline-offset aus der Palette setzen.
- Icons aus einem Satz mit einheitlicher Strichstärke, nie Unicode-Zeichen oder Emojis.
- Kein Dialogfenster für etwas, das weder Unterbrechung noch geschützten Fokus braucht.
- Hell oder dunkel nach der Nutzungssituation wählen (wer, wo, bei welchem Licht), nicht nach Branche.
F. UX-Texte: Knöpfe als Verb plus Gegenstand; Fehler nennen Problem und Ausweg; ein Begriff je Sache auf der ganzen Seite (nicht abwechselnd "Termin", "Buchung", "Reservierung"); Hilfetext steht dort, wo die Frage entsteht.
G. Ergebnis: Liste der Probleme mit Rang P0 (blockiert die Conversion) bis P3 (Feinschliff), je mit Fix. P0 und P1 werden behoben, bevor abgegeben wird.

======================================================================
17. BEWEGUNGS-REVIEW: PRÜFEN, STREICHEN, GEZIELT ERGÄNZEN
======================================================================
Ergänzt die Regeln aus Abschnitt 5.
Zehn Standards, jede Animation gegen alle prüfen: begründet; zur Häufigkeit passend; ease-out oder eigene Kurve beim Erscheinen; unter 300 ms; richtiger Ursprung und nie aus scale(0); unterbrechbar; nur transform und opacity; reduced motion und Hover-Gate; bewusste Aktion langsamer als die Antwort des Systems (ungleiche Zeiten für Hin und Zurück); passt zur Art des Betriebs.
Reihenfolge der Abhilfe: 1. streichen, 2. verkleinern, 3. Easing korrigieren, 4. Ursprung korrigieren, 5. unterbrechbar machen, 6. auf transform/opacity umstellen, 7. Zeiten ungleich machen, 8. Feinschliff, 9. Zugänglichkeit.
Verkleinern statt streichen:
- Hover mit Skalieren, Anheben oder Schatten → nur Farbe/Deckkraft, höchstens 150 ms.
- Hereingleiten auf häufig gesehener Fläche → nur Deckkraft, 150 ms, ease-out.
- UI-Animation über 300 ms → 200–250 ms.
- Staffel über 80 ms je Element oder über 300 ms gesamt → 30 ms je Element oder Gruppe als Ganzes einblenden.
- Endlosschleife (Pulsieren, Schimmern) auf Dauerelement → einmal abspielen oder Endzustand stehen lassen.
Vor dem Streichen prüfen: Bleibt das Element sonst unsichtbar (Startwert opacity: 0)? Hängt ein Ausblenden zeitlich daran? Danach verwaiste Keyframes, Klassen und Variablen entfernen und per grep bestätigen.
Neue Bewegung nur, wenn alle vier Fragen bestehen: selten genug gesehen, klarer Zweck, innerhalb des Zeitbudgets, hilft statt zu stören. Höchstens fünf Stellen je Seite. Lohnende Stellen: Rückmeldung beim Drücken, Bestätigung nach dem Absenden, Öffnen von Menü und Dialog, Wechsel zwischen Schritten der Buchung, neu geladene Slots.
Gesten (Schieber, Schublade, Vorher/Nachher): Element folgt dem Finger 1:1 ohne Verzögerung; jederzeit unterbrechbar und umkehrbar; beim Loslassen die Geschwindigkeit des Fingers übernehmen; am Rand weich nachgeben statt hart stoppen; gleicher Weg hinein wie hinaus; bei pointercancel und Fensterwechsel den Zieh-Zustand sauber beenden.
Ausgabe: Tabelle Vorher / Nachher / Warum, dazu Listen "gestrichen" und "behalten, weil".

======================================================================
18. PRÜFSKRIPT: AUTOMATISCHE MESSUNG OHNE FREMDE SKILLS
======================================================================
Als pruefe.mjs NEBEN website-fertig/ speichern. Erst "node mock.mjs" starten, dann "node pruefe.mjs" (Startseite) und "node pruefe.mjs /leistungen.html" für jede weitere Seite. Braucht Playwright im Arbeitsordner (npm i -D playwright && npx playwright install chromium; ein vorhandenes Chrome über die Umgebungsvariable CHROME angeben). Fehlt beides und lässt es sich nicht installieren: Punkte von Hand prüfen und im Bericht "NICHT TESTBAR" schreiben.
Misst bei 1440, 768, 390 und 320 px: seitlichen Überlauf mit den verursachenden Elementen, Zahl der H1, Überschriften mit mehr als zwei Zeilen, Tippziele unter 44 px, Eingabefelder unter 16 px und ohne Label, Bilder ohne alt oder width/height, mehr als zwei Schriftfamilien, Kontrast unter 4,5:1 (großer Text 3:1), Abrufe fremder Server, fehlende Dateien, Konsolenfehler, transition: all, 100vh, gesperrten Zoom. Legt von jeder Breite einen Screenshot der ganzen Seite in shots/ ab.
Jeden Fund beheben oder begründen. Der Kontrast auf Fotos und Verläufen wird nicht gemessen und muss am Screenshot geprüft werden. Das Skript ersetzt das Ansehen der Screenshots nicht.

```js
import { chromium } from 'playwright'; import fs from 'node:fs';
const BASE = process.env.BASE || 'http://localhost:8787', PFAD = process.argv[2] || '/', BREITEN = [1440, 768, 390, 320], funde = [];
const F = (b, typ, text) => funde.push(`${b}px  ${typ}: ${text}`);
fs.mkdirSync('shots', { recursive: true });
const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
for (const b of BREITEN) {
  const page = await browser.newPage({ viewport: { width: b, height: b > 600 ? 900 : 800 } });
  page.on('console', m => m.type() === 'error' && F(b, 'KONSOLE', m.text().slice(0, 90)));
  page.on('request', r => { const u = r.url(); if (!u.startsWith(BASE) && !u.startsWith('data:')) F(b, 'FREMDABRUF', u.slice(0, 90)); });
  page.on('response', r => r.status() >= 400 && !r.url().includes('/api/') && F(b, 'FEHLT', `${r.status()} ${r.url().replace(BASE, '')}`));
  await page.goto(BASE + PFAD, { waitUntil: 'networkidle' });
  (await page.evaluate(() => {
    const out = [], kurz = e => (e.tagName.toLowerCase() + (e.className ? '.' + String(e.className).split(' ')[0] : '') + ' "' + (e.textContent || e.name || '').trim().slice(0, 28) + '"');
    const sichtbar = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
    const lum = c => { const [r, g, bl] = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * bl; };
    const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
    const grund = e => { for (; e; e = e.parentElement) { const s = getComputedStyle(e); if (s.backgroundImage !== 'none') return null; const c = rgb(s.backgroundColor); if (c.length === 3 || c[3] > .5) return c; } return [255, 255, 255]; };
    if (document.documentElement.scrollWidth > innerWidth + 1) out.push(['UEBERLAUF', `Seite ist ${document.documentElement.scrollWidth}px breit`]);
    [...document.querySelectorAll('body *')].filter(e => sichtbar(e) && e.getBoundingClientRect().right > innerWidth + 1).slice(0, 3).forEach(e => out.push(['UEBERLAUF', kurz(e)]));
    const h1 = document.querySelectorAll('h1').length; if (h1 !== 1) out.push(['H1', `${h1} statt 1`]);
    document.querySelectorAll('h1,h2,h3').forEach(h => { const z = Math.round(h.getBoundingClientRect().height / parseFloat(getComputedStyle(h).lineHeight)); if (z > 2) out.push(['HEADLINE', `${z} Zeilen: ${kurz(h)}`]); });
    if (innerWidth < 600) document.querySelectorAll('a,button,input,select,textarea,[role=button]').forEach(e => { if (!sichtbar(e) || e.type === 'hidden') return; const r = e.getBoundingClientRect(); if (r.height < 44 && !(e.tagName === 'A' && e.closest('p,li'))) out.push(['TIPPZIEL', `${Math.round(r.height)}px hoch: ${kurz(e)}`]); });
    document.querySelectorAll('input,select,textarea').forEach(e => { if (sichtbar(e) && parseFloat(getComputedStyle(e).fontSize) < 16) out.push(['EINGABE', `Schrift unter 16px (iOS zoomt): ${kurz(e)}`]); if (sichtbar(e) && !e.labels?.length && !e.getAttribute('aria-label')) out.push(['LABEL', `fehlt: ${kurz(e)}`]); });
    document.querySelectorAll('img').forEach(i => { if (!i.hasAttribute('alt')) out.push(['ALT', i.getAttribute('src')]); if (!i.getAttribute('width') || !i.getAttribute('height')) out.push(['BILDMASS', `width/height fehlt: ${i.getAttribute('src')}`]); });
    const fam = new Set(); document.querySelectorAll('body *').forEach(e => { if (sichtbar(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) { fam.add(getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g, '').trim());
      const s = getComputedStyle(e), bg = grund(e), fg = rgb(s.color); if (bg && fg.length >= 3) { const a = lum(fg), c = lum(bg), k = (Math.max(a, c) + .05) / (Math.min(a, c) + .05), gross = parseFloat(s.fontSize) >= 24; if (k < (gross ? 3 : 4.5)) out.push(['KONTRAST', `${k.toFixed(1)}:1 ${kurz(e)}`]); } } });
    if (fam.size > 2) out.push(['SCHRIFTEN', `${fam.size} Familien: ${[...fam].join(', ')}`]);
    const css = [...document.styleSheets].flatMap(s => { try { return [...s.cssRules].map(r => r.cssText); } catch { return []; } }).join('\n');
    const tAll = [...document.querySelectorAll('body *')].find(e => { const s = getComputedStyle(e); return s.transitionProperty === 'all' && parseFloat(s.transitionDuration) > 0; }); if (tAll) out.push(['CSS', `transition: all an ${kurz(tAll)}`]);
    if (/100vh/.test(css)) out.push(['CSS', '100vh (besser 100svh/100dvh)']);
    if (/user-scalable\s*=\s*no|maximum-scale\s*=\s*1/.test(document.querySelector('meta[name=viewport]')?.content || '')) out.push(['ZOOM', 'Zoom gesperrt']);
    return out;
  })).forEach(([t, x]) => F(b, t, x));
  await page.screenshot({ path: `shots/${PFAD.replace(/\W+/g, '_').replace(/^_+|_+$/g, '') || 'start'}_${b}.png`, fullPage: true });
  await page.close();
}
await browser.close();
console.log(funde.length ? [...new Set(funde)].join('\n') : 'Keine Funde.'); console.log(`\n${new Set(funde).size} Funde. Screenshots in shots/ ansehen.`);
process.exit(funde.length ? 1 : 0);
```

ZWEITES SKRIPT, PFLICHT: qa-statisch.py (Python 3, ohne Zusatzpakete, ohne Netz) NEBEN website-fertig/ speichern und mit "python3 qa-statisch.py website-fertig" ausführen. Es prüft je Seite: lang, Title (höchstens 60), Description, Viewport, genau eine H1 (ohne zusammengeklebte Sätze, höchstens 90 Zeichen, Hinweis ab 70), übersprungene Überschriftenebenen, Pflichtlinks Impressum und Datenschutz, Bilder (alt, width, height), tote Links und Anker, Links mit Parametern ohne nofollow, target=_blank ohne noopener, Formulare ohne Pflicht-Einwilligung oder Datenschutz-Link, verbotene Zusagen und Platzhalter, ungültiges JSON-LD, aggregateRating, fehlende Pflichtdateien, noindex-Seiten in der Sitemap. Jeder FEHLER wird behoben, jeder HINWEIS gesichtet. Es ersetzt weder das Ansehen der Screenshots noch das Prüfskript oben (Layout, Kontrast, Tippziele); es fängt die Fehler, die dort nicht gemessen werden.

```python
#!/usr/bin/env python3
"""qa-statisch.py: Qualitäts-Gate für eine statische Kundenwebsite. Aufruf: python3 qa-statisch.py website-fertig
Prüft ohne Netz und ohne Browser: Pflichtangaben je Seite, Überschriften, Links, Bilder, Formulare, Wortwahl, Sitemap, JSON-LD.
Exit-Code 1 bei FEHLER. HINWEIS = ansehen, kein Abbruch."""
import os, re, sys, json, glob, html, collections

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'website-fertig'
errors, notes = [], []
def err(m): errors.append(m)
def note(m): notes.append(m)
def txt(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()

files = sorted(glob.glob(ROOT + '/**/*.html', recursive=True))
if not files: sys.exit('Keine HTML-Dateien in ' + ROOT)
pages = {os.path.relpath(f, ROOT).replace(os.sep, '/'): open(f, encoding='utf-8').read() for f in files}
def exists(p):
    p = p.split('#')[0].split('?')[0]
    if p.startswith('/'): p = p[1:]
    return p == '' or os.path.exists(os.path.join(ROOT, p)) or os.path.exists(os.path.join(ROOT, p, 'index.html')) or os.path.exists(os.path.join(ROOT, p + '.html'))

BAD = ['rechtssicher', 'abmahnsicher', '24/7', 'rund um die Uhr', 'Haftung für Links', 'jederzeit an eine', 'nahtlos', 'ganzheitlich',
       'maßgeschneidert', 'innovativ', 'Ihr Partner für', 'auf das nächste Level', 'Lorem ipsum', 'Platzhalter', 'localhost']
NOINDEX_OK = ('404.html', 'danke.html')
for rel, t in pages.items():
    low = rel in NOINDEX_OK
    main = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<!--.*?-->', '', t, flags=re.S)
    if not re.search(r'<html[^>]*\blang="de"', t): err(f'{rel}: <html lang="de"> fehlt')
    ti = re.search(r'<title>(.*?)</title>', t, re.S)
    if not ti: err(f'{rel}: kein <title>')
    elif len(txt(ti.group(1))) > 60: err(f'{rel}: Title {len(txt(ti.group(1)))} Zeichen (über 60)')
    d = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', t)
    if not low:
        if not d: err(f'{rel}: keine Description')
        elif not 70 <= len(d.group(1)) <= 160: note(f'{rel}: Description {len(d.group(1))} Zeichen (70 bis 160)')
    if 'name="viewport"' not in t: err(f'{rel}: kein viewport')
    if low and 'noindex' not in t: err(f'{rel}: noindex fehlt')
    # Überschriften
    hs = [(int(m.group(1)), txt(m.group(2))) for m in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', main, re.S)]
    h1 = [h for l, h in hs if l == 1]
    if len(h1) != 1: err(f'{rel}: {len(h1)} H1')
    else:
        raw = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'<h1[^>]*>(.*?)</h1>', main, re.S).group(1)))  # wie der Browser: Tags ohne Leerzeichen entfernen
        if re.search(r'[a-zäöüß][.!?][A-ZÄÖÜ][a-zäöüß]', raw): err(f'{rel}: H1 ohne Leerzeichen zwischen Sätzen (Unterzeile gehört nicht ins H1): {h1[0][:50]}')
        if len(h1[0]) > 90: err(f'{rel}: H1 {len(h1[0])} Zeichen')
        elif len(h1[0]) > 70: note(f'{rel}: H1 {len(h1[0])} Zeichen (über 70)')
    prev = 0
    for l, h in hs:
        if prev and l > prev + 1: err(f'{rel}: Überschriftenebene übersprungen (H{prev} auf H{l}: {h[:40]})')
        prev = l
    if '<main' not in t: note(f'{rel}: kein <main>')
    # Pflichtlinks auf jeder Seite
    for pf in ('impressum', 'datenschutz'):
        if not re.search(r'href="[^"]*' + pf + r'(\.html)?(#[^"]*)?"', t): err(f'{rel}: kein Link auf {pf}')
    # Bilder
    for im in re.findall(r'<img[^>]*>', main):
        if 'alt=' not in im: err(f'{rel}: Bild ohne alt: {im[:60]}')
        elif re.search(r'alt=""', im) and 'aria-hidden' not in im: note(f'{rel}: Bild mit leerem alt ohne aria-hidden')
        if not (re.search(r'\bwidth=', im) and re.search(r'\bheight=', im)): err(f'{rel}: Bild ohne width/height: {im[:60]}')
    # Links
    seen = collections.defaultdict(set)
    for m in re.finditer(r'<a ([^>]*)href="([^"#][^"]*|#[^"]+)"([^>]*)>(.*?)</a>', main, re.S):
        a, href, text = m.group(1) + m.group(3), m.group(2), txt(m.group(4))
        if re.match(r'(https?:|mailto:|tel:|javascript:)', href):
            if 'target="_blank"' in a and 'noopener' not in a: err(f'{rel}: target=_blank ohne rel=noopener: {href[:50]}')
            if href.startswith('http://') and 'localhost' not in href: note(f'{rel}: unsichere http-Adresse: {href[:50]}')
            continue
        if href.startswith('#'):
            if f'id="{href[1:]}"' not in t: err(f'{rel}: Anker fehlt {href}')
            continue
        base = os.path.dirname(rel)
        target = href if href.startswith('/') else os.path.normpath(os.path.join(base, href)).replace(os.sep, '/')
        if not exists(target): err(f'{rel}: toter Link {href}')
        if '?' in href.split('#')[0] and 'nofollow' not in a: err(f'{rel}: Link mit Parameter ohne rel="nofollow": {href}')
        if len(text) > 90: note(f'{rel}: sehr langer Linktext ({len(text)}): {text[:40]}… (nur die Überschrift verlinken)')
        if text: seen[text.lower()].add(href.split('#')[0])
    for k, v in seen.items():
        if len(v) > 1: note(f'{rel}: gleicher Linktext „{k[:30]}“ mit {len(v)} Zielen')
    # Formulare
    for fm in re.finditer(r'<form[^>]*>(.*?)</form>', main, re.S):
        f = fm.group(1)
        if not re.search(r'type="(email|tel)"|name="(email|telefon|tel|name)"', f): continue  # Suche, Filter und ähnliche Formulare ohne persönliche Daten
        if not re.search(r'name="einwilligung"[^>]*required|required[^>]*name="einwilligung"', f): err(f'{rel}: Formular ohne Pflicht-Einwilligung (name="einwilligung")')
        if not re.search(r'href="[^"]*datenschutz', f): err(f'{rel}: Formular ohne Datenschutz-Link in der Einwilligung')
    # Wortwahl (Rechtstexte ausgenommen)
    if rel not in ('impressum.html', 'datenschutz.html', 'agb.html'):
        body = txt(main)
        for p in BAD:
            if re.search(re.escape(p), body, re.I): err(f'{rel}: „{p}“ (Zusage, Floskel oder Platzhalter)')
        if re.search(r'(?<!Ist das alles )DSGVO-konform(?!\?)', body): err(f'{rel}: „DSGVO-konform“ als Zusage')
    # JSON-LD
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try: json.loads(m.group(1))
        except Exception as e: err(f'{rel}: JSON-LD ungültig ({e})')
        if 'aggregateRating' in m.group(1): err(f'{rel}: aggregateRating im JSON-LD (nicht erlaubt ohne echte Quelle)')

# Pflichtdateien, Sitemap
for must in ('index.html', 'impressum.html', 'datenschutz.html', '404.html', 'robots.txt', 'sitemap.xml'):
    if not os.path.exists(os.path.join(ROOT, must)): err(f'Datei fehlt: {must}')
sm = os.path.join(ROOT, 'sitemap.xml')
if os.path.exists(sm):
    locs = re.findall(r'<loc>(.*?)</loc>', open(sm, encoding='utf-8').read())
    for l in locs:
        p = re.sub(r'^https?://[^/]+', '', l) or '/'
        if not exists(p): err(f'Sitemap-URL ohne Seite: {l}')
        if any(p.endswith(n) or p.endswith(n[:-5]) for n in NOINDEX_OK): err(f'noindex-Seite in der Sitemap: {l}')
    note(f'Sitemap: {len(locs)} Adressen')

for n in sorted(set(notes)): print('HINWEIS', n)
for e in errors: print('FEHLER ', e)
print(f'{len(pages)} Seiten: {len(errors)} Fehler, {len(set(notes))} Hinweise')
sys.exit(1 if errors else 0)
```

======================================================================
19. RELAUNCH: ALTE SEITE ERSETZEN, OHNE GOOGLE-PLATZIERUNGEN ZU VERLIEREN
======================================================================
1. Alte Seite erfassen, bevor entworfen wird: alle Adressen (aus sitemap.xml, Navigation, internen Links und einer Suche nach "site:domain"), je Adresse Title, H1 und worum es geht. Dazu alle Links, die auf fremde oder geschützte Bereiche zeigen (Mitgliederbereich, Adminbereich, Buchungssystem, Shop bei Dritten).
2. Diese fremden Pflichtlinks bleiben auf der neuen Seite an gut auffindbarer Stelle erhalten, mit unveränderter Zieladresse.
3. Adressen behalten, wo es geht: Die neue Seite legt Inhalte unter demselben Pfad ab (alt /leistungen/ wird neu leistungen/index.html). Das braucht keine Weiterleitung.
4. Was nicht denselben Pfad behalten kann, kommt in WEITERLEITUNGEN.md neben website-fertig/: Tabelle alt → neu, je Zeile eine Adresse. Jede alte Adresse hat genau ein Ziel; was ersatzlos entfällt, zeigt auf die nächstpassende Seite, nicht pauschal auf die Startseite.
5. Die Weiterleitungen selbst richtet der Server ein. Im Bericht unter "OFFEN:" führen: "Weiterleitungen laut WEITERLEITUNGEN.md im Portal/Server einrichten". Keine eigenen Weiterleitungs-Skripte in die Seite bauen. Nur wenn Markentrix es ausdrücklich verlangt: je alte Adresse eine kleine statische Seite mit Meta-Refresh (0 Sekunden) und Canonical auf das neue Ziel, als Notlösung gekennzeichnet.
6. Inhalte, die bisher gefunden wurden, nicht verlieren: Leistungen, Orte und Begriffe aus Title und H1 der alten Seiten kommen auf der neuen Seite wieder vor. Texte dürfen besser werden, Themen dürfen nicht verschwinden.
7. Name, Adresse und Telefon bleiben identisch zum Google-Profil; die Website-Adresse im Google-Profil bleibt gleich.
8. Nach dem Livegang (Aufgabe für Markentrix, im Bericht nennen): neue Sitemap in der Search Console einreichen, nach zwei Wochen den Seiten-Bericht auf "Nicht gefunden (404)" prüfen.

======================================================================
20. ÄNDERUNGSAUFTRAG: BESTEHENDE KUNDENSEITE ANPASSEN
======================================================================
Gilt, wenn eine mit diesem Skill gebaute Seite geändert wird. Kein neues Design, keine neue Idee, keine neue Signatur.
1. Ausgangsstand ist der zuletzt hochgeladene Ordner website-fertig/ samt DESIGN.md. Fehlt DESIGN.md, Farben, Schriften und Abstände aus dem vorhandenen CSS ablesen und als DESIGN.md nachtragen, bevor etwas geändert wird. Fehlt der Ordner, nachfragen statt nachbauen.
2. Nur ändern, was beauftragt ist. Neue Inhalte nutzen die vorhandenen Tokens, Komponenten und den vorhandenen Ton. Fällt dabei ein echter Fehler auf (kaputter Link, falsche Angabe, Rechtslücke), nicht stillschweigend beheben, sondern im Bericht nennen und fragen.
3. Neue Unterseite: Navigation, Footer, Sitemap und interne Links auf allen Seiten mitziehen; Title, Description und H1 nach Abschnitt 7.
4. Geänderte Preise, Zeiten oder Kontaktdaten überall angleichen: sichtbarer Text, JSON-LD, Impressum, Datenschutzerklärung.
5. Prüfen, was betroffen ist: Prüfliste Punkte 1 bis 4 immer; Prüfskript und qa-statisch.py (Abschnitt 18) auf jeder geänderten Seite; Formulartest (Abschnitt 21), wenn ein Formular oder sein Skript berührt wurde; Härtetest nur für geänderte Datenanzeigen.
6. AENDERUNGEN.md neben website-fertig/ fortschreiben: Datum, was geändert wurde, welche Dateien. Hochgeladen wird immer der ganze Ordner.
7. Bericht kurz: geänderte Dateien, Prüfergebnis, "OFFEN:".

======================================================================
21. FORMULARTEST: ABSENDEN, FEHLER UND AUSFALL AUTOMATISCH PRÜFEN
======================================================================
Als formtest.mjs NEBEN website-fertig/ speichern. Erst "node mock.mjs" starten, dann "node formtest.mjs /kontakt.html" für jede Seite mit Formular. Braucht Playwright wie Abschnitt 18.
NUR gegen den Mock-Server laufen lassen, NIE gegen eine Live-Seite: der Erfolgstest sendet eine echte Anfrage ab.
Prüft acht Punkte: leeres Formular geht nicht durch; Lockfeld "website" vorhanden und leer; Erfolg führt auf danke.html mit Vorgangsnummer; bei 422 erscheint der Fehlertext, die Eingaben bleiben und der Knopf ist wieder bedienbar; bei 429 erscheint der Hinweis "später"; bei ausgefallener API ist ein Ausweichkontakt sichtbar.
Das Skript füllt das erste Formular der Seite mit Testwerten. Mehrstufige Buchungen mit eigener Tag- und Zeitwahl kann es nicht immer bedienen: scheitert der Erfolgstest daran, diesen Weg von Hand gegen den Mock prüfen und das im Bericht sagen.

```js
import { chromium } from 'playwright';
const BASE = process.env.BASE || 'http://localhost:8787', PFAD = process.argv[2] || '/', erg = [];
const E = (ok, text) => erg.push(`${ok ? 'PASS' : 'FAIL'}  ${text}`);
const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
const neu = async (antwort) => { const p = await browser.newPage({ viewport: { width: 390, height: 800 } });
  if (antwort) await p.route('**/api/anfrage', r => antwort === 'aus' ? r.abort() : r.fulfill({ status: antwort.status, contentType: 'application/json', body: JSON.stringify(antwort.body) }));
  await p.goto(BASE + PFAD, { waitUntil: 'networkidle' }); return p; };
const fuellen = p => p.evaluate(() => { const f = document.querySelector('form'); if (!f) return false;
  f.querySelectorAll('input,textarea,select').forEach(e => { if (e.name === 'website' || e.type === 'hidden' || e.type === 'submit') return;
    if (e.type === 'checkbox' || e.type === 'radio') { if (e.required || e.name === 'einwilligung' || e.name === 'agb') e.checked = true; }
    else if (e.tagName === 'SELECT') { const o = [...e.options].find(o => o.value && !o.disabled); if (o) e.value = o.value; }
    else e.value = e.type === 'email' ? 'test@example.com' : e.type === 'tel' ? '05141 123456' : e.type === 'date' ? new Date(Date.now() + 6048e5).toISOString().slice(0, 10) : e.type === 'number' ? '1' : 'Test Person';
    e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }); return true; });
const senden = async p => { await p.locator('form button[type=submit], form button:not([type])').first().click(); await p.waitForTimeout(1200); };
const text = p => p.evaluate(() => document.body.innerText);
let p = await neu(); if (!(await p.locator('form').count())) { console.log('Kein Formular auf ' + PFAD); await browser.close(); process.exit(2); }
await senden(p); E(!p.url().includes('danke'), 'leeres Formular wird nicht abgeschickt');
p = await neu(); await fuellen(p); await p.evaluate(() => { const w = document.querySelector('[name=website]'); window.__lock = w ? w.value : null; });
E(await p.evaluate(() => window.__lock === ''), 'Lockfeld "website" vorhanden und leer');
await senden(p); E(p.url().includes('danke.html') && /MOCK-/.test(await text(p)), 'Erfolg: Weiterleitung auf danke.html mit Vorgangsnummer');
p = await neu({ status: 422, body: { ok: false, errors: { name: 'TESTFEHLER-NAME' } } }); await fuellen(p); await senden(p);
E(/TESTFEHLER-NAME/.test(await text(p)), '422: Fehlertext erscheint'); E(await p.evaluate(() => [...document.querySelectorAll('form input')].some(e => e.value === 'test@example.com')), '422: Eingaben bleiben erhalten');
E(await p.evaluate(() => !document.querySelector('form button')?.disabled), '422: Knopf wieder bedienbar');
p = await neu({ status: 429, body: { ok: false } }); await fuellen(p); await senden(p); E(/später/i.test(await text(p)), '429: Hinweis "später noch einmal"');
p = await neu('aus'); await fuellen(p); await senden(p); E(/tel:|\d{4,}[\s\/-]?\d{3,}|@/.test(await p.evaluate(() => document.body.innerText + [...document.querySelectorAll('a[href^="tel:"],a[href^="mailto:"]')].map(a => a.href).join(' '))), 'API aus: Ausweichkontakt sichtbar');
await browser.close(); console.log(erg.join('\n')); process.exit(erg.some(e => e.startsWith('FAIL')) ? 1 : 0);
```

======================================================================
22. KUNDENÜBERGABE: MAIL-ENTWURF NACH DEM BERICHT
======================================================================
Nach dem internen Bericht einen Mail-Entwurf an den Kunden schreiben. Nur als Entwurf ausgeben, nie selbst versenden.
Regeln:
- Einfache Sprache, kein Fachjargon, kein Prüfprotokoll. Der Kunde ist Handwerker oder Ladeninhaber, kein Techniker.
- Nur Belegtes: nichts versprechen, was nicht gebaut und geprüft ist; keine Zusagen zu Platzierungen oder Anfragen.
- Im Namen von Markentrix unterschreiben ("Ihr Markentrix-Team"). Nie einen KI-Namen oder ein KI-Werkzeug nennen. Wenn von automatischen Funktionen die Rede ist: "der Agent", nicht "die KI".
- Am Ende ein kleiner, allgemeiner Hinweis: "Dieser Text wurde mit KI-Unterstützung vorbereitet."
Aufbau:
1. Betreff: "Ihre neue Website: Stand und nächste Schritte" (bei Änderung: "Änderungen an Ihrer Website sind umgesetzt").
2. Was fertig ist, in drei bis fünf Sätzen, mit den Funktionen in Kundensprache ("Kunden können jetzt online einen Termin wählen").
3. "Das brauchen wir noch von Ihnen": jeder Punkt aus "OFFEN:", den nur der Kunde liefern kann (Fotos, Preise, Öffnungszeiten, Steuernummer, Rechtstexte), als nummerierte Liste mit je einem Satz, wofür es gebraucht wird.
4. "Bitte kurz bestätigen": Angaben, die der Kunde prüfen soll (Schreibweise des Namens, Adresse, Telefon, Preise, Öffnungszeiten).
5. Wie es weitergeht: nächster Schritt und wer ihn macht. Kein Datum nennen, das nicht feststeht.
6. Gruß, "Ihr Markentrix-Team", KI-Hinweis.
Interne Punkte (Portal-Aufgaben, Prüfwerte, technische FAILs) gehören nicht in diese Mail.