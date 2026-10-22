# Portal-Erweiterung: Farbtermine mit persönlicher Bestätigung und Anzahlung

Für AJ Atelier (und jeden anderen Kunden mit langen Farb- oder Spezialterminen).
Ziel: Schnitte sind sofort gebucht. **Balayage, Babylights, Blondierung und Color Correction** sind ein
**Terminwunsch**: Die Uhrzeit wird vorgemerkt, der Salon bestätigt persönlich und schickt einen
**PayPal.Me-Link für die Anzahlung**.

Die Website ist schon fertig dafür und schaltet **automatisch** um, sobald das Portal die neuen Felder liefert.

---

## Stand heute (ohne Portal-Änderung) – so funktioniert es jetzt schon

| | Schnitt, Styling, Pflege … | Balayage, Babylights, Blondierung, Color Correction |
|---|---|---|
| Website | Sofortbuchung | Terminwunsch mit Fragebogen (Haarlänge, Haarzustand, letzte Behandlung, Neukundin) |
| Gesendet an `/api/anfrage` | `typ=termin`, `datum`, **`uhrzeit`** | `typ=termin`, `datum`, **`wunschzeit`** (keine `uhrzeit`), `terminart`, Fragebogen-Felder |
| Im Portal | Termin gebucht | landet als **Anfrage** („Terminanfrage“) mit allen Angaben, **ohne** Kalendereintrag |
| Salon | – | ruft an oder antwortet per Mail, trägt den Termin im Portal ein und schickt den PayPal.Me-Link von Hand |

Nachteil: Die Wunschzeit ist **nicht blockiert**, sie könnte in der Zwischenzeit von jemand anderem gebucht werden.
Deshalb diese Erweiterung.

---

## Was im Portal ergänzt werden soll

### 1. Datenbank (neue Migration, z. B. `db/0xx_leistung_freigabe.sql`)

```sql
ALTER TABLE website_leistungen
  ADD COLUMN IF NOT EXISTS freigabe  boolean      NOT NULL DEFAULT false,  -- Salon bestätigt diese Leistung selbst
  ADD COLUMN IF NOT EXISTS anzahlung numeric(8,2);                          -- Anzahlung in €, NULL = keine
```

### 2. Kundenportal → Website-Dienste → Leistungen (Formular je Leistung)

- Neues Häkchen **„Diese Leistung bestätige ich selbst (Terminwunsch)“** → `freigabe`
- Neues Feld **„Anzahlung (€)“** (optional, nur sichtbar wenn das Häkchen gesetzt ist) → `anzahlung`
- Hinweis darunter: „Die Uhrzeit wird für *Haltefrist* Stunden vorgemerkt. Mit der Bestätigung geht der PayPal.Me-Link über die Anzahlung an die Kundin.“

### 3. `GET /api/leistungen` – zwei Felder ergänzen (Vertrag bleibt kompatibel, nur neue Felder)

```python
cur.execute("SELECT schluessel, name, beschreibung, preis, dauer_min, freigabe, anzahlung FROM website_leistungen ...")
# je Leistung zusätzlich:
{"key": ..., "name": ..., "beschreibung": ..., "preis": ..., "dauer": ...,
 "freigabe": bool(r["freigabe"]),
 "anzahlung": float(r["anzahlung"]) if r["anzahlung"] is not None else None}
```

### 4. `POST /api/anfrage` (typ `termin` mit `uhrzeit`) – Freigabe pro Leistung

In `routes_siteapi.py`, dort wo heute `frei_gabe = bool(z["kal_freigabe"])` steht:

```python
frei_gabe = bool(z["kal_freigabe"]) or bool((lz or {}).get("freigabe"))
```

Damit wird der Termin wie bei der globalen Freigabe als **„reserviert“** (Status `geplant`) mit Haltefrist angelegt,
die Mail an den Salon lautet „Neue Terminanfrage … bitte bestätigen oder ablehnen“ und die Kundin bekommt
eine Eingangsbestätigung statt einer Buchungsbestätigung. Alles andere (Doppelbuchungsschutz, 422 auf `uhrzeit`) bleibt.

