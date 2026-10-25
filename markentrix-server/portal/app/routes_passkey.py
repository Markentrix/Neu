"""Anmeldung mit Passkey (Fingerabdruck, Face-ID, Geräte-PIN). Einrichten im Konto, Anmelden auf der Anmeldeseite ohne Passwort."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from . import config, passkey
from .db import tx
from .security import COOKIE, audit, client_ip, current_user, new_token, rate_limit, token_hash

router = APIRouter(prefix="/api/passkey")
MAX_PRO_BENUTZER = 10


@router.get("")
def liste(user: dict = Depends(current_user)):
    with tx("system") as cur:
        cur.execute("SELECT id, name, erstellt_am, zuletzt_am FROM passkeys WHERE benutzer_id=%s ORDER BY erstellt_am", (user["id"],))
        return cur.fetchall()


@router.post("/registrieren/start")
def reg_start(user: dict = Depends(current_user)):
    rate_limit("passkey-reg:" + str(user["id"]), 20, 3600)
    with tx("system") as cur:
        cur.execute("SELECT credential_id FROM passkeys WHERE benutzer_id=%s", (user["id"],))
        vorhandene = [{"type": "public-key", "id": passkey.b64u(bytes(r["credential_id"]))} for r in cur.fetchall()]
    if len(vorhandene) >= MAX_PRO_BENUTZER:
        raise HTTPException(400, f"Es sind höchstens {MAX_PRO_BENUTZER} Passkeys möglich. Bitte zuerst einen entfernen.")
    return {"challenge": passkey.neue_aufforderung("registrieren", user["id"]), "rp": {"id": passkey.rp_id(), "name": "Markentrix Portal"},
            "user": {"id": passkey.b64u(str(user["id"]).encode()), "name": user["email"], "displayName": user.get("name") or user["email"]},
            "pubKeyCredParams": [{"type": "public-key", "alg": -7}, {"type": "public-key", "alg": -257}],
            "excludeCredentials": vorhandene, "timeout": 60000, "attestation": "none",
            "authenticatorSelection": {"residentKey": "required", "requireResidentKey": True, "userVerification": "required"}}


class RegIn(BaseModel):
    clientDataJSON: str = Field(max_length=4000)
    attestationObject: str = Field(max_length=20000)
    name: str | None = Field(default=None, max_length=60)


@router.post("/registrieren/fertig")
def reg_fertig(data: RegIn, user: dict = Depends(current_user)):
    try:
        cid, der, alg, zaehler, ch = passkey.registrierung_pruefen(data.clientDataJSON, data.attestationObject)
        if passkey.aufforderung_verbrauchen(ch, "registrieren") != user["id"]:
            raise passkey.PasskeyFehler("Die Anfrage gehört zu einem anderen Konto.")
    except passkey.PasskeyFehler as e:
        raise HTTPException(400, str(e))
    name = (data.name or "").strip() or "Dieses Gerät"
    with tx("system") as cur:
        cur.execute("SELECT count(*) AS n FROM passkeys WHERE benutzer_id=%s", (user["id"],))
        if cur.fetchone()["n"] >= MAX_PRO_BENUTZER:
            raise HTTPException(400, "Zu viele Passkeys.")
        cur.execute("""INSERT INTO passkeys (benutzer_id, credential_id, public_key, alg, sign_count, name) VALUES (%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (credential_id) DO NOTHING RETURNING id""", (user["id"], cid, der, alg, zaehler, name[:60]))
        neu = cur.fetchone()
        if not neu:
            raise HTTPException(400, "Dieser Passkey ist schon eingerichtet.")
        audit(cur, user, "passkey_eingerichtet", user.get("kunden_id"), {"name": name[:60]})
    return {"ok": True, "id": str(neu["id"])}


@router.delete("/{pid}")
def entfernen(pid: str, user: dict = Depends(current_user)):
    with tx("system") as cur:
        try:
            cur.execute("DELETE FROM passkeys WHERE id=%s AND benutzer_id=%s", (pid, user["id"]))
        except Exception:
            raise HTTPException(404, "Passkey nicht gefunden.")
        if not cur.rowcount:
            raise HTTPException(404, "Passkey nicht gefunden.")
        audit(cur, user, "passkey_entfernt", user.get("kunden_id"), {})
    return {"ok": True}


# ---------------------------------------------------------------- Anmeldung (öffentlich)
@router.post("/login/start")
def login_start(request: Request):
    rate_limit("passkey-login:" + client_ip(request), 60, 300)
    return {"challenge": passkey.neue_aufforderung("login"), "rpId": passkey.rp_id(), "timeout": 60000, "userVerification": "required", "allowCredentials": []}


class LoginIn(BaseModel):
    id: str = Field(max_length=1400)
    clientDataJSON: str = Field(max_length=4000)
    authenticatorData: str = Field(max_length=2000)
    signature: str = Field(max_length=2000)


@router.post("/login/fertig")
def login_fertig(data: LoginIn, request: Request, response: Response):
    rate_limit("passkey-login:" + client_ip(request), 60, 300)
    try:
        cid = passkey.unb64u(data.id)
    except Exception:
        raise HTTPException(401, "Die Anmeldung hat nicht geklappt.")
    fehler = None
    with tx("system") as cur:
        cur.execute("""SELECT p.id AS pid, p.public_key, p.alg, p.sign_count, b.id, b.rolle, b.kunden_id, b.gesperrt_bis,
                              (b.aktiv AND (b.zugang_bis IS NULL OR b.zugang_bis >= current_date)
                               AND (b.vertriebspartner_id IS NULL OR NOT EXISTS (SELECT 1 FROM vertriebspartner v WHERE v.id = b.vertriebspartner_id AND v.status = 'beendet'))) AS aktiv
                       FROM passkeys p JOIN benutzer b ON b.id = p.benutzer_id WHERE p.credential_id=%s""", (cid,))
        u = cur.fetchone()
        try:
            if not u:
                raise passkey.PasskeyFehler("Dieser Passkey ist nicht (mehr) eingerichtet.")
            zaehler, ch = passkey.anmeldung_pruefen(u, data.clientDataJSON, data.authenticatorData, data.signature)
            passkey.aufforderung_verbrauchen(ch, "login")
            if not u["aktiv"] or (u["gesperrt_bis"] and u["gesperrt_bis"] > datetime.now(timezone.utc)):
                raise passkey.PasskeyFehler("Dieses Konto ist gerade nicht freigegeben.")
        except passkey.PasskeyFehler as e:
            fehler = str(e)
        if not fehler:
            cur.execute("UPDATE passkeys SET sign_count=%s, zuletzt_am=now() WHERE id=%s", (zaehler, u["pid"]))
            tok = new_token()
            cur.execute("INSERT INTO sitzungen (token_hash, benutzer_id, ablauf, ip, passkey) VALUES (%s,%s,now()+make_interval(hours=>%s),%s,true)",
                        (token_hash(tok), u["id"], config.SESSION_HOURS, client_ip(request)))
            cur.execute("UPDATE benutzer SET fehlversuche=0, gesperrt_bis=NULL, letzter_login=now() WHERE id=%s", (u["id"],))
            audit(cur, {"id": u["id"]}, "login_passkey", u["kunden_id"])
            cur.execute("DELETE FROM sitzungen WHERE ablauf < now()")
    if fehler:
        raise HTTPException(401, fehler)
    response.set_cookie(COOKIE, tok, max_age=config.SESSION_HOURS * 3600, httponly=True, secure=config.COOKIE_SECURE, samesite="lax", path="/")
    return {"rolle": u["rolle"], "ziel": {"admin": "/admin", "vertrieb": "/vertrieb"}.get(u["rolle"], "/app")}
