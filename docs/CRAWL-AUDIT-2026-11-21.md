# Crawl-Audit der Seite (Stand 21.11.2026)

Auslöser: Liste der Prüfungen eines SEO-Crawlers (Beispiel Screaming Frog). Wir nutzen kein solches Programm, sondern eigene Skripte auf der gebauten Seite (`dist/`, entspricht dem ausgelieferten Quelltext) plus Stichproben am Live-Server. Wiederholbar mit `python3 tools/build.py && python3 tools/crawl_audit.py`.

| Prüfung (Crawler-Funktion) | Ergebnis |
|---|---|
| Defekte Links, Anker, Weiterleitungen (intern) | 0 defekt (104 Seiten, alle Links und Anker). Live: `http`→`https` (308), `www`→ohne www (301), `/index.html`, `/impressum/` und `/impressum.html` (301) auf die eine Adresse, unbekannte Adresse = 404. |
| Externe Links | 44 Adressen. 42 erreichbar. 3 Links auf Google-Hilfeseiten waren veraltet (Weiterleitung auf Startseite bzw. andere Seite) und sind ersetzt. Instagram antwortet Crawlern mit 429 (Schutz, kein Fehler). |
| Titel und Meta | Alle Seiten haben Title und Description. Keine doppelten. 2 Titles gekürzt (Startseite, KI-Checkliste). `lang`, `viewport`, Open Graph und Twitter-Karte vorhanden. |
| Meta-Robots und Canonical | Jede indexierbare Seite hat ein selbstverweisendes Canonical. Nur die Karten-Seite (noindex, Einbettung) hat keines. |
| hreflang | Nicht eingesetzt, nicht nötig (einsprachig, de). |
| Exakte Duplikate | 0. |
| Beinahe-Duplikate und Ähnlichkeit | Regionalseiten teilen etwa ein Drittel der Sätze (Standardbausteine), Branchenseiten ähnlich. Siehe Prüfbericht. Keine Änderung. |
| XML-Sitemap | 90 URLs mit lastmod, alle vorhanden, keine noindex-Seiten, nicht durch robots.txt gesperrt, alle indexierbaren Seiten enthalten. |
| Crawl-Tiefe, verwaiste Seiten | Tiefe 0 bis 2 (1 + 48 + 50 Seiten). Jede indexierbare Seite hat mehr als 2 interne Verweise. Nicht von der Startseite erreichbar sind nur absichtlich `noindex`: Danke-Seite, KI-Checkliste, zwei Anzeigen-Landingpages. |
| Bilder | Alle mit Alt-Attribut sowie Breite und Höhe, keine fehlenden Dateien, kein unsicherer Inhalt. |
| Struktur der Überschriften | Eine H1 je Seite, keine Ebene übersprungen, Keywords in H1 (siehe Prüfbericht). |
| Strukturierte Daten und Prüfung | Alle JSON-LD-Blöcke geparst, keine doppelten Kennungen, Pflichtangaben vorhanden. Das Google-Prüfwerkzeug selbst nicht aufrufbar. |
| Rechtschreibung und Grammatik | Ohne Wörterbuch: keine doppelten Wörter (Treffer waren korrektes Deutsch), keine fehlenden Leerzeichen nach Satzzeichen. **Keine vollständige Rechtschreibprüfung möglich**, dafür fehlt hier ein Wörterbuch. |
| Eigene Suche und Extraktion | Keine Platzhaltertexte (Lorem, TODO), keine unsicheren `http://`-Adressen im Inhalt, keine dünnen Seiten (unter 250 Wörter, ausgenommen Rechtstexte und Werkzeugseiten). |
| JavaScript-Rendering | Aller Text liegt schon im Quelltext, kein Inhalt entsteht erst durch Skripte. |
| Barrierefreiheit | axe mit WCAG 2.2 AA und Best Practice auf 93 Seiten bei 390 px: keine Verstöße. Zwei Funde behoben (ungültige Rolle im Projektstreifen, fehlendes `<main>` auf der Karten-Seite). |
| Mobile Bedienbarkeit | Viewport überall, keine Überläufe, Zielgrößen (WCAG 2.2) bestanden. Echte Geräte nicht getestet. |
| Server und Sicherheits-Header | HSTS, CSP, `nosniff`, `X-Frame-Options`, Referrer- und Permissions-Policy, Kompression (gzip), Assets 1 Jahr unveränderlich. |
| PageSpeed Insights | **Nicht möglich**: Die öffentliche Schnittstelle ohne Schlüssel ist ausgeschöpft (429). Mit einem PageSpeed-API-Schlüssel oder in Chrome (Lighthouse) lässt es sich nachholen. |
| Google Analytics, Search Console, KI-Integration, Segmentierung, Zeitplan, Crawl-Vergleich | Nicht Teil unseres Skripts. Search Console und Bing Webmaster nach dem Einspielen selbst auswerten (Seiten mit Fehlern, Abdeckung). |