### 5. Bestätigen-Dialog im Portal

- Betrag der Anzahlung **vorbelegen** mit `website_leistungen.anzahlung` der gebuchten Leistung (änderbar).
- PayPal.Me-Link mit Betrag erzeugen: `https://paypal.me/<name>/<betrag>EUR`.
- Mail an die Kundin: „Ihr Termin am … ist reserviert. Bitte leisten Sie die Anzahlung von X € innerhalb von 48 Stunden: <Link>. Sie wird beim Termin vollständig verrechnet.“
- Optional: Status „Anzahlung offen / eingegangen“ zum Abhaken; nach Ablauf ohne Zahlung Erinnerung an den Salon.

### 6. Haltefrist

Für Termine mit Anzahlung reicht die normale Haltefrist (`kal_halte_std`) oft nicht, weil die Kundin erst nach der
Bestätigung zahlt. Vorschlag: Haltefrist endet mit der **Bestätigung**. Danach gilt der Termin, bis der Salon ihn
bei fehlender Zahlung selbst absagt.

### 7. Bezeichnungen in Mails und Portal (`LABELS` in `routes_siteapi.py`)

```python
"wunschzeit": "Wunschzeit", "terminart": "Terminart", "haarlaenge": "Haarlänge",
"vorbehandlung": "Haarzustand", "letzte_behandlung": "Letzte chemische Behandlung", "kundin": "Schon einmal da",
"leistung_name": "Leistung", "mitarbeiter_name": "Mitarbeiter",
```

### 8. Kleiner Fehler, gleich mit beheben

`GET /api/verfuegbarkeit` liefert heute **immer** `selfBooking: true`, auch wenn „Ich bestätige jede Buchung selbst“
(`kal_freigabe`) eingeschaltet ist. Websites können dann nicht „Terminwunsch“ anzeigen. Richtig wäre:

```python
"selfBooking": not z["kal_freigabe"],
```

### 9. Dokumentation

In `docs/WEBSITE-API.md` bei `/api/leistungen` ergänzen: `freigabe` (bool) und `anzahlung` (Zahl oder null),
und bei `selfBooking` den Bezug zu „Ich bestätige jede Buchung selbst“.

---

## Was die Website dann automatisch macht

| Portal liefert | Website |
|---|---|
| kein Feld `freigabe` (heute) | nutzt ihre eigene Liste (Balayage, Babylights, Blondierung, Color Correction) und sendet `wunschzeit` |
| `freigabe: true` | Terminwunsch, sendet **`uhrzeit`** → Portal reserviert die Zeit |
| `freigabe: false` | Sofortbuchung (auch für Farbe, falls der Salon das so will) |
| `anzahlung: 50` | zeigt „Anzahlung von 50 € per PayPal“ im Formular und auf der Danke-Seite |

## Im Portal für AJ Atelier einstellen (nach der Erweiterung)

| Leistung (key) | Freigabe | Anzahlung (Vorschlag, mit dem Salon abstimmen) |
|---|---|---|
| `f-balayage` | ✓ | 50 € |
| `f-babylights` | ✓ | 50 € |
| `f-blondierung` | ✓ | 30 € |
| `f-correction` | ✓ | – (Beratungstermin) |
| alle anderen | – | – |

Außerdem: PayPal.Me-Name des Salons unter Website-Dienste → PayPal hinterlegen.

**Rechtlich (an die Anwalts-Checkliste):** Regeln zur Anzahlung (Verrechnung, Erstattung bei Absage bis X Stunden vorher,
Verfall bei Nichterscheinen) müssen der Kundin vor der Zahlung mitgeteilt werden, am besten in der Bestätigungs-Mail
und in kurzen Terminbedingungen auf der Website.
