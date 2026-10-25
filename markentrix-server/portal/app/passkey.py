"""WebAuthn (Passkeys) ohne Zusatzpakete: minimaler CBOR-Leser, Prüfung von Registrierung und Anmeldung mit `cryptography`.
Unterstützt ES256 (P-256) und RS256, Attestation „none“ und beliebige Formate ohne Prüfung der Hersteller-Kette (wir brauchen nur den Schlüssel).
Ein Passkey mit Gerätesperre (Fingerabdruck, Face-ID, PIN) zählt als zwei Faktoren: besitzen + wissen/sein."""
import base64
import hashlib
import json
import secrets
import struct
from urllib.parse import urlparse

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

from . import config
from .db import tx


class PasskeyFehler(Exception):
    pass


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def unb64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def rp_id() -> str:
    return urlparse(config.BASE_URL).hostname or "localhost"


def origin() -> str:
    u = urlparse(config.BASE_URL)
    return f"{u.scheme}://{u.netloc}"


# ---------------------------------------------------------------- CBOR (nur, was WebAuthn braucht)
def cbor(data: bytes, pos: int = 0):
    """Liest ein CBOR-Element. Gibt (Wert, neue Position) zurück."""
    if pos >= len(data):
        raise PasskeyFehler("Ungültige Antwort des Geräts.")
    ib = data[pos]; pos += 1
    typ, info = ib >> 5, ib & 31
    if info < 24:
        n = info
    elif info in (24, 25, 26, 27):
        ln = {24: 1, 25: 2, 26: 4, 27: 8}[info]
        if pos + ln > len(data):
            raise PasskeyFehler("Ungültige Antwort des Geräts.")
        n = int.from_bytes(data[pos:pos + ln], "big"); pos += ln
    else:
        raise PasskeyFehler("Nicht unterstütztes Format.")
    if typ == 0:
        return n, pos
    if typ == 1:
        return -1 - n, pos
    if typ in (2, 3):
        if pos + n > len(data):
            raise PasskeyFehler("Ungültige Antwort des Geräts.")
        raw = data[pos:pos + n]
        return (raw if typ == 2 else raw.decode("utf8", "replace")), pos + n
    if typ == 4:
        out = []
        for _ in range(n):
            v, pos = cbor(data, pos); out.append(v)
        return out, pos
    if typ == 5:
        out = {}
        for _ in range(n):
            k, pos = cbor(data, pos); v, pos = cbor(data, pos); out[k] = v
        return out, pos
    raise PasskeyFehler("Nicht unterstütztes Format.")


# ---------------------------------------------------------------- Aufforderungen
def neue_aufforderung(art: str, benutzer_id=None) -> str:
    ch = b64u(secrets.token_bytes(32))
    with tx("system") as cur:
        cur.execute("DELETE FROM passkey_challenges WHERE ablauf < now()")
        cur.execute("INSERT INTO passkey_challenges (hash, benutzer_id, art, ablauf) VALUES (%s,%s,%s, now() + interval '5 minutes')",
                    (hashlib.sha256(ch.encode()).hexdigest(), benutzer_id, art))
    return ch


def aufforderung_verbrauchen(ch: str, art: str):
    """Einmalig einlösen. Gibt die benutzer_id (oder None) zurück, wirft bei ungültig/abgelaufen."""
    with tx("system") as cur:
        cur.execute("DELETE FROM passkey_challenges WHERE hash=%s AND art=%s AND ablauf > now() RETURNING benutzer_id", (hashlib.sha256(ch.encode()).hexdigest(), art))
        r = cur.fetchone()
    if not r:
        raise PasskeyFehler("Die Anfrage ist abgelaufen. Bitte noch einmal versuchen.")
    return r["benutzer_id"]


def _client_data(raw_b64: str, typ: str) -> tuple[dict, str]:
    raw = unb64u(raw_b64)
    try:
        cd = json.loads(raw)
    except ValueError:
        raise PasskeyFehler("Ungültige Antwort des Geräts.")
    if cd.get("type") != typ:
        raise PasskeyFehler("Ungültige Antwort des Geräts.")
    if cd.get("origin") != origin():
        raise PasskeyFehler("Diese Anmeldung gehört zu einer anderen Webseite.")
    if cd.get("crossOrigin"):
        raise PasskeyFehler("Ungültige Anmeldung.")
    return cd, hashlib.sha256(raw).hexdigest()


