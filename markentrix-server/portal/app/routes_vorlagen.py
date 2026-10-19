"""Branchenvorlagen auf einen Kunden anwenden."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .branchenvorlagen import VORLAGEN
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")


@router.get("/vorlagen")
def liste(user: dict = Depends(require_admin)):
    return [{"code": c, "name": v["name"], "beschreibung": v["beschreibung"], "wissen": len(v["wissen"]), "beitraege": len(v["beitraege"]), "aufgaben": len(v["aufgaben"])}
            for c, v in VORLAGEN.items()]


class AnwendenIn(BaseModel):
    code: str = Field(max_length=30)


@router.post("/kunden/{kid}/vorlage")
def anwenden(kid: str, data: AnwendenIn, user: dict = Depends(require_admin)):
    v = VORLAGEN.get(data.code)
    if not v:
        raise HTTPException(404, "Unbekannte Vorlage.")
    with tx("admin") as cur:
        try:
            cur.execute("SELECT id, firma, ort, vorlage FROM kunden WHERE id=%s", (kid,))
        except Exception:
            raise HTTPException(404, "Kunde nicht gefunden.")
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Kunde nicht gefunden.")
        if k["vorlage"]:
            raise HTTPException(409, "Bei diesem Kunden wurde schon eine Vorlage angewendet.")
        ort = k["ort"] or "Ihrer Region"
        wissen = 0
        for bereich, schluessel, wert in v["wissen"]:
            cur.execute("""INSERT INTO wissensbasis (kunden_id, bereich, schluessel, wert, quelle, aktiv) VALUES (%s,%s,%s,%s,'vorlage',false)
                           ON CONFLICT (kunden_id, bereich, schluessel) DO NOTHING""", (kid, bereich, schluessel, wert))
            wissen += cur.rowcount
        for kanal, text in v["beitraege"]:
            cur.execute("INSERT INTO content_beitraege (kunden_id, kanal, text, status) VALUES (%s,%s,%s,'entwurf')", (kid, kanal, text.replace("{firma}", k["firma"]).replace("{ort}", ort)))
        cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
        a = cur.fetchone()
        for i, titel in enumerate(v["aufgaben"]):
            cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel) VALUES (%s,%s,%s,%s,'auto',%s) ON CONFLICT DO NOTHING""",
                        (kid, f"{k['firma']}: {titel}"[:200], a and a["email"], date.today() + timedelta(days=7 + 3 * i), f"vorlage-{data.code}-{i}-{kid}"))
        cur.execute("UPDATE kunden SET vorlage=%s, vorlage_am=now() WHERE id=%s", (data.code, kid))
        audit(cur, user, "vorlage_angewendet", kid, {"vorlage": data.code})
    return {"wissen": wissen, "beitraege": len(v["beitraege"]), "aufgaben": len(v["aufgaben"]), "name": v["name"]}
