"""Zwei-Faktor-Anmeldung mit Authenticator-App (TOTP, RFC 6238) ohne Fremdbibliothek, plus Notfallcodes."""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

import segno

from . import einstellungen

SCHRITT = 30


def neues_geheimnis() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _code(geheimnis: str, zaehler: int) -> str:
    key = base64.b32decode(geheimnis + "=" * (-len(geheimnis) % 8))
    mac = hmac.new(key, struct.pack(">Q", zaehler), hashlib.sha1).digest()
    o = mac[-1] & 15
    return "%06d" % ((struct.unpack(">I", mac[o:o + 4])[0] & 0x7FFFFFFF) % 1_000_000)


def pruefen_code(geheimnis: str, code: str, letzter_schritt: int = 0, jetzt: float | None = None) -> int | None:
    """Gibt den Zeitschritt zurück, wenn der Code stimmt (±1 Schritt) und noch nicht benutzt wurde, sonst None."""
    code = "".join(ch for ch in code if ch.isdigit())
    if len(code) != 6:
        return None
    s = int((jetzt if jetzt is not None else time.time()) // SCHRITT)
    for k in (s - 1, s, s + 1):
        if k > letzter_schritt and hmac.compare_digest(_code(geheimnis, k), code):
            return k
    return None


def uri(geheimnis: str, email: str) -> str:
    return f"otpauth://totp/Markentrix:{quote(email)}?secret={geheimnis}&issuer=Markentrix&digits=6&period={SCHRITT}"


def qr(uri_text: str) -> str:
    return segno.make(uri_text, error="m").svg_data_uri(scale=5, border=2)


def _h(c: str) -> str:
    return hashlib.sha256(c.strip().lower().replace("-", "").encode()).hexdigest()


def notfallcodes(n: int = 10) -> tuple[list[str], list[str]]:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    klar = ["".join(secrets.choice(alphabet) for _ in range(5)) + "-" + "".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(n)]
    return klar, [_h(c) for c in klar]


def pruefen_login(u: dict, code: str) -> tuple[bool, dict]:
    """Prüft App-Code oder Notfallcode. Gibt (ok, Änderungen an der DB) zurück."""
    geheimnis = einstellungen.entschluesseln(u.get("totp_secret"))
    if geheimnis:
        k = pruefen_code(geheimnis, code, u.get("totp_letzter_schritt") or 0)
        if k:
            return True, {"totp_letzter_schritt": k}
    h = _h(code)
    rest = list(u.get("totp_recovery") or [])
    if len(code.strip()) >= 10 and h in rest:
        rest.remove(h)
        return True, {"totp_recovery": rest}
    return False, {}
