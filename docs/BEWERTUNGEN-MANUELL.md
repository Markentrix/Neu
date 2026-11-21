# Echte Google-Bewertungen auf der Website anzeigen (zwei Wege)

Die Website zeigt Bewertungen in dieser Reihenfolge:

1. **Live von Google** über `/api/bewertungen.php` (siehe `docs/server/BEWERTUNGEN.md`). Braucht auf dem Server `MX_GOOGLE_API_KEY` und `MX_GOOGLE_PLACE_ID`. **Stand 21.11.2026: nicht eingerichtet**, der Endpunkt antwortet `{"ok":false}`.
2. **Von Hand übernommen** aus `static/data/bewertungen.json` (neu). Wird angezeigt, solange Weg 1 nicht läuft und die Liste nicht leer ist.
3. Sonst nur die Anzahl mit Link zu Google (heutiger Zustand).

## Weg 2: Bewertungen eintragen

Datei `static/data/bewertungen.json`:

```json
{
  "stand": "November 2026",
  "gesamt": null,
  "anzahl": 11,
  "profil": "https://www.google.com/maps?cid=12094138210775533768",
  "bewertungen": [
    { "name": "Vorname N.", "sterne": 5, "zeit": "vor 2 Monaten", "text": "Wörtlich kopierter Text der Bewertung." }
  ]
}
```

Regeln, damit es ehrlich und rechtlich sauber bleibt:
- Nur **echte** Bewertungen, **wörtlich** aus Google kopiert (Name wie angezeigt, Sterne, Zeitangabe). Nichts umformulieren, nichts erfinden. Kürzungen mit „…“ kennzeichnen.
- Keine Auswahl nach Sternen verschweigen: Die Seite sagt, dass wir ausgewählt haben und alle Bewertungen auf Google einsehbar sind. Sie sollte trotzdem nicht nur Bestnoten zeigen, wenn es auch andere gibt.
- `anzahl` und `stand` bei jeder Änderung anpassen. `gesamt` (Durchschnitt, zum Beispiel `4.9`) nur eintragen, wenn Sie ihn auf Google sehen.
- Höchstens 6 Einträge werden angezeigt.
- Danach `python3 tools/qa.py`, bauen und einspielen.

Rechtlich offen (bitte mit Ihrem Anwalt klären): Veröffentlichung fremder Bewertungstexte mit Namen auf der eigenen Seite und der Hinweis nach § 5b Abs. 3 UWG zur Prüfung der Echtheit. Der Text auf der Seite sagt ehrlich, dass wir die Echtheit nicht eigenständig prüfen.

## Weg 1 ist die bessere Dauerlösung

Mit dem Google-Schlüssel und der Place-ID (Schritte in `docs/server/BEWERTUNGEN.md`) zeigt die Seite die von Google gelieferten Bewertungen automatisch und aktuell, ohne dass jemand Texte kopieren muss.
