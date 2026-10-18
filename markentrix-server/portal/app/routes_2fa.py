import json

from psycopg import errors
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import zweifaktor
from .db import tx
from .einstellungen import entschluesseln, verschluesseln
from .security import audit, client_ip, current_user, rate_limit, require_admin, verify_password

router = APIRouter(prefix="/api")


@router.get("/2fa")
def status(user: dict = Depends(current_user)):
    with tx("system") as cur:
        cur.execute("SELECT totp_aktiv, jsonb_array_length(totp_recovery) AS codes FROM benutzer WHERE id=%s", (user["id"],))
        r = cur.fetchone()
    return {"aktiv": r["totp_aktiv"], "notfallcodes_uebrig": r["codes"]}


@router.post("/2fa/start")
def start(request: Request, user: dict = Depends(current_user)):
    rate_limit("2fa-start:" + str(user["id"]), 10, 600)
    with tx("system") as cur:
        cur.execute("SELECT totp_aktiv FROM benutzer WHERE id=%s", (user["id"],))
        if cur.fetchone()["totp_aktiv"]:
            raise HTTPException(400, "Die Zwei-Faktor-Anmeldung ist schon aktiv. Zum Neueinrichten erst ausschalten.")
        g = zweifaktor.neues_geheimnis()
        cur.execute("UPDATE benutzer SET totp_secret=%s WHERE id=%s", (verschluesseln(g), user["id"]))
    u = zweifaktor.uri(g, user["email"])
    return {"geheimnis": g, "uri": u, "qr": zweifaktor.qr(u)}


class CodeIn(BaseModel):
    code: str = Field(max_length=40)


@router.post("/2fa/aktivieren")
def aktivieren(data: CodeIn, request: Request, user: dict = Depends(current_user)):
    rate_limit("2fa-akt:" + str(user["id"]), 10, 600)
    fehler = False
    with tx("system") as cur:
        cur.execute("SELECT totp_secret, totp_aktiv FROM benutzer WHERE id=%s", (user["id"],))
        r = cur.fetchone()
        g = entschluesseln(r["totp_secret"])
        if r["totp_aktiv"] or not g:
            raise HTTPException(400, "Bitte zuerst die Einrichtung starten.")
        k = zweifaktor.pruefen_code(g, data.code)
        if not k:
            fehler = True
        else:
            klar, gehasht = zweifaktor.notfallcodes()
            cur.execute("UPDATE benutzer SET totp_aktiv=true, totp_letzter_schritt=%s, totp_recovery=%s::jsonb WHERE id=%s", (k, json.dumps(gehasht), user["id"]))
            audit(cur, user, "2fa_aktiviert", user["kunden_id"])
    if fehler:
        raise HTTPException(400, "Der Code stimmt nicht. Bitte den aktuellen Code aus der App eingeben.")
    return {"ok": True, "notfallcodes": klar}


class AusIn(BaseModel):
    passwort: str = Field(max_length=200)
    code: str = Field(max_length=40)


@router.post("/2fa/deaktivieren")
def deaktivieren(data: AusIn, request: Request, user: dict = Depends(current_user)):
    rate_limit("2fa-aus:" + str(user["id"]), 8, 600)
    fehler = None
    with tx("system") as cur:
        cur.execute("SELECT passwort_hash, totp_secret, totp_letzter_schritt, totp_recovery, totp_aktiv FROM benutzer WHERE id=%s", (user["id"],))
        r = cur.fetchone()
        if not verify_password(data.passwort, r["passwort_hash"]):
            fehler = "Das Passwort stimmt nicht."
        elif not r["totp_aktiv"]:
            fehler = "Die Zwei-Faktor-Anmeldung ist nicht aktiv."
        elif not zweifaktor.pruefen_login(r, data.code)[0]:
            fehler = "Der Code stimmt nicht."
        else:
            cur.execute("UPDATE benutzer SET totp_aktiv=false, totp_secret=NULL, totp_recovery='[]'::jsonb, totp_letzter_schritt=0 WHERE id=%s", (user["id"],))
            audit(cur, user, "2fa_deaktiviert", user["kunden_id"])
    if fehler:
        raise HTTPException(400, fehler)
    return {"ok": True}


@router.post("/admin/benutzer/{bid}/2fa-zuruecksetzen")
def admin_reset(bid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE benutzer SET totp_aktiv=false, totp_secret=NULL, totp_recovery='[]'::jsonb, totp_letzter_schritt=0 WHERE id=%s RETURNING kunden_id", (bid,))
            r = cur.fetchone()
            if r:
                audit(cur, user, "2fa_zurueckgesetzt", r["kunden_id"], {"benutzer": bid})
    except errors.InvalidTextRepresentation:
        r = None
    if not r:
        raise HTTPException(404, "Benutzer nicht gefunden.")
    return {"ok": True}
