"""Web-Push (RFC 8030/8291) mit VAPID (RFC 8292), nur mit der 'cryptography'-Bibliothek.
Nachrichten enthalten bewusst keine Personennamen, weil sie auf dem Sperrbildschirm erscheinen."""
import base64
import json
import logging
import os
import threading
import time
from urllib.parse import urlsplit

import ipaddress
import socket
import urllib.error
import urllib.request
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


# Push-Adressen gehören den Push-Diensten der Browser. Alles andere (eigene Server, interne Adressen) wird weder angenommen noch angerufen.
ERLAUBTE_PUSH_DIENSTE = ("googleapis.com", "push.services.mozilla.com", "notify.windows.com", "push.apple.com", "push.samsungosp.com")


def ziel_erlaubt(endpoint: str, aufloesen: bool = True) -> bool:
    """True, wenn die Adresse https ist, auf einen bekannten Push-Dienst zeigt und (bei aufloesen) nur öffentliche IP-Adressen liefert."""
    from . import config
    if config.PUSH_HTTP_ERLAUBT:      # nur für Tests mit lokalem Gegenstellen-Server
        return True
    try:
        u = urlsplit(endpoint)
        host = (u.hostname or "").lower()
        if u.scheme != "https" or u.username or u.password or u.port not in (None, 443) or not host:
            return False
        if not any(host == d or host.endswith("." + d) for d in ERLAUBTE_PUSH_DIENSTE):
            return False
        if aufloesen:
            for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP):
                ip = ipaddress.ip_address(info[4][0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
                    return False
        return True
    except (ValueError, OSError):
        return False


class _KeineWeiterleitung(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


def _senden_an(abo: dict, nutzlast: bytes, k: dict) -> int:
    if not ziel_erlaubt(abo["endpoint"]):
        return 410                    # wird wie ein abgemeldetes Gerät behandelt und entfernt
    req = urllib.request.Request(abo["endpoint"], data=verschluesseln(nutzlast, abo["p256dh"], abo["auth"]), method="POST",
                                 headers={"Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream", "TTL": "86400", "Urgency": "normal",
                                          "Authorization": _vapid_kopf(abo["endpoint"], k)})
    try:
        with urllib.request.build_opener(_KeineWeiterleitung).open(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _lauf(benutzer_ids: list, titel: str, text: str, url: str, tag: str | None):
    try:
        if not benutzer_ids:
            return
        nutzlast = json.dumps({"titel": titel, "text": text, "url": url, "tag": tag}).encode()
        with tx("system") as cur:
            k = schluessel(cur)
            cur.execute("""SELECT a.id, a.endpoint, a.p256dh, a.auth FROM push_abos a JOIN benutzer b ON b.id = a.benutzer_id
                           WHERE a.benutzer_id = ANY(%s::uuid[]) AND NOT (coalesce(b.ansicht->'push_aus', '[]'::jsonb) @> to_jsonb(%s::text))""",
                        ([str(b) for b in benutzer_ids], tag or ""))
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
    if tag != "test":
        try:                                              # Glocke: jede Meldung bleibt im Posteingang des Benutzers
            with tx("system") as cur:
                cur.executemany("INSERT INTO benachrichtigungen (benutzer_id, tag, titel, text, url) VALUES (%s,%s,%s,%s,%s)", [(i, tag, titel, text, url) for i in ids])
        except Exception:
            log.exception("Benachrichtigung speichern")
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
