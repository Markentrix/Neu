"""Buchungsvorlagen (Leistungen, Zusatzfragen, Arbeitszeiten) auf einen Kunden anwenden. Standardmäßig inaktiv und ohne Preise."""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import sitedienste as sd
from .buchungsvorlagen import BUCHUNGSVORLAGEN
from .db import tx
from .routes_sitedienste import LeistungIn, _leistung_neu
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")


@router.get("/buchungsvorlagen")
def liste(user: dict = Depends(require_admin)):
    return [{"code": c, "name": v["name"], "leistungen": [x["name"] for x in v["leistungen"]]} for c, v in BUCHUNGSVORLAGEN.items()]


class AnwendenIn(BaseModel):
    code: str = Field(max_length=30)


@router.post("/kunden/{kid}/buchungsvorlage")
def anwenden(kid: str, data: AnwendenIn, user: dict = Depends(require_admin)):
    v = BUCHUNGSVORLAGEN.get(data.code)
    if not v:
        raise HTTPException(404, "Unbekannte Vorlage.")
    with tx("system") as cur:
        try:
            cur.execute("SELECT id FROM kunden WHERE id=%s", (kid,))
        except Exception:
            raise HTTPException(404, "Kunde nicht gefunden.")
        if not cur.fetchone():
            raise HTTPException(404, "Kunde nicht gefunden.")
        cur.execute("SELECT count(*) AS n FROM website_leistungen WHERE kunden_id=%s", (kid,))
        if cur.fetchone()["n"]:
            raise HTTPException(409, "Dieser Kunde hat schon Leistungen. Die Vorlage legt nur bei einem leeren Stand an.")
        sd.zeile(cur, kid)
        plan = sd.plan_lesen(v["plan"])
        tage, von, bis = sd.plan_grenzen(plan)
        cur.execute("UPDATE website_dienste SET kal_wochenplan=%s::jsonb, kal_wochentage=%s, kal_von=%s, kal_bis=%s, geaendert_am=now() WHERE kunden_id=%s", (json.dumps(plan), tage, von, bis, kid))
        for l in v["leistungen"]:
            _leistung_neu(cur, kid, LeistungIn(**{"puffer_min": 0, "freigabe": False, **l, "aktiv": False}).pruefen())
        audit(cur, user, "buchungsvorlage_angewendet", kid, {"vorlage": data.code})
    return {"name": v["name"], "leistungen": len(v["leistungen"])}
