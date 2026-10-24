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


def _rate_speicher(key: str, maximal: int, fenster: int):
    """Notlösung im Arbeitsspeicher, falls die Datenbank gerade nicht erreichbar ist."""
    jetzt = time.time()
    if len(_versuche) > 5000:   # Speicher begrenzen: leere und alte Einträge entfernen
        for k in [k for k, v in _versuche.items() if not v or v[-1] < jetzt - 3600]:
            _versuche.pop(k, None)
    q = _versuche[key]
    while q and q[0] < jetzt - fenster:
        q.popleft()
    if len(q) >= maximal:
        raise HTTPException(429, "Zu viele Versuche. Bitte in ein paar Minuten erneut probieren.")
    q.append(jetzt)


def rate_limit(key: str, maximal: int = 10, fenster: int = 300):
    """Begrenzt Versuche je Schlüssel auf `maximal` pro Zeitfenster (Sekunden). Der Zähler liegt in der Datenbank (überlebt Neustarts, gilt für alle Prozesse);
    das Fenster beginnt beim ersten Versuch und läuft fest ab."""
    try:
        with tx("system") as cur:
            cur.execute("""INSERT INTO rate_zaehler (schluessel, fenster_start, anzahl) VALUES (%s, now(), 1)
                           ON CONFLICT (schluessel) DO UPDATE SET
                             fenster_start = CASE WHEN rate_zaehler.fenster_start < now() - make_interval(secs => %s) THEN now() ELSE rate_zaehler.fenster_start END,
                             anzahl = CASE WHEN rate_zaehler.fenster_start < now() - make_interval(secs => %s) THEN 1 ELSE rate_zaehler.anzahl + 1 END
                           RETURNING anzahl""", (key[:200], fenster, fenster))
            n = cur.fetchone()["anzahl"]
    except Exception:  # noqa: BLE001 - Datenbank nicht erreichbar: Notlösung im Speicher
        _rate_speicher(key, maximal, fenster)
        return
    if n > maximal:
        raise HTTPException(429, "Zu viele Versuche. Bitte in ein paar Minuten erneut probieren.")


def rate_aufraeumen(cur) -> int:
    """Löscht Zähler, deren Fenster längst vorbei ist (täglicher Job)."""
    cur.execute("DELETE FROM rate_zaehler WHERE fenster_start < now() - interval '2 days'")
    return cur.rowcount


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unbekannt"


def current_user(request: Request) -> dict:
    t = request.cookies.get(COOKIE)
    if not t:
        raise HTTPException(401, "Nicht angemeldet.")
    with tx("system") as cur:
        cur.execute(
            """SELECT b.id, b.email, b.name, b.rolle, b.kunden_id, b.vertriebspartner_id, b.totp_aktiv, b.kunden_rolle, b.admin_rechte, b.website_mitarbeiter_id
               FROM sitzungen s JOIN benutzer b ON b.id = s.benutzer_id
               WHERE s.token_hash = %s AND s.ablauf > now() AND b.aktiv AND (b.zugang_bis IS NULL OR b.zugang_bis >= current_date)
                 AND (b.vertriebspartner_id IS NULL OR NOT EXISTS (SELECT 1 FROM vertriebspartner p WHERE p.id = b.vertriebspartner_id AND p.status = 'beendet'))""",
            (token_hash(t),),
        )
        u = cur.fetchone()
    if not u:
        raise HTTPException(401, "Sitzung abgelaufen.")
    return u


# Bereiche für Mitarbeiter mit eingeschränkten Rechten (admin_rechte NULL = alles)
RECHTE = {"kunden": "Kunden & Projekte", "nachrichten": "Nachrichten", "leads": "Leads & Vertrieb", "finanzen": "Angebote, Rechnungen & Preise", "einstellungen": "Einstellungen & Protokoll"}
_IMMER = {"uebersicht", "heute", "aufgaben", "suche", "textvorlagen", "meine-filter"}
_BEREICH = {"tickets": "nachrichten", "leads": "leads", "gespraeche": "leads", "vertrieb": "leads", "website-check": "leads", "provisionsregeln": "leads",
            "belege": "finanzen", "belege-export.csv": "finanzen", "belege-auswertung": "finanzen", "preise": "finanzen", "konditionen": "finanzen", "katalog": "finanzen", "kennzahlen": "finanzen",
            "kunden": "kunden", "berichte": "kunden", "avv": "kunden", "avv-fehlt": "kunden", "avv-veraltet": "kunden", "avv-vorschlag": "kunden", "avv-vorschau": "kunden", "uav-aenderungen": "kunden", "domains": "kunden", "portal-qr": "kunden", "freigabe-vorlagen": "kunden", "freigabe-kalender": "kunden", "domains-ablauf": "kunden", "onboarding": "kunden", "dateien": "kunden", "websites": "kunden", "vertragsdokumente": "kunden", "umfragen": "kunden", "referenzseite": "kunden",
            "freigaben-kunden": "kunden", "unterlagen": "kunden", "buchungen": "kunden", "paket-buchungen": "kunden", "fruehwarnung": "kunden", "vorlagen": "kunden", "buchungsvorlagen": "kunden", "kunden-ampel": "kunden", "angebote-erinnerung": "leads", "angebote-grund": "leads", "preisanfragen": "leads", "hilfe-rueckmeldungen": "nachrichten", "cockpit": "finanzen", "lastschrift": "finanzen", "mahnvorschlaege": "finanzen", "mahnungen": "finanzen", "angebotsanfragen": "leads", "pipeline": "leads"}


