# Content-Takt und Redaktionsplan · Stand 19.10.2026

Ziel: Die Seite bleibt aktuell, deckt echte Suchfragen von Betrieben vor Ort ab und liefert jeden Monat Material für alle Kanäle. Der Blog hat 15 Beiträge, das ist die Basis.

## Rhythmus

| Takt | Was | Aufwand |
|---|---|---|
| Alle zwei Wochen | ein neuer Beitrag (500 bis 800 Wörter) | ca. 2 Stunden mit Prüfung der Quellen |
| Zu jedem Beitrag | vier Social-Posts (siehe unten) | ca. 45 Minuten |
| Monatlich | alte Beiträge prüfen: Links, Preise, Zahlen, „Aktualisiert“-Datum | ca. 1 Stunde |
| Monatlich | Anfragen auszählen (Herkunft, siehe `docs/MESSUNG.md`) | 15 Minuten |
| Quartalsweise | Search Console: Suchanfragen mit vielen Anzeigen und wenigen Klicks → Titel schärfen oder Beitrag ergänzen | 1 Stunde |

## Regeln für jeden Beitrag

1. Eine Suchfrage pro Beitrag, im Titel und in der ersten Zeile beantwortet.
2. Aussagen mit Quelle: Google-Dokumentation, Gesetzestext, Behörde. Link vorher öffnen und lesen, nicht aus dem Gedächtnis zitieren.
3. Preise nur aus der Preisliste (Stand 01.10.2026, netto). Keine Kennzahlen, keine Kundennamen, keine Ergebnisgarantien.
4. Beispielszenarien sind frei erfunden und so gekennzeichnet.
5. Zwei bis drei Links auf passende Leistungsseiten, am Ende drei verwandte Beiträge.
6. Keine Werkzeug- oder Modellnamen in Fließtexten, Anrede „Sie“, keine Gedankenstriche.
7. Rechtliche Themen immer als Überblick ohne Rechtsberatung kennzeichnen.

## Ablauf: Beitrag veröffentlichen

1. Beitrag nach dem Muster eines bestehenden Beitrags in `src/pages/blog/` anlegen (Front Matter mit `article:published_time`, JSON-LD Article, Breadcrumb, FAQ).
2. In `src/pages/blog.html` Karte ergänzen, in `static/llms.txt` eintragen.
3. Drei verwandte Beiträge am Ende und passende Leistungsseite verlinken; auf zwei bis drei älteren Beiträgen zurücklinken.
4. `python3 tools/build.py --check`, `html-validate`, Sichtprüfung bei 390 und 1280 px.
5. ZIP bauen (`tools/paket.sh`), hochladen, in der Search Console die neue Adresse prüfen lassen und Indexierung beantragen. Der Feed `https://markentrix.de/feed.xml` aktualisiert sich automatisch.
6. Social-Posts planen (Metricool), Links mit Kampagnenparametern (`docs/SOCIAL.md`).

## Zwölf Wochen: Themenvorschläge

Reihenfolge nach Nutzen für Anfragen. Vor dem Schreiben die genannte Quellenart prüfen.

| Woche | Arbeitstitel | Kategorie | Verlinkt auf | Quellenart |
|---|---|---|---|---|
| 1 (26.10.) | Website-Texte, die Anfragen bringen: Aufbau einer Leistungsseite | Website | Webdesign, Landingpage | Google Search Central (hilfreiche Inhalte) |
| 3 (09.11.) | Mobile Website: fünf Prüfungen, die Sie selbst machen können | Website | Webdesign, Website-Pflege | web.dev Core Web Vitals |
| 5 (23.11.) | KI-Antworten und Ihre Website: wie Inhalte zitierfähig werden (GEO) | SEO/GEO | SEO und GEO | Google Search Central zu KI-Funktionen |
| 7 (07.12.) | Terminbuchung auf der Website: Formular, Kalender oder Anruf? | Website | Landingpage, KI-Automatisierung | eigene Praxis, keine Zahlen |
| 9 (21.12.) | Echte Fotos statt Stockbilder: warum Betriebe vor Ort davon profitieren | Marke | Corporate Identity, Webdesign | Google-Hilfe zu Bildern |
| 11 (04.01.) | Kontaktformular: welche Felder Sie wirklich brauchen | Website | Landingpage | Datenminimierung nach DSGVO Art. 5 |

Weitere Ideen für später: Preise auf der Website nennen (UWG-Hinweise prüfen), Barrierefreiheit für kleine Betriebe (Geltungsbereich des Barrierefreiheitsstärkungsgesetzes vorher in der Quelle prüfen), Antwortzeit auf Anfragen, Checkliste vor dem Livegang, ein Jahr Website: was Sie mit den Zahlen tun.

## Aus jedem Beitrag vier Social-Posts

| Kanal | Format | Aufbau |
|---|---|---|
| Instagram | Karussell, 5 bis 7 Folien | Folie 1 Frage aus dem Beitrag, Folien 2 bis 6 je ein Merksatz, letzte Folie Link in Bio (`utm_campaign=<beitrag>`) |
| Facebook | Beitrag mit Link | Zwei Sätze Nutzen, ein Satz Beispiel, Link zum Beitrag |
| LinkedIn / Unternehmensprofil | kurzer Text | Eine Beobachtung aus dem Alltag lokaler Betriebe, drei Stichpunkte, Link |
| YouTube Shorts / TikTok | 30 bis 45 Sekunden | Hook mit der Frage, ein Merksatz pro Einstellung, Schluss: „Mehr dazu im Blog“ (nur wenn der Kanal bespielt wird) |

Kennzeichnen, wenn Inhalte mit KI erstellt wurden. Keine Versprechen zu Platzierungen oder Ergebnissen.

## Kennzahlen

- Neue Beiträge pro Monat (Ziel: 2)
- Anfragen mit Herkunft „Google-Suche“ und „Blog“ (aus dem Protokoll, siehe `docs/MESSUNG.md`)
- Beiträge mit Anzeigen in der Search Console, aber unter 1 % Klickrate → Titel überarbeiten
