# Farbvarianten (Vorschau, nicht Teil der Auslieferung)

`gen_thema.py` erzeugt aus `static/assets/mx.css` und `thema-hand.css` ein Überlagerungs-Stylesheet mit drei Varianten
(`data-thema="a|b|c"` am `<html>`-Element). Aufruf: `python3 gen_thema.py <mx.css> <thema.css>`.

- **A Klarweiß**: kühles Weiß statt Creme, blaugraue Linien.
- **B Tiefsee-Rhythmus**: hell im Wechsel mit Pfauenblau- und Tiefsee-Flächen (Angebot, Vorher-nachher, Fuß).
- **C Nacht**: gesamte Seite auf Tiefsee; Hell-Dunkel-Umkehr aus den vorhandenen Regeln, Vorschauen und Illustrationen bleiben hell.

Geprüft mit axe (WCAG 2.1 AA, 390 und 1280 px) auf Startseite, Pakete, Referenzen, Webdesign, Portal, Über uns, FAQ, Blog, Prozess, Kontakt: keine Verstöße.
Übernahme in die Seite: gewählte Variante in `static/assets/mx.css` und `docs/brand` einarbeiten, danach OG-Bilder neu erzeugen.
