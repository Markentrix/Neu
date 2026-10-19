"""Kunden-Frühwarnung: erkennt Kunden mit Kündigungsrisiko aus Anmeldungen, Anfragen, Zahlungen und Zufriedenheit."""
from fastapi import APIRouter, Depends

from .db import tx
from .security import require_admin

router = APIRouter(prefix="/api/admin")

SQL = """
SELECT k.id, k.kundennummer, k.firma, k.referenzkunde, k.erstellt_am,
  (SELECT max(b.letzter_login) FROM benutzer b WHERE b.kunden_id = k.id) AS login,
  (SELECT count(*) FROM anfragen a WHERE a.kunden_id = k.id AND a.status <> 'spam' AND a.erstellt_am > now() - interval '30 days') AS a30,
  (SELECT count(*) FROM anfragen a WHERE a.kunden_id = k.id AND a.status <> 'spam' AND a.erstellt_am <= now() - interval '30 days' AND a.erstellt_am > now() - interval '60 days') AS a60,
  (SELECT count(*) FROM belege b WHERE b.kunden_id = k.id AND b.art = 'rechnung' AND b.status IN ('gestellt','versendet') AND b.faellig_am < current_date) AS ueberfaellig,
  (SELECT coalesce(max(b.mahnstufe), 0) FROM belege b WHERE b.kunden_id = k.id AND b.art = 'rechnung' AND b.status IN ('gestellt','versendet') AND b.faellig_am < current_date) AS mahnstufe,
  (SELECT z.punkte FROM zufriedenheit z WHERE z.kunden_id = k.id ORDER BY z.erstellt_am DESC LIMIT 1) AS letzte_punkte,
  (SELECT count(*) FROM tickets t WHERE t.kunden_id = k.id AND t.status IN ('offen','in_arbeit') AND t.letzte_nachricht_von = 'kunde' AND t.geaendert_am < now() - interval '3 days') AS ticket_wartet
FROM kunden k WHERE k.status = 'aktiv' AND k.erstellt_am < now() - interval '14 days'
"""


def bewerten(r: dict, heute=None) -> tuple[int, list]:
    """Punktzahl 0–100 und die Gründe in Klartext."""
    from datetime import datetime, timezone
    jetzt = datetime.now(timezone.utc)
    punkte, gruende = 0, []
    if r["login"] is None:
        punkte += 25
        gruende.append("Hat sich noch nie im Portal angemeldet.")
    else:
        tage = (jetzt - r["login"]).days
        if tage > 45:
            punkte += 30
            gruende.append(f"Seit {tage} Tagen nicht mehr im Portal.")
        elif tage > 21:
            punkte += 15
            gruende.append(f"Seit {tage} Tagen nicht mehr im Portal.")
    if r["a30"] == 0 and r["a60"] > 0:
        punkte += 25
        gruende.append(f"Keine Anfragen mehr in den letzten 30 Tagen (davor {r['a60']}).")
    elif r["a60"] >= 4 and r["a30"] * 2 <= r["a60"]:
        punkte += 15
        gruende.append(f"Anfragen haben sich halbiert ({r['a60']} → {r['a30']}).")
    if r["ueberfaellig"]:
        punkte += 25 + (10 if r["mahnstufe"] >= 2 else 0)
        gruende.append(f"{r['ueberfaellig']} überfällige Rechnung" + ("en" if r["ueberfaellig"] > 1 else "") + (f" (Mahnstufe {r['mahnstufe']})." if r["mahnstufe"] else "."))
    if r["letzte_punkte"] is not None and r["letzte_punkte"] <= 6:
        punkte += 25
        gruende.append(f"Letzte Zufriedenheit nur {r['letzte_punkte']} von 10.")
    if r["ticket_wartet"]:
        punkte += 10
        gruende.append("Eine Nachricht des Kunden wartet seit über 3 Tagen auf Antwort.")
    return min(punkte, 100), gruende


def berechnen(cur) -> dict:
    cur.execute(SQL)
    alle = cur.fetchall()
    liste = []
    for r in alle:
        p, g = bewerten(r)
        stufe = "hoch" if p >= 50 else "mittel" if p >= 25 else "ok"
        if stufe != "ok":
            liste.append({"id": r["id"], "kundennummer": r["kundennummer"], "firma": r["firma"], "punkte": p, "stufe": stufe, "gruende": g})
    liste.sort(key=lambda x: -x["punkte"])
    return {"kunden": liste, "geprueft": len(alle), "hoch": sum(1 for x in liste if x["stufe"] == "hoch")}


@router.get("/fruehwarnung")
def fruehwarnung(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return berechnen(cur)
