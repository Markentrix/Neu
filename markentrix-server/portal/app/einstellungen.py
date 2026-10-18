"""Verschlüsselte Einstellungen (SMTP, API-Schlüssel). Der Schlüssel liegt nur in der .env des Servers."""
import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken

from . import config


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
        return json.loads(_fernet().decrypt(r["wert"].encode()).decode())
    except (InvalidToken, ValueError, RuntimeError):
        return {}


def schreiben(cur, schluessel: str, wert: dict):
    token = _fernet().encrypt(json.dumps(wert).encode()).decode()
    cur.execute("""INSERT INTO portal_einstellungen (schluessel, wert) VALUES (%s,%s)
                   ON CONFLICT (schluessel) DO UPDATE SET wert=EXCLUDED.wert, geaendert_am=now()""", (schluessel, token))
