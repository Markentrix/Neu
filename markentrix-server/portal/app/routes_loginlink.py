"""Anmelden per Link aus einer E-Mail (ohne Passwort) für Kunden und Vertriebler ohne Zwei-Faktor-Anmeldung."""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from . import config, mailer
from .db import tx
from .security import COOKIE, EMAIL_RE, audit, client_ip, new_token, rate_limit, token_hash

router = APIRouter(prefix="/api")
GUELTIG_MINUTEN = 15


class LinkIn(BaseModel):
    email: str = Field(max_length=254)


class EinloesenIn(BaseModel):
    token: str = Field(min_length=10, max_length=100)


@router.post("/login-link")
def anfordern(data: LinkIn, request: Request):
    """Antwortet immer gleich. Konten mit Zwei-Faktor-Anmeldung und Administratoren bekommen keinen Link, dort bleibt das Passwort Pflicht."""
    rate_limit("loginlink:" + client_ip(request), 5, 600)
    antwort = {"ok": True, "hinweis": "Wenn es dazu ein Konto gibt, ist eine E-Mail mit einem Anmelde-Link unterwegs. Er gilt 15 Minuten."}
    email = data.email.strip().lower()
    if not EMAIL_RE.match(email):
        return antwort
    rate_limit("loginlink-mail:" + email, 3, 3600)
    link = None
    with tx("system") as cur:
        cur.execute("""SELECT id FROM benutzer WHERE lower(email)=%s AND aktiv AND passwort_hash IS NOT NULL AND NOT totp_aktiv AND rolle IN ('kunde','vertrieb')""", (email,))
        u = cur.fetchone()
        if u:
            tok = new_token()
            cur.execute("INSERT INTO login_links (token_hash, benutzer_id, ablauf) VALUES (%s,%s, now() + make_interval(mins => %s))", (token_hash(tok), u["id"], GUELTIG_MINUTEN))
            cur.execute("DELETE FROM login_links WHERE ablauf < now() - interval '1 day'")
            audit(cur, {"id": u["id"]}, "login_link_angefordert")
            link = f"{config.BASE_URL}/anmelden?t={tok}"
    if link:
        mailer.senden(email, "Ihr Anmelde-Link für das Markentrix-Portal",
                      f"Guten Tag,\n\nmit diesem Link melden Sie sich einmalig im Portal an (gültig {GUELTIG_MINUTEN} Minuten):\n\n{link}\n\n"
                      "Wenn Sie das nicht angefordert haben, ignorieren Sie diese E-Mail. Es passiert nichts." + mailer.SIGNATUR)
    return antwort


@router.post("/login-link/einloesen")
def einloesen(data: EinloesenIn, request: Request, response: Response):
    """Wird erst durch einen Klick auf der Seite ausgelöst, damit Mail-Scanner den Link nicht verbrauchen."""
    rate_limit("loginlink-einl:" + client_ip(request), 15, 600)
    with tx("system") as cur:
        cur.execute("""UPDATE login_links l SET benutzt_am = now() FROM benutzer b
                       WHERE l.token_hash=%s AND l.benutzt_am IS NULL AND l.ablauf > now() AND b.id = l.benutzer_id AND b.aktiv AND NOT b.totp_aktiv AND b.rolle IN ('kunde','vertrieb')
                       RETURNING b.id, b.rolle, b.kunden_id""", (token_hash(data.token),))
        u = cur.fetchone()
        if not u:
            raise HTTPException(400, "Dieser Link ist abgelaufen oder wurde schon benutzt. Bitte fordern Sie einen neuen an.")
        tok = new_token()
        cur.execute("INSERT INTO sitzungen (token_hash, benutzer_id, ablauf, ip) VALUES (%s,%s,now()+make_interval(hours=>%s),%s)", (token_hash(tok), u["id"], config.SESSION_HOURS, client_ip(request)))
        cur.execute("UPDATE benutzer SET fehlversuche=0, gesperrt_bis=NULL, letzter_login=now() WHERE id=%s", (u["id"],))
        audit(cur, {"id": u["id"]}, "login_per_link", u["kunden_id"])
    response.set_cookie(COOKIE, tok, max_age=config.SESSION_HOURS * 3600, httponly=True, secure=config.COOKIE_SECURE, samesite="lax", path="/")
    return {"rolle": u["rolle"], "ziel": {"vertrieb": "/vertrieb"}.get(u["rolle"], "/app")}
