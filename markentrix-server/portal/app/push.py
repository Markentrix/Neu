"""Web-Push (RFC 8030/8291) mit VAPID (RFC 8292), nur mit der 'cryptography'-Bibliothek.
Nachrichten enthalten bewusst keine Personennamen, weil sie auf dem Sperrbildschirm erscheinen."""
import base64
import json
import logging
import os
import threading
import time
from urllib.parse import urlsplit

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from . import einstellungen
from .db import tx

log = logging.getLogger("push")
KONTAKT = os.environ.get("PUSH_KONTAKT", "mailto:info@markentrix.de")


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def schluessel(cur) -> dict:
    """VAPID-Schlüsselpaar, wird beim ersten Gebrauch erzeugt und verschlüsselt gespeichert."""
    c = einstellungen.lesen(cur, "push")
    if not c.get("privat"):
        priv = ec.generate_private_key(ec.SECP256R1())
        pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
        pub = priv.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        c = {"privat": pem, "public": _b64(pub)}
        einstellungen.schreiben(cur, "push", c)
    return c


def verschluesseln(daten: bytes, p256dh: str, auth: str) -> bytes:
    """aes128gcm-Inhaltskodierung nach RFC 8291, ein Datensatz."""
    ua_pub = _unb64(p256dh)
    auth_secret = _unb64(auth)
    eph = ec.generate_private_key(ec.SECP256R1())
    as_pub = eph.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    gemeinsam = eph.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub))
    ikm = HKDF(hashes.SHA256(), 32, auth_secret, b"WebPush: info\x00" + ua_pub + as_pub).derive(gemeinsam)
    salt = os.urandom(16)
    cek = HKDF(hashes.SHA256(), 16, salt, b"Content-Encoding: aes128gcm\x00").derive(ikm)
    nonce = HKDF(hashes.SHA256(), 12, salt, b"Content-Encoding: nonce\x00").derive(ikm)
    chiffre = AESGCM(cek).encrypt(nonce, daten + b"\x02", None)
    return salt + (4096).to_bytes(4, "big") + bytes([len(as_pub)]) + as_pub + chiffre


def _vapid_kopf(endpoint: str, k: dict) -> str:
    u = urlsplit(endpoint)
    kopf = _b64(json.dumps({"typ": "JWT", "alg": "ES256"}).encode())
    claims = _b64(json.dumps({"aud": f"{u.scheme}://{u.netloc}", "exp": int(time.time()) + 12 * 3600, "sub": KONTAKT}).encode())
    priv = serialization.load_pem_private_key(k["privat"].encode(), None)
    r, s = decode_dss_signature(priv.sign(f"{kopf}.{claims}".encode(), ec.ECDSA(hashes.SHA256())))
    sig = _b64(r.to_bytes(32, "big") + s.to_bytes(32, "big"))
    return f"vapid t={kopf}.{claims}.{sig}, k={k['public']}"


def _senden_an(abo: dict, nutzlast: bytes, k: dict) -> int:
    r = httpx.post(abo["endpoint"], content=verschluesseln(nutzlast, abo["p256dh"], abo["auth"]), timeout=10,
                   headers={"Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream", "TTL": "86400", "Urgency": "normal",
                            "Authorization": _vapid_kopf(abo["endpoint"], k)})
    return r.status_code


def _lauf(benutzer_ids: list, titel: str, text: str, url: str, tag: str | None):
    try:
        if not benutzer_ids:
            return
        nutzlast = json.dumps({"titel": titel, "text": text, "url": url, "tag": tag}).encode()
        with tx("system") as cur:
            k = schluessel(cur)
            cur.execute("SELECT id, endpoint, p256dh, auth FROM push_abos WHERE benutzer_id = ANY(%s::uuid[])", ([str(b) for b in benutzer_ids],))
            abos = cur.fetchall()
        for abo in abos:
            try:
                code = _senden_an(abo, nutzlast, k)
            except Exception as e:                       # Netzwerkfehler: zählen, nicht abbrechen
                log.warning("Push fehlgeschlagen: %s", e)
                code = 0
            with tx("system") as cur:
                if code in (404, 410):
                    cur.execute("DELETE FROM push_abos WHERE id=%s", (abo["id"],))
                elif 200 <= code < 300:
                    cur.execute("UPDATE push_abos SET fehler=0 WHERE id=%s", (abo["id"],))
                else:
                    cur.execute("UPDATE push_abos SET fehler=fehler+1 WHERE id=%s", (abo["id"],))
                    cur.execute("DELETE FROM push_abos WHERE id=%s AND fehler >= 8", (abo["id"],))
    except Exception:
        log.exception("Push-Versand")


def senden(benutzer_ids: list, titel: str, text: str, url: str = "/", tag: str | None = None, sofort: bool = False):
    """Schickt eine Nachricht an alle Geräte der Benutzer. Wirft nie; läuft im Hintergrund."""
    ids = [b for b in benutzer_ids if b]
    if not ids:
        return
    if sofort:
        _lauf(ids, titel, text, url, tag)
    else:
        threading.Thread(target=_lauf, args=(ids, titel, text, url, tag), daemon=True).start()


# ---------------------------------------------------------------- Empfänger
def admins(cur) -> list:
    cur.execute("SELECT id FROM benutzer WHERE rolle='admin' AND aktiv")
    return [r["id"] for r in cur.fetchall()]


def kunde(cur, kid) -> list:
    cur.execute("SELECT id FROM benutzer WHERE rolle='kunde' AND kunden_id=%s AND aktiv", (kid,))
    return [r["id"] for r in cur.fetchall()]


def partner(cur, pid) -> list:
    cur.execute("SELECT id FROM benutzer WHERE rolle='vertrieb' AND vertriebspartner_id=%s AND aktiv", (pid,))
    return [r["id"] for r in cur.fetchall()]
