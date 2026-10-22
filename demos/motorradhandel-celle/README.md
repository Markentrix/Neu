# Demo: Motorradhandel-Celle (verkaufsorientiertes Redesign, Paket WEB + FUNNEL)

Entwurf von Markentrix nach Skill `markentrix-kundenwebsite` (Muster: `references/verkauf-haendler.md`). **Nicht veröffentlichen**, solange nicht freigegeben: `noindex`, Demo-Leiste, kein Tracking, keine Drittanbieter, Formulare ohne Funktion.

Start lokal: `python3 -m http.server 8766` im Ordner, dann `http://127.0.0.1:8766/`. Seiten neu erzeugen: `python3 build/build.py` (Bestand steht in `build/build.py`, Kopie in `assets/bestand.json`).

## Grundlage
Inhalte, Kontaktdaten, Leistungen, Fahrzeuge, Preise und Fotos stammen von motorradhandel-celle.de (Stand 06.10.2026). Texte sind gekürzte Vorschläge. Die alte Seite ist ein WebPlus-Tabellenlayout mit Text in Bildern, 26 Seiten, ohne mobile Darstellung, mit YouTube-Links und Verweisen auf speedrad.de.

## Aufbau
**SEO-Seiten:** 5 Marken- und 4 Arten-Seiten, 2 Ratgeber (Gebrauchtkauf, Überwintern). **Inhaltsseiten:** Start, Motorräder (Bestand mit Filter und Sortierung), Überwintern (Winterlager), Motorrad verkaufen (Ankauf), Service & Finanzierung, Über uns, Kontakt (Probefahrt, Wunschsuche). **Verkaufsstrecke:** 16 Fahrzeug-Detailseiten mit Probefahrt-Formular, Danke-Seite. Dazu Impressum, Datenschutz, 404.
**Saison-Kampagne Winterlager** (Schalter `WINTER` in `build/build.py`): Banner auf jeder Seite, Hero-Link und Streifen auf der Startseite, „Überwintern“ in der Navigation und als erste Leistung, eigene Seite `ueberwintern.html` mit Ablauf, Konditionen (Platzhalter), Winterplatz-Formular und FAQ, Querverweise zu Verkauf in Kommission und Inzahlungnahme. Im Frühjahr Schalter ausstellen oder durch eine Saisonstart-Kampagne ersetzen.
**Verkaufs-Bausteine:** Suchfilter im Hero, Preis-Kacheln, Highlights, Probefahrt je Fahrzeug, Anrufen/WhatsApp, mobile Aktionsleiste, Ankauf-Strecke, Inzahlungnahme/Finanzierung-Häkchen, FAQ, ehrlicher Hinweis „Zwischenverkauf vorbehalten“.
**Design (Vorschlag, keine CI vorhanden):** Schwarz, Signalrot #C8102E, Barlow Condensed (Überschriften) und Inter, selbst gehostet. Logo/Wortmarke ist ein Platzhalter-Entwurf von Markentrix, kein Kundenlogo.

## SEO und GEO
Details, Keyword-Zuordnung, Go-live- und Nachsorge-Checkliste und KI-Testfragen: **`SEO-GEO.md`**. Live-Build mit Indexierung: `python3 build/build.py --live` (schreibt nach `live/`), Prüfer: `python3 build/check_seo.py [ordner] [--live]` (Demo: 0 FAIL, 0 WARN; Live: 0 FAIL, offene Platzhalter werden gemeldet). Live-Build gemessen (Lighthouse mobil gedrosselt, Start, Bestand, Fahrzeug, Überwintern): Performance, Barrierefreiheit, Best Practices und SEO je **100**.

## Messung (Lighthouse 12, mobil, Slow 4G + 4x CPU)
Start, Bestand, Detailseite, Ankauf: Performance 100 · Barrierefreiheit 100 · Best Practices 100 · LCP 1,0–1,9 s · CLS ≤ 0,04. Labordaten, kein Feldwert. Filter-Logik, Leer-Zustand und alle Links geprüft. Audit-Skript: 0 FAIL.

