"""Staffelpreise je Vertragsmonat: z. B. Monat 1 = 149 €, Monat 2 = 199 €, ab Monat 3 = 249 €.
Gespeichert als Liste [{"ab_monat": 1, "cent": 14900}, ...]. Der Preis der letzten Stufe ist der Regelpreis (monatlich_cent)."""
from fastapi import HTTPException


def _eur(c: int) -> str:
    return f"{c / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def pruefen(eingabe) -> list | None:
    """Prüft und ordnet die Stufen. Leere Eingabe = keine Staffel. Erste Stufe muss bei Monat 1 beginnen."""
    if not eingabe:
        return None
    try:
        stufen = sorted(({"ab_monat": int(s["ab_monat"]), "cent": int(s["cent"])} for s in eingabe), key=lambda s: s["ab_monat"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, "Die Staffel ist ungültig.")
    if len(stufen) > 12 or stufen[0]["ab_monat"] != 1:
        raise HTTPException(400, "Die Staffel braucht höchstens 12 Stufen und muss bei Monat 1 beginnen.")
    if any(s["cent"] < 0 or s["ab_monat"] < 1 or s["ab_monat"] > 120 for s in stufen) or len({s["ab_monat"] for s in stufen}) != len(stufen):
        raise HTTPException(400, "Jeder Monat darf nur einmal vorkommen, Beträge dürfen nicht negativ sein.")
    return stufen if len(stufen) > 1 else None


def regelpreis(stufen: list) -> int:
    return stufen[-1]["cent"]


def preis_im_monat(stufen, regel: int, vm: int) -> int:
    if not stufen:
        return int(regel)
    gueltig = [s for s in stufen if s["ab_monat"] <= vm]
    return int(gueltig[-1]["cent"]) if gueltig else int(regel)


def text(stufen) -> str:
    """„Monat 1: 149,00 €, Monat 2: 199,00 €, ab Monat 3: 249,00 €“"""
    if not stufen:
        return ""
    teile = []
    for i, s in enumerate(stufen):
        letzte = i == len(stufen) - 1
        teile.append(("ab " if letzte else "") + f"Monat {s['ab_monat']}: {_eur(int(s['cent']))}")
    return ", ".join(teile)


def skaliert(stufen, rechne) -> list | None:
    return [{"ab_monat": s["ab_monat"], "cent": rechne(int(s["cent"]))} for s in stufen] if stufen else None


def monat_nr(beginn, start) -> int:
    """Vertragsmonat (1 = Monat des Beginns) für einen Zeitraum, der am Datum start beginnt."""
    return max(1, (start.year - beginn.year) * 12 + start.month - beginn.month + 1)
