import json

from psycopg import errors
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import config, einstellungen, zweifaktor
from .db import tx
from .einstellungen import entschluesseln, verschluesseln
from .security import _sicherheit, audit, current_user, rate_limit, require_admin, require_voll, verify_password

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
def admin_reset(bid: str, user: dict = Depends(require_voll)):
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


@router.get("/admin/sicherheit")
def sicherheit(user: dict = Depends(require_admin)):
    """Wer hat die Zwei-Faktor-Anmeldung eingerichtet? Plus Schalter, ob sie für Vertriebs-Zugänge Pflicht ist."""
    from .security import vertrieb_2fa_pflicht
    with tx("admin") as cur:
        cur.execute("""SELECT id, email, name, rolle, aktiv, totp_aktiv, letzter_login FROM benutzer WHERE rolle IN ('admin','vertrieb') AND aktiv
                       ORDER BY rolle, lower(email)""")
        konten = cur.fetchall()
    from .security import kunden_2fa_pflicht
    return {"vertrieb_pflicht": vertrieb_2fa_pflicht(True), "kunden_pflicht": kunden_2fa_pflicht(True), "admin_pflicht": config.ADMIN_2FA_PFLICHT, "lange_sitzung": bool(_sicherheit(True).get("lange_sitzung")), "offline_daten": bool(_sicherheit().get("offline_daten")), "konten": konten}


class SicherheitIn(BaseModel):
    vertrieb_2fa: bool | None = None
    kunden_2fa: bool | None = None
    lange_sitzung: bool | None = None
    offline_daten: bool | None = None


@router.put("/admin/sicherheit")
def sicherheit_speichern(data: SicherheitIn, user: dict = Depends(require_admin)):
    from .security import vertrieb_2fa_pflicht
    with tx("admin") as cur:
        alt = einstellungen.lesen(cur, "sicherheit")
        neu = {**alt}
        if data.vertrieb_2fa is not None:
            neu["vertrieb_2fa"] = data.vertrieb_2fa
            audit(cur, user, "sicherheit_vertrieb_2fa", None, {"pflicht": data.vertrieb_2fa})
        if data.kunden_2fa is not None:
            neu["kunden_2fa"] = data.kunden_2fa
            audit(cur, user, "sicherheit_kunden_2fa", None, {"pflicht": data.kunden_2fa})
        if data.lange_sitzung is not None:
            neu["lange_sitzung"] = data.lange_sitzung
            audit(cur, user, "sicherheit_lange_sitzung", None, {"erlaubt": data.lange_sitzung})
        if data.offline_daten is not None:
            neu["offline_daten"] = data.offline_daten
            audit(cur, user, "sicherheit_offline_daten", None, {"erlaubt": data.offline_daten})
        einstellungen.schreiben(cur, "sicherheit", neu)
    vertrieb_2fa_pflicht(True)
    return {"ok": True}