def _auth_data(ad: bytes) -> tuple[int, int]:
    if len(ad) < 37 or ad[:32] != hashlib.sha256(rp_id().encode()).digest():
        raise PasskeyFehler("Diese Anmeldung gehört zu einer anderen Webseite.")
    flags = ad[32]
    if not flags & 0x01:
        raise PasskeyFehler("Bitte das Gerät bestätigen (Fingerabdruck, Gesicht oder PIN).")
    if not flags & 0x04:
        raise PasskeyFehler("Bitte die Gerätesperre benutzen (Fingerabdruck, Gesicht oder PIN).")
    return flags, struct.unpack(">I", ad[33:37])[0]


# ---------------------------------------------------------------- Registrierung
def registrierung_pruefen(client_data_b64: str, attestation_b64: str) -> tuple[bytes, bytes, int, int, str]:
    """Gibt (credential_id, public_key_der, alg, sign_count, challenge) zurück."""
    cd, _ = _client_data(client_data_b64, "webauthn.create")
    att, _p = cbor(unb64u(attestation_b64))
    ad = att.get("authData") if isinstance(att, dict) else None
    if not isinstance(ad, bytes):
        raise PasskeyFehler("Ungültige Antwort des Geräts.")
    flags, zaehler = _auth_data(ad)
    if not flags & 0x40 or len(ad) < 55:
        raise PasskeyFehler("Das Gerät hat keinen Schlüssel geliefert.")
    cid_len = struct.unpack(">H", ad[53:55])[0]
    cid = ad[55:55 + cid_len]
    if len(cid) != cid_len or not cid:
        raise PasskeyFehler("Ungültige Antwort des Geräts.")
    key, _p = cbor(ad, 55 + cid_len)
    alg = key.get(3)
    if key.get(1) == 2 and alg == -7 and key.get(-1) == 1:
        pub = ec.EllipticCurvePublicNumbers(int.from_bytes(key[-2], "big"), int.from_bytes(key[-3], "big"), ec.SECP256R1()).public_key()
    elif key.get(1) == 3 and alg == -257:
        pub = rsa.RSAPublicNumbers(int.from_bytes(key[-2], "big"), int.from_bytes(key[-1], "big")).public_key()
    else:
        raise PasskeyFehler("Dieses Gerät nutzt ein nicht unterstütztes Schlüsselformat.")
    der = pub.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return cid, der, alg, zaehler, cd["challenge"]


# ---------------------------------------------------------------- Anmeldung
def anmeldung_pruefen(passkey: dict, client_data_b64: str, auth_data_b64: str, signatur_b64: str) -> tuple[int, str]:
    """Prüft Signatur und Zähler. Gibt (neuer Zähler, challenge) zurück."""
    cd, _ = _client_data(client_data_b64, "webauthn.get")
    ad = unb64u(auth_data_b64)
    _flags, zaehler = _auth_data(ad)
    signiert = ad + hashlib.sha256(unb64u(client_data_b64)).digest()
    pub = serialization.load_der_public_key(bytes(passkey["public_key"]))
    try:
        if passkey["alg"] == -7:
            pub.verify(unb64u(signatur_b64), signiert, ec.ECDSA(hashes.SHA256()))
        else:
            pub.verify(unb64u(signatur_b64), signiert, padding.PKCS1v15(), hashes.SHA256())
    except (InvalidSignature, ValueError):
        raise PasskeyFehler("Die Anmeldung konnte nicht bestätigt werden.")
    if (zaehler or passkey["sign_count"]) and zaehler <= passkey["sign_count"]:
        raise PasskeyFehler("Dieser Passkey wurde möglicherweise kopiert und wird abgelehnt. Bitte einen neuen einrichten.")
    return zaehler, cd["challenge"]
