# Kundenvorlage Werkstatt (portalfähig)

Vorlage nach dem Skill „Website mit Portal“: statische Seite ohne eigenes Backend, die auf dem Markentrix-Server läuft und über das Portal Termine, Anfragen, Bewertungen und Statistik bezieht.

- `website-fertig/` ist die Abgabe (index.html liegt direkt darin). Diesen Ordner hochladen.
- `bauen.py` erzeugt den Ordner neu und die Vorschau unter `static/beispiel/werkstatt-portal/`.
- `vorschau-api.js` und `vorschau.css` gehören nur zur Vorschau und simulieren Schnittstellen und Bausteine. Sie sind nicht Teil von `website-fertig/`.

Genutzte Portal-Funktionen: Terminanfrage über die Website-API (Variante B: `/api/verfuegbarkeit`, `/api/leistungen`, `/api/mitarbeiter`, `/api/slots`, `/api/anfrage`), Kontaktformular, Google-Bewertungen und Statistik-Einstellung als Bausteine (Variante A, `data-mk`).

Offene Punkte vor einer echten Seite:
- Firmendaten in Impressum, Datenschutz, Kopf und Fuß (hier fiktive Musterangaben), USt-IdNr., Telefon, E-Mail, WhatsApp-Nummer.
- `noindex` in den Seitenköpfen und `Disallow: /` in robots.txt entfernen, Sitemap mit der echten Domain füllen (hier relative Pfade, weil keine feste Domain im Code stehen darf).
- Leistungen, Preise, Mitarbeiter und Uhrzeiten im Portal anlegen (die Terminauswahl kommt von dort), „Feste Uhrzeiten“ passend zu den Zeiten der Seite.
- Bilder durch echte Fotos des Betriebs ersetzen (die Motive sind KI-Symbolbilder), Texte und Datenschutzerklärung rechtlich prüfen lassen.
