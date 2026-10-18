"""Kontoauszug (CSV) mit offenen Rechnungen abgleichen. Es werden nur Eingänge betrachtet; gebucht wird nur bei Rechnungsnummer UND passendem Betrag."""
import csv
import io
import re
from datetime import datetime

KOPF_DATUM = ("buchungstag", "buchungsdatum", "valuta", "datum", "date", "wertstellung")
KOPF_TEXT = ("verwendungszweck", "buchungstext", "zweck", "beschreibung", "reference", "verwendung", "text")
KOPF_BETRAG = ("betrag", "umsatz", "amount", "soll/haben")


def _trenner(text: str) -> str:
    kopf = "\n".join(text.splitlines()[:15])
    return max(";,\t", key=lambda c: kopf.count(c))


def betrag_cent(s: str):
    s = (s or "").strip().replace("€", "").replace("EUR", "").replace(" ", "").replace(" ", "")
    if not s:
        return None
    neg = s.startswith("-") or s.endswith("-") or s.lower().endswith("s")
    s = s.strip("-+").rstrip("SsHh")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        c = round(float(s) * 100)
    except ValueError:
        return None
    return -c if neg else c


def datum_lesen(s: str):
    s = (s or "").strip()
    for f in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None


def zeilen_lesen(text: str) -> list:
    text = text.lstrip("﻿")
    rows = list(csv.reader(io.StringIO(text), delimiter=_trenner(text)))
    kopf_i = None
    for i, r in enumerate(rows[:40]):
        low = [c.strip().lower() for c in r]
        if any(any(k in c for k in KOPF_BETRAG) for c in low) and any(any(k in c for k in KOPF_TEXT) for c in low):
            kopf_i = i
            break
    if kopf_i is None:
        raise ValueError("Die Spaltenüberschriften (Betrag, Verwendungszweck) wurden nicht gefunden. Bitte die CSV-Datei direkt aus dem Online-Banking exportieren.")
    low = [c.strip().lower() for c in rows[kopf_i]]
    def finde(namen, ausser=()):
        for i, c in enumerate(low):
            if i not in ausser and any(n in c for n in namen):
                return i
    i_betrag = finde(KOPF_BETRAG)
    i_datum = finde(KOPF_DATUM)
    i_text = [i for i, c in enumerate(low) if any(k in c for k in KOPF_TEXT) and i != i_betrag]
    out = []
    for r in rows[kopf_i + 1:]:
        if len(r) <= max(i_betrag, *(i_text or [0])):
            continue
        b = betrag_cent(r[i_betrag])
        if b is None:
            continue
        out.append({"datum": datum_lesen(r[i_datum]) if i_datum is not None and i_datum < len(r) else None, "betrag_cent": b,
                    "text": " ".join(r[i] for i in i_text if i < len(r)).strip()})
    return out


def abgleichen(cur, zeilen: list) -> dict:
    cur.execute("""SELECT b.id, b.nummer, b.brutto_cent, k.firma FROM belege b JOIN kunden k ON k.id=b.kunden_id
                   WHERE b.art='rechnung' AND b.status IN ('gestellt','versendet') AND b.nummer IS NOT NULL""")
    offen = cur.fetchall()
    sicher, abweichend, unbekannt = [], [], []
    benutzt = set()
    for z in zeilen:
        if z["betrag_cent"] <= 0:
            continue
        norm = re.sub(r"\s+", "", z["text"]).lower()
        treffer = [o for o in offen if o["nummer"].lower() in norm and o["id"] not in benutzt]
        if len(treffer) == 1:
            o = treffer[0]
            eintrag = {"beleg_id": o["id"], "nummer": o["nummer"], "firma": o["firma"], "rechnung_cent": o["brutto_cent"], "eingang_cent": z["betrag_cent"], "datum": z["datum"], "text": z["text"][:160]}
            if o["brutto_cent"] == z["betrag_cent"]:
                sicher.append(eintrag); benutzt.add(o["id"])
            else:
                abweichend.append(eintrag)
        elif len(treffer) > 1:
            abweichend.append({"beleg_id": None, "nummer": ", ".join(t["nummer"] for t in treffer), "firma": "mehrere Rechnungen", "rechnung_cent": None,
                               "eingang_cent": z["betrag_cent"], "datum": z["datum"], "text": z["text"][:160]})
        else:
            unbekannt.append({"eingang_cent": z["betrag_cent"], "datum": z["datum"], "text": z["text"][:160]})
    return {"sicher": sicher, "abweichend": abweichend, "unbekannt": unbekannt[:100]}