## Offen vor einer Veröffentlichung (Kunde klären)
0. **Winterlager-Konditionen:** Auf der alten Seite steht nur „Gern kann Ihr Bike auch bei uns überwintern“. Preis, Zeitraum, Leistungen (z. B. Batteriepflege), Versicherung/Haftung, Bringen/Abholen und Anzahl Plätze sind **Platzhalter** und müssen vom Kunden kommen. Keine Kapazitäts- oder Verknappungsaussage ohne Beleg.
1. **Bestand aktuell?** 20 Fahrzeuge standen auf der alten Seite, 16 sind übernommen. Nicht übernommen: Yamaha YZF-R1 (2004), Suzuki DR 650, Yamaha R6 RJ03, Honda „Auswahl“ (keine oder zu kleine Fotos, 160–260 px). Preise, Kilometer, Verfügbarkeit bestätigen lassen. **Pflegeweg für den Bestand festlegen**, sonst veraltet die Seite.
2. **Fotos sind der Engpass:** nur 250–400 px breit, uneinheitlich, teils mit Nummernschildern und Passanten. Empfehlung: neues Fotoset je Fahrzeug (Zusatzleistung, Preis vorab vereinbaren). Bildrechte und Personen/Kennzeichen prüfen.
3. **Zuordnung Foto zu Fahrzeug** prüfen (Honda CBR 600 RR: Foto von Unterseite der alten Seite übernommen; einzelne Galeriebilder der alten Seite gehören evtl. zu anderen Fahrzeugen).
4. **Texte bestätigen:** „TÜV neu (nach Vereinbarung)“ (alte Seite: „TÜV neu (Vereinbar.)“), „Gepflegt“, „17 Jahre Erfahrung“, „fünfköpfiges Team“, Historie des Standorts, „Finanzierung auf Anfrage“, Gewährleistung/Garantie (Platzhalter), Zeiten.
5. **Kontakt:** zwei E-Mail-Adressen auf der alten Seite (tollertag@freenet.de und vollcool007@web.de, Impressum nutzt die zweite), Telefon 01520 8880000, **WhatsApp** nur verlinken, wenn der Kunde WhatsApp nutzt.
6. **Logo/CI:** Kunde hat kein Logo außer einem Foto-Banner. Mini-CI vorschlagen oder CI-Paket anbieten.
7. **Rechtstexte** (Impressum, Datenschutz, AGB) liefert der Kunde. Die Platzhalterseiten enthalten die Angaben der alten Seite. Preisangaben (PAngV, Differenzbesteuerung) und Widerruf/Haustürgeschäft bei Fernabsatz prüfen lassen.
8. **Nicht übernommen:** E-Bikes/Speedrad.de (eigene externe Seite), Fahrrad-Werkstatt, Vermietung, Ausfahrten, YouTube-Testvideos (nur per Zwei-Klick zulässig), Foto des Inhabers.
9. **Weiterleitungen:** alte URLs (`Seite21.html` usw.) per 301 auf neue Bestands-/Detailseiten.
10. Formulare anbinden (Zustellung beim Kunden, SPF/DKIM, Foto-Upload mit Größenlimit und Datenschutz), Domain/DNS laut Anlage „Domain und Technik“.

## Neu: Merkliste, Ratenrechner, mobile Kontaktleiste
- Merkliste (Herz auf Karten und Detailseite, Zähler im Header, `merkliste.html`): nur lokal im Browser (localStorage), keine Daten an Server, daher keine Einwilligung nötig. Seite ist noindex.
- Ratenrechner auf Fahrzeugseiten: reine Beispielrechnung mit editierbarem Zins. **Vor Go-live prüfen:** Sobald konkrete Zinssätze/Raten beworben werden, gelten die Pflichtangaben für Kreditwerbung (PAngV/BGB). Entweder Rechner mit Partnerbank-Konditionen und Pflichtangaben ausstatten (Rechtsprüfung) oder entfernen.
- Mobile Leiste (Anrufen, WhatsApp, Probefahrt) auf Fahrzeugseiten.
- Getestet: Lighthouse mobil (devtools-Drosselung) 100/100/100, SEO 69 nur wegen Demo-noindex.
