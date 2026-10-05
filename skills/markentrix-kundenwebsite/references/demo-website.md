# Demo-Website für den passenden Kunden (Pflicht-Phase)

Für **jeden** Interessenten/Kunden entsteht eine individuelle Demo, bevor oder mit dem Angebot. Sie zeigt konkret, wie seine Website aussehen und wirken würde. Keine Standard-Demo, kein fremdes Template.

## Wann
Nach dem Erstgespräch/Briefing-Kurzcheck, vor dem Angebot (oder gemeinsam mit ihm). Bei Bestandskunden/Relaunch vor Projektstart.

## Umfang (Zeitbox, typisch 2–4 h)
- **1 Seite**: Startseite oder Landingpage, above-the-fold + 3–5 Sektionen, mobil und Desktop.
- Branchenpassend (`branchen.md`), Hero mit Nutzen + Ort, Leistungen, Vertrauen (nur Echtes), Kontakt/CTA.
- Eigene Farb-/Typo-Ableitung aus dem **öffentlichen** Auftritt des Kunden (Logo, Farben) als Vorschlag (`design-system-kunde.md`), kein 1:1-Kopieren fremder Layouts.
- Performance und Barrierefreiheit auf Endniveau (Starter), damit der Kunde Qualität spürt, nicht nur Optik.
- Eine ruhige Signature-Animation (`animation.md`), nicht mehr.

## Inhalte und Recht (Hard Gates für Demos)
1. **Als Entwurf gekennzeichnet:** sichtbarer Hinweis „Designvorschlag für [Firma] – nicht veröffentlicht“ (Demo-Leiste), `noindex, nofollow`, keine Veröffentlichung in Suchmaschinen.
2. **Zugriff begrenzt:** unlistbare URL + Passwortschutz oder Token-Link, nur an den Ansprechpartner. Kein Teilen in Social Media ohne Kundenfreigabe.
3. **Keine fremden Rechte verletzen:** Texte/Fotos/Logos des Kunden nur aus öffentlichen Quellen als Anschauung nutzen, wenn der Kunde zustimmt oder es offenkundig sein eigenes Material ist; Kundenlogo nur vom Kunden bzw. sinngemäß aus seinem Auftritt zur Ansicht. Keine fremden Marken, keine Bilder Dritter. Stock/KI-Bilder markieren (`Platzhalterbild`); Lizenz für Demo-Bilder klären, KI-Bilder nach CI-Bildrichtlinie.
4. **Nichts erfinden:** keine erfundenen Bewertungen, Zahlen, Referenzen, Teamfotos. Platzhalter sichtbar kennzeichnen. Texte als „Textvorschlag“.
5. **Kein Tracking, keine Drittanbieter, kein Formularversand an Dritte.** Formular in der Demo funktionslos mit Hinweis oder an Test-Postfach.
6. **Keine Personendaten** von Mitarbeitern/Kunden des Interessenten ohne Einwilligung.
7. **Aufräumen:** Demo wird nach vereinbarter Frist (z. B. 30 Tage) ohne Auftrag gelöscht. Dem Kunden mitteilen.
8. Nach außen nur Markentrix, keine Tool-/Modellnamen.

## Ablauf
1. Öffentlichen Auftritt, Google-Profil, 3 Wettbewerber ansehen (10 min), USP und Schwäche der aktuellen Seite notieren.
2. Hero-Aussage und Struktur festlegen (ein Ziel, ein CTA).
3. Aus dem Starter bauen, Tokens ableiten, Demo-Leiste und `noindex` einschalten (`assets/starter/demo-snippet.txt`).
4. Messen: Lighthouse mobil, `audit.sh` (ohne FAIL; Demo-Platzhalter erlaubt).
5. Hosten (Staging/Preview, passwortgeschützt), Link + Kurz-Screenshot mobil/Desktop erstellen.
6. Begleittext (3–5 Sätze): was wir gesehen haben, was die Demo zeigt, nächster Schritt (Angebot, Termin). Ehrlich, ohne Versprechen zu Rankings/Anfragen.
7. Feedback sammeln, in Angebot/Briefing einarbeiten.

## Verkaufsargumentation (zulässig)
Konkret zeigen: Ladezeit-Werte (Lab, belegt), Barrierefreiheit, Datenschutz-Konzept, klare Struktur auf Anfrage-Ziel. Keine Behauptung, die aktuelle Seite sei rechtswidrig oder schlecht, ohne Beleg und sachlichen Ton. Kein Wettbewerbsbashing.

## Übergang in das Projekt
Genehmigte Demo ist Basis für Phase 2–4. Demo-Leiste und `noindex` beim Livegang entfernen. Platzhalter ersetzen. Nicht genutzte Demos löschen.