def recht_fuer_pfad(pfad: str) -> str:
    teile = pfad.split("/")
    erst = teile[3] if len(teile) > 3 else ""
    if erst in _IMMER:
        return ""
    return _BEREICH.get(erst, "einstellungen")


_sicherheit_cache = (0.0, {})


def _sicherheit(neu_laden: bool = False) -> dict:
    """Einstellung „sicherheit“ (60 Sekunden zwischengespeichert)."""
    global _sicherheit_cache
    if neu_laden or time.time() - _sicherheit_cache[0] > 60:
        try:
            from . import einstellungen
            with tx("system") as cur:
                _sicherheit_cache = (time.time(), dict(einstellungen.lesen(cur, "sicherheit") or {}))
        except Exception:  # noqa: BLE001
            _sicherheit_cache = (time.time(), {})
    return _sicherheit_cache[1]


def vertrieb_2fa_pflicht(neu_laden: bool = False) -> bool:
    """Ist die Zwei-Faktor-Anmeldung für Vertriebs-Zugänge Pflicht?"""
    return bool(_sicherheit(neu_laden).get("vertrieb_2fa"))


def kunden_2fa_pflicht(neu_laden: bool = False) -> bool:
    """Ist die Zwei-Faktor-Anmeldung für Kunden-Inhaber Pflicht? (Standard aus)"""
    return bool(_sicherheit(neu_laden).get("kunden_2fa"))


def _zwei_faktor_fehlt(user: dict) -> bool:
    from . import config
    if user.get("totp_aktiv"):
        return False
    if user["rolle"] == "admin":
        return bool(config.ADMIN_2FA_PFLICHT)
    if user["rolle"] == "kunde" and user.get("kunden_rolle") == "inhaber":
        return kunden_2fa_pflicht()
    return user["rolle"] == "vertrieb" and vertrieb_2fa_pflicht()


ZWEI_FAKTOR_PFLICHT = "Für Administratoren ist die Zwei-Faktor-Anmeldung Pflicht. Bitte zuerst einrichten."


def require_admin(request: Request, user: dict = Depends(current_user)) -> dict:
    if user["rolle"] != "admin":
        raise HTTPException(403, "Nur für Administratoren.")
    if _zwei_faktor_fehlt(user):
        raise HTTPException(403, ZWEI_FAKTOR_PFLICHT)
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
    if _zwei_faktor_fehlt(user):
        raise HTTPException(403, ZWEI_FAKTOR_PFLICHT)
    return user


# Rolle „Empfang“: nur das Tagesgeschäft (Anfragen, Termine, Nachrichten, Kontakte), kein Geld, keine Verträge, keine Einstellungen
EMPFANG_ERLAUBT = {"start", "status", "startliste", "heute", "anfragen", "termine", "kontakte", "tickets", "profil", "passwort", "logo"}


def require_kunde(request: Request, user: dict = Depends(current_user)) -> dict:
    if user["rolle"] != "kunde" or not user["kunden_id"]:
        raise HTTPException(403, "Nur für Kunden.")
    if _zwei_faktor_fehlt(user):
        raise HTTPException(403, "Für Ihren Zugang ist die Zwei-Faktor-Anmeldung Pflicht. Bitte zuerst einrichten (Konto).")
    if user["kunden_rolle"] == "empfang":
        teile = request.url.path.split("/")      # ["", "api", "kunde", <bereich>, …]
        bereich = teile[3] if len(teile) > 3 else ""
        if bereich not in EMPFANG_ERLAUBT:
            raise HTTPException(403, "Dein Zugang (Empfang) ist nur für Anfragen, Termine und Nachrichten freigegeben.")
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
    if _zwei_faktor_fehlt(user):
        raise HTTPException(403, "Die Zwei-Faktor-Anmeldung ist für Vertriebs-Zugänge Pflicht. Bitte zuerst einrichten (Konto).")
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
