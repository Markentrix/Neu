"""Verschlüsselte Einstellungen (SMTP, API-Schlüssel). Der Schlüssel liegt nur in der .env des Servers."""
import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken

import logging

from . import config

log = logging.getLogger("markentrix.einstellungen")
defekt: set[str] = set()   # Schlüssel, die sich nicht entschlüsseln ließen (falsches PORTAL_SECRET?)


def _fernet() -> Fernet:
    if not config.PORTAL_SECRET:
        raise RuntimeError("PORTAL_SECRET fehlt in der .env")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("mk-einstellungen:" + config.PORTAL_SECRET).encode()).digest()))


def lesen(cur, schluessel: str) -> dict:
    cur.execute("SELECT wert FROM portal_einstellungen WHERE schluessel=%s", (schluessel,))
    r = cur.fetchone()
    if not r:
        return {}
    try:
        wert = json.loads(_fernet().decrypt(r["wert"].encode()).decode())
        defekt.discard(schluessel)
        return wert
    except (InvalidToken, ValueError, RuntimeError):
        if schluessel not in defekt:
            log.error("Einstellung %s lässt sich nicht entschlüsseln – stimmt PORTAL_SECRET noch?", schluessel)
        defekt.add(schluessel)
        return {}


def schreiben(cur, schluessel: str, wert: dict):
    token = _fernet().encrypt(json.dumps(wert).encode()).decode()
    cur.execute("""INSERT INTO portal_einstellungen (schluessel, wert) VALUES (%s,%s)
                   ON CONFLICT (schluessel) DO UPDATE SET wert=EXCLUDED.wert, geaendert_am=now()""", (schluessel, token))


def verschluesseln(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def entschluesseln(token: str | None) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError, RuntimeError):
        return ""
