"""Anmeldung von Geräten für Push-Nachrichten (alle Rollen)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, push
from .db import tx
from .security import current_user, rate_limit

router = APIRouter(prefix="/api/push")


@router.get("/status")
def status(user: dict = Depends(current_user)):
    with tx("system") as cur:
        k = push.schluessel(cur)
        cur.execute("SELECT count(*) AS n FROM push_abos WHERE benutzer_id=%s", (user["id"],))
        n = cur.fetchone()["n"]
    return {"schluessel": k["public"], "geraete": n}


class AboIn(BaseModel):
    endpoint: str = Field(min_length=20, max_length=1000, pattern=r"^https?://")
    p256dh: str = Field(min_length=20, max_length=200)
    auth: str = Field(min_length=8, max_length=100)
    geraet: str = Field(default="", max_length=200)


@router.post("/abo")
def anmelden(data: AboIn, user: dict = Depends(current_user)):
    rate_limit("pushabo:" + str(user["id"]), 20, 3600)
    if not data.endpoint.startswith("https://") and not config.PUSH_HTTP_ERLAUBT:
        raise HTTPException(400, "Ungültige Geräte-Anmeldung.")
    try:
        if len(push._unb64(data.p256dh)) != 65 or len(push._unb64(data.auth)) < 8:
            raise ValueError
        from cryptography.hazmat.primitives.asymmetric import ec
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), push._unb64(data.p256dh))
    except Exception:
        raise HTTPException(400, "Ungültige Geräte-Anmeldung.")
    with tx("system") as cur:
        cur.execute("""INSERT INTO push_abos (benutzer_id, endpoint, p256dh, auth, geraet) VALUES (%s,%s,%s,%s,%s)
                       ON CONFLICT (endpoint) DO UPDATE SET benutzer_id=EXCLUDED.benutzer_id, p256dh=EXCLUDED.p256dh, auth=EXCLUDED.auth, geraet=EXCLUDED.geraet, fehler=0""",
                    (user["id"], data.endpoint, data.p256dh, data.auth, data.geraet[:200] or None))
    return {"ok": True}


class AboWeg(BaseModel):
    endpoint: str = Field(max_length=1000)


@router.post("/abmelden")
def abmelden(data: AboWeg, user: dict = Depends(current_user)):
    with tx("system") as cur:
        cur.execute("DELETE FROM push_abos WHERE endpoint=%s AND benutzer_id=%s", (data.endpoint, user["id"]))
    return {"ok": True}


@router.post("/test")
def test(user: dict = Depends(current_user)):
    rate_limit("pushtest:" + str(user["id"]), 5, 600)
    push.senden([user["id"]], "Markentrix", "Benachrichtigungen funktionieren auf diesem Gerät.", "/", "test")
    return {"ok": True}
