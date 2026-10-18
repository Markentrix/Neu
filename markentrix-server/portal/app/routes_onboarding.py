
from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import onboarding
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")


def _pruefen(cur, kid):
    try:
        cur.execute("SELECT id FROM kunden WHERE id=%s", (kid,))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    if not cur.fetchone():
        raise HTTPException(404, "Kunde nicht gefunden.")


@router.get("/kunden/{kid}/onboarding")
def liste(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _pruefen(cur, kid)
        punkte = onboarding.lesen(cur, kid)
        cur.execute("SELECT status FROM kunden WHERE id=%s", (kid,))
        status = cur.fetchone()["status"]
    fertig = sum(1 for p in punkte if p["fertig"])
    return {"punkte": punkte, "fertig": fertig, "gesamt": len(punkte), "status": status}


class PunktIn(BaseModel):
    erledigt: bool | None = None
    notiz: str | None = Field(default=None, max_length=1000)


@router.patch("/kunden/{kid}/onboarding/{code}")
def aendern(kid: str, code: str, data: PunktIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _pruefen(cur, kid)
        cur.execute("""UPDATE onboarding_punkte SET erledigt=coalesce(%s,erledigt),
                              erledigt_am=CASE WHEN %s IS NULL THEN erledigt_am WHEN %s THEN now() ELSE NULL END,
                              notiz=coalesce(%s,notiz) WHERE kunden_id=%s AND code=%s RETURNING code""",
                    (data.erledigt, data.erledigt, data.erledigt, data.notiz, kid, code))
        if not cur.fetchone():
            raise HTTPException(404, "Punkt nicht gefunden.")
        audit(cur, user, "onboarding_punkt", kid, {"code": code, "erledigt": data.erledigt})
    return {"ok": True}


class NeuIn(BaseModel):
    titel: str = Field(min_length=1, max_length=200)


@router.post("/kunden/{kid}/onboarding")
def hinzufuegen(kid: str, data: NeuIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _pruefen(cur, kid)
        cur.execute("SELECT count(*) AS n FROM onboarding_punkte WHERE kunden_id=%s AND code LIKE 'x-%%'", (kid,))
        n = cur.fetchone()["n"] + 1
        cur.execute("INSERT INTO onboarding_punkte (kunden_id, code, titel, sortierung) VALUES (%s,%s,%s,500) ON CONFLICT DO NOTHING", (kid, f"x-{n}", data.titel.strip()))
        audit(cur, user, "onboarding_punkt_neu", kid)
    return {"ok": True}


@router.get("/onboarding/offen")
def offen(user: dict = Depends(require_admin)):
    """Kunden im Status 'onboarding' mit Fortschritt – für die Übersicht."""
    with tx("admin") as cur:
        cur.execute("SELECT id, kundennummer, firma FROM kunden WHERE status='onboarding' ORDER BY erstellt_am DESC LIMIT 50")
        kunden = cur.fetchall()
        out = []
        for k in kunden:
            punkte = onboarding.lesen(cur, k["id"])
            out.append({**k, "fertig": sum(1 for p in punkte if p["fertig"]), "gesamt": len(punkte)})
    return out
