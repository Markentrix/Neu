import base64
import hashlib
import hmac
import re
import secrets
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

from .db import tx

ITER = 600_000
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
COOKIE = "mk_session"


def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER)
    return "pbkdf2$%d$%s$%s" % (ITER, base64.b64encode(salt).decode(), base64.b64encode(h).decode())


def verify_password(pw: str, stored: str | None) -> bool:
    dummy = "pbkdf2$%d$%s$%s" % (ITER, base64.b64encode(b"x" * 16).decode(), base64.b64encode(b"y" * 32).decode())
    try:
        _, it, salt, h = (stored or dummy).split("$")
        calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), base64.b64decode(salt), int(it))
        return hmac.compare_digest(calc, base64.b64decode(h)) and stored is not None
    except Exception:
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def check_password_rules(pw: str):
    if len(pw) < 10:
        raise HTTPException(400, "Das Passwort muss mindestens 10 Zeichen lang sein.")
    if len(pw) > 200:
        raise HTTPException(400, "Das Passwort ist zu lang.")


# einfache Begrenzung gegen Durchprobieren (pro Adresse)
_versuche: dict[str, deque] = defaultdict(deque)


def rate_limit(key: str, maximal: int = 10, fenster: int = 300):
    jetzt = time.time()
    q = _versuche[key]
    while q and q[0] < jetzt - fenster:
        q.popleft()
    if len(q) >= maximal:
        raise HTTPException(429, "Zu viele Versuche. Bitte in ein paar Minuten erneut probieren.")
    q.append(jetzt)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unbekannt"


def current_user(request: Request) -> dict:
    t = request.cookies.get(COOKIE)
    if not t:
        raise HTTPException(401, "Nicht angemeldet.")
    with tx("system") as cur:
        cur.execute(
            """SELECT b.id, b.email, b.name, b.rolle, b.kunden_id, b.vertriebspartner_id, b.totp_aktiv, b.kunden_rolle, b.admin_rechte
               FROM sitzungen s JOIN benutzer b ON b.id = s.benutzer_id
               WHERE s.token_hash = %s AND s.ablauf > now() AND b.aktiv""",
            (token_hash(t),),
        )
        u = cur.fetchone()
    if not u:
        raise HTTPException(401, "Sitzung abgelaufen.")
    return u


# Bereiche für Mitarbeiter mit eingeschränkten Rechten (admin_rechte NULL = alles)
RECHTE = {"kunden": "Kunden & Projekte", "nachrichten": "Nachrichten", "leads": "Leads & Vertrieb", "finanzen": "Angebote, Rechnungen & Preise", "einstellungen": "Einstellungen & Protokoll"}
_IMMER = {"uebersicht", "heute", "aufgaben"}
_BEREICH = {"tickets": "nachrichten", "leads": "leads", "gespraeche": "leads", "vertrieb": "leads", "website-check": "leads", "provisionsregeln": "leads",
            "belege": "finanzen", "belege-export.csv": "finanzen", "preise": "finanzen", "konditionen": "finanzen", "katalog": "finanzen", "kennzahlen": "finanzen",
            "kunden": "kunden", "berichte": "kunden", "avv": "kunden", "avv-fehlt": "kunden", "onboarding": "kunden", "dateien": "kunden", "websites": "kunden",
            "freigaben-kunden": "kunden", "unterlagen": "kunden", "buchungen": "kunden", "fruehwarnung": "kunden", "vorlagen": "kunden"}


def recht_fuer_pfad(pfad: str) -> str:
    teile = pfad.split("/")
    erst = teile[3] if len(teile) > 3 else ""
    if erst in _IMMER:
        return ""
    return _BEREICH.get(erst, "einstellungen")


def require_admin(request: Request, user: dict = Depends(current_user)) -> dict:
    if user["rolle"] != "admin":
        raise HTTPException(403, "Nur für Administratoren.")
    r = user.get("admin_rechte")
    if r is not None:
        b = recht_fuer_pfad(request.url.path)
        if b and b not in r:
            raise HTTPException(403, "Dafür hast du keine Berechtigung. Bitte wende dich an die Inhaber.")
    return user


def require_voll(user: dict = Depends(current_user)) -> dict:
    """Nur Administratoren ohne Einschränkung (Mitarbeiter anlegen und Rechte vergeben)."""
    if user["rolle"] != "admin" or user.get("admin_rechte") is not None:
        raise HTTPException(403, "Nur für Administratoren mit vollem Zugriff.")
    return user


def require_kunde(request: Request, user: dict = Depends(current_user)) -> dict:
    if user["rolle"] != "kunde" or not user["kunden_id"]:
        raise HTTPException(403, "Nur für Kunden.")
    if user["kunden_rolle"] == "nur_lesen" and request.method not in ("GET", "HEAD"):
        raise HTTPException(403, "Dein Zugang ist nur zum Ansehen freigegeben.")
    return user


def require_inhaber(user: dict = Depends(require_kunde)) -> dict:
    """Team, Rechnungen und Verträge: nur für Inhaber-Zugänge eines Kunden."""
    if user["kunden_rolle"] != "inhaber":
        raise HTTPException(403, "Dafür brauchst du einen Inhaber-Zugang.")
    return user


def require_vertrieb(user: dict = Depends(current_user)) -> dict:
    if user["rolle"] != "vertrieb" or not user["vertriebspartner_id"]:
        raise HTTPException(403, "Nur für Vertriebler.")
    return user


def modul_aktiv(cur, kunden_id, code: str) -> bool:
    cur.execute("SELECT 1 FROM kunden_module WHERE kunden_id=%s AND modul_code=%s AND aktiv", (kunden_id, code))
    return cur.fetchone() is not None


def require_modul(cur, user: dict, code: str):
    if not modul_aktiv(cur, user["kunden_id"], code):
        raise HTTPException(403, "Dieses Modul ist für dein Konto nicht freigeschaltet.")


def audit(cur, user: dict | None, aktion: str, kunden_id=None, details: dict | None = None):
    import json
    cur.execute(
        "INSERT INTO audit_log (benutzer_id, kunden_id, aktion, details) VALUES (%s,%s,%s,%s::jsonb)",
        (user["id"] if user else None, kunden_id, aktion, json.dumps(details or {})),
    )
