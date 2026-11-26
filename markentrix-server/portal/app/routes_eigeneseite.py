"""Eigene Website (markentrix.de) im Portal: Domain, Google-Bewertungen und Einbau-Code ohne Kundenzugang.
Technisch ein interner Eintrag in "kunden" (Status "intern", ohne Login). Er taucht in keiner Kundenliste-Auswertung, Rechnung, Provision oder Ampel auf."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, sitedienste as sd
from .db import tx
from .publish import DOMAIN_RE
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin/eigene-seite")
FIRMA = "Markentrix (eigene Seite)"


def _kunde(cur):
    cur.execute("SELECT id FROM kunden WHERE status='intern'")
    r = cur.fetchone()
    return r["id"] if r else None


def _zustand(cur, kid) -> dict:
    z = sd.zeile(cur, kid)
    cur.execute("SELECT domain FROM domains WHERE kunden_id=%s AND status<>'gekuendigt' ORDER BY erstellt_am", (kid,))
    cache = z.get("bew_cache") or {}
    return {"eingerichtet": True, "kunden_id": str(kid), "site_id": z["site_id"], "domains": [r["domain"] for r in cur.fetchall()],
            "place_id": z.get("bew_place_id") or "", "bew_aktiv": bool(z.get("bew_aktiv")),
            "einbau": f'<script src="{config.BASE_URL}/static/js/site.js" data-site="{z["site_id"]}" defer></script>',
            "google": {"sterne": cache.get("sterne"), "anzahl": cache.get("anzahl"), "stand": z["bew_stand"].isoformat() if z.get("bew_stand") else None}}


@router.get("")
def lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        kid = _kunde(cur)
        return _zustand(cur, kid) if kid else {"eingerichtet": False}


class EigeneSeiteIn(BaseModel):
    domain: str = Field(default="", max_length=253)
    place_id: str = Field(default="", max_length=200)
    aktiv: bool = False


@router.put("")
def speichern(data: EigeneSeiteIn, user: dict = Depends(require_admin)):
    dom, pid = data.domain.strip().lower(), data.place_id.strip()
    if dom and not DOMAIN_RE.match(dom):
        raise HTTPException(400, "Die Domain ist ungültig (zum Beispiel markentrix.de).")
    if pid and not sd.PLACE_ID.match(pid):
        raise HTTPException(400, "Die Place-ID sieht ungültig aus. Sie beginnt meist mit „ChIJ“.")
    if data.aktiv and not pid:
        raise HTTPException(400, "Für die Live-Bewertungen wird die Place-ID gebraucht.")
    with tx("admin") as cur:
        kid = _kunde(cur)
        if not kid:
            cur.execute("INSERT INTO kunden (firma, status, referenzkunde) VALUES (%s,'intern',true) RETURNING id", (FIRMA,))
            kid = cur.fetchone()["id"]
        sd.zeile(cur, kid)
        if dom:
            cur.execute("INSERT INTO domains (kunden_id, domain) VALUES (%s,%s) ON CONFLICT (kunden_id, lower(domain)) DO NOTHING", (kid, dom))
        cur.execute("""UPDATE website_dienste SET bew_aktiv=%s, bew_place_id=%s, bew_cache=NULL, bew_stand=NULL, geaendert_am=now() WHERE kunden_id=%s""", (data.aktiv, pid or None, kid))
        audit(cur, user, "eigene_seite_gespeichert", kid, {"domain": dom, "aktiv": data.aktiv})
        return _zustand(cur, kid)
