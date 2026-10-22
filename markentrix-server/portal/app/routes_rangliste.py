"""Rangliste im Partnerportal (Monat): Anrufe, Termine, Abschlüsse. Nur wenn der Admin sie einschaltet; Namen nur mit Zustimmung des Teams (sonst „Vertriebler 2“)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from . import einstellungen
from .db import tx
from .security import audit, require_admin, require_vertrieb

vertrieb = APIRouter(prefix="/api/vertrieb")
admin = APIRouter(prefix="/api/admin/vertrieb/rangliste-einstellung")
TITEL = {"anrufe": "Anrufe", "termine": "Termine", "abschluesse": "Abschlüsse"}


def einst(cur) -> dict:
    return {"aktiv": False, "namen": False, **(einstellungen.lesen(cur, "rangliste") or {})}


def werte(cur) -> list:
    cur.execute("""SELECT v.id, v.name,
                     (SELECT count(*) FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=v.id AND a.art='anruf' AND a.zeit >= date_trunc('month', now())) AS anrufe,
                     (SELECT count(*) FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=v.id AND a.art='termin' AND a.zeit >= date_trunc('month', now())) AS termine,
                     (SELECT count(*) FROM kunden k WHERE k.vertriebspartner_id=v.id AND k.erstellt_am >= date_trunc('month', now())) AS abschluesse
                   FROM vertriebspartner v WHERE v.status='aktiv' ORDER BY v.erstellt_am""")
    return cur.fetchall()


def bauen(zeilen: list, ich, namen: bool) -> dict:
    out = {}
    nummer = {str(z["id"]): i + 1 for i, z in enumerate(zeilen)}
    for art in TITEL:
        sortiert = sorted(zeilen, key=lambda z: -z[art])
        rang, letzte, liste = 0, None, []
        for i, z in enumerate(sortiert):
            if z[art] != letzte:
                rang, letzte = i + 1, z[art]
            liste.append((rang, z))
        eigene = str(ich)
        zeigen = [(r, z) for r, z in liste if (z[art] > 0 and r <= 5) or str(z["id"]) == eigene]
        out[art] = [{"rang": r, "name": "Du" if str(z["id"]) == eigene else ((z["name"] or "").split()[0] if namen and z["name"] else f"Vertriebler {nummer[str(z['id'])]}"), "wert": z[art], "ich": str(z["id"]) == eigene} for r, z in zeigen]
    return out


@vertrieb.get("/rangliste")
def rangliste(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        s = einst(cur)
        if not s["aktiv"]:
            return {"aktiv": False}
        zeilen = werte(cur)
    return {"aktiv": True, "titel": TITEL, "listen": bauen(zeilen, user["vertriebspartner_id"], s["namen"]), "teilnehmer": len(zeilen)}


class RangIn(BaseModel):
    aktiv: bool = False
    namen: bool = False


@admin.get("")
def lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return einst(cur)


@admin.put("")
def speichern(data: RangIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "rangliste", data.model_dump())
        audit(cur, user, "einstellungen_rangliste", None, data.model_dump())
    return {"ok": True}
