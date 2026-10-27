import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from . import config, mailer, zweifaktor
from .db import tx
from .security import (COOKIE, EMAIL_RE, _sicherheit, _zwei_faktor_fehlt, audit, check_password_rules, client_ip, current_user, hash_password,
                       new_token, rate_limit, sitzung_stunden, token_hash, verify_password)

router = APIRouter(prefix="/api")


class LoginIn(BaseModel):
    email: str
    password: str
    code: str | None = None
    bleiben: bool = False


class EinladungIn(BaseModel):
    token: str
    password: str


@router.post("/login")
def login(data: LoginIn, request: Request, response: Response):
    rate_limit("login:" + client_ip(request))
    email = data.email.strip().lower()
    if not EMAIL_RE.match(email) or len(data.password) > 200:
        raise HTTPException(401, "E-Mail oder Passwort stimmt nicht.")
    with tx("system") as cur:
        cur.execute("SELECT id, passwort_hash, rolle, kunden_id, (aktiv AND (zugang_bis IS NULL OR zugang_bis >= current_date)) AS aktiv, gesperrt_bis, fehlversuche, totp_aktiv, totp_secret, totp_letzter_schritt, totp_recovery FROM benutzer WHERE lower(email)=%s", (email,))
        u = cur.fetchone()
        gesperrt = u and u["gesperrt_bis"] and u["gesperrt_bis"] > datetime.now(timezone.utc)
        ok = verify_password(data.password, u["passwort_hash"] if u else None)
        pw_ok = ok
        fehler = None
        zwei = False
        if u and ok and u["aktiv"] and not gesperrt and u["totp_aktiv"]:
            if not data.code:
                zwei = True
            else:
                gut, aend = zweifaktor.pruefen_login(u, data.code)
                if gut:
                    for sp, wert in aend.items():
                        cur.execute(f"UPDATE benutzer SET {sp}=%s{'::jsonb' if sp == 'totp_recovery' else ''} WHERE id=%s", (json.dumps(wert) if sp == 'totp_recovery' else wert, u["id"]))
                else:
                    ok = False
        if zwei:
            pass
        elif not u or not ok or not u["aktiv"] or gesperrt:
            if gesperrt:
                fehler = (429, "Zu viele Fehlversuche. Das Konto ist für 15 Minuten gesperrt.")
            else:
                if u:
                    n = u["fehlversuche"] + 1
                    cur.execute("UPDATE benutzer SET fehlversuche=%s, gesperrt_bis=CASE WHEN %s>=5 THEN now()+interval '15 minutes' END WHERE id=%s", (n, n, u["id"]))
                fehler = (401, "Der Code stimmt nicht." if (u and pw_ok and data.code and u["totp_aktiv"]) else "E-Mail oder Passwort stimmt nicht.")
    if fehler:
        # erst nach dem Commit abbrechen, sonst wird der Fehlversuch zurückgerollt
        raise HTTPException(*fehler)
    if zwei:
        return {"zwei_faktor": True}
    with tx("system") as cur:
        tok = new_token()
        stunden = sitzung_stunden(u["rolle"], data.bleiben)
        cur.execute("INSERT INTO sitzungen (token_hash, benutzer_id, ablauf, ip) VALUES (%s,%s,now()+make_interval(hours=>%s),%s)",
                    (token_hash(tok), u["id"], stunden, client_ip(request)))
        cur.execute("UPDATE benutzer SET fehlversuche=0, gesperrt_bis=NULL, letzter_login=now() WHERE id=%s", (u["id"],))
        audit(cur, {"id": u["id"]}, "login", u["kunden_id"])
        cur.execute("DELETE FROM sitzungen WHERE ablauf < now()")
    response.set_cookie(COOKIE, tok, max_age=stunden * 3600, httponly=True, secure=config.COOKIE_SECURE, samesite="lax", path="/")
    return {"rolle": u["rolle"], "ziel": {"admin": "/admin", "vertrieb": "/vertrieb"}.get(u["rolle"], "/app")}


@router.get("/public/login-optionen")
def login_optionen():
    """Für die Anmeldeseite: darf „Angemeldet bleiben“ angeboten werden?"""
    return {"bleiben": bool(_sicherheit().get("lange_sitzung"))}


@router.post("/logout")
def logout(request: Request, response: Response):
    t = request.cookies.get(COOKIE)
    if t:
        with tx("system") as cur:
            cur.execute("DELETE FROM sitzungen WHERE token_hash=%s", (token_hash(t),))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"], "rolle": user["rolle"], "kunden_id": user["kunden_id"], "vertriebspartner_id": user["vertriebspartner_id"], "zwei_faktor": user["totp_aktiv"], "zwei_faktor_pflicht": _zwei_faktor_fehlt(user), "kunden_rolle": user["kunden_rolle"], "admin_rechte": user.get("admin_rechte"), "offline_daten": bool(_sicherheit().get("offline_daten"))}


@router.get("/einladung/{token}")
def einladung_pruefen(token: str):
    with tx("system") as cur:
        cur.execute("SELECT email FROM benutzer WHERE einladung_token_hash=%s AND einladung_ablauf > now() AND aktiv", (token_hash(token),))
        u = cur.fetchone()
    if not u:
        raise HTTPException(404, "Der Einladungslink ist ungültig oder abgelaufen.")
    return {"email": u["email"]}


@router.post("/einladung")
def einladung_annehmen(data: EinladungIn, request: Request):
    rate_limit("einl:" + client_ip(request), 20, 300)
    check_password_rules(data.password)
    with tx("system") as cur:
        cur.execute("SELECT id, kunden_id FROM benutzer WHERE einladung_token_hash=%s AND einladung_ablauf > now() AND aktiv", (token_hash(data.token),))
        u = cur.fetchone()
        if not u:
            raise HTTPException(404, "Der Einladungslink ist ungültig oder abgelaufen.")
        cur.execute("UPDATE benutzer SET passwort_hash=%s, einladung_token_hash=NULL, einladung_ablauf=NULL, fehlversuche=0, gesperrt_bis=NULL WHERE id=%s",
                    (hash_password(data.password), u["id"]))
        cur.execute("DELETE FROM sitzungen WHERE benutzer_id=%s", (u["id"],))  # alte Sitzungen enden
        audit(cur, {"id": u["id"]}, "passwort_gesetzt", u["kunden_id"])
    return {"ok": True}


class VergessenIn(BaseModel):
    email: str


@router.post("/passwort-vergessen")
def passwort_vergessen(data: VergessenIn, request: Request):
    """Antwortet immer gleich, damit niemand erraten kann, welche Adressen es gibt."""
    rate_limit("vergessen:" + client_ip(request), 5, 600)
    email = data.email.strip().lower()
    antwort = {"ok": True, "hinweis": "Wenn es dazu ein Konto gibt, ist eine E-Mail mit einem Link unterwegs."}
    if not EMAIL_RE.match(email):
        return antwort
    rate_limit("vergessen-mail:" + email, 3, 3600)
    with tx("system") as cur:
        cur.execute("SELECT id FROM benutzer WHERE lower(email)=%s AND aktiv AND passwort_hash IS NOT NULL", (email,))
        u = cur.fetchone()
        if not u:
            return antwort
        tok = new_token()
        cur.execute("UPDATE benutzer SET einladung_token_hash=%s, einladung_ablauf=now()+make_interval(hours=>%s) WHERE id=%s", (token_hash(tok), config.RESET_HOURS, u["id"]))
        audit(cur, {"id": u["id"]}, "passwort_vergessen")
    mailer.passwort_zuruecksetzen(email, f"{config.BASE_URL}/einladung?token={tok}")
    return antwort
