"""AGB-Verwaltung (Admin → Einstellungen) und Bestätigung durch Kunden bei der Anmeldung im Portal."""
import base64
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import agb
from .db import tx
from .security import audit, client_ip, rate_limit, require_admin, require_inhaber

router = APIRouter(prefix="/api")
MAX = 6 * 1024 * 1024


def _pdf(daten: bytes, name: str) -> Response:
    return Response(daten, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"'})


class AgbIn(BaseModel):
    version: str = Field(min_length=1, max_length=60)
    datei_base64: str = Field(max_length=9_000_000)
    datei_name: str = Field(default="AGB.pdf", max_length=200)
    mitsenden: bool = True
    login_pflicht: bool = True


@router.get("/admin/agb")
def liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT v.id, v.version, v.dateiname, v.aktiv, v.mitsenden, v.login_pflicht, v.erstellt_am, v.hochgeladen_von,
                              (SELECT count(DISTINCT z.kunden_id) FROM agb_zustimmungen z WHERE z.agb_id=v.id) AS bestaetigt
                       FROM agb_versionen v ORDER BY v.erstellt_am DESC""")
        versionen = cur.fetchall()
        cur.execute("SELECT count(*) AS n FROM kunden WHERE status IN ('aktiv','onboarding')")
        kunden = cur.fetchone()["n"]
        cur.execute("""SELECT z.zeit, z.version, z.benutzer, z.ip, k.firma, k.kundennummer FROM agb_zustimmungen z JOIN kunden k ON k.id=z.kunden_id
                       ORDER BY z.zeit DESC LIMIT 100""")
        zustimmungen = cur.fetchall()
    return {"versionen": versionen, "kunden": kunden, "zustimmungen": zustimmungen}


@router.post("/admin/agb")
def hochladen(data: AgbIn, user: dict = Depends(require_admin)):
    try:
        roh = base64.b64decode(data.datei_base64.split(",")[-1], validate=True)
    except Exception:
        raise HTTPException(400, "Die Datei konnte nicht gelesen werden.")
    if not roh.startswith(b"%PDF"):
        raise HTTPException(400, "Bitte die AGB als PDF hochladen.")
    if len(roh) > MAX:
        raise HTTPException(400, "Die Datei ist zu groß (maximal 6 MB).")
    name = "".join(c if c.isalnum() or c in "._- " else "_" for c in data.datei_name)[:120] or "AGB.pdf"
    with tx("admin") as cur:
        cur.execute("UPDATE agb_versionen SET aktiv=false WHERE aktiv")
        cur.execute("""INSERT INTO agb_versionen (version, dateiname, datei, sha256, aktiv, mitsenden, login_pflicht, hochgeladen_von)
                       VALUES (%s,%s,%s,%s,true,%s,%s,%s) RETURNING id""",
                    (data.version.strip(), name, roh, hashlib.sha256(roh).hexdigest(), data.mitsenden, data.login_pflicht, user["email"]))
        vid = cur.fetchone()["id"]
        audit(cur, user, "agb_hochgeladen", None, {"version": data.version.strip(), "mitsenden": data.mitsenden, "login_pflicht": data.login_pflicht})
    return {"ok": True, "id": str(vid)}


class AgbFlags(BaseModel):
    mitsenden: bool | None = None
    login_pflicht: bool | None = None
    aktiv: bool | None = None


@router.put("/admin/agb/{vid}")
def aendern(vid: str, data: AgbFlags, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT id FROM agb_versionen WHERE id=%s", (vid,))
        if not cur.fetchone():
            raise HTTPException(404, "Version nicht gefunden.")
        if data.aktiv is True:
            cur.execute("UPDATE agb_versionen SET aktiv=false WHERE aktiv AND id<>%s", (vid,))
        for feld in ("mitsenden", "login_pflicht", "aktiv"):
            wert = getattr(data, feld)
            if wert is not None:
                cur.execute(f"UPDATE agb_versionen SET {feld}=%s WHERE id=%s", (wert, vid))
        audit(cur, user, "agb_geaendert", None, {"id": vid})
    return {"ok": True}


@router.get("/admin/agb/{vid}/datei")
def datei_admin(vid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT dateiname, datei FROM agb_versionen WHERE id=%s", (vid,))
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Version nicht gefunden.")
    return _pdf(bytes(r["datei"]), r["dateiname"])


@router.get("/agb.pdf")
def datei_oeffentlich(request: Request):
    """Aktuelle AGB zum Ansehen (Link auf Angebotsseiten und in der Bestätigung)."""
    rate_limit("agb:" + client_ip(request), 60, 60)
    with tx("system") as cur:
        cur.execute("SELECT dateiname, datei FROM agb_versionen WHERE aktiv")
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Es sind keine AGB hinterlegt.")
    return _pdf(bytes(r["datei"]), r["dateiname"])


class ZustimmenIn(BaseModel):
    bestaetigt: bool = False
    agb_id: str


@router.post("/kunde/agb/zustimmen")
def zustimmen(data: ZustimmenIn, request: Request, user: dict = Depends(require_inhaber)):
    if not data.bestaetigt:
        raise HTTPException(400, "Bitte bestätigen Sie die AGB mit dem Haken.")
    with tx("system") as cur:
        a = agb.aktiv(cur)
        if not a or str(a["id"]) != data.agb_id:
            raise HTTPException(409, "Die AGB wurden inzwischen aktualisiert. Bitte laden Sie die Seite neu.")
        cur.execute("""INSERT INTO agb_zustimmungen (kunden_id, agb_id, benutzer_id, benutzer, version, sha256, ip, user_agent)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (user["kunden_id"], a["id"], user["id"], user["email"], a["version"], a["sha256"], client_ip(request), (request.headers.get("user-agent") or "")[:300]))
        audit(cur, user, "agb_bestaetigt", user["kunden_id"], {"version": a["version"]})
    return {"ok": True}
