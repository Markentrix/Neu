from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from . import config
from .db import tx
from .security import (COOKIE, EMAIL_RE, audit, check_password_rules, client_ip, current_user, hash_password,
                       new_token, rate_limit, token_hash, verify_password)

router = APIRouter(prefix="/api")


class LoginIn(BaseModel):
    email: str
    password: str


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
        cur.execute("SELECT id, passwort_hash, rolle, kunden_id, aktiv, gesperrt_bis, fehlversuche FROM benutzer WHERE lower(email)=%s", (email,))
        u = cur.fetchone()
        gesperrt = u and u["gesperrt_bis"] and u["gesperrt_bis"] > datetime.now(timezone.utc)
        ok = verify_password(data.password, u["passwort_hash"] if u else None)
        fehler = None
        if not u or not ok or not u["aktiv"] or gesperrt:
            if gesperrt:
                fehler = (429, "Zu viele Fehlversuche. Das Konto ist für 15 Minuten gesperrt.")
            else:
                if u:
                    n = u["fehlversuche"] + 1
                    cur.execute("UPDATE benutzer SET fehlversuche=%s, gesperrt_bis=CASE WHEN %s>=5 THEN now()+interval '15 minutes' END WHERE id=%s", (n, n, u["id"]))
                fehler = (401, "E-Mail oder Passwort stimmt nicht.")
    if fehler:
        # erst nach dem Commit abbrechen, sonst wird der Fehlversuch zurückgerollt
        raise HTTPException(*fehler)
    with tx("system") as cur:
        tok = new_token()
        cur.execute("INSERT INTO sitzungen (token_hash, benutzer_id, ablauf, ip) VALUES (%s,%s,now()+make_interval(hours=>%s),%s)",
                    (token_hash(tok), u["id"], config.SESSION_HOURS, client_ip(request)))
        cur.execute("UPDATE benutzer SET fehlversuche=0, gesperrt_bis=NULL, letzter_login=now() WHERE id=%s", (u["id"],))
        audit(cur, {"id": u["id"]}, "login", u["kunden_id"])
        cur.execute("DELETE FROM sitzungen WHERE ablauf < now()")
    response.set_cookie(COOKIE, tok, max_age=config.SESSION_HOURS * 3600, httponly=True, secure=config.COOKIE_SECURE, samesite="lax", path="/")
    return {"rolle": u["rolle"], "ziel": "/admin" if u["rolle"] == "admin" else "/app"}


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
    return {"id": user["id"], "email": user["email"], "name": user["name"], "rolle": user["rolle"], "kunden_id": user["kunden_id"]}


@router.get("/einladung/{token}")
def einladung_pruefen(token: str):
    with tx("system") as cur:
        cur.execute("SELECT email FROM benutzer WHERE einladung_token_hash=%s AND einladung_ablauf > now()", (token_hash(token),))
        u = cur.fetchone()
    if not u:
        raise HTTPException(404, "Der Einladungslink ist ungültig oder abgelaufen.")
    return {"email": u["email"]}


@router.post("/einladung")
def einladung_annehmen(data: EinladungIn, request: Request):
    rate_limit("einl:" + client_ip(request), 20, 300)
    check_password_rules(data.password)
    with tx("system") as cur:
        cur.execute("SELECT id, kunden_id FROM benutzer WHERE einladung_token_hash=%s AND einladung_ablauf > now()", (token_hash(data.token),))
        u = cur.fetchone()
        if not u:
            raise HTTPException(404, "Der Einladungslink ist ungültig oder abgelaufen.")
        cur.execute("UPDATE benutzer SET passwort_hash=%s, einladung_token_hash=NULL, einladung_ablauf=NULL, aktiv=true, fehlversuche=0, gesperrt_bis=NULL WHERE id=%s",
                    (hash_password(data.password), u["id"]))
        audit(cur, {"id": u["id"]}, "passwort_gesetzt", u["kunden_id"])
    return {"ok": True}
