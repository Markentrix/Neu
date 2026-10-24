"""Steuerung des Lead-Geschäfts im Admin: automatische Zuweisung, Reaktionszeit, Sperrliste."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import einstellungen, sperre, zuweisung
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin/vertrieb")


@router.get("/steuerung")
def steuerung(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        e = zuweisung.einstellung(cur)
        e["partner"] = [{"id": str(p["id"]), "name": p["name"], "offen": p["offen"]} for p in zuweisung.aktive_partner(cur)]
        cur.execute("SELECT count(*) AS n FROM sperrliste")
        e["sperrliste_anzahl"] = cur.fetchone()["n"]
    return e


class SteuerungIn(BaseModel):
    auto_zuweisung: bool = False
    reaktionsstunden: int = Field(default=4, ge=1, le=72)
    preise_sichtbar: bool = False
    vertrieb_angebote: bool = False


@router.put("/steuerung")
def steuerung_setzen(data: SteuerungIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "vertrieb", {"auto_zuweisung": data.auto_zuweisung, "reaktionsstunden": data.reaktionsstunden, "preise_sichtbar": data.preise_sichtbar, "vertrieb_angebote": data.vertrieb_angebote})
        audit(cur, user, "vertrieb_steuerung", None, {"auto_zuweisung": data.auto_zuweisung, "reaktionsstunden": data.reaktionsstunden, "vertrieb_angebote": data.vertrieb_angebote})
    return {"ok": True}


@router.get("/sperrliste")
def sperrliste(q: str = "", user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT id, art, wert, grund, quelle, erstellt_am FROM sperrliste WHERE %s='' OR wert ILIKE %s ORDER BY erstellt_am DESC LIMIT 200", (q, f"%{q.lower()}%"))
        return cur.fetchall()


class SperreIn(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=253)
    grund: str = "manuell"


@router.post("/sperrliste")
def sperrliste_neu(data: SperreIn, user: dict = Depends(require_admin)):
    if data.grund not in ("widerspruch", "abmeldung", "beschwerde", "manuell", "kein_interesse"):
        raise HTTPException(400, "Ungültiger Grund.")
    with tx("admin") as cur:
        n = sperre.eintragen(cur, data.grund, "manuell im Admin", data.email, data.telefon, data.website)
        if not sperre.schluessel(data.email, data.telefon, data.website):
            raise HTTPException(400, "Bitte E-Mail, Telefonnummer oder Website angeben (Freemail-Adressen zählen nur als E-Mail).")
        audit(cur, user, "sperrliste_neu", None, {"grund": data.grund, "neu": n})
    return {"neu": n}


@router.delete("/sperrliste/{sid}")
def sperrliste_weg(sid: int, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("DELETE FROM sperrliste WHERE id=%s RETURNING art", (sid,))
        if not cur.fetchone():
            raise HTTPException(404, "Eintrag nicht gefunden.")
        audit(cur, user, "sperrliste_weg", None, {"id": sid})
    return {"ok": True}
